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

def parse_nl_query(q: str) -> dict:
    """Parse natural language query into filter parameters."""
    if not q or not q.strip():
        raise ValueError("Empty query")

    q_lower = q.lower().strip()
    filters = {}
    
    # Palindrome check
    if any(word in q_lower for word in ['palindrome', 'palindromes', 'palindromic']):
        filters['is_palindrome'] = True
    
    # Word count patterns
    word_patterns = [
        r'(\d+) words?',
        r'word count(?: is)? (\d+)',
        r'word count(?: of)? (\d+)',
        r'with (\d+) words?',
        r'that has (\d+) words?',
        r'having (\d+) words?',
        r'(\d+)[- ]word'
    ]
    
    for pattern in word_patterns:
        match = re.search(pattern, q_lower)
        if match:
            filters['word_count'] = int(match.group(1))
            break

    # Length patterns
    length_patterns = {
        'min_length': [
            r'longer than (\d+)(?:\s*characters?)?',
            r'at least (\d+) characters?',
            r'minimum (?:length|characters) (?:of )?(\d+)',
            r'more than (\d+) characters?'
        ],
        'max_length': [
            r'shorter than (\d+)(?:\s*characters?)?',
            r'at most (\d+) characters?',
            r'maximum (?:length|characters) (?:of )?(\d+)',
            r'less than (\d+) characters?'
        ]
    }

    for filter_key, patterns in length_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, q_lower)
            if match:
                val = int(match.group(1))
                if filter_key == 'min_length':
                    filters[filter_key] = val + 1  # exclusive
                else:
                    filters[filter_key] = val - 1  # exclusive
                break

    # Character containment
    char_patterns = [
        r'containing (?:the )?(?:letter )?["\']?(\w)["\']?',
        r'with (?:the )?(?:letter )?["\']?(\w)["\']?',
        r'has (?:the )?(?:letter )?["\']?(\w)["\']?',
        r'contains (?:the )?(?:letter )?["\']?(\w)["\']?',
        r'including (?:the )?(?:letter )?["\']?(\w)["\']?'
    ]
    
    for pattern in char_patterns:
        match = re.search(pattern, q_lower)
        if match:
            filters['contains_character'] = match.group(1)
            break

    if not filters:
        suggestions = [
            "palindrome strings",
            "strings with 3 words",
            "strings longer than 5 characters",
            "strings containing the letter a",
            "strings with word count 2"
        ]
        raise ValueError(f"Could not understand the query. Try phrases like: {', '.join(suggestions)}")

    return filters
