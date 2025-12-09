import os
import csv
import json
import numpy as np
from model_engine import load_embedding_model, get_embedding

ROOT = os.path.join(os.path.dirname(__file__), "..")
CHUNKS_CSV = os.path.join(ROOT, "data", "chunks.csv")
EMB_OUT = os.path.join(ROOT, "models", "chunk_embeddings.npy")
META_OUT = os.path.join(ROOT, "models", "chunk_meta.json")

def read_chunks(csv_path):
    rows = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "chunk_id": r.get("chunk_id", "").strip(),
                "article_id": r.get("article_id", "").strip(),
                "title": r.get("title", "").strip(),
                "chunk_text": r.get("chunk_text", "").strip()
            })
    return rows

def embed_all(chunks, model, batch_size=64):
    texts = [c["chunk_text"] for c in chunks]
    n = len(texts)
    if n == 0:
        return np.zeros((0, 384), dtype="float32"), []

    embeddings = []
    for i in range(0, n, batch_size):
        batch = texts[i:i+batch_size]
        emb = get_embedding(model, batch) 
        if emb is None:
            raise RuntimeError("Embedding returned None for batch starting at %d" % i)
        embeddings.append(emb)
        print(f"Embedded {min(i+batch_size, n)}/{n}")

    embeddings = np.vstack(embeddings).astype("float32")
    return embeddings, chunks

def main(batch_size=64):
    os.makedirs(os.path.join(ROOT, "models"), exist_ok=True)

    print("Reading chunks from:", CHUNKS_CSV)
    chunks = read_chunks(CHUNKS_CSV)
    print("Num chunks:", len(chunks))

    model = load_embedding_model()  
    emb_matrix, meta = embed_all(chunks, model, batch_size=batch_size)

    print("Embeddings shape:", emb_matrix.shape)
    np.save(EMB_OUT, emb_matrix)
    with open(META_OUT, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("Saved embeddings ->", EMB_OUT)
    print("Saved metadata ->", META_OUT)

if __name__ == "__main__":
    main(batch_size=64)
    
