from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import AnalyzedString
from .utils import compute_properties, parse_nl_query

class StringsView(APIView):
    """Handle POST /strings (create) and GET /strings (list/filter)"""
    
    def post(self, request):
        """
        Create/Analyze String endpoint
        POST /strings
        Request Body: {"value": "string to analyze"}
        """
        # Check for missing value field
        if 'value' not in request.data:
            return Response(
                {"detail": "Missing 'value' field"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        value = request.data.get('value')
        
        # Validate value type
        if not isinstance(value, str):
            return Response(
                {"detail": "Invalid data type for 'value' (must be string)"}, 
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )

        # Check for empty string
        if not value.strip():
            return Response(
                {"detail": "String value cannot be empty or whitespace only"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Compute string properties
            properties = compute_properties(value)
            
            # Check for duplicate string by value, not by hash
            if AnalyzedString.objects.filter(value=value).exists():
                return Response(
                    {"detail": "String already exists in the system"}, 
                    status=status.HTTP_409_CONFLICT
                )
            
            # Create new string entry
            obj = AnalyzedString.objects.create(
                id=properties['sha256_hash'],
                value=value,
                properties=properties,
                created_at=timezone.now()
            )

            # Return created object with 201 Created status
            return Response(obj.to_response(), status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"Internal server error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    def get(self, request):
        """
        Get All Strings with Filtering
        GET /strings?is_palindrome=true&min_length=5&max_length=20&word_count=2&contains_character=a
        """
        try:
            # Start with all strings
            qs = list(AnalyzedString.objects.all())
            filters_applied = {}

            # Check for filters
            filter_params = request.query_params

            # Palindrome filter
            if 'is_palindrome' in filter_params:
                palindrome = filter_params['is_palindrome'].lower()
                if palindrome not in ('true', 'false'):
                    return Response(
                        {"detail": "is_palindrome must be 'true' or 'false'"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                is_palindrome = palindrome == 'true'
                qs = [obj for obj in qs if obj.properties.get('is_palindrome') == is_palindrome]
                filters_applied['is_palindrome'] = is_palindrome

            # Length filters
            min_length = filter_params.get('min_length')
            max_length = filter_params.get('max_length')
            
            if min_length is not None:
                try:
                    min_len = int(min_length)
                    if min_len < 0:
                        return Response(
                            {"detail": "min_length must be non-negative"}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    qs = [obj for obj in qs if obj.properties.get('length', 0) >= min_len]
                    filters_applied['min_length'] = min_len
                except ValueError:
                    return Response(
                        {"detail": "min_length must be a valid integer"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            if max_length is not None:
                try:
                    max_len = int(max_length)
                    if max_len < 0:
                        return Response(
                            {"detail": "max_length must be non-negative"}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    qs = [obj for obj in qs if obj.properties.get('length', 0) <= max_len]
                    filters_applied['max_length'] = max_len
                except ValueError:
                    return Response(
                        {"detail": "max_length must be a valid integer"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Check length constraints
            if min_length is not None and max_length is not None:
                if int(min_length) > int(max_length):
                    return Response(
                        {"detail": "min_length cannot be greater than max_length"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Word count filter
            if 'word_count' in filter_params:
                try:
                    count = int(filter_params['word_count'])
                    if count < 0:
                        return Response(
                            {"detail": "word_count must be non-negative"}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    qs = [obj for obj in qs if obj.properties.get('word_count') == count]
                    filters_applied['word_count'] = count
                except ValueError:
                    return Response(
                        {"detail": "word_count must be a valid integer"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Contains character filter
            contains_char = filter_params.get('contains_character')
            if contains_char is not None:
                if not isinstance(contains_char, str) or len(contains_char) != 1:
                    return Response(
                        {"detail": "contains_character must be a single character"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                qs = [obj for obj in qs if contains_char in obj.value]
                filters_applied['contains_character'] = contains_char

            # Prepare response
            results = [obj.to_response() for obj in qs]

            # Build response with metadata
            response_data = {
                "data": results,
                "count": len(results),
                "filters_applied": filters_applied
            }

            return Response(response_data)

        except ValueError as e:
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"Internal server error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetSpecificStringView(APIView):
    """Handle GET and DELETE /strings/{string_value}"""

    def get(self, request, string_value):
        """
        Get Specific String
        GET /strings/{string_value}
        """
        if not string_value:
            return Response(
                {"detail": "String value is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Use filter().first() instead of get() to handle DoesNotExist more gracefully
            obj = AnalyzedString.objects.filter(value=string_value).first()
            if not obj:
                return Response(
                    {"detail": "String does not exist in the system"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(obj.to_response())
            
        except Exception as e:
            return Response(
                {"detail": f"Internal server error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request, string_value):
        """
        Delete String
        DELETE /strings/{string_value}
        """
        if not string_value:
            return Response(
                {"detail": "String value is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            obj = AnalyzedString.objects.filter(value=string_value).first()
            if not obj:
                return Response(
                    {"detail": "String does not exist in the system"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Exception as e:
            return Response(
                {"detail": f"Internal server error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )








class NaturalLanguageFilterView(APIView):
    """Handle GET /strings/filter-by-natural-language"""

    def get(self, request):
        """
        Filter Strings Using Natural Language
        GET /strings/filter-by-natural-language?query=your query here
        """
        # Validate query parameter
        query = request.query_params.get('query', '').strip()
        if not query:
            return Response(
                {"detail": "Query parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Parse natural language query
            try:
                parsed = parse_nl_query(query)
                if not parsed:
                    raise ValueError("Could not understand the query")
            except ValueError as e:
                return Response(
                    {
                        "detail": str(e),
                        "suggestions": [
                            "Try using phrases like 'palindromes'",
                            "Try 'strings with N words' where N is a number",
                            "Try 'strings longer than N characters'",
                            "Try 'strings containing the letter X'",
                            "Try 'strings with word count N'"
                        ]
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Convert queryset to list for in-memory filtering
            qs = list(AnalyzedString.objects.all())
            
            # Apply filters
            if 'is_palindrome' in parsed:
                qs = [obj for obj in qs if obj.properties.get('is_palindrome') == parsed['is_palindrome']]
            
            if 'word_count' in parsed:
                if not isinstance(parsed['word_count'], int) or parsed['word_count'] < 0:
                    return Response(
                        {"detail": "Invalid word count value"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                qs = [obj for obj in qs if obj.properties.get('word_count') == parsed['word_count']]
            
            if 'min_length' in parsed:
                if not isinstance(parsed['min_length'], int) or parsed['min_length'] < 0:
                    return Response(
                        {"detail": "Invalid minimum length value"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                qs = [obj for obj in qs if obj.properties.get('length', 0) >= parsed['min_length']]
            
            if 'max_length' in parsed:
                if not isinstance(parsed['max_length'], int) or parsed['max_length'] < 0:
                    return Response(
                        {"detail": "Invalid maximum length value"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                qs = [obj for obj in qs if obj.properties.get('length', 0) <= parsed['max_length']]
                
            if 'contains_character' in parsed:
                if not isinstance(parsed['contains_character'], str) or len(parsed['contains_character']) != 1:
                    return Response(
                        {"detail": "Character filter must be a single character"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                qs = [obj for obj in qs if parsed['contains_character'] in obj.value]

            # Length constraint validation
            if 'min_length' in parsed and 'max_length' in parsed:
                if parsed['min_length'] > parsed['max_length']:
                    return Response(
                        {"detail": "Minimum length cannot be greater than maximum length"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Convert matching objects to response format
            results = [obj.to_response() for obj in qs]
            
            # Build response with metadata
            response_data = {
                "data": results,
                "count": len(results),
                "interpreted_query": {
                    "original": query,
                    "understood_filters": parsed
                }
            }

            return Response(response_data)

        except ValueError as e:
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
