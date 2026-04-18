# ⚖️ LexAI — AI Legal Document Analyzer

An AI-powered Django web app that uploads legal documents (PDF/DOCX/TXT),
uses **LangChain + ChromaDB** for chunking & vector storage, and
**Claude (Anthropic)** to simplify clauses, score risks, and generate
child-friendly "Explain Like I'm 10" summaries.

---

## 🗂 Project Structure

```
legal_analyzer/
├── legal_analyzer/          # Django project settings, urls, wsgi
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── legal_app/               # Main app
│   ├── models.py            # DocumentAnalysis + Clause models
│   ├── views.py             # Upload, Analysis, ELI5 endpoints
│   ├── urls.py              # App URL routing
│   ├── langchain_service.py # LangChain + ChromaDB + GPT pipeline
│   ├── migrations/
│   ├── templates/legal_app/
│   │   ├── base.html
│   │   ├── index.html       # Upload landing page
│   │   └── analysis.html    # Results page
│   └── static/legal_app/
│       ├── css/main.css     # Full stylesheet
│       └── js/
│           ├── main.js      # Shared utilities
│           ├── upload.js    # Upload + progress logic
│           └── analysis.js  # Filter + ELI5 typewriter
├── media/uploads/           # Uploaded documents
├── vectorstore/             # ChromaDB persisted embeddings
├── manage.py
└── requirements.txt
```

---

## ⚡ Quick Start

### 1. Clone / unzip the project

```bash
cd legal_analyzer
```

### 2. Create a virtual environment & install dependencies

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

> **Note:** `sentence-transformers` downloads a ~90 MB model on first run.

### 3. Set your GPT API key

```bash

# Windows PowerShell
$env:OPENAI_API_KEY = "sk-ant-..."
```

Or add it to a `.env` file and use `python-decouple` / `django-environ`.

### 4. Apply migrations & collect static

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### 5. Run the development server

```bash
python manage.py runserver
```

Open → **http://127.0.0.1:8000**

---

## 🔧 How the AI Pipeline Works

```
Upload File
    │
    ▼
extract_text()          # pdfplumber / python-docx / plain text
    │
    ▼
store_document_chunks() # LangChain RecursiveCharacterTextSplitter
    │                   # → ChromaDB (sentence-transformers embeddings)
    ▼
analyze_document()      # GPT-5
    │                   # Returns JSON: title, simplified, risk, type
    ▼
Save Clause objects     # Django ORM → SQLite
    │
    ▼
Render analysis.html    # Risk sidebar, filter bar, ELI5 buttons
    │
    ▼ (on demand)
generate_eli5()         # Second Claude call per clause
```

---

## 🌐 Key Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET    | `/` | Upload landing page |
| POST   | `/upload/` | Upload & analyze document |
| GET    | `/analysis/<uuid>/` | View analysis results |
| POST   | `/api/eli5/<id>/` | Generate ELI5 for a clause |
| GET    | `/api/status/<uuid>/` | Poll processing status |

---

## 🚀 Production Tips

- Replace SQLite with PostgreSQL in `settings.py`
- Use Celery + Redis for async document processing
- Store uploads on S3 (django-storages)
- Set `DEBUG=False` and configure `ALLOWED_HOSTS`
- Use gunicorn + nginx for serving

---

## 📦 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2 |
| AI Orchestration | LangChain |
| Vector DB | ChromaDB |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| LLM | OPEN AI (GPT-5) |
| PDF parsing | pdfplumber / PyPDF2 |
| DOCX parsing | python-docx |
| Frontend | HTML + CSS + Vanilla JS |
| Database | SQLite (dev) / PostgreSQL (prod) |
