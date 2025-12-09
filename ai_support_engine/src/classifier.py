# src/classifier.py
from typing import List, Tuple

def classify_ticket(text: str) -> dict:
    """
    Analyzes ticket text to return tags, sentiment, and priority.
    """
    text_lower = text.lower()
    tags = []
    
    # 1. Tagging
    keywords = {
        "billing": ["bill", "invoice", "charge", "payment", "cost", "price", "subscription", "refund"],
        "technical": ["error", "bug", "fail", "crash", "login", "password", "access", "connect", "broken"],
        "account": ["account", "profile", "email", "username", "settings", "reset"],
        "feature_request": ["feature", "request", "add", "improve", "suggestion", "idea"],
        "urgent": ["urgent", "asap", "immediately", "critical", "emergency"]
    }

    for tag, words in keywords.items():
        if any(w in text_lower for w in words):
            tags.append(tag)

    if not tags:
        tags.append("general")
    
    tags = list(set(tags))

    # 2. Sentiment Analysis (Simple Keyword-based)
    # In a real app, use NLTK or a Transformer model
    positive_words = ["great", "awesome", "thanks", "thank", "good", "love", "helpful", "best"]
    negative_words = ["bad", "terrible", "worst", "hate", "angry", "upset", "fail", "broken", "slow", "useless", "waiting"]
    
    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    
    sentiment = "neutral"
    if neg_count > pos_count:
        sentiment = "negative"
    elif pos_count > neg_count:
        sentiment = "positive"

    # 3. Priority Assignment
    priority = "medium"
    if "urgent" in tags or sentiment == "negative":
        priority = "high"
    elif "feature_request" in tags and sentiment == "positive":
        priority = "low"

    return {
        "tags": tags,
        "sentiment": sentiment,
        "priority": priority
    }
