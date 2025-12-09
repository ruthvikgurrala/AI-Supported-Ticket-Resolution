# src/vector_store.py
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

ROOT = os.path.join(os.path.dirname(__file__), "..")
EMB_PATH = os.path.join(ROOT, "models", "chunk_embeddings.npy")
META_PATH = os.path.join(ROOT, "models", "chunk_meta.json")

class SimpleVectorStore:
    def __init__(self, emb_path=EMB_PATH, meta_path=META_PATH):
        if not os.path.exists(emb_path):
            raise FileNotFoundError(f"Embeddings not found: {emb_path}")
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"Metadata not found: {meta_path}")

        self.emb = np.load(emb_path)           # shape: (N, D)
        with open(meta_path, "r", encoding="utf-8") as f:
            self.meta = json.load(f)           # list of dicts
        # small sanity checks
        if len(self.meta) != self.emb.shape[0]:
            print("Warning: meta length and embeddings count mismatch.")
        # pre-normalize if not already normalized (cosine on normalized vectors = dot product)
        # but we used normalize_embeddings=True earlier, so vectors are already normalized.
    
    def search(self, query_vec, top_k=5):
        """
        query_vec: 1D numpy array shape (D,)
        returns list of hits: {idx, score, meta}
        """
        if query_vec is None:
            return []
        # Ensure shape
        q = query_vec.reshape(1, -1)
        sims = cosine_similarity(q, self.emb)[0]   # (N,)
        idxs = sims.argsort()[-top_k:][::-1]
        hits = []
        for i in idxs:
            hits.append({
                "idx": int(i),
                "score": float(sims[i]),
                "meta": self.meta[i]
            })
        return hits

    def get_all_chunks(self):
        """Returns all chunks with their metadata."""
        return self.meta

    def delete_chunk(self, chunk_id):
        """Deletes a chunk by its chunk_id."""
        # Find index
        idx_to_remove = -1
        for i, m in enumerate(self.meta):
            if m.get("chunk_id") == chunk_id:
                idx_to_remove = i
                break
        
        if idx_to_remove == -1:
            return False # Not found

        # Remove from meta
        self.meta.pop(idx_to_remove)
        
        # Remove from emb
        self.emb = np.delete(self.emb, idx_to_remove, axis=0)

        # Save to disk
        self._save()
        return True

    def _save(self):
        """Saves current embeddings and metadata to disk."""
        np.save(EMB_PATH, self.emb)
        with open(META_PATH, "w", encoding="utf-8") as f:
            json.dump(self.meta, f, indent=2)

if __name__ == "__main__":
    # quick smoke test
    vs = SimpleVectorStore()
    print("Loaded vector store. Embeddings shape:", vs.emb.shape, "meta len:", len(vs.meta))
    # dummy zero vector test (will return top arbitrary chunks)
    import numpy as np
    q = np.zeros(vs.emb.shape[1], dtype="float32")
    print("Top hits for zero vector:", vs.search(q, top_k=3))
