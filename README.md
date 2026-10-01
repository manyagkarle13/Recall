# Recall — Personal AI Memory System

Recall is an intelligent personal memory assistant that captures text notes, webpages, PDFs, and screenshots, storing them in a 384-dimensional semantic vector space for natural language retrieval and LLM-synthesized answers with interactive source citations.

---

## 🌟 Key Features

- **Hybrid Semantic Retrieval**: Combines dense vector search (`all-MiniLM-L6-v2` / fine-tuned weights) with PostgreSQL keyword search & score fusion.
- **RAG Answer Synthesis**: Uses Groq LPU inference (LLaMA 3.1 / Qwen) for low-latency answer generation grounded strictly in your saved memories.
- **Markdown & Interactive Citations**: Synthesized AI responses render as structured Markdown with interactive citation pills (`[1]`, `[2]`) that open the underlying source memory or preview.
- **Multi-Modal Document & OCR Ingestion**: Supports `.txt`, `.md`, `.pdf` documents and screenshot image captures processed via RapidOCR / PyTesseract into shared vector space.
- **Chrome Extension (Manifest V3)**: One-click page capture, text selection context menu, and visible tab screenshot capture directly from your browser toolbar.
- **Dual Database Fallback**: Built-in SQLite simulation fallback when running without a live PostgreSQL `pgvector` container.

---

## 🏗️ Architecture & Project Structure

```
recall/
│
├── backend/                      # Phase 1, 2, 4 — Django REST API + pgvector
│   ├── recall_api/               # Django project configuration & settings
│   ├── memories/                 # Memory storage, OCR & retrieval app
│   │   ├── models.py             # MemoryItem schema with 384-d vector embeddings
│   │   ├── serializers.py        # Serializers for memories, search & auth
│   │   ├── views.py              # Endpoints: /memories/, /search/, /ask/, /auth/
│   │   └── utils/
│   │       ├── embedding.py      # Sentence-transformers embedding pipeline
│   │       ├── retrieval.py      # Hybrid vector + keyword search engine
│   │       ├── llm.py            # Groq LLaMA 3.1 RAG answer synthesis
│   │       └── ocr.py            # RapidOCR / PyTesseract OCR extraction
│   ├── requirements.txt
│   └── manage.py
│
├── ml/                           # Phase 3 — Deep Learning Fine-Tuning Core
│   ├── data/                     # Triplet generator (query, positive, negative)
│   ├── train/                    # Triplet & contrastive loss fine-tuning
│   ├── eval/                     # Evaluation metrics (Recall@5, MRR)
│   └── results/                  # Evaluation report & loss curve plots
│
├── frontend/                     # Phase 5 — Next.js + TypeScript + Tailwind
│   ├── app/                      # Next.js App Router (Search & Memory Manager)
│   ├── components/               # React UI components (AnswerCard, MemoryCard, Modals)
│   ├── lib/api.ts                # Typed client API for Django backend
│   └── package.json
│
├── extension/                    # Phase 6 & 7 — Chrome Extension (Manifest V3)
│   ├── manifest.json
│   ├── background.js             # Service worker handling capture events
│   ├── content-script.js         # Page text extraction & DOM parsing
│   └── popup/                    # One-click quick save popup UI
│
├── docs/                         # Phase 8 — Architecture Documentation & Reports
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Backend Setup (Django REST API)

```bash
cd backend

# Create & activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1    # Windows PowerShell
# source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start Django development server
python manage.py runserver 8000
```
Backend will be live at `http://127.0.0.1:8000`.

---

### 2. Frontend Setup (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```
Frontend web application will be live at `http://localhost:3000`.

---

## 🧩 Installing Chrome Extension (Manifest V3)

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle switch in the top-right corner).
3. Click **Load unpacked** in the top-left corner.
4. Select the `recall/extension` folder:
   `c:\Users\manya\OneDrive\Desktop\recall\extension`
5. The **Recall AI Memory** icon will appear in your browser toolbar!

---

## 🛠️ Phases & Milestones Roadmap

- [x] **Phase 1 — Backend Core**: Django REST Framework, PostgreSQL `pgvector`, embedding generation pipeline.
- [x] **Phase 2 — Semantic + Hybrid Search**: Vector cosine similarity + keyword search fusion & reranking.
- [x] **Phase 3 — Deep Learning Fine-Tuning**: Triplet loss fine-tuning pipeline & evaluation metrics.
- [x] **Phase 4 — LLM Answer Layer**: RAG using Groq LPU inference with structured prompt templates & citations.
- [x] **Phase 5 — Modern Frontend**: Next.js App Router, responsive UI, Markdown rendering, interactive citation pills.
- [x] **Phase 6 — Chrome Extension (Text Capture)**: Manifest V3 extension with quick-save popup and right-click context menu.
- [x] **Phase 7 — Chrome Extension (Screenshot Capture + OCR)**: Tab screenshot capture and RapidOCR text extraction into shared vector space.
- [x] **Phase 8 — Documentation & Deliverables**: Consolidated metrics, architecture diagrams, and deployment guides.

