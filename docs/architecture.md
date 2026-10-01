# Recall: System Architecture & Data Flow

This document details the architectural layout, data flow schemas, and component interactions of the Recall AI memory system.

---

## 1. High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                            CLIENT SURFACES LAYER                                  |
|                                                                                   |
|  +-------------------------------------+   +------------------------------------+  |
|  |     Chrome Extension (MV3)          |   |     Next.js 14 Frontend Web App    |  |
|  | - One-Click DOM Text & URL Capture  |   | - Natural Language Search (/api/ask) |  |
|  | - Context Menu: "Remember this"    |   | - Grounded Answer Card with Sources|  |
|  | - captureVisibleTab() Screenshot    |   | - Memory Manager & Type Filters    |  |
|  +-------------------------------------+   +------------------------------------+  |
+------------------------------------------+----------------------------------------+
                                           | HTTP REST
                                           v
+-----------------------------------------------------------------------------------+
|                        BACKEND SERVICE LAYER (Django DRF)                         |
|                                                                                   |
|  [POST /api/memories/]         [POST /api/memories/screenshot/]   [POST /api/ask/]|
|         |                                      |                          |       |
|         v                                      v                          v       |
|  +---------------+                     +---------------+          +---------------+
|  | Token Chunker |                     | pytesseract   |          | Hybrid Search |
|  | (>500 tokens) |                     | OCR Engine    |          | Retrieval     |
|  +---------------+                     +---------------+          +---------------+
|         |                                      |                          |       |
|         +-------------------+------------------+                          |       |
|                             |                                             |       |
|                             v                                             v       |
|                  +----------------------+                      +------------------+
|                  | Embedding Singleton  |                      | Groq LPU Client  |
|                  | (all-MiniLM-L6-v2    |<-------------------->| (LLaMA 3.1)      |
|                  |  recall-finetuned-v1)|                      | + Guardrail      |
|                  +----------------------+                      +------------------+
|                             |                                             |       |
+-----------------------------|---------------------------------------------|-------+
                              | Vectors (384-d)                             | Citations
                              v                                             v
+-----------------------------------------------------------------------------------+
|                        DATABASE LAYER (PostgreSQL 16)                             |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Table: memory_items                                                         |  |
|  | - id (UUID, PK)                                                             |  |
|  | - source_type ('text' | 'webpage' | 'screenshot' | 'pdf')                    |  |
|  | - title (VARCHAR)                                                           |  |
|  | - raw_content (TEXT)                                                        |  |
|  | - source_url (VARCHAR)                                                      |  |
|  | - embedding (vector(384) with HNSW Cosine Index <=> )                       |  |
|  | - chunk_index (INT), parent_id (UUID)                                        |  |
|  | - Full-Text Search Vector (SearchVector on title + content)                 |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Ingestion Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Ext as Chrome Extension
    participant API as Django Backend
    participant OCR as Pytesseract OCR
    participant Chunk as Chunking Engine
    participant Model as Fine-Tuned Embedding
    participant DB as PostgreSQL pgvector

    alt Webpage or Text Note
        User->>Ext: Click "Remember this Page"
        Ext->>API: POST /api/memories/ {title, raw_content, url}
    else Screenshot Capture
        User->>Ext: Click "Remember (Screenshot)"
        Ext->>API: POST /api/memories/screenshot/ {image_base64, url}
        API->>OCR: Preprocess & Extract text
        OCR-->>API: Extracted raw_content & dimensions
    end

    API->>Chunk: Evaluate token length
    alt > 500 tokens
        Chunk-->>API: Split into N chunks (50-token overlap)
    else <= 500 tokens
        Chunk-->>API: 1 single chunk
    end

    API->>Model: Encode text passages (batch)
    Model-->>API: 384-dimensional normalized vectors
    API->>DB: Bulk INSERT memory_items with embedding
    DB-->>API: Stored UUIDs
    API-->>Ext: 201 Created ("Saved! Chunked & Embedded")
```

---

## 3. Query & Synthesis Flow (/api/ask/)

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Next.js Search UI
    participant API as Django Backend
    participant Model as Fine-Tuned Embedding
    participant DB as PostgreSQL pgvector
    participant Groq as Groq LPU (LLaMA 3.1)

    User->>UI: Types question: "How does triplet loss work?"
    UI->>API: POST /api/ask/ {question, top_k: 5, threshold: 0.45}
    API->>Model: Encode question
    Model-->>API: Query vector (384-d)

    par Vector Similarity Search
        API->>DB: CosineDistance('embedding', query_vec) LIMIT 20
        DB-->>API: Vector candidate matches
    and Lexical Keyword Search
        API->>DB: SearchRank(SearchVector, SearchQuery) LIMIT 20
        DB-->>API: Keyword candidate matches
    end

    API->>API: Weighted Score Fusion (alpha * V + (1-alpha) * K)
    
    alt Max Score < Threshold (0.45)
        API-->>UI: Refusal ("I couldn't find anything relevant...")
    else Max Score >= Threshold
        API->>Groq: ChatCompletion with in-context memories & prompt template
        Groq-->>API: Grounded answer with [Memory Title] citations
        API-->>UI: Synthesized answer + Citation cards + Similarity badges
    end
    UI-->>User: Renders AnswerCard with source links
```

---

## 4. Key Endpoints Reference

| Endpoint | Method | Input | Output | Purpose |
|---|---|---|---|---|
| `/api/memories/` | `GET` | `?page=1&source_type=pdf` | Paginated list | Browse and filter memories |
| `/api/memories/` | `POST` | JSON note or file upload | 201 Created MemoryItem | Text/file ingestion & chunking |
| `/api/memories/screenshot/` | `POST` | `{image_base64, title, url}` | 201 Created MemoryItem | Screenshot OCR + 384-d vector ingest |
| `/api/memories/<uuid>/` | `DELETE` | Path UUID | 204 No Content | Delete memory |
| `/api/search/` | `POST` | `{query, top_k, alpha, mode}` | Ranked candidate items | Hybrid semantic + keyword retrieval |
| `/api/ask/` | `POST` | `{question, top_k, threshold}` | Grounded answer + citations | Groq LPU RAG synthesis |
