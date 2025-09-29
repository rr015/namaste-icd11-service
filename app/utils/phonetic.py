# app/utils/phonetic.py
import rapidfuzz
from rapidfuzz import fuzz, process
from typing import List

def phonetic_similarity(word1: str, word2: str) -> float:
    """Calculate phonetic similarity between two words"""
    return fuzz.ratio(word1.lower(), word2.lower()) / 100

def find_phonetic_matches(query: str, choices: List[str], threshold: float = 0.7) -> List[str]:
    """Find phonetic matches for a query"""
    results = process.extract(query, choices, scorer=fuzz.ratio, limit=5)
    return [result[0] for result in results if result[1] / 100 >= threshold]

def normalize_text(text: str) -> str:
    """Normalize text for search"""
    # Remove special characters and convert to lowercase
    normalized = ''.join(c for c in text if c.isalnum() or c.isspace()).lower()
    return normalized