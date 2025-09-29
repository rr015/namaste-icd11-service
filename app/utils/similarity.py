# app/utils/similarity.py
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re
from typing import List

# Initialize the sentence transformer model
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def semantic_similarity(text1: str, text2: str) -> float:
    """Calculate semantic similarity between two texts"""
    embeddings = model.encode([text1, text2])
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(similarity)

def stem_word(word: str) -> str:
    """Simple stemmer for medical terms"""
    # Remove common suffixes
    suffixes = ['ing', 'ed', 's', 'es', 'ies', 'ly']
    for suffix in suffixes:
        if word.endswith(suffix):
            word = word[:-len(suffix)]
            break
    return word

def extract_keywords(text: str) -> List[str]:
    """Extract keywords from text"""
    # Remove stopwords and extract meaningful terms
    stopwords = {'the', 'and', 'or', 'in', 'of', 'for', 'with', 'to', 'a', 'an'}
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    keywords = [stem_word(word) for word in words if word not in stopwords and len(word) > 2]
    return keywords