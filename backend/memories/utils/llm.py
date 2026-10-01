"""
LLM Answer Synthesis Layer for Recall.
Uses Groq LPU inference for low-latency generation.
Features:
- Prompt token truncation to prevent Groq HTTP 413 errors
- Similarity threshold filtering (only cites memories above threshold)
- Automatic fallback cascade across active models
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

curr_file_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(curr_file_dir, "..", ".."))
load_dotenv(os.path.join(backend_dir, ".env"))

SYSTEM_PROMPT_TEMPLATE = """You are Recall, a personal AI memory assistant.
Synthesize a concise, direct answer based STRICTLY and ONLY on the provided memory context.
Cite sources using bracketed citations like [Memory Title] or [1].
If the provided context does not contain enough information to answer the question, state:
"I couldn't find anything relevant in your saved memories."
Do NOT hallucinate or assume facts not present in the context."""


def format_memories_context(memories: List[Dict[str, Any]], max_chars_per_memory: int = 1500) -> str:
    """Formats retrieved memories into structured prompt context with character limits."""
    context_blocks = []
    for idx, mem in enumerate(memories):
        title = mem.get("title") or "Untitled Memory"
        raw_content = mem.get("raw_content", "").strip()
        # Truncate content to avoid exceeding Groq TPM / ITPM limits
        if len(raw_content) > max_chars_per_memory:
            content_snippet = raw_content[:max_chars_per_memory] + "... [truncated]"
        else:
            content_snippet = raw_content
        
        source_type = mem.get("source_type", "note")
        score = mem.get("score") or mem.get("hybrid_score") or mem.get("vector_score") or 0.0

        block = (
            f"--- MEMORY [{idx + 1}]: {title} (Type: {source_type}, Match: {round(score * 100)}%) ---\n"
            f"{content_snippet}\n"
        )
        context_blocks.append(block)

    return "\n".join(context_blocks)


def synthesize_answer(
    question: str,
    memories: Optional[List[Dict[str, Any]]] = None,
    retrieved_memories: Optional[List[Dict[str, Any]]] = None,
    threshold: float = 0.45,
    preferred_model: Optional[str] = None,
) -> Dict[str, Any]:
    """Synthesizes answer using Groq with token limits and similarity guardrails."""
    retrieved_memories = memories if memories is not None else (retrieved_memories or [])
    # Filter memories strictly by threshold
    valid_memories = [
        m for m in retrieved_memories
        if (m.get("score") or m.get("hybrid_score") or m.get("vector_score") or 0.0) >= threshold
    ]

    if not valid_memories:
        return {
            "question": question,
            "answer": f"I couldn't find anything relevant to '{question}' in your saved memories.",
            "has_relevant_memories": False,
            "top_score": (retrieved_memories[0].get("score", 0.0) if retrieved_memories else 0.0),
            "threshold": threshold,
            "citations": [],
            "model": "guardrail-filter",
            "retrieved_count": 0,
        }

    # Use at most top 3 memories to keep token count compact
    prompt_memories = valid_memories[:3]
    top_score = prompt_memories[0].get("score") or prompt_memories[0].get("hybrid_score") or prompt_memories[0].get("vector_score") or 0.0
    context_str = format_memories_context(prompt_memories, max_chars_per_memory=1500)

    user_prompt = f"""RETRIEVED MEMORY CONTEXT:
{context_str}

USER QUESTION:
{question}

Please answer the question based only on the retrieved memories above."""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {
            "question": question,
            "answer": f"Based on your saved memory '{prompt_memories[0].get('title')}', relevant information was retrieved.",
            "has_relevant_memories": True,
            "top_score": top_score,
            "threshold": threshold,
            "citations": _build_citations(prompt_memories),
            "model": "mock-simulator",
            "retrieved_count": len(prompt_memories),
        }

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        candidate_models = [
            preferred_model,
            "qwen/qwen3.8-27b",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "groq/compound",
        ]
        candidate_models = [m for m in candidate_models if m]

        chosen_model = None
        completion_text = None

        for model_name in candidate_models:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=600,
                )
                completion_text = response.choices[0].message.content
                chosen_model = model_name
                break
            except Exception as model_err:
                logger.warning(f"Groq model {model_name} failed: {model_err}. Trying fallback...")
                continue

        if not completion_text:
            raise RuntimeError("All Groq candidate models failed to return a response.")

        return {
            "question": question,
            "answer": completion_text.strip(),
            "has_relevant_memories": True,
            "top_score": top_score,
            "threshold": threshold,
            "citations": _build_citations(prompt_memories),
            "model": f"groq/{chosen_model}",
            "retrieved_count": len(prompt_memories),
        }

    except Exception as e:
        logger.exception("Error during Groq synthesis")
        return {
            "question": question,
            "answer": f"Error during synthesis: {str(e)}",
            "has_relevant_memories": False,
            "top_score": top_score,
            "threshold": threshold,
            "citations": _build_citations(prompt_memories),
            "model": "error",
            "retrieved_count": len(prompt_memories),
        }


def _build_citations(memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    citations = []
    for mem in memories:
        score = mem.get("score") or mem.get("hybrid_score") or mem.get("vector_score") or 0.0
        meta = mem.get("metadata") or {}
        media_url = mem.get("media_url") or meta.get("media_url") or ""
        created_at = mem.get("created_at") or ""
        citations.append({
            "id": str(mem.get("id")),
            "title": mem.get("title") or "Untitled Memory",
            "source_type": mem.get("source_type", "text"),
            "source_url": mem.get("source_url", ""),
            "media_url": media_url,
            "raw_content": mem.get("raw_content", ""),
            "created_at": created_at,
            "metadata": meta,
            "score": round(score, 5),
        })
    return citations
