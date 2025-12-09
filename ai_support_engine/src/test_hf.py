# save as test_router_check.py and run: python test_router_check.py
from dotenv import load_dotenv
import os, requests
load_dotenv()
token = os.getenv("inferenceapi")
print("TOKEN_LOADED:", bool(token))
url = "https://router.huggingface.co/hf-inference/google/flan-t5-large"
r = requests.post(url,
                  headers={"Authorization": f"Bearer {token}", "Content-Type":"application/json"},
                  json={"inputs":"Say hi in one short sentence."},
                  timeout=20)
print("status:", r.status_code)
print("text_preview:", r.text[:400])
