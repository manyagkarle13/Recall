import uuid
import logging
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from .models import MemoryItem
from .serializers import (
    MemoryItemSerializer,
    MemoryItemDetailSerializer,
    MemoryCreateRequestSerializer,
    ScreenshotCreateSerializer,
    SearchRequestSerializer,
    AskRequestSerializer,
    RegisterSerializer,
    LoginSerializer,
)
from .utils.chunking import chunk_text, count_tokens
from .utils.embedding import get_embedding, get_embeddings_batch
from .utils.file_parser import extract_content_from_file
from .utils.retrieval import search_memories
from .utils.llm import synthesize_answer
from .utils.ocr import extract_text_from_screenshot

logger = logging.getLogger(__name__)


class MemoryPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


def user_payload(user):
    return {"id": user.id, "username": user.username, "email": user.email}


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, token = serializer.save()
        if not MemoryItem.objects.filter(owner__isnull=False).exists():
            MemoryItem.objects.filter(owner__isnull=True).update(owner=user)
        return Response({"token": token.key, "user": user_payload(user)}, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"token": serializer.validated_data["token"], "user": user_payload(serializer.validated_data["user"])})


class MeAPIView(APIView):
    def get(self, request):
        return Response(user_payload(request.user))


class MemoryListCreateAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    pagination_class = MemoryPagination

    def get(self, request):
        queryset = MemoryItem.objects.filter(owner=request.user)

        source_type = request.query_params.get("source_type")
        if source_type:
            queryset = queryset.filter(source_type=source_type)

        q = request.query_params.get("q")
        if q:
            queryset = queryset.filter(raw_content__icontains=q) | queryset.filter(title__icontains=q)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        serializer = MemoryItemSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = MemoryCreateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        title = data.get("title", "").strip()
        raw_content = data.get("raw_content", "").strip()
        source_type = data.get("source_type", "text")
        source_url = data.get("source_url", None)
        uploaded_file = data.get("file", None)

        metadata = {}

        if uploaded_file:
            extracted_text, inferred_type, file_meta = extract_content_from_file(
                uploaded_file, uploaded_file.name
            )
            raw_content = extracted_text
            metadata.update(file_meta)
            if not title:
                title = uploaded_file.name
            if source_type == "text" and inferred_type != "text":
                source_type = inferred_type

        if not title:
            first_line = raw_content.split("\n")[0].strip()
            title = (first_line[:60] + "...") if len(first_line) > 60 else (first_line or "Untitled Memory")

        total_tokens = count_tokens(raw_content)
        metadata["total_tokens"] = total_tokens

        chunks = chunk_text(raw_content, max_tokens=500, overlap_tokens=50)

        try:
            if len(chunks) <= 1:
                emb = get_embedding(raw_content)
                memory = MemoryItem.objects.create(
                    owner=request.user,
                    source_type=source_type,
                    title=title,
                    raw_content=raw_content,
                    source_url=source_url,
                    embedding=emb,
                    chunk_index=0,
                    parent_id=None,
                    metadata=metadata,
                )
                return Response(
                    MemoryItemSerializer(memory).data,
                    status=status.HTTP_201_CREATED,
                )
            else:
                parent_id = uuid.uuid4()
                chunk_texts = [c[1] for c in chunks]
                embeddings = get_embeddings_batch(chunk_texts)

                created_items = []
                for i, (idx, chunk_body, tok_count) in enumerate(chunks):
                    chunk_meta = dict(metadata)
                    chunk_meta["chunk_tokens"] = tok_count
                    chunk_meta["total_chunks"] = len(chunks)

                    item = MemoryItem(
                        owner=request.user,
                        source_type=source_type,
                        title=f"{title} (Part {i+1}/{len(chunks)})",
                        raw_content=chunk_body,
                        source_url=source_url,
                        embedding=embeddings[i],
                        chunk_index=idx,
                        parent_id=parent_id,
                        metadata=chunk_meta,
                    )
                    created_items.append(item)

                saved_memories = MemoryItem.objects.bulk_create(created_items)
                
                return Response(
                    {
                        "message": f"Successfully ingested and split document into {len(saved_memories)} chunks.",
                        "parent_id": str(parent_id),
                        "chunks_count": len(saved_memories),
                        "chunks": MemoryItemSerializer(saved_memories, many=True).data,
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            logger.exception("Failed to generate embedding or save memory")
            return Response(
                {"error": "Failed to process memory", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ScreenshotMemoryCreateAPIView(APIView):
    """
    Phase 7 Screenshot Capture Endpoint.
    POST /api/memories/screenshot/
    Payload:
        - image_base64: str (base64 PNG from chrome.tabs.captureVisibleTab)
        - title: str (optional)
        - source_url: str (optional)
    Extracts text via pytesseract OCR, generates 384-d fine-tuned embedding,
    and stores alongside text memories with source_type='screenshot'.
    """
    parser_classes = [JSONParser]

    def post(self, request):
        serializer = ScreenshotCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        image_base64 = data["image_base64"]
        title = data.get("title", "").strip() or "Screenshot Capture"
        source_url = data.get("source_url", "")

        try:
            # 1. Run OCR on Screenshot
            extracted_text, ocr_metadata = extract_text_from_screenshot(
                image_data=image_base64,
                filename=f"{title}.png",
            )
            ocr_metadata["capture_type"] = "chrome_captureVisibleTab"

            # 2. Chunk text if > 500 tokens
            chunks = chunk_text(extracted_text, max_tokens=500, overlap_tokens=50)

            # 3. Vectorize and save in shared vector space
            if len(chunks) <= 1:
                emb = get_embedding(extracted_text)
                memory = MemoryItem.objects.create(
                    owner=request.user,
                    source_type="screenshot",
                    title=title,
                    raw_content=extracted_text,
                    source_url=source_url,
                    embedding=emb,
                    chunk_index=0,
                    parent_id=None,
                    metadata=ocr_metadata,
                )
                return Response(
                    {
                        "message": "Screenshot captured, text extracted via OCR, and stored in vector space.",
                        "memory": MemoryItemSerializer(memory).data,
                        "ocr_preview": extracted_text[:200],
                    },
                    status=status.HTTP_201_CREATED,
                )
            else:
                parent_id = uuid.uuid4()
                chunk_texts = [c[1] for c in chunks]
                embeddings = get_embeddings_batch(chunk_texts)

                created_items = []
                for i, (idx, chunk_body, tok_count) in enumerate(chunks):
                    meta = dict(ocr_metadata)
                    meta["chunk_tokens"] = tok_count
                    meta["total_chunks"] = len(chunks)

                    item = MemoryItem(
                        owner=request.user,
                        source_type="screenshot",
                        title=f"{title} [OCR Part {i+1}/{len(chunks)}]",
                        raw_content=chunk_body,
                        source_url=source_url,
                        embedding=embeddings[i],
                        chunk_index=idx,
                        parent_id=parent_id,
                        metadata=meta,
                    )
                    created_items.append(item)

                saved_memories = MemoryItem.objects.bulk_create(created_items)
                return Response(
                    {
                        "message": f"Screenshot OCR text split into {len(saved_memories)} chunks & embedded.",
                        "parent_id": str(parent_id),
                        "chunks_count": len(saved_memories),
                        "chunks": MemoryItemSerializer(saved_memories, many=True).data,
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            logger.exception("Error processing screenshot capture")
            return Response(
                {"error": "Failed to process screenshot memory", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MemoryDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return MemoryItem.objects.get(pk=pk, owner=self.request.user)
        except MemoryItem.DoesNotExist:
            return None

    def get(self, request, pk):
        memory = self.get_object(pk)
        if memory is None:
            return Response({"error": "Memory item not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = MemoryItemDetailSerializer(memory)
        return Response(serializer.data)

    def delete(self, request, pk):
        memory = self.get_object(pk)
        if memory is None:
            return Response({"error": "Memory item not found"}, status=status.HTTP_404_NOT_FOUND)
        memory.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SearchAPIView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request):
        serializer = SearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        query = data["query"]
        top_k = data.get("top_k", 5)
        alpha = data.get("alpha", 0.6)
        mode = data.get("mode", "hybrid")
        source_type = data.get("source_type")
        threshold = data.get("threshold", 0.45)

        queryset = MemoryItem.objects.filter(owner=request.user)
        if source_type:
            queryset = queryset.filter(source_type=source_type)

        try:
            results = search_memories(
                query=query,
                top_k=top_k,
                alpha=alpha,
                mode=mode,
                queryset=queryset,
            )
            results = [
                result
                for result in results
                if result.get("hybrid_score", 0.0) >= threshold
            ]
            serialized_by_id = {
                str(item.id): item
                for item in queryset.filter(id__in=[result["id"] for result in results])
            }
            for result in results:
                item = serialized_by_id.get(result["id"])
                if item:
                    result["metadata"] = item.metadata or {}
                    result["media_url"] = (item.metadata or {}).get("media_url", "")
            return Response(
                {
                    "query": query,
                    "mode": mode,
                    "alpha": alpha,
                    "threshold": threshold,
                    "count": len(results),
                    "results": results,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception("Error executing search")
            return Response(
                {"error": "Search failed", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AskAPIView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request):
        serializer = AskRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        question = data["question"]
        top_k = data.get("top_k", 5)
        threshold = data.get("threshold", 0.45)
        alpha = data.get("alpha", 0.6)
        mode = data.get("mode", "hybrid")
        preferred_model = data.get("model", None)

        try:
            memories = search_memories(
                query=question,
                top_k=top_k,
                alpha=alpha,
                mode=mode,
                queryset=MemoryItem.objects.filter(owner=request.user),
            )

            synthesis_result = synthesize_answer(
                question=question,
                memories=memories,
                threshold=threshold,
                preferred_model=preferred_model,
            )

            return Response(
                {
                    "question": question,
                    "answer": synthesis_result["answer"],
                    "has_relevant_memories": synthesis_result["has_relevant_memories"],
                    "top_score": synthesis_result["top_score"],
                    "threshold": synthesis_result["threshold"],
                    "citations": synthesis_result["citations"],
                    "model": synthesis_result["model"],
                    "retrieved_count": len(memories),
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.exception("Error during /api/ask/ execution")
            return Response(
                {"error": "Failed to synthesize answer", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
