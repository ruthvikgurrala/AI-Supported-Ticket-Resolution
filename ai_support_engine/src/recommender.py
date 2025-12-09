# src/recommender.py
import os
import time
import json
from collections import defaultdict
from model_engine import load_embedding_model, get_embedding
from vector_store import SimpleVectorStore

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "logs", "recs.jsonl")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def shorten(text, n=200):
    if not text:
        return ""
    text = text.strip()
    if len(text) <= n:
        return text
    # avoid cutting mid-word
    s = text[:n].rsplit(" ", 1)[0]
    return s + "..."

# ---------------- Aggregation helpers ----------------
def aggregate_max(hits):
    out = {}
    for h in hits:
        aid = h["meta"].get("article_id")
        s = float(h["score"])
        if aid is None:
            continue
        out[aid] = max(out.get(aid, -1e9), s)
    return out

def aggregate_mean(hits):
    sums = defaultdict(float)
    counts = defaultdict(int)
    for h in hits:
        aid = h["meta"].get("article_id")
        s = float(h["score"])
        if aid is None:
            continue
        sums[aid] += s
        counts[aid] += 1
    return {aid: (sums[aid] / counts[aid]) for aid in sums}

def aggregate_hybrid(hits, alpha=0.7):
    maxs = aggregate_max(hits)
    means = aggregate_mean(hits)
    keys = set(list(maxs.keys()) + list(means.keys()))
    return {k: alpha * maxs.get(k, 0.0) + (1 - alpha) * means.get(k, 0.0) for k in keys}

# ---------------- Utility: title boost ----------------
def title_boost(results, query, boost=0.05):
    q = (query or "").lower()
    for r in results:
        title = (r.get("title") or "").lower()
        # simple token overlap
        if title:
            for tok in title.split():
                if tok and tok in q:
                    r["score"] = float(r["score"]) + boost
                    break
    return sorted(results, key=lambda x: x["score"], reverse=True)

# ---------------- Logging ----------------
def log_query(query, preproc_query, agg_method, params, results, logfile=LOG_PATH):
    record = {
        "ts": time.time(),
        "query": query,
        "preproc": preproc_query,
        "agg_method": agg_method,
        "params": params,
        "results": results
    }
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

# ---------------- Core recommend functions ----------------
def recommend_ticket(ticket_text, top_k=3, chunk_hits_k=9, agg="max"):
    """
    Basic recommendation (no chunk snippets) kept for compatibility.
    agg: "max" | "mean" | "hybrid"
    """
    model = load_embedding_model()
    q_vec = get_embedding(model, ticket_text)
    vs = SimpleVectorStore()
    hits = vs.search(q_vec, top_k=chunk_hits_k)

    if agg == "mean":
        scores = aggregate_mean(hits)
    elif agg == "hybrid":
        scores = aggregate_hybrid(hits)
    else:
        scores = aggregate_max(hits)

    # sort and return top_k
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    results = []
    for aid, sc in sorted_items:
        title = next((m["title"] for m in vs.meta if m["article_id"] == aid), "")
        results.append({"article_id": aid, "title": title, "score": float(sc)})
    return results

def recommend_ticket_with_chunks(
    ticket_text,
    top_k=3,
    chunk_hits_k=12,
    agg="hybrid",
    keyword_boost=0.03,
    threshold=0.30,
    title_boost_value=0.03,
    shorten_snippet_len=200
):
    """
    Full recommendation returning best chunk snippet per article.
    - keyword_boost: small additive boost when query and chunk share keywords
    - threshold: minimum score to display an article (fallback to top-1 if none)
    - agg: aggregation method for chunk -> article ("max","mean","hybrid")
    """
    model = load_embedding_model()
    q_vec = get_embedding(model, ticket_text)
    vs = SimpleVectorStore()
    
    # 2. Search
    print(f"DEBUG: Searching for query: '{ticket_text}'")
    chunk_hits = vs.search(q_vec, top_k=chunk_hits_k)
    print(f"DEBUG: Found {len(chunk_hits)} raw hits")
    for h in chunk_hits:
        print(f"DEBUG: Hit: {h['score']:.4f} - {h['meta'].get('chunk_id')}")

    # --- Keyword boosting (conservative list, can be extended later) ---
    query_lower = (ticket_text or "").lower()
    keywords = ["order id", "order", "tracking", "tracking number", "password", "refund", "charged", "login"]
    for h in chunk_hits:
        text_lower = (h["meta"].get("chunk_text", "") or "").lower()
        # if both query and chunk share the same useful token -> small boost
        for kw in keywords:
            if kw in query_lower and kw in text_lower:
                h["score"] = float(h["score"]) + float(keyword_boost)

    # --- Aggregate (max / mean / hybrid) ---
    if agg == "mean":
        article_scores = aggregate_mean(chunk_hits)
    elif agg == "hybrid":
        article_scores = aggregate_hybrid(chunk_hits)
    else:
        article_scores = aggregate_max(chunk_hits)

    # build results with best chunk info (choose chunk with highest score for each article)
    # we need to find the best chunk per article using the (possibly boosted) chunk_hits
    best_chunk_per_article = {}
    for h in chunk_hits:
        aid = h["meta"].get("article_id")
        if aid is None:
            continue
        s = float(h["score"])
        if aid not in best_chunk_per_article or s > best_chunk_per_article[aid]["score"]:
            best_chunk_per_article[aid] = {
                "score": s,
                "chunk_id": h["meta"].get("chunk_id", ""),
                "chunk_text": h["meta"].get("chunk_text", "")
            }

    # prepare result objects
    results = []
    for aid, score in sorted(article_scores.items(), key=lambda x: x[1], reverse=True):
        title = next((m["title"] for m in vs.meta if m["article_id"] == aid), "")
        best = best_chunk_per_article.get(aid, {"chunk_id": "", "chunk_text": "", "score": score})
        results.append({
            "article_id": aid,
            "title": title,
            "score": float(score),
            "best_chunk_id": best.get("chunk_id", ""),
            "best_chunk_text": shorten(best.get("chunk_text", ""), shorten_snippet_len)
        })
        if len(results) >= top_k * 5:
            # safety: don't build huge lists; we'll filter & return top_k anyway
            break

    # apply title-boost re-ranking (small bump for exact token overlap with title)
    results = title_boost(results, ticket_text, boost=title_boost_value)

    # apply thresholding (but ensure at least 1 result available)
    filtered = [r for r in results if r["score"] >= threshold]
    if not filtered:
        filtered = results[:1] if results else []

    final = filtered[:top_k]

    # log query for offline analysis
    try:
        params = {
            "chunk_hits_k": chunk_hits_k,
            "agg": agg,
            "keyword_boost": keyword_boost,
            "threshold": threshold,
            "title_boost_value": title_boost_value
        }
        log_query(ticket_text, ticket_text.lower(), agg, params, final)
    except Exception:
        # logging should not break recommendation
        pass

    return final

# ---------------- CLI/Test harness ----------------
if __name__ == "__main__":
    tests = [
        "I was charged twice and want a refund",
        "I forgot my password and can't login",
        "My order tracking isn't updating"
    ]
    for t in tests:
        print("Query:", t)
        recs = recommend_ticket_with_chunks(t)
        for r in recs:
            print(" -", r["article_id"], r["title"], f"(score={r['score']:.3f})")
            print("    snippet:", r.get("best_chunk_text",""))
        print("----")
