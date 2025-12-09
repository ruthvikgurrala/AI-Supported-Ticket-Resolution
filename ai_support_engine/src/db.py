import os
import time
import uuid
from typing import List, Optional, Dict, Any
from google.cloud import firestore
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()

# Configuration
FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH")
USE_FIRESTORE = False
db = None

# Initialize Firestore
if FIREBASE_KEY_PATH and os.path.exists(FIREBASE_KEY_PATH):
    try:
        cred = service_account.Credentials.from_service_account_file(FIREBASE_KEY_PATH)
        db = firestore.Client(credentials=cred)
        USE_FIRESTORE = True
        print(f"[OK] Firestore initialized using {FIREBASE_KEY_PATH}")
    except Exception as e:
        print(f"[WARN] Failed to initialize Firestore: {e}")
else:
    print("[WARN] FIREBASE_KEY_PATH not found or invalid. Using in-memory storage (data will be lost on restart).")

# In-memory fallback
_tickets_memory = {}

# --- DB Operations ---

def create_ticket(customer_id: str, text: str, tags: List[str] = [], sentiment: str = "neutral", priority: str = "medium") -> str:
    ticket_id = str(uuid.uuid4())
    now = time.time()
    ticket_data = {
        "id": ticket_id,
        "customer_id": customer_id,
        "text": text,
        "tags": tags,
        "sentiment": sentiment,
        "priority": priority,
        "status": "open",  # open, resolved
        "created_at": now,
        "updated_at": now,
        "messages": [
            {
                "role": "customer",
                "content": text,
                "ts": now
            }
        ]
    }

    if USE_FIRESTORE:
        db.collection("tickets").document(ticket_id).set(ticket_data)
    else:
        _tickets_memory[ticket_id] = ticket_data
    
    return ticket_id

def get_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
    if USE_FIRESTORE:
        doc = db.collection("tickets").document(ticket_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    else:
        return _tickets_memory.get(ticket_id)

def get_tickets(status: Optional[str] = None, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
    if USE_FIRESTORE:
        ref = db.collection("tickets")
        if status:
            ref = ref.where("status", "==", status)
        if customer_id:
            ref = ref.where("customer_id", "==", customer_id)
        
        # Order by created_at desc (requires index in Firestore, usually)
        # For now, we'll sort in python to avoid index creation errors during dev
        docs = ref.stream()
        tickets = [d.to_dict() for d in docs]
        tickets.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return tickets
    else:
        tickets = list(_tickets_memory.values())
        if status:
            tickets = [t for t in tickets if t.get("status") == status]
        if customer_id:
            tickets = [t for t in tickets if t.get("customer_id") == customer_id]
        tickets.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        return tickets

def add_message(ticket_id: str, role: str, content: str):
    now = time.time()
    msg = {"role": role, "content": content, "ts": now}
    
    if USE_FIRESTORE:
        ref = db.collection("tickets").document(ticket_id)
        # Atomically update messages array and updated_at
        ref.update({
            "messages": firestore.ArrayUnion([msg]),
            "updated_at": now
        })
    else:
        if ticket_id in _tickets_memory:
            _tickets_memory[ticket_id]["messages"].append(msg)
            _tickets_memory[ticket_id]["updated_at"] = now

def update_ticket_status(ticket_id: str, status: str):
    if USE_FIRESTORE:
        db.collection("tickets").document(ticket_id).update({"status": status})
    else:
            _tickets_memory[ticket_id]["status"] = status

def update_ticket_metadata(ticket_id: str, updates: Dict[str, Any]):
    if USE_FIRESTORE:
        db.collection("tickets").document(ticket_id).update(updates)
    else:
        if ticket_id in _tickets_memory:
            _tickets_memory[ticket_id].update(updates)

def delete_ticket(ticket_id: str):
    if USE_FIRESTORE:
        db.collection("tickets").document(ticket_id).delete()
    else:
        if ticket_id in _tickets_memory:
            del _tickets_memory[ticket_id]
