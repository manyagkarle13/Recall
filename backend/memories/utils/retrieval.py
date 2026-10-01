"""
Retrieval and Hybrid Ranking Engine for Recall.
Combines dense vector similarity search (pgvector cosine distance)
with PostgreSQL full-text keyword search using weighted score fusion
and Reciprocal Rank Fusion (RRF).
"""

import logging
from typing import List, Dict, Any, Optional
from django.db import connection
from django.conf import settings
from memories.models import MemoryItem
from memories.utils.embedding import get_embedding

logger = logging.getLogger(__name__)

# Check if pgvector is available
try:
    from pgvector.django import CosineDistance
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

# Check if postgres full-text search is available
try:
    from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
    HAS_POSTGRES_SEARCH = True
except ImportError:
    HAS_POSTGRES_SEARCH = False


def vector_search(
    query_vector: List[float],
    top_k: int = 20,
    queryset = None
) -> List[Dict[str, Any]]:
    """
    Performs cosine similarity search using pgvector.
    Cosine distance in pgvector is (1 - cosine_similarity).
    Returns list of dicts with memory details and normalized vector_score in [0, 1].
    """
    if queryset is None:
        queryset = MemoryItem.objects.filter(embedding__isnull=False)
    else:
        queryset = queryset.filter(embedding__isnull=False)

    results = []

    if HAS_PGVECTOR:
        try:
            # CosineDistance: 0 means identical, 2 means opposite directions
            items = (
                queryset.annotate(distance=CosineDistance('embedding', query_vector))
                .order_by('distance')[:top_k]
            )
            for item in items:
                # Convert cosine distance into [0, 1] cosine similarity
                cos_sim = max(0.0, min(1.0, 1.0 - (float(item.distance) / 2.0)))
                meta = item.metadata or {}
                results.append({
                    'id': str(item.id),
                    'source_type': item.source_type,
                    'title': item.title,
                    'raw_content': item.raw_content,
                    'source_url': item.source_url,
                    'created_at': item.created_at.isoformat() if hasattr(item.created_at, 'isoformat') else str(item.created_at),
                    'vector_score': round(cos_sim, 5),
                    'metadata': meta,
                    'media_url': meta.get('media_url', ''),
                    'raw_item': item
                })
            return results
        except Exception as e:
            logger.warning(f"pgvector query failed or not active, falling back to python cosine sim: {e}")

    # Fallback in-memory cosine similarity (e.g. for sqlite/mock testing)
    import numpy as np
    q_vec = np.array(query_vector, dtype=np.float32)
    norm_q = np.linalg.norm(q_vec)
    if norm_q > 0:
        q_vec = q_vec / norm_q

    scored_items = []
    for item in queryset:
        if item.embedding is not None:
            emb = np.array(item.embedding, dtype=np.float32)
            norm_e = np.linalg.norm(emb)
            if norm_e > 0:
                emb = emb / norm_e
            sim = float(np.dot(q_vec, emb))
            norm_sim = max(0.0, min(1.0, (sim + 1.0) / 2.0))
            scored_items.append((norm_sim, item))

    scored_items.sort(key=lambda x: x[0], reverse=True)
    for score, item in scored_items[:top_k]:
        meta = item.metadata or {}
        results.append({
            'id': str(item.id),
            'source_type': item.source_type,
            'title': item.title,
            'raw_content': item.raw_content,
            'source_url': item.source_url,
            'created_at': item.created_at.isoformat() if hasattr(item.created_at, 'isoformat') else str(item.created_at),
            'vector_score': round(score, 5),
            'metadata': meta,
            'media_url': meta.get('media_url', ''),
            'raw_item': item
        })
    return results


def keyword_search(
    query: str,
    top_k: int = 20,
    queryset = None
) -> List[Dict[str, Any]]:
    """
    Performs full-text keyword search.
    Prefers PostgreSQL full-text search (SearchVector + SearchRank),
    with graceful fallback to token overlap scoring.
    """
    if queryset is None:
        queryset = MemoryItem.objects.all()

    query_clean = query.strip()
    if not query_clean:
        return []

    results = []

    # Attempt PostgreSQL full-text search
    if HAS_POSTGRES_SEARCH and connection.vendor == 'postgresql':
        try:
            search_vector = SearchVector('title', weight='A') + SearchVector('raw_content', weight='B')
            search_query = SearchQuery(query_clean)
            items = (
                queryset.annotate(rank=SearchRank(search_vector, search_query))
                .filter(rank__gt=0.001)
                .order_by('-rank')[:top_k]
            )
            items_list = list(items)
            max_rank = max([float(item.rank) for item in items_list], default=1.0)
            if max_rank <= 0:
                max_rank = 1.0

            for item in items_list:
                norm_score = min(1.0, float(item.rank) / max_rank)
                meta = item.metadata or {}
                results.append({
                    'id': str(item.id),
                    'source_type': item.source_type,
                    'title': item.title,
                    'raw_content': item.raw_content,
                    'source_url': item.source_url,
                    'created_at': item.created_at.isoformat() if hasattr(item.created_at, 'isoformat') else str(item.created_at),
                    'keyword_score': round(norm_score, 5),
                    'metadata': meta,
                    'media_url': meta.get('media_url', ''),
                    'raw_item': item
                })
            return results
        except Exception as e:
            logger.warning(f"Postgres full-text search failed, using fallback keyword matcher: {e}")

    # Fallback keyword overlap scoring
    terms = set(query_clean.lower().split())
    scored_items = []

    for item in queryset:
        title_lower = (item.title or '').lower()
        content_lower = (item.raw_content or '').lower()
        
        matches = 0.0
        for t in terms:
            if t in title_lower:
                matches += 2.0  # title weight boost
            elif t in content_lower:
                matches += 1.0

        if matches > 0:
            scored_items.append((matches, item))

    scored_items.sort(key=lambda x: x[0], reverse=True)
    max_m = scored_items[0][0] if scored_items else 1.0

    for score, item in scored_items[:top_k]:
        meta = item.metadata or {}
        norm_score = min(1.0, score / max_m)
        results.append({
            'id': str(item.id),
            'source_type': item.source_type,
            'title': item.title,
            'raw_content': item.raw_content,
            'source_url': item.source_url,
            'created_at': item.created_at.isoformat() if hasattr(item.created_at, 'isoformat') else str(item.created_at),
            'keyword_score': round(norm_score, 5),
            'metadata': meta,
            'media_url': meta.get('media_url', ''),
            'raw_item': item
        })
    return results


def hybrid_search(
    query: str,
    top_k: int = 5,
    alpha: float = 0.6,
    queryset = None
) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval merging Dense Vector search and Keyword search.
    Weighted formula:
        score = alpha * vector_score + (1 - alpha) * keyword_score
    Also records Reciprocal Rank Fusion (RRF) rank score.
    """
    query_vector = get_embedding(query)

    pool_size = max(top_k * 4, 30)
    vec_results = vector_search(query_vector, top_k=pool_size, queryset=queryset)
    kw_results = keyword_search(query, top_k=pool_size, queryset=queryset)

    candidates: Dict[str, Dict[str, Any]] = {}
    RRF_K = 60.0

    for rank, item in enumerate(vec_results):
        item_id = item['id']
        candidates[item_id] = {
            'id': item_id,
            'source_type': item['source_type'],
            'title': item['title'],
            'raw_content': item['raw_content'],
            'source_url': item['source_url'],
            'created_at': item['created_at'],
            'metadata': item.get('metadata', {}),
            'media_url': item.get('media_url', ''),
            'vector_score': item['vector_score'],
            'keyword_score': 0.0,
            'vec_rank': rank + 1,
            'kw_rank': None
        }

    for rank, item in enumerate(kw_results):
        item_id = item['id']
        if item_id in candidates:
            candidates[item_id]['keyword_score'] = item['keyword_score']
            candidates[item_id]['kw_rank'] = rank + 1
        else:
            candidates[item_id] = {
                'id': item_id,
                'source_type': item['source_type'],
                'title': item['title'],
                'raw_content': item['raw_content'],
                'source_url': item['source_url'],
                'created_at': item['created_at'],
                'metadata': item.get('metadata', {}),
                'media_url': item.get('media_url', ''),
                'vector_score': 0.0,
                'keyword_score': item['keyword_score'],
                'vec_rank': None,
                'kw_rank': rank + 1
            }

    scored_list = []
    for cid, cand in candidates.items():
        v_score = cand['vector_score']
        k_score = cand['keyword_score']
        
        hybrid_score = (alpha * v_score) + ((1.0 - alpha) * k_score)
        
        rrf_vec = 1.0 / (RRF_K + cand['vec_rank']) if cand['vec_rank'] else 0.0
        rrf_kw = 1.0 / (RRF_K + cand['kw_rank']) if cand['kw_rank'] else 0.0
        rrf_score = rrf_vec + rrf_kw

        cand['hybrid_score'] = round(hybrid_score, 5)
        cand['rrf_score'] = round(rrf_score, 5)
        scored_list.append(cand)

    scored_list.sort(key=lambda x: x['hybrid_score'], reverse=True)
    return scored_list[:top_k]


def search_memories(
    query: str,
    top_k: int = 5,
    alpha: float = 0.6,
    mode: str = 'hybrid',
    queryset = None
) -> List[Dict[str, Any]]:
    """
    Unified search dispatcher.
    mode: 'hybrid' | 'vector' | 'keyword'
    """
    if mode == 'vector':
        q_vec = get_embedding(query)
        results = vector_search(q_vec, top_k=top_k, queryset=queryset)
        for r in results:
            r['hybrid_score'] = r['vector_score']
            r['keyword_score'] = 0.0
            r.pop('raw_item', None)
        return results
    elif mode == 'keyword':
        results = keyword_search(query, top_k=top_k, queryset=queryset)
        for r in results:
            r['hybrid_score'] = r['keyword_score']
            r['vector_score'] = 0.0
            r.pop('raw_item', None)
        return results
    else:  # hybrid
        results = hybrid_search(query, top_k=top_k, alpha=alpha, queryset=queryset)
        for r in results:
            r.pop('vec_rank', None)
            r.pop('kw_rank', None)
        return results
