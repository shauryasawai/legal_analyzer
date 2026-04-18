import os
import json
import logging
from pathlib import Path
from typing import Optional
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LCDoc

logger = logging.getLogger(__name__)


# ── Text extraction ────────────────────────────────────────────────────────────

def extract_text(file_path: str) -> str:
    """Extract plain text from PDF or DOCX or TXT."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == '.pdf':
        return _extract_pdf(file_path)
    elif ext in ('.docx', '.doc'):
        return _extract_docx(file_path)
    elif ext == '.txt':
        return path.read_text(encoding='utf-8', errors='ignore')
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _extract_pdf(file_path: str) -> str:
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
        return "\n\n".join(text_parts)
    except ImportError:
        # Fallback
        try:
            import PyPDF2
            text_parts = []
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text_parts.append(page.extract_text() or '')
            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return ""


def _extract_docx(file_path: str) -> str:
    try:
        from docx import Document
        doc = Document(file_path)
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
        return ""


# ── Vector store (ChromaDB) ────────────────────────────────────────────────────

def get_vectorstore(persist_dir: str):
    """Return (or create) a ChromaDB vector store with sentence-transformers."""
    try:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vectorstore = Chroma(
            collection_name="legal_docs",
            embedding_function=embeddings,
            persist_directory=persist_dir,
        )
        return vectorstore
    except Exception as e:
        logger.error(f"Vectorstore init failed: {e}")
        return None


def store_document_chunks(text: str, doc_id: str, persist_dir: str):
    """Chunk the text and store embeddings in ChromaDB."""
    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", " "],
        )

        chunks = splitter.split_text(text)

        docs = [
            LCDoc(page_content=chunk, metadata={"doc_id": doc_id, "chunk": i})
            for i, chunk in enumerate(chunks)
        ]

        vs = get_vectorstore(persist_dir)

        if vs and docs:
            vs.add_documents(docs)

        return len(chunks)

    except Exception as e:
        logger.error(f"Chunk storage failed: {e}")
        return 0


# ── OpenAI calle────────────────────────────────────────────────────────────

def call_openai(system: str, user: str, api_key: str, max_tokens: int = 2000) -> str:
    """Call OpenAI Chat Completion API directly."""
    import urllib.request
    import json

    payload = json.dumps({
        "model": "gpt-4o",                     # you can change to "gpt-4", "gpt-3.5-turbo", etc.
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


# ── Main analysis pipeline ─────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert legal document analyst. Analyze legal text and return ONLY valid JSON — no markdown, no extra text.

Your job:
1. Identify distinct clauses/sections
2. Simplify each clause in plain English
3. Flag risk level: "low", "medium", or "high"
4. Provide a brief risk reason
5. Identify clause type (e.g., Liability, Termination, Payment, IP, Privacy, etc.)

Return this exact JSON structure:
{
  "clauses": [
    {
      "title": "Section name",
      "original_text": "The original legal text...",
      "simplified_text": "Plain English explanation...",
      "risk_level": "low|medium|high",
      "risk_reason": "Why this is risky (or not)",
      "clause_type": "Type of clause"
    }
  ]
}"""

ELI5_SYSTEM = """You are explaining legal concepts to a 10-year-old child.
Use very simple words, short sentences, and friendly analogies.
Make it fun and easy. Return only the explanation text, no JSON."""


def analyze_document(text: str, api_key: str) -> list[dict]:
    """Send document text to OpenAI and parse clause analysis."""
    # Truncate if too long (keep first ~6000 chars for the main analysis)
    truncated = text[:6000] if len(text) > 6000 else text

    prompt = f"Analyze this legal document and extract all clauses:\n\n{truncated}"

    try:
        raw = call_openai(SYSTEM_PROMPT, prompt, api_key, max_tokens=3000)

        # Clean up response
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("```").strip()

        data = json.loads(raw)
        return data.get("clauses", [])
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}\nRaw: {raw[:500]}")
        return _fallback_clauses(text)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return _fallback_clauses(text)


def generate_eli5(clause_text: str, api_key: str) -> str:
    """Generate an ELI5 explanation for a specific clause."""
    try:
        return call_openai(
            ELI5_SYSTEM,
            f"Explain this legal clause like I'm 10 years old:\n\n{clause_text}",
            api_key,
            max_tokens=400,
        )
    except Exception as e:
        logger.error(f"ELI5 generation failed: {e}")
        return "This part of the document means the people signing it agree to some rules. Ask a grown-up for help understanding more!"


def _fallback_clauses(text: str) -> list[dict]:
    """Minimal fallback when API fails."""
    return [{
        "title": "Full Document",
        "original_text": text[:500] + "..." if len(text) > 500 else text,
        "simplified_text": "Could not automatically analyze this document. Please review manually.",
        "risk_level": "medium",
        "risk_reason": "Automatic analysis unavailable",
        "clause_type": "Unknown",
    }]