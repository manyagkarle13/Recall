"""
Evaluation Script for the Base Pretrained Model (all-MiniLM-L6-v2).
Computes Recall@1, Recall@5, and MRR across Vector, Keyword, and Hybrid Search.
Saves results to ml/results/baseline_metrics.json and ml/results/baseline_metrics.md
to establish the 'before' baseline for Phase 3 deep learning comparison.
"""

import os
import json
import sys
import numpy as np
from datetime import datetime

# Add paths for standalone execution
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_DIR = os.path.dirname(ML_DIR)
BACKEND_DIR = os.path.join(PROJECT_DIR, "backend")

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from eval_metrics import compute_recall_at_k, compute_reciprocal_rank


def run_baseline_evaluation():
    dataset_path = os.path.join(CURRENT_DIR, "eval_dataset.json")
    if not os.path.exists(dataset_path):
        print(f"Error: dataset file not found at {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    memories = data["memories"]
    queries = data["queries"]

    print("=" * 70)
    print("RECALL BENCHMARK: BASE PRETRAINED MODEL (all-MiniLM-L6-v2)")
    print(f"Loaded {len(memories)} benchmark memories and {len(queries)} test queries.")
    print("=" * 70)

    # 1. Load base embedding model
    print("Loading base pretrained model: 'all-MiniLM-L6-v2'...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # 2. Compute embeddings for all memories
    print("Computing base embeddings for memories...")
    mem_texts = [m["raw_content"] for m in memories]
    mem_embeddings = model.encode(mem_texts, normalize_embeddings=True, show_progress_bar=False)
    mem_ids = [m["id"] for m in memories]

    # Compute query embeddings
    q_texts = [q["query"] for q in queries]
    q_embeddings = model.encode(q_texts, normalize_embeddings=True, show_progress_bar=False)

    # 3. Define retrieval methods
    def vector_retrieve(q_idx: int, top_k: int = 10):
        q_vec = q_embeddings[q_idx]
        sims = np.dot(mem_embeddings, q_vec)
        ranked_indices = np.argsort(-sims)[:top_k]
        return [mem_ids[i] for i in ranked_indices], [float(sims[i]) for i in ranked_indices]

    def keyword_retrieve(query_text: str, top_k: int = 10):
        terms = set(query_text.lower().split())
        scored = []
        for i, m in enumerate(memories):
            t_lower = (m.get("title") or "").lower()
            c_lower = m["raw_content"].lower()
            score = 0.0
            for t in terms:
                if t in t_lower:
                    score += 2.0
                elif t in c_lower:
                    score += 1.0
            scored.append((score, mem_ids[i]))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    def hybrid_retrieve(q_idx: int, query_text: str, alpha: float = 0.6, top_k: int = 10):
        vec_retrieved, vec_sims = vector_retrieve(q_idx, top_k=20)
        kw_retrieved = keyword_retrieve(query_text, top_k=20)

        # Normalize vector scores
        cand_scores = {}
        for rank, (mid, score) in enumerate(zip(vec_retrieved, vec_sims)):
            norm_v = max(0.0, min(1.0, (score + 1.0) / 2.0))
            cand_scores[mid] = {"vector": norm_v, "keyword": 0.0}

        # Normalize keyword scores
        terms = set(query_text.lower().split())
        for mid in kw_retrieved:
            mem = next(m for m in memories if m["id"] == mid)
            c_score = sum(1 for t in terms if t in mem["raw_content"].lower())
            norm_k = min(1.0, c_score / max(len(terms), 1))
            if mid in cand_scores:
                cand_scores[mid]["keyword"] = norm_k
            else:
                cand_scores[mid] = {"vector": 0.0, "keyword": norm_k}

        final_ranked = []
        for mid, scores in cand_scores.items():
            f_score = alpha * scores["vector"] + (1.0 - alpha) * scores["keyword"]
            final_ranked.append((mid, f_score))

        final_ranked.sort(key=lambda x: x[1], reverse=True)
        return [item[0] for item in final_ranked[:top_k]]

    # 4. Run Evaluations across modalities
    modalities = {
        "Vector Search (Base all-MiniLM-L6-v2)": lambda i, q: vector_retrieve(i, top_k=10)[0],
        "Keyword Search (Lexical Overlap)": lambda i, q: keyword_retrieve(q, top_k=10),
        "Hybrid Search (alpha=0.6)": lambda i, q: hybrid_retrieve(i, q, alpha=0.6, top_k=10),
    }

    all_results = {}

    print("\n" + "=" * 75)
    print(f"{'Modality':<38} | {'Recall@1':<10} | {'Recall@5':<10} | {'MRR':<10}")
    print("-" * 75)

    for mod_name, fn in modalities.items():
        r1_list = []
        r5_list = []
        rr_list = []

        for q_idx, q_item in enumerate(queries):
            gt = set(q_item["expected_memory_ids"])
            retrieved = fn(q_idx, q_item["query"])

            r1 = compute_recall_at_k(retrieved, gt, k=1)
            r5 = compute_recall_at_k(retrieved, gt, k=5)
            rr = compute_reciprocal_rank(retrieved, gt)

            r1_list.append(r1)
            r5_list.append(r5)
            rr_list.append(rr)

        avg_r1 = round(sum(r1_list) / len(r1_list), 4)
        avg_r5 = round(sum(r5_list) / len(r5_list), 4)
        avg_mrr = round(sum(rr_list) / len(rr_list), 4)

        all_results[mod_name] = {
            "recall@1": avg_r1,
            "recall@5": avg_r5,
            "mrr": avg_mrr,
        }

        print(f"{mod_name:<38} | {avg_r1:<10.4f} | {avg_r5:<10.4f} | {avg_mrr:<10.4f}")

    print("=" * 75)

    # 5. Save Results
    results_dir = os.path.join(PROJECT_DIR, "ml", "results")
    os.makedirs(results_dir, exist_ok=True)

    output_payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "model_name": "all-MiniLM-L6-v2 (pretrained base)",
        "embedding_dimension": 384,
        "dataset_size": len(memories),
        "query_count": len(queries),
        "results": all_results,
    }

    json_out_path = os.path.join(results_dir, "baseline_metrics.json")
    with open(json_out_path, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    # Also save Markdown report
    md_report = f"""# Baseline Retrieval Evaluation Report (Phase 2)

**Evaluated Model:** `all-MiniLM-L6-v2` (Pretrained Base Model)  
**Embedding Dimension:** 384  
**Benchmark Set:** 20 ground-truth memories, 10 domain queries  
**Timestamp:** {output_payload['timestamp']}  

## Summary of Baseline Metrics

| Search Modality | Recall@1 | Recall@5 | MRR (Mean Reciprocal Rank) |
|---|---|---|---|
| **Vector Search (Base all-MiniLM-L6-v2)** | **{all_results['Vector Search (Base all-MiniLM-L6-v2)']['recall@1']}** | **{all_results['Vector Search (Base all-MiniLM-L6-v2)']['recall@5']}** | **{all_results['Vector Search (Base all-MiniLM-L6-v2)']['mrr']}** |
| **Keyword Search (Lexical Overlap)** | **{all_results['Keyword Search (Lexical Overlap)']['recall@1']}** | **{all_results['Keyword Search (Lexical Overlap)']['recall@5']}** | **{all_results['Keyword Search (Lexical Overlap)']['mrr']}** |
| **Hybrid Search (alpha=0.6)** | **{all_results['Hybrid Search (alpha=0.6)']['recall@1']}** | **{all_results['Hybrid Search (alpha=0.6)']['recall@5']}** | **{all_results['Hybrid Search (alpha=0.6)']['mrr']}** |

> [!NOTE]
> These figures represent the **"Before" Baseline** for Recall. In Phase 3, we will fine-tune `all-MiniLM-L6-v2` with Triplet Loss on our generated dataset and compare against these baseline numbers to prove measurable retrieval quality improvement.
"""

    md_out_path = os.path.join(results_dir, "baseline_metrics.md")
    with open(md_out_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    print(f"\nSaved baseline metrics to:\n - {json_out_path}\n - {md_out_path}")


if __name__ == "__main__":
    run_baseline_evaluation()
