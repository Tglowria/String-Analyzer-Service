import hashlib
import re
from collections import Counter
from datetime import datetime, timezone
from django.utils import timezone as dj_timezone

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def compute_properties(s: str) -> dict:
    """
    Compute required properties for a string:
      - length: number of characters
      - is_palindrome: case-insensitive
      - unique_characters: count of distinct characters
      - word_count: number of words separated by whitespace
      - sha256_hash: SHA-256 hash of the string
      - character_frequency_map: mapping each character to its occurrence count
    """
    try:
        # Input validation
        if not isinstance(s, str):
            raise ValueError("Input must be a string")
            
        if not s.strip():
            raise ValueError("Input string cannot be empty or whitespace only")

        # Calculate string properties
        length = len(s)  # raw length including whitespace
        words = [w for w in s.split() if w]  # split and filter out empty strings
        word_count = len(words)
        
        # Case-insensitive palindrome check
        # Remove spaces and convert to lowercase
        stripped = ''.join(s.lower().split())
        is_palindrome = stripped == stripped[::-1]
        
        # Get unique characters (case-sensitive)
        unique_chars = sorted(set(s))
        unique_count = len(unique_chars)
        
        # Character frequency map (case-sensitive)
        freq_map = {}
        for char in s:
            if char in freq_map:
                freq_map[char] += 1
            else:
                freq_map[char] = 1
        
        # Calculate SHA-256 hash of original string
        sha256_hash = hashlib.sha256(s.encode('utf-8')).hexdigest()

        # Construct final properties dict
        properties = {
            "length": length,
            "is_palindrome": is_palindrome,
            "unique_characters": unique_count,
            "word_count": word_count,
            "sha256_hash": sha256_hash,
            "character_frequency_map": freq_map
        }

        return properties
        
    except Exception as e:
        raise ValueError(f"Error computing string properties: {str(e)}")

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
