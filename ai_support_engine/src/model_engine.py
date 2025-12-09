import os
import openai
from dotenv import load_dotenv
import numpy as np

load_dotenv()

# Global client
_client = None

def load_embedding_model(model_name: str = "text-embedding-3-small"):
    """
    In the OpenAI version, this just initializes the client if needed.
    The 'model_name' argument is kept for compatibility but defaults to OpenAI's model.
    """
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("[WARN] OPENAI_API_KEY not found. Embeddings will fail.")
        _client = openai.OpenAI(api_key=api_key)
        print(f"Initialized OpenAI Client for embeddings ({model_name})")
    return _client

def get_embedding(model, text):
    """
    Fetches embeddings from OpenAI API.
    'model' here is the OpenAI client instance.
    """
    if not text:
        return None
    
    # Ensure client is ready
    client = model or load_embedding_model()
    model_id = "text-embedding-3-small"

    try:
        # Handle string input
        if isinstance(text, str):
            text = text.replace("\n", " ")
            response = client.embeddings.create(input=[text], model=model_id)
            return np.array(response.data[0].embedding, dtype="float32")
        
        # Handle list input
        if isinstance(text, list):
            # OpenAI recommends batching, but for simplicity we send the list
            # Ensure no newlines
            clean_texts = [t.replace("\n", " ") for t in text]
            response = client.embeddings.create(input=clean_texts, model=model_id)
            # Map results back to order
            embeddings = [item.embedding for item in response.data]
            return np.array(embeddings, dtype="float32")
            
    except Exception as e:
        print(f"[ERROR] Embedding generation failed: {e}")
        return None

    raise ValueError("Input must be a string or list of strings.")

# Alias for compatibility
get_embeddings = get_embedding

if __name__ == "__main__":
    client = load_embedding_model()
    s = "My payment failed and I need a refund"
    arr = get_embedding(client, s)
    if arr is not None:
        print("Single shape:", arr.shape, "dtype:", arr.dtype)
    else:
        print("Failed to get embedding")

