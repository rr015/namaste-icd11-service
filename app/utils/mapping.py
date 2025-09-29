# app/utils/mapping.py
from typing import Dict, List, Optional
from rapidfuzz import process

# Synonym mapping for common terms
SYNONYM_MAP = {
    "fever": ["jwara", "jvar", "pyrexia", "temperature"],
    "diarrhea": ["atisara", "loose motions", "dysentery"],
    "anemia": ["pandu", "raktalpata", "pallor"],
    "diabetes": ["madhumeha", "sugar disease", "prameha"],
    "arthritis": ["amavata", "sandhivata", "joint inflammation"],
    "tb": ["rajayakshma", "tuberculosis", "kshaya roga"],
    "asthma": ["shwasa", "breathing difficulty", "dyspnea"],
    "piles": ["arsha", "hemorrhoids", "bawaseer"],
    "skin disease": ["kushtha", "dermatitis", "twak roga"],
    "mental disorder": ["unmada", "psychosis", "mana vikara"]
}

def expand_synonyms(query: str) -> List[str]:
    """Expand query with synonyms"""
    expanded = [query.lower()]
    for key, synonyms in SYNONYM_MAP.items():
        if query.lower() in synonyms or any(syn in query.lower() for syn in synonyms):
            expanded.extend(synonyms)
            expanded.append(key)
    return list(set(expanded))

def map_abbreviations(query: str) -> str:
    """Map common abbreviations to full forms"""
    abbreviation_map = {
        "ra": "rheumatoid arthritis",
        "oa": "osteoarthritis",
        "tb": "tuberculosis",
        "dm": "diabetes mellitus",
        "cvd": "cardiovascular disease",
        "mi": "myocardial infarction",
        "copd": "chronic obstructive pulmonary disease",
        "uti": "urinary tract infection",
        "ari": "acute respiratory infection",
        "pid": "pelvic inflammatory disease"
    }
    
    for abbr, full in abbreviation_map.items():
        if query.lower() == abbr:
            return full
    return query