# Recall Frontend (Next.js + TypeScript + Tailwind CSS)

Clean, high-aesthetic user interface for the Recall personal AI memory system.

## Features
- **Ask & Search UI (`/`)**: Natural language question bar hitting `/api/ask/`, showing the Groq LLaMA synthesized answer with clickable source citations and similarity matching cards.
- **Controls & Guardrail**: Interactive sliders for Hybrid Balance ($\\alpha$) and relevance threshold to showcase hallucination prevention.
- **Memories Manager (`/memories`)**: Filterable, paginated card view with icons for Text Notes, Webpages, Screenshots, and PDFs.
- **Add Memory Modal**: Fast modal to paste notes or upload documents (`.txt`, `.md`, `.pdf`).

## Quick Start

From `frontend/`:
```bash
# 1. Install dependencies
npm install

# 2. Run dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.
