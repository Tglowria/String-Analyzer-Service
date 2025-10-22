import hashlib
import re
from collections import Counter
from datetime import datetime, timezone
from django.utils import timezone as dj_timezone

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def compute_properties(s: str, ignore_non_alnum_for_palindrome: bool = False) -> dict:
    """
    Compute required properties:
      - length: number of characters
      - is_palindrome: case-insensitive (optional: ignore non-alnum)
      - unique_characters: number of distinct characters
      - word_count: number of whitespace-separated words
      - sha256_hash: hex
      - character_frequency_map: dict char -> count
    """
    length = len(s)
    # Palindrome check
    if ignore_non_alnum_for_palindrome:
        cleaned = re.sub(r'[^A-Za-z0-9]', '', s).lower()
    else:
        cleaned = s.lower()
    is_palindrome = cleaned == cleaned[::-1]

    unique_characters = len(set(s))
    word_count = 0 if s.strip() == "" else len(re.findall(r'\S+', s))
    sha = sha256_hex(s)
    freq_map = dict(Counter(s))

    properties = {
        "length": length,
        "is_palindrome": is_palindrome,
        "unique_characters": unique_characters,
        "word_count": word_count,
        "sha256_hash": sha,
        "character_frequency_map": freq_map
    }
    return properties

# Basic natural language parser for filters
def parse_nl_query(q: str) -> dict:
    """
    Returns dict of parsed filters or raises ValueError on unparseable queries.
    Supports these heuristics:
      - "single word" -> word_count = 1
      - "palindrom" -> is_palindrome = True
      - "strings longer than N characters" -> min_length = N+1
      - "longer than N characters" or "longer than N" -> min_length = N+1
      - "strings containing the letter x" -> contains_character = x
      - "strings containing the letter z" or "contain letter z"
      - "strings with word count N" -> word_count = N
    """
    if not q or not q.strip():
        raise ValueError("Empty query")

    q_lower = q.lower()
    filters = {}

    # single word
    if re.search(r'\bsingle word\b', q_lower):
        filters['word_count'] = 1

    # palindrome
    if 'palindrom' in q_lower:  # matches palindrome/palindromic
        filters['is_palindrome'] = True

    # longer than N characters
    m = re.search(r'longer than (\d+)', q_lower)
    if m:
        n = int(m.group(1))
        # "longer than 10 characters" means min_length = 11
        filters['min_length'] = n + 1

    # strings longer than N characters (the example "longer than 10 characters")
    m2 = re.search(r'longer than (\d+)\s*characters', q_lower)
    if m2:
        n = int(m2.group(1))
        filters['min_length'] = n + 1

    # contains letter x / containing the letter x
    m3 = re.search(r'contain(?:s|ing)?(?: the)? letter (\w)', q_lower)
    if m3:
        filters['contains_character'] = m3.group(1)

    # containing the letter x (alternative phrasing)
    m4 = re.search(r'containing the letter (\w)', q_lower)
    if m4:
        filters['contains_character'] = m4.group(1)

    # strings containing the letter z
    m5 = re.search(r'containing the letter (\w)', q_lower)
    if m5:
        filters['contains_character'] = m5.group(1)

    # exactly "strings containing the letter z"
    m6 = re.search(r'containing the letter (\w)', q_lower)
    if m6:
        filters['contains_character'] = m6.group(1)

    # word count N
    m7 = re.search(r'word count(?: of)? (\d+)', q_lower)
    if m7:
        filters['word_count'] = int(m7.group(1))

    # fallback: if no filters parsed, raise
    if not filters:
        raise ValueError("Unable to parse natural language query")

    return filters
