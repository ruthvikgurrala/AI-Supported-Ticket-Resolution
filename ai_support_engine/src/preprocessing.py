import re
import emoji
from nltk.corpus import stopwords

def clean_text(text):
    text = to_lowercase(text)
    text = normalize_apostrophes(text)
    text = remove_emojis(text)
    text = remove_small_numbers(text)
    text = remove_punctuation(text)
    tokens = tokenize(text)
    clean_tokens = remove_stopwords(tokens)
    cleaned_text = " ".join(clean_tokens)
    cleaned_text = normalize_spaces(cleaned_text)
    return cleaned_text

def to_lowercase(text):
    return text.lower()

def normalize_apostrophes(text):
    return text.replace("’", "'")

def remove_emojis(text):
    return emoji.replace_emoji(text, replace='')

def remove_small_numbers(text):
    return re.sub(r"\b\d{1,4}\b", " ", text)

def remove_punctuation(text):
    return re.sub(r"[^\w\s']", " ", text)

def tokenize(text):
    return text.split()

def remove_stopwords(tokens):
    stop_words = set(stopwords.words("english"))
    negations = {
    "no", "not", "never",
    "dont", "don't", "dont'", 
    "didnt", "didn't", "didn’t",
    "wont", "won't", "won’t",
    "cant", "can't", "can’t"
    }

    clean_stopwords = stop_words - negations
    return [word for word in tokens if word not in clean_stopwords]

def normalize_spaces(text):
    return " ".join(text.split())

if __name__ == "__main__":
    sample = "My payment failed!! But I didn't get any refund 😭😭  !!!!"
    sample2="My payment failed but I was charged twice."
    sample3="I can't login to my account, forgot password."
    sample4="Order not delivered, tracking not updating."
    sample5="Received wrong item, need to return."
    print(clean_text(sample))
    print(clean_text(sample2))
    print(clean_text(sample3))
    print(clean_text(sample4))
    print(clean_text(sample5))
    
