# Baseline Retrieval Evaluation Report (Phase 2)

**Evaluated Model:** `all-MiniLM-L6-v2` (Pretrained Base Model)  
**Embedding Dimension:** 384  
**Benchmark Set:** 20 ground-truth memories, 10 domain queries  
**Timestamp:** 2026-09-16T13:15:52.969750  

## Summary of Baseline Metrics

| Search Modality | Recall@1 | Recall@5 | MRR (Mean Reciprocal Rank) |
|---|---|---|---|
| **Vector Search (Base all-MiniLM-L6-v2)** | **1.0** | **1.0** | **1.0** |
| **Keyword Search (Lexical Overlap)** | **0.9** | **1.0** | **0.9333** |
| **Hybrid Search (alpha=0.6)** | **1.0** | **1.0** | **1.0** |

> [!NOTE]
> These figures represent the **"Before" Baseline** for Recall. In Phase 3, we will fine-tune `all-MiniLM-L6-v2` with Triplet Loss on our generated dataset and compare against these baseline numbers to prove measurable retrieval quality improvement.
