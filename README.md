# String Analyzer Service

A RESTful API service that analyzes strings and stores their computed properties. Built with Django and Django REST Framework.

## Features

- String analysis with computed properties:
  - Length calculation
  - Palindrome detection (case-insensitive)
  - Unique character count
  - Word count
  - SHA-256 hash generation
  - Character frequency mapping
- CRUD operations for string management
- Advanced filtering capabilities
- Natural language query support

## Requirements

- Python 3.12+
- Django
- Django REST Framework

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd backend_wizards_stage1
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install django djangorestframework
```

4. Apply database migrations:
```bash
python manage.py migrate
```

5. Run the development server:
```bash
python manage.py runserver
```

## API Endpoints

### 1. Create/Analyze String
```
POST /strings
Content-Type: application/json

{
    "value": "string to analyze"
}
```

**Success Response (201 Created):**
```json
{
    "id": "sha256_hash_value",
    "value": "string to analyze",
    "properties": {
        "length": 16,
        "is_palindrome": false,
        "unique_characters": 12,
        "word_count": 3,
        "sha256_hash": "abc123...",
        "character_frequency_map": {
            "s": 2,
            "t": 3,
            "r": 2
        }
    },
    "created_at": "2025-08-27T10:00:00Z"
}
```

### 2. Get Specific String
```
GET /strings/{string_value}
```

### 3. Get All Strings with Filtering
```
GET /strings?is_palindrome=true&min_length=5&max_length=20&word_count=2&contains_character=a
```

### 4. Natural Language Filtering
```
GET /strings/filter-by-natural-language?query=all%20single%20word%20palindromic%20strings
```

### 5. Delete String
```
DELETE /strings/{string_value}
```

## Query Parameters

- `is_palindrome`: boolean (true/false)
- `min_length`: integer (minimum string length)
- `max_length`: integer (maximum string length)
- `word_count`: integer (exact word count)
- `contains_character`: string (single character to search for)

## Error Responses

- **409 Conflict**: String already exists in the system
- **400 Bad Request**: Invalid request body or missing "value" field
- **422 Unprocessable Entity**: Invalid data type for "value" (must be string)
- **404 Not Found**: String does not exist in the system

## Natural Language Query Examples

- "all single word palindromic strings"
- "strings longer than 10 characters"
- "palindromic strings that contain the first vowel"
- "strings containing the letter z"

## Project Structure

```
backend_wizards_stage1/
├── main/                   # Main project directory
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── strings/               # Strings app directory
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   ├── utils.py
│   └── views.py
├── manage.py
├── README.md
└── requirements.txt
```

## Running Tests

```bash
python manage.py test
```

## Author

Gloria Oluwafemi