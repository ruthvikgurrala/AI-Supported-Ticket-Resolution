import re
import csv
import os

def split_into_sentences(text):
    text = text.strip()
    sentences = re.split(r'(?<=[\.\?\!])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def make_chunks_from_sentences(sentences, max_chars=400):
    chunks = []
    current = ""

    for s in sentences:
        if len(current) + len(s) + 1 <= max_chars:
            if current:
                current = current + " " + s
            else:
                current = s
        else:
            chunks.append(current)
            current = s 

    if current:
        chunks.append(current)

    return chunks

def chunk_text(text, chunk_size=400, overlap=0):
    """
    Wrapper to chunk raw text into a list of string chunks.
    overlap is currently ignored to keep it simple with existing logic.
    """
    sentences = split_into_sentences(text)
    return make_chunks_from_sentences(sentences, max_chars=chunk_size)



ARTICLES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "articles.csv")
CHUNKS_PATH   = os.path.join(os.path.dirname(__file__), "..", "data", "chunks.csv")

def build_chunks(articles_csv=ARTICLES_PATH, out_csv=CHUNKS_PATH, max_chars=400):
    chunks = []
    with open(articles_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for raw_row in reader:
            row = { (k.strip().lower() if k else k): (v if v is not None else "") for k, v in raw_row.items() }
            aid = row.get('id','').strip()
            title = row.get('title','').strip()
            body = row.get('body','').strip()
            if not body:
                continue
            sentences = split_into_sentences(body)
            piece_list = make_chunks_from_sentences(sentences, max_chars=max_chars)
            for i, chunk_text in enumerate(piece_list):
                chunk_id = f"{aid}_{i}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "article_id": aid,
                    "title": title,
                    "chunk_text": chunk_text
                })

    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ["chunk_id", "article_id", "title", "chunk_text"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in chunks:
            writer.writerow(c)

    print(f"Wrote {len(chunks)} chunks to {out_csv}")


if __name__ == "__main__":
    # call with defaults (reads data/articles.csv and writes data/chunks.csv)
    build_chunks()
