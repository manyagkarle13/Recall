"""
Evaluation Metrics for Retrieval Systems.
Computes Recall@K (e.g. Recall@1, Recall@5) and Mean Reciprocal Rank (MRR).
Used to evaluate base pretrained vs fine-tuned models.
"""

from typing import List, Set, Dict, Any


def compute_recall_at_k(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int = 5) -> float:
    """
    Computes Recall@K:
    Returns 1.0 if at least one relevant ground truth item is present in top K retrieved items, else 0.0.
    (Binary hit rate at K standard in QA retrieval).
    """
    if not ground_truth_ids:
        return 0.0
    top_k_retrieved = set(retrieved_ids[:k])
    hit = bool(top_k_retrieved.intersection(ground_truth_ids))
    return 1.0 if hit else 0.0


def compute_reciprocal_rank(retrieved_ids: List[str], ground_truth_ids: Set[str]) -> float:
    """
    Computes Reciprocal Rank (RR):
    Returns 1 / rank of the first relevant document found (1-indexed).
    Returns 0.0 if no relevant document appears in the retrieved list.
    """
    if not ground_truth_ids:
        return 0.0
    for rank_idx, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in ground_truth_ids:
            return 1.0 / float(rank_idx)
    return 0.0


def evaluate_retrieval_run(
    queries: List[Dict[str, Any]],
    search_fn,
    k_values: List[int] = [1, 5],
    max_candidates: int = 20,
) -> Dict[str, Any]:
    """
    Runs full evaluation over queries using provided search_fn(query, top_k) -> List[doc_id].
    Returns average Recall@K for each K in k_values, MRR, and per-query breakdown.
    """
    recalls = {k: [] for k in k_values}
    reciprocal_ranks = []
    per_query_details = []

    for item in queries:
        qid = item.get("query_id", "")
        query_text = item["query"]
        ground_truth = set(item["expected_memory_ids"])

        retrieved_ids = search_fn(query_text, top_k=max_candidates)

        rr = compute_reciprocal_rank(retrieved_ids, ground_truth)
        reciprocal_ranks.append(rr)

        query_recalls = {}
        for k in k_values:
            r_k = compute_recall_at_k(retrieved_ids, ground_truth, k=k)
            recalls[k].append(r_k)
            query_recalls[f"recall@{k}"] = r_k

        per_query_details.append({
            "query_id": qid,
            "query": query_text,
            "expected_ids": list(ground_truth),
            "retrieved_ids": retrieved_ids[:max(k_values)],
            "reciprocal_rank": round(rr, 4),
            **query_recalls,
        })

    summary = {
        "num_queries": len(queries),
        "mrr": round(sum(reciprocal_ranks) / len(reciprocal_ranks), 4) if reciprocal_ranks else 0.0,
    }
    for k in k_values:
        avg_r = sum(recalls[k]) / len(recalls[k]) if recalls[k] else 0.0
        summary[f"recall@{k}"] = round(avg_r, 4)

    return {
        "summary": summary,
        "per_query": per_query_details,
    }
