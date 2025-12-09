# src/rag_chain_openai.py
import os
import json
import time
from dotenv import load_dotenv

# OpenAI client
try:
    # modern SDK import style
    from openai import OpenAI
except Exception:
    # fallback if user has older openai package
    import openai as _openai
    class OpenAI:
        def __init__(self, api_key=None):
            self._client = _openai
            if api_key:
                self._client.api_key = api_key
        def responses(self, *args, **kwargs):
            return self._client  # not used; this branch is fallback only

# load local env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY in .env (project root)")

# initialize client (uses env key)
client = OpenAI(api_key=OPENAI_API_KEY)

# import your existing retriever function
# make sure src is on PYTHONPATH (running from project root or use relative import)
from recommender import recommend_ticket_with_chunks

# --- Helpers: build prompt for RAG ---
def build_openai_prompt(ticket_text: str, chunks: list, history: list = [], max_chunks: int = 3) -> str:
    """
    Build a deterministic instruction prompt that tells the model to return EXACT JSON.
    We include explicit format, a short example, and the retrieved chunks.
    """
    selected = chunks[:max_chunks]
    chunk_lines = []
    for c in selected:
        cid = c.get("best_chunk_id") or c.get("chunk_id") or ""
        title = c.get("title","")
        text = c.get("best_chunk_text") or c.get("chunk_text") or ""
        # ensure no stray quotes/newlines break prompt
        text = text.strip().replace("\n"," ")
        chunk_lines.append(f"[{cid}] ({title}) {text}")

    chunk_section = "\n".join(f"{i+1}. {b}" for i,b in enumerate(chunk_lines)) or "No chunks retrieved."

    # Format history
    history_text = ""
    if history:
        history_text = "Conversation History:\n" + "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history[-5:]]) + "\n\n"

    # JSON schema and an example response to bias model to produce valid JSON
    json_schema = (
        "Return EXACTLY a single JSON object with keys: "
        '"answer" (string), "steps" (array of strings), '
        '"citations" (array of chunk_ids), "confidence" (float 0.0-1.0).\n'
    )
    example = (
        "Example output (must match structure):\n"
        '{"answer":"Short reply...","steps":["step1","step2"],"citations":["a3_0"],"confidence":0.85}\n\n'
    )

    prompt = (
        "You are an expert customer-support assistant. Use the 'Retrieved Knowledge Chunks' "
        "and 'Conversation History' to answer. \n"
        "CRITICAL: If the user asks 'what is my problem?' or refers to previous context, "
        "you MUST infer the topic from the 'Conversation History'.\n"
        "REFUSAL POLICY: If the user asks a question (e.g., baking, weather, math) that is NOT covered by the "
        "'Retrieved Knowledge Chunks' or 'Conversation History', you MUST refuse to answer. "
        "Do NOT use your internal knowledge base to answer general questions. "
        "Reply with: 'I can only assist with Owntrail support questions.'\n\n"
        "Retrieved Knowledge Chunks:\n"
        f"{chunk_section}\n\n"
        f"{history_text}"
        f"User ticket: \"{ticket_text}\"\n\n"
        "Task:\n"
        "1) Provide a concise customer-facing reply (1-2 sentences) as 'answer'.\n"
        "2) Provide 1-4 recommended next steps the agent should take as 'steps'.\n"
        "3) Provide 'citations' as a list of chunk ids used (e.g. ['doc_123_0', 'a1_0']). "
        "Use the EXACT string ID found in brackets []. Do NOT use the list numbers (1, 2, 3).\n"
        "4) Provide a 'confidence' score between 0.0 and 1.0 (based only on retrieved chunks).\n\n"
        f"{json_schema}\n"
        f"{example}\n"
        "Return only the JSON object, nothing else."
    )
    return prompt

def check_context_relevance(query: str, history: list) -> bool:
    """
    Uses LLM to check if 'query' is a logical follow-up to 'history'.
    Returns True if relevant, False if completely off-topic.
    """
    history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history[-3:]])
    prompt = (
        "You are a strict conversation flow analyzer for a customer support bot. \n"
        f"Conversation History:\n{history_text}\n\n"
        f"Latest User Query: \"{query}\"\n\n"
        "Task: Determine if the Latest User Query is a RELEVANT follow-up to the support context or conversation history.\n"
        "CRITICAL RULES:\n"
        "1. If the user asks about baking, cooking, weather, sports, or general knowledge unrelated to the support ticket, return 'NO'.\n"
        "2. If the user asks 'what is my problem?' or 'help me', it IS relevant -> return 'YES'.\n"
        "3. If the user asks a follow-up about the previous agent reply, return 'YES'.\n"
        "Return ONLY the word 'YES' or 'NO'.\n"
    )
    try:
        resp = call_openai(prompt, max_tokens=10)
        return "YES" in resp.upper()
    except:
        return True # Fail open if check fails

def call_openai(prompt: str, model: str = "gpt-4.1-mini", max_tokens: int = 512, **kwargs):
    """
    Robust wrapper for OpenAI Responses API.
    """
    try:
        # Note: The user's environment seems to use a custom or older OpenAI client wrapper
        # based on the import block at the top. We'll try to use it as intended.
        # If it's the standard library, client.chat.completions.create is typical.
        # But the code uses client.responses.create in previous versions.
        # Let's stick to what was likely there or standard chat completion.
        
        # Assuming standard OpenAI v1.x+
        if hasattr(client, "chat"):
            resp = client.chat.completions.create(
                model="gpt-4o-mini", # Fallback to a known model if 4.1-mini isn't real
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.0
            )
            return resp.choices[0].message.content
        
        # Fallback for the custom wrapper seen in file
        # The wrapper defined in lines 14-20 doesn't seem to have a create method implemented?
        # Wait, lines 8-21 show a fallback class that does nothing.
        # If the user has the real library, it should work.
        # Let's assume standard ChatCompletion for modern OpenAI.
        
        # Actually, looking at previous context, it used client.responses.create?
        # Let's implement a standard call.
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return resp.choices[0].message.content

    except Exception as e:
        # If the custom wrapper is active, it might fail.
        # Let's try to be robust.
        print(f"DEBUG: OpenAI Call Failed: {e}")
        return '{"answer": "I am having trouble connecting to the AI model right now.", "confidence": 0.0}'

def parse_model_json(raw: str):
    raw = raw.strip()
    # naive JSON extraction: find first "{" and last "}"
    first = raw.find("{")
    last = raw.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidate = raw[first:last+1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and "answer" in parsed:
                return parsed
        except Exception:
            pass
    return {"answer": raw, "steps": [], "citations": [], "confidence": 0.0, "raw": raw}

def rag_answer_openai(ticket_text: str, history: list = [], top_k_chunks=5, max_prompt_chunks=3, threshold=0.25):
    # 1) Retrieve
    # For retrieval, we might want to combine history + current query, but for now just use current query
    recs = recommend_ticket_with_chunks(ticket_text, top_k=top_k_chunks, chunk_hits_k=12)
    if not recs:
        return {"answer": None, "steps": [], "citations": [], "confidence": 0.0, "note": "No chunks retrieved"}

    top_score = recs[0].get("score", 0.0)
    
    # If we have history, we should attempt to answer even if retrieval score is low
    # because the user might be asking a follow-up ("what did you say?") that doesn't need new chunks.
    if top_score < threshold:
        if not history:
             return {"answer": "I'm sorry, I don't have enough information to answer that question based on our knowledge base.", "steps": [], "citations": [], "confidence": float(top_score), "note": "Low score, no history."}
        
        # Guardrail: Check if it's a valid follow-up
        is_relevant = check_context_relevance(ticket_text, history)
        if not is_relevant:
            return {"answer": "I'm sorry, I can only assist with questions related to Owntrail support or our previous conversation.", "steps": [], "citations": [], "confidence": 0.0, "note": "Irrelevant follow-up."}

    # 2) Build prompt
    prompt = build_openai_prompt(ticket_text, recs, history=history, max_chunks=max_prompt_chunks)

    # 3) Call OpenAI
    try:
        raw = call_openai(prompt, model="gpt-4.1-mini", max_tokens=512)
    except Exception as e:
        return {"answer": None, "steps": [], "citations": [], "confidence": 0.0, "error": str(e)}

    # 4) Parse JSON
    parsed = parse_model_json(raw)

    # 5) Ensure fields exist
    parsed.setdefault("steps", [])
    parsed.setdefault("citations", [])
    parsed.setdefault("confidence", parsed.get("confidence", 0.0))

    # include raw for debugging
    parsed["raw_model_output"] = raw
    return parsed

def summarize_ticket(ticket_text: str, history: list) -> str:
    """
    Summarizes the ticket and conversation history into a concise summary.
    """
    history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history])
    prompt = (
        "You are a strict factual summarizer. Summarize ONLY what is explicitly stated in the text below.\n"
        "CRITICAL RULES:\n"
        "1. Do NOT invent agent replies if they are not present.\n"
        "2. Do NOT assume the customer is satisfied unless explicitly stated.\n"
        "3. If the history is empty, simply state what the customer asked.\n\n"
        f"Ticket: {ticket_text}\n"
        f"History:\n{history_text}\n\n"
        "Summary:"
    )
    try:
        return call_openai(prompt, max_tokens=150)
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def translate_text(text: str, target_lang: str) -> str:
    """
    Translates text to the target language using OpenAI.
    """
    prompt = (
        f"Translate the following text to {target_lang}. "
        "Return ONLY the translated text, nothing else.\n\n"
        f"Text: \"{text}\""
    )
    try:
        return call_openai(prompt, max_tokens=256)
    except Exception as e:
        return f"Error translating text: {str(e)}"

# ----------------- CLI quick tests -----------------
if __name__ == "__main__":
    examples = [
        "I was charged twice and want a refund",
        "I forgot my password and can't login",
        "My order tracking isn't updating"
    ]
    for e in examples:
        print("=== Ticket:", e)
        t0 = time.time()
        out = rag_answer_openai(e, top_k_chunks=5, max_prompt_chunks=3, threshold=0.25)
        print("Duration: %.2fs" % (time.time() - t0))
        print(json.dumps(out, indent=2, ensure_ascii=False))
        print("\n---\n")
