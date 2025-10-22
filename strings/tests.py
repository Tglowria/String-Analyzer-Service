from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from .models import AnalyzedString
from .utils import compute_properties, parse_nl_query
import json

class StringAnalyzerTests(APITestCase):
    def setUp(self):
        # Create some test strings
        self.test_strings = [
            "racecar",  # palindrome, 7 chars, 1 word
            "Hello World",  # not palindrome, 11 chars, 2 words
            "A man a plan a canal Panama",  # palindrome with spaces
        ]
        
        # Create initial test data
        for s in self.test_strings:
            properties = compute_properties(s)
            AnalyzedString.objects.create(
                id=properties['sha256_hash'],
                value=s,
                properties=properties
            )

    def test_create_string(self):
        """Test string creation endpoint"""
        # Test valid string creation
        response = self.client.post('/strings', {'value': 'test string'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['value'], 'test string')
        
        # Test duplicate string
        response = self.client.post('/strings', {'value': 'test string'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        
        # Test missing value
        response = self.client.post('/strings', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid type
        response = self.client.post('/strings', {'value': 123}, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_get_specific_string(self):
        """Test getting a specific string"""
        # Test existing string
        response = self.client.get('/strings/racecar')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['value'], 'racecar')
        self.assertTrue(response.data['properties']['is_palindrome'])
        
        # Test non-existent string
        response = self.client.get('/strings/nonexistent')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_strings(self):
        """Test string filtering"""
        # Test palindrome filter
        response = self.client.get('/strings?is_palindrome=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)  # racecar and Panama
        
        # Test length filter
        response = self.client.get('/strings?min_length=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)  # Hello World and Panama
        
        # Test word count filter
        response = self.client.get('/strings?word_count=2')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 1)  # Hello World
        
        # Test character filter
        response = self.client.get('/strings?contains_character=a')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all('a' in item['value'] for item in response.data['data']))

    def test_natural_language_filter(self):
        """Test natural language filtering"""
        # Test palindrome query
        response = self.client.get('/strings/filter-by-natural-language?query=all palindromic strings')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(item['properties']['is_palindrome'] for item in response.data['data']))
        
        # Test length query
        response = self.client.get('/strings/filter-by-natural-language?query=strings longer than 5 characters')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(item['properties']['length'] > 5 for item in response.data['data']))
        
        # Test invalid query
        response = self.client.get('/strings/filter-by-natural-language?query=invalid query format')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_string(self):
        """Test string deletion"""
        # Test deleting existing string
        response = self.client.delete('/strings/racecar')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify it's deleted
        response = self.client.get('/strings/racecar')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test deleting non-existent string
        response = self.client.delete('/strings/nonexistent')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class UtilsTests(TestCase):
    def test_compute_properties(self):
        """Test string property computation"""
        # Test basic string
        props = compute_properties("hello")
        self.assertEqual(props['length'], 5)
        self.assertEqual(props['unique_characters'], 4)
        self.assertEqual(props['word_count'], 1)
        self.assertFalse(props['is_palindrome'])
        
        # Test palindrome
        props = compute_properties("A man a plan a canal Panama")
        self.assertTrue(props['is_palindrome'])
        self.assertEqual(props['word_count'], 7)
        
        # Test empty string
        props = compute_properties("")
        self.assertEqual(props['length'], 0)
        self.assertEqual(props['word_count'], 0)
        self.assertTrue(props['is_palindrome'])

    def test_parse_nl_query(self):
        """Test natural language query parsing"""
        # Test palindrome query
        parsed = parse_nl_query("find all palindromic strings")
        self.assertTrue(parsed['is_palindrome'])
        
        # Test length query
        parsed = parse_nl_query("strings longer than 10 characters")
        self.assertEqual(parsed['min_length'], 11)
        
        # Test word count
        parsed = parse_nl_query("strings with word count 2")
        self.assertEqual(parsed['word_count'], 2)
        
        # Test character contains
        parsed = parse_nl_query("strings containing the letter a")
        self.assertEqual(parsed['contains_character'], 'a')
