from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import torch

_model_cache = None
def load_embedding_model(model_name: str = "all-MiniLM-L6-v2"):
    global _model_cache
    if _model_cache is None:
        device="cuda" if torch.cuda.is_available() else "cpu"
        _model_cache = SentenceTransformer(model_name, device=device)
        print("Loading model all-MiniLM-L6-v2 on "+ device)
    return _model_cache

def get_embedding(model, text):
    if not text:
        return None
    
    if isinstance(text, str):
        embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.astype("float32")
    
    if isinstance(text, list):
        embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.astype("float32")
    
    raise ValueError("Input must be a string or list of strings.")

# Alias for plural usage
get_embeddings = get_embedding

if __name__ == "__main__":
    model = load_embedding_model()
    s = "My payment failed and I need a refund"
    arr = get_embedding(model, s)
    print("Single shape:", arr.shape, "dtype:", arr.dtype)

    texts = [
        "My payment failed and I need a refund",
        "I can't login to my account",
        "Order not delivered tracking not updating"
    ]
    arr2 = get_embedding(model, texts)
    print("List shape:", arr2.shape, "dtype:", arr2.dtype)
