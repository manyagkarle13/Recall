# Recall — Personal AI Memory System

Recall is an intelligent personal memory assistant that captures text notes, webpages, and screenshot captures, storing them in a semantic vector space for natural language query retrieval and LLM-synthesized answers.

## Architecture & Phases Overview

```
recall/
│
├── backend/                      # Phase 1, 2, 4 — Django REST API + pgvector
│   ├── recall_api/               # Django project configuration
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── memories/                 # Memory storage & retrieval app
│   │   ├── models.py             # MemoryItem with vector embeddings
│   │   ├── serializers.py        # Serializers for memories & search queries
│   │   ├── views.py              # Endpoints: /memories/, /search/, /ask/
│   │   ├── urls.py
│   │   └── utils/
│   │       ├── embedding.py      # Base & fine-tuned embedding inference
│   │       ├── retrieval.py      # Semantic & hybrid search (pgvector + BM25/keyword)
│   │       ├── llm.py            # Groq LLaMA 3.1 answer synthesis with citations
│   │       └── ocr.py            # pytesseract screenshot OCR
│   ├── requirements.txt
│   └── manage.py
│
├── ml/                           # Phase 3 — Deep Learning fine-tuning core
│   ├── data/
│   │   ├── generate_triplets.py  # Triplet dataset generator (query, positive, negative)
│   │   └── triplets.json         # Generated training/val dataset
│   ├── train/
│   │   └── finetune.py           # Fine-tuning all-MiniLM-L6-v2 (Triplet / Contrastive loss)
│   ├── eval/
│   │   ├── eval_metrics.py       # Metrics: Recall@5, MRR (Mean Reciprocal Rank)
│   │   └── compare_plot.py       # Plots comparing base vs fine-tuned model
│   ├── checkpoints/
│   │   └── recall-finetuned-v1/   # Saved fine-tuned transformer weights
│   └── results/
│       ├── loss_curve.png        # Training & validation loss curves
│       ├── comparison_chart.png  # Evaluation metric bar charts
│       └── eval_report.md        # Comprehensive evaluation report
│
├── frontend/                     # Phase 5 — Next.js + TypeScript + Tailwind
│   ├── app/
│   │   ├── page.tsx              # Natural language search UI & answer display
│   │   └── memories/page.tsx     # Memory browser, filter & manual creation
│   ├── components/
│   ├── lib/api.ts                # Typed client API for Django backend
│   └── package.json
│
├── extension/                    # Phase 6 & 7 — Chrome Extension (Manifest V3)
│   ├── manifest.json
│   ├── background.js             # Service worker handling capture events
│   ├── content-script.js         # Page text extraction & DOM parsing
│   └── popup/
│       ├── popup.html            # One-click quick save popup
│       └── popup.js              # Capture trigger & feedback
│
├── docs/                         # Phase 8 — Project Report & Submission
│   ├── architecture.md           # System architecture document
│   ├── report.md                 # Deep learning course report
│   └── diagrams/                 # Architectural & data flow diagrams
│
└── README.md
```

## Phases Roadmap

- **Phase 1 — Backend Core**: Django REST Framework setup, PostgreSQL with `pgvector` extension, `MemoryItem` model, embedding generation pipeline with `sentence-transformers` (`all-MiniLM-L6-v2` base model).
- **Phase 2 — Semantic + Hybrid Search**: Vector cosine similarity search via pgvector + keyword search, score fusion / reranking, baseline evaluation suite (Recall@5, MRR).
- **Phase 3 — Deep Learning Fine-Tuning Pipeline**: Triplet dataset generation, contrastive / triplet loss fine-tuning, loss curves, validation evaluation (base vs fine-tuned), model checkpointing and hot-swapping into the live backend.
- **Phase 4 — LLM Answer Layer**: Retrieval-Augmented Generation (RAG) using Groq LLaMA 3.1 with structured prompt templates and memory citations.
- **Phase 5 — Frontend**: Next.js App Router, modern responsive interface, natural language search, source citation cards, and memory management.
- **Phase 6 — Chrome Extension (Text Capture)**: Manifest V3 extension with one-click page and text excerpt capture.
- **Phase 7 — Chrome Extension (Screenshot Capture + OCR)**: Visible tab capture and backend `pytesseract` OCR processing into shared embedding space.
- **Phase 8 — Final Report & Deliverables**: Consolidated metrics, loss curves, ablation findings, and architecture documentation for course submission.
