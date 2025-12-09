# src/api.py
import os, json, uuid
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# load .env
load_dotenv()

# import your functions (adjust import paths if needed)
from recommender import recommend_ticket_with_chunks
from rag_chain import rag_answer_openai, summarize_ticket
import db

ROOT = os.path.join(os.path.dirname(__file__), "..")
META_PATH = os.path.join(ROOT, "models", "chunk_meta.json")

# ------- Pydantic models -------
class RecommendRequest(BaseModel):
    ticket_text: str
    top_k: Optional[int] = 5

class EvidenceItem(BaseModel):
    chunk_id: str
    article_id: Optional[str] = None
    title: Optional[str] = None
    chunk_text: Optional[str] = None
    file_url: Optional[str] = None

class RecommendResponse(BaseModel):
    answer: Optional[str]
    steps: List[str] = []
    citations: List[str] = []
    confidence: float = 0.0
    evidence: List[EvidenceItem] = []
    raw_model_output: Optional[str] = None
    note: Optional[str] = None

class FeedbackRequest(BaseModel):
    ticket_text: str
    accepted: bool
    comment: Optional[str] = None
    used_citations: Optional[List[str]] = []

class CreateTicketRequest(BaseModel):
    customer_id: str
    text: str

class ReplyRequest(BaseModel):
    role: str  # "customer" or "agent"
    content: str

class SuggestionResponse(BaseModel):
    answer: str
    evidence: List[EvidenceItem]


# ------- app -------
app = FastAPI(title="AI Support Engine API")

# CORS (allow local dev frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# load chunk metadata into memory (simple)
def load_chunk_meta():
    if not os.path.exists(META_PATH):
        return []
    with open(META_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

_chunk_meta = load_chunk_meta()
_by_chunk = {m["chunk_id"]: m for m in _chunk_meta}

def expand_citations(citation_list):
    out = []
    for c in citation_list:
        info = _by_chunk.get(c)
        if info:
            print(f"DEBUG: expand_citations {c} -> title='{info.get('title')}'")
            # optional: set file_url if your article has a file path in metadata
            file_url = info.get("file_url")  # if you added this during ingestion
            # developer instruction: if you want to expose uploaded file, here's the local path:
            # /mnt/data/Ruthvik Gurrala (2).pdf
            out.append({
                "chunk_id": c,
                "article_id": info.get("article_id"),
                "title": info.get("title"),
                "chunk_text": info.get("chunk_text"),
                "file_url": file_url or None
            })
        else:
            print(f"DEBUG: expand_citations {c} -> MISSING")
            out.append({"chunk_id": c, "missing": True})
    return out

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    if not req.ticket_text.strip():
        raise HTTPException(status_code=400, detail="ticket_text is empty")

    # call your RAG wrapper which already returns parsed JSON
    resp = rag_answer_openai(req.ticket_text, top_k_chunks=req.top_k, max_prompt_chunks=3, threshold=0.25)

    # expand citations
    evidence = expand_citations(resp.get("citations", []))

    return RecommendResponse(
        answer=resp.get("answer"),
        steps=resp.get("steps", []),
        citations=resp.get("citations", []),
        confidence=resp.get("confidence", 0.0) or 0.0,
        evidence=evidence,
        raw_model_output=resp.get("raw_model_output"),
        note=resp.get("note")
    )

# simple feedback endpoint (append to a local file)
FEEDBACK_PATH = os.path.join(ROOT, "data", "feedback.json")
@app.post("/feedback")
def feedback(f: FeedbackRequest):
    os.makedirs(os.path.dirname(FEEDBACK_PATH), exist_ok=True)
    entry = {
        "ticket_text": f.ticket_text,
        "accepted": f.accepted,
        "comment": f.comment,
        "used_citations": f.used_citations
    }
    # append
    existing = []
    if os.path.exists(FEEDBACK_PATH):
        with open(FEEDBACK_PATH, "r", encoding="utf-8") as fh:
            try:
                existing = json.load(fh)
            except Exception:
                existing = []
    existing.append(entry)
    with open(FEEDBACK_PATH, "w", encoding="utf-8") as fh:
        json.dump(existing, fh, ensure_ascii=False, indent=2)
    return {"saved": True}

# ------- Ticket Endpoints -------

from classifier import classify_ticket

@app.post("/tickets")
def create_new_ticket(req: CreateTicketRequest):
    analysis = classify_ticket(req.text)
    tags = analysis["tags"]
    sentiment = analysis["sentiment"]
    priority = analysis["priority"]
    
    tid = db.create_ticket(req.customer_id, req.text, tags, sentiment, priority)
    return {"ticket_id": tid, "tags": tags, "sentiment": sentiment, "priority": priority}

@app.get("/tickets")
def list_tickets(status: Optional[str] = None, customer_id: Optional[str] = None):
    return db.get_tickets(status, customer_id)

@app.get("/tickets/{ticket_id}")
def get_ticket_detail(ticket_id: str):
    t = db.get_ticket(ticket_id)
    if not t:
        raise HTTPException(404, "Ticket not found")
    return t

    return t

@app.post("/tickets/{ticket_id}/reply")
def reply_ticket(ticket_id: str, req: ReplyRequest):
    t = db.get_ticket(ticket_id)
    if not t:
        raise HTTPException(404, "Ticket not found")
    
    db.add_message(ticket_id, req.role, req.content)
    
    # Dynamic Analysis: If customer replies, re-evaluate sentiment/priority
    if req.role == "customer":
        analysis = classify_ticket(req.content)
        db.update_ticket_metadata(ticket_id, {
            "sentiment": analysis["sentiment"],
            "priority": analysis["priority"]
        })

    return {"status": "success"}

@app.post("/tickets/{ticket_id}/suggest")
def suggest_reply(ticket_id: str):
    t = db.get_ticket(ticket_id)
    if not t:
        raise HTTPException(404, "Ticket not found")
    
    # Use the last customer message as the query, but pass full history for context
    messages = t.get("messages", [])
    last_customer_msg = next((m["content"] for m in reversed(messages) if m["role"] == "customer"), None)
    
    if not last_customer_msg:
        return {"answer": "No customer message found to reply to.", "evidence": []}

    # Call RAG with history
    # We exclude the very last message from history because it's the 'current query'
    # But rag_chain prompt builder handles it if we pass full history, or we can slice it.
    # Let's pass the *previous* messages as history.
    history = [m for m in messages if m["content"] != last_customer_msg] 
    
    print(f"DEBUG: suggest_reply query='{last_customer_msg}' history_len={len(history)}")
    resp = rag_answer_openai(last_customer_msg, history=messages, top_k_chunks=5)
    evidence = expand_citations(resp.get("citations", []))
    
    return {
        "answer": resp.get("answer"),
        "evidence": evidence,
        "confidence": resp.get("confidence")
    }

@app.post("/tickets/{ticket_id}/resolve")
def resolve_ticket(ticket_id: str):
    db.update_ticket_status(ticket_id, "resolved")
    return {"status": "resolved"}

@app.delete("/tickets/{ticket_id}")
def delete_ticket(ticket_id: str):
    db.delete_ticket(ticket_id)
    return {"status": "deleted"}


@app.get("/analytics/gaps")
def get_content_gaps():
    if not os.path.exists(FEEDBACK_PATH):
        return {"gaps": [], "stats": {"total": 0, "rejected": 0}}
    
    try:
        with open(FEEDBACK_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {"gaps": [], "stats": {"total": 0, "rejected": 0}}

    total = len(data)
    rejected = [d for d in data if not d.get("accepted", True)]
    
    # Group by similarity or just list them for now
    # Simple gap detection: Rejected suggestions are potential gaps
    gaps = []
    for r in rejected:
        gaps.append({
            "query": r.get("ticket_text"),
            "comment": r.get("comment"),
            "timestamp": "N/A" # Feedback doesn't have timestamp yet, maybe add later
        })
    
    return {
        "gaps": gaps,
        "stats": {
            "total": total,
            "rejected": len(rejected),
            "gap_rate": len(rejected) / total if total > 0 else 0
        }
    }

# ------- Upload & Ingestion -------
from fastapi import UploadFile, File
import shutil
from pypdf import PdfReader
import uuid
from chunker import chunk_text
from model_engine import load_embedding_model, get_embeddings
import numpy as np

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # 1. Save file locally
    local_path = os.path.join(ROOT, "data", file.filename)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Extract text (PDF only for now)
    text = ""
    try:
        reader = PdfReader(local_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    except Exception as e:
        return {"error": f"Failed to parse PDF: {str(e)}"}

    if not text.strip():
        return {"error": "No text extracted from file"}

    # 3. Chunking
    # We need a unique article ID
    article_id = "doc_" + str(uuid.uuid4())[:8]
    chunks = chunk_text(text, chunk_size=300, overlap=50)
    
    new_meta = []
    for i, c in enumerate(chunks):
        new_meta.append({
            "chunk_id": f"{article_id}_{i}",
            "article_id": article_id,
            "title": file.filename,
            "chunk_text": c,
            "file_url": f"/files/{file.filename}"
        })

    # 4. Embedding
    model = load_embedding_model()
    new_texts = [m["chunk_text"] for m in new_meta]
    new_embs = get_embeddings(model, new_texts) # numpy array

    # 5. Update Vector Store (Append)
    # Load existing
    global _chunk_meta, _by_chunk
    
    # Update Metadata
    _chunk_meta.extend(new_meta)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(_chunk_meta, f, ensure_ascii=False, indent=2)
    
    # Update Embeddings
    EMB_PATH = os.path.join(ROOT, "models", "chunk_embeddings.npy")
    if os.path.exists(EMB_PATH):
        existing_embs = np.load(EMB_PATH)
        combined_embs = np.vstack([existing_embs, new_embs])
    else:
        combined_embs = new_embs
    
    np.save(EMB_PATH, combined_embs)

    # Refresh memory
    _by_chunk = {m["chunk_id"]: m for m in _chunk_meta}
    
    return {
        "status": "success", 
        "chunks_added": len(new_meta), 
        "article_id": article_id,
        "filename": file.filename
    }

# optional: serve local files for dev (maps filename -> /mnt/data/<filename>)
from fastapi.responses import FileResponse
@app.get("/files/{filename}")
def serve_file(filename: str):
    # CAUTION: dev-only. sanitize filename in prod
    local_base = "/mnt/data"
    path = os.path.join(local_base, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="file missing")
    return FileResponse(path, filename=filename)

@app.post("/tickets/{ticket_id}/summarize")
def summarize_ticket_endpoint(ticket_id: str):
    t = db.get_ticket(ticket_id)
    if not t:
        raise HTTPException(404, "Ticket not found")
    
    messages = t.get("messages", [])
    if not messages:
        return {"summary": "No messages to summarize."}
        
    summary = summarize_ticket(t.get("text", ""), messages)
    return {"summary": summary}

@app.get("/canned_responses")
def get_canned_responses():
    return [
        {"id": "reset_pwd", "title": "Reset Password", "text": "To reset your password, please visit the settings page and click on 'Forgot Password'."},
        {"id": "refund_policy", "title": "Refund Policy", "text": "Our refund policy allows returns within 30 days of purchase. Please provide your order ID."},
        {"id": "contact_support", "title": "Contact Support", "text": "You can reach our support team at support@owntrail.com or call 1-800-123-4567."},
        {"id": "thank_you", "title": "Thank You", "text": "Thank you for contacting Owntrail Support. Have a great day!"}
    ]

# ------- Knowledge Base Endpoints -------

from vector_store import SimpleVectorStore
from rag_chain import translate_text

@app.get("/knowledge")
def list_knowledge_chunks():
    """Returns all chunks in the knowledge base."""
    vs = SimpleVectorStore()
    return vs.get_all_chunks()

@app.delete("/knowledge/{chunk_id}")
def delete_knowledge_chunk(chunk_id: str):
    """Deletes a specific chunk by ID."""
    vs = SimpleVectorStore()
    success = vs.delete_chunk(chunk_id)
    if not success:
        raise HTTPException(404, "Chunk not found")
    
    # Refresh in-memory cache
    global _chunk_meta, _by_chunk
    _chunk_meta = vs.get_all_chunks()
    _by_chunk = {m["chunk_id"]: m for m in _chunk_meta}
    
    return {"status": "deleted", "chunk_id": chunk_id}

class TranslateRequest(BaseModel):
    text: str
    target_lang: str

@app.post("/translate")
def translate_endpoint(req: TranslateRequest):
    """Translates text to target language."""
    translated = translate_text(req.text, req.target_lang)
    return {"translated_text": translated}
