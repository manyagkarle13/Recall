# Recall — Personal AI Memory System

Recall is an intelligent personal memory assistant that captures text notes, webpages, PDFs, and screenshots, storing them in a 384-dimensional semantic vector space for natural language query retrieval and LLM-synthesized answers with interactive source citations.

---

## 🌟 Key Features

- **Hybrid Semantic Retrieval**: Combines dense vector similarity search (`all-MiniLM-L6-v2`) with PostgreSQL full-text keyword search and Reciprocal Rank Fusion (RRF) score fusion.
- **RAG Answer Synthesis**: Powered by Groq LPU inference (LLaMA 3.1 / Qwen) for ultra-fast answer generation grounded strictly in your personal memories.
- **Markdown & Interactive Source Citations**: Synthesized answers render as structured Markdown with interactive inline citation buttons (`[1]`, `[2]`). Clicking any citation pill opens the original memory, PDF, or screenshot.
- **Multi-Modal Document & OCR Ingestion**: Seamlessly processes text notes, `.pdf` documents, and screenshot captures with RapidOCR / PyTesseract into a shared vector space.
- **Chrome Extension (Manifest V3)**: One-click webpage save popup, right-click context menu ("Remember this with Recall"), and tab screenshot capture.
- **Dual Database Engine**: Native support for PostgreSQL + `pgvector` with built-in SQLite vector simulation fallback.

---

## 🏗️ Project Architecture

```
recall/
│
├── backend/                      # Django REST Framework API & Retrieval Core
│   ├── recall_api/               # Django project settings & configuration
│   ├── memories/                 # Core memory models, serializers, views & search
│   │   ├── models.py             # MemoryItem schema with 384-d vector embeddings
│   │   ├── serializers.py        # REST API serializers
│   │   ├── views.py              # Endpoints: /memories/, /search/, /ask/, /auth/
│   │   └── utils/
│   │       ├── embedding.py      # Sentence-transformers embedding pipeline
│   │       ├── retrieval.py      # Hybrid vector + keyword search engine
│   │       ├── llm.py            # Groq LLaMA 3.1 RAG answer synthesis
│   │       └── ocr.py            # RapidOCR / PyTesseract screenshot OCR
│   ├── requirements.txt
│   └── manage.py
│
├── frontend/                     # Next.js + TypeScript + Tailwind CSS Frontend
│   ├── app/                      # App router (Search interface, Memories browser, Auth)
│   ├── components/               # React UI components (AnswerCard, MemoryCard, Modals)
│   ├── lib/api.ts                # Typed client API for Django backend
│   └── package.json
│
├── extension/                    # Chrome Extension (Manifest V3)
│   ├── manifest.json             # Extension manifest configuration
│   ├── background.js             # Service worker handling context menus & events
│   ├── content-script.js         # Page text extraction & DOM parser
│   └── popup/                    # Quick-save extension popup UI
│
├── ml/                           # Deep Learning Fine-Tuning & Evaluation
│   ├── data/                     # Triplet dataset generator
│   ├── train/                    # Triplet & contrastive loss fine-tuning
│   └── eval/                     # Evaluation metrics (Recall@5, MRR)
│
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **PostgreSQL 15+** (Optional, automatic fallback to SQLite)

---

### 2. Backend Setup (Django REST API)

```bash
cd backend

# Create & activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1    # Windows PowerShell
# source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Start Django development server
python manage.py runserver 8000
```
*Backend server runs at `http://127.0.0.1:8000`*

---

### 3. Frontend Setup (Next.js)

```bash
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```
*Frontend application runs at `http://localhost:3000`*

---

## 🧩 Installing the Chrome Extension (Manifest V3)

1. Open Google Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle switch in the top-right corner).
3. Click **Load unpacked** in the top-left corner.
4. Select the extension directory:
   `c:\Users\manya\OneDrive\Desktop\recall\extension`
5. The **Recall AI Memory** icon will appear in your browser toolbar!

---

## 📡 API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register/` | Register a new user account & get Token |
| `POST` | `/api/auth/login/` | Authenticate user & receive Auth Token |
| `GET` | `/api/memories/` | List user memories (paginated, source filter) |
| `POST` | `/api/memories/` | Ingest new text memory or document file (.pdf, .txt) |
| `POST` | `/api/memories/screenshot/` | Ingest screenshot capture with OCR text extraction |
| `POST` | `/api/search/` | Perform hybrid vector + keyword semantic search |
| `POST` | `/api/ask/` | RAG answer synthesis with citations via Groq LLaMA 3.1 |
