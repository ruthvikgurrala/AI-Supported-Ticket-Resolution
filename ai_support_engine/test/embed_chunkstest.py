import numpy as np, json
if __name__ == "__main__":
    emb = np.load("../models/chunk_embeddings.npy")
    print("shape:", emb.shape, "dtype:", emb.dtype)

    with open("../models/chunk_meta.json","r",encoding="utf-8") as f:
        meta = json.load(f)
    print("meta len:", len(meta))
    print("first item:", meta[0])