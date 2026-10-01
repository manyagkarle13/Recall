# Recall Backend Setup Guide (Phase 1)

This guide walks you through setting up and running the Recall backend with Django REST Framework, PostgreSQL, `pgvector`, and `sentence-transformers`.

---

## 1. Prerequisites
- Python 3.10+
- PostgreSQL 15+ or Docker Desktop

---

## 2. Setting Up PostgreSQL with `pgvector`

### Option A: Docker (Recommended - Quickest)
We've included a `docker-compose.yml` pre-configured with `pgvector/pgvector:pg16`.

Run in terminal from `backend/`:
```bash
docker compose up -d
```
This starts PostgreSQL 16 on port `5432` with user `recall_user`, password `recall_password`, and database `recall_db`.

---

### Option B: Native PostgreSQL Installation

#### Windows:
1. If PostgreSQL is already installed, install `pgvector`:
   - Download the latest pgvector Windows binary release from [pgvector GitHub releases](https://github.com/pgvector/pgvector/releases).
   - Copy `vector.dll` into your PostgreSQL `lib/` directory (e.g. `C:\Program Files\PostgreSQL\16\lib`).
   - Copy `vector.control` and `vector--*.sql` into your PostgreSQL `share/extension/` directory.
2. Open `psql` or pgAdmin as superuser:
```sql
CREATE DATABASE recall_db;
CREATE USER recall_user WITH PASSWORD 'recall_password';
GRANT ALL PRIVILEGES ON DATABASE recall_db TO recall_user;
\c recall_db
CREATE EXTENSION IF NOT EXISTS vector;
```

#### macOS (via Homebrew):
```bash
brew install pgvector
brew services restart postgresql
psql postgres -c "CREATE DATABASE recall_db;"
psql recall_db -c "CREATE EXTENSION vector;"
```

#### Ubuntu / Debian:
```bash
sudo apt-get install postgresql-server-dev-all git build-essential
git clone --branch v0.7.4 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
sudo -u postgres psql -c "CREATE DATABASE recall_db;"
sudo -u postgres psql -d recall_db -c "CREATE EXTENSION vector;"
```

---

## 3. Python Virtual Environment Setup

From the `backend/` directory:

```bash
# 1. Create a virtual environment
python -m venv venv

# 2. Activate the virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (Command Prompt):
venv\Scripts\activate.bat
# Linux / macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 4. Configuration & Database Migrations

Copy the example environment file and edit if necessary:
```bash
cp .env.example .env
```

Apply database migrations (this automatically registers the `vector` extension and creates the `memory_items` table):
```bash
python manage.py migrate
```

Create a superuser (optional, for the Django Admin interface at `/admin/`):
```bash
python manage.py createsuperuser
```

---

## 5. Run the Development Server

```bash
python manage.py runserver 8000
```
Your backend will be live at `http://127.0.0.1:8000`.

---

## 6. Testing the Phase 1 Endpoints

### 1. Ingest a Text Memory
```bash
curl -X POST http://127.0.0.1:8000/api/memories/ \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "text",
    "title": "Deep Learning Loss Functions",
    "raw_content": "Contrastive loss and triplet loss are widely used in metric learning. Triplet loss optimizes anchor-positive distance to be smaller than anchor-negative distance by a defined margin alpha.",
    "source_url": "https://example.com/notes"
  }'
```

### 2. Ingest via File Upload (.txt, .md, .pdf)
```bash
curl -X POST http://127.0.0.1:8000/api/memories/ \
  -F "title=Lecture Notes" \
  -F "file=@/path/to/document.pdf"
```
*Note: If the document exceeds 500 tokens, Recall automatically segments the content into overlapping chunks, generates 384-dimensional embeddings for each chunk, and links them via a shared `parent_id`.*

### 3. List Saved Memories (Paginated)
```bash
curl -X GET "http://127.0.0.1:8000/api/memories/?page=1&page_size=10"
```

### 4. Filter Memories by Source Type
```bash
curl -X GET "http://127.0.0.1:8000/api/memories/?source_type=webpage"
```

### 5. Get Individual Memory with Embedding Vector
```bash
curl -X GET "http://127.0.0.1:8000/api/memories/<UUID>/"
```


---

## 7. Optional: Installing Tesseract-OCR for Screenshot Text Extraction (Phase 7)
Recall uses pytesseract to extract text from screenshots. If you want native local OCR text extraction:

### Windows:
Run in PowerShell as Administrator:
`powershell
winget install UB-Mannheim.TesseractOCR
`
Or download the installer from: [UB-Mannheim Tesseract Releases](https://github.com/UB-Mannheim/tesseract/wiki).
Default install path: C:\\Program Files\\Tesseract-OCR\\tesseract.exe (automatically detected by Recall).

### macOS:
`ash
brew install tesseract
`

### Ubuntu / Debian:
`ash
sudo apt-get install tesseract-ocr
`
