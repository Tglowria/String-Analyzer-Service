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

        try:
            # Compute string properties
            properties = compute_properties(value)
            sha = properties['sha256_hash']
            
            # Check for duplicate string
            if AnalyzedString.objects.filter(pk=sha).exists():
                return Response(
                    {"detail": "String already exists in the system"}, 
                    status=status.HTTP_409_CONFLICT
                )
            
            # Create new string entry
            obj = AnalyzedString.objects.create(
                id=sha,
                value=value,
                properties=properties,
                created_at=timezone.now()
            )

            # Return created object
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
        qs = AnalyzedString.objects.all()
        filters_applied = {}

        try:
            # Boolean filter for palindrome
            is_palindrome = request.query_params.get('is_palindrome')
            if is_palindrome is not None:
                if is_palindrome.lower() not in ('true', 'false'):
                    return Response(
                        {"detail": "is_palindrome must be true or false"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                flag = is_palindrome.lower() == 'true'
                qs = [obj for obj in qs if obj.properties.get('is_palindrome') == flag]
                filters_applied['is_palindrome'] = flag

            # Integer filters
            for param in ['min_length', 'max_length', 'word_count']:
                value = request.query_params.get(param)
                if value is not None:
                    try:
                        num = int(value)
                        if num < 0:
                            return Response(
                                {"detail": f"{param} must be non-negative"}, 
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        if param == 'min_length':
                            qs = [obj for obj in qs if obj.properties.get('length', 0) >= num]
                        elif param == 'max_length':
                            qs = [obj for obj in qs if obj.properties.get('length', 0) <= num]
                        else:  # word_count
                            qs = [obj for obj in qs if obj.properties.get('word_count') == num]
                        filters_applied[param] = num
                    except ValueError:
                        return Response(
                            {"detail": f"{param} must be a valid integer"}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )

            # Character filter
            contains_character = request.query_params.get('contains_character')
            if contains_character is not None:
                if len(contains_character) != 1:
                    return Response(
                        {"detail": "contains_character must be a single character"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                qs = [obj for obj in qs if contains_character in obj.value]
                filters_applied['contains_character'] = contains_character

            # Check if min_length > max_length
            if ('min_length' in filters_applied and 
                'max_length' in filters_applied and 
                filters_applied['min_length'] > filters_applied['max_length']):
                return Response(
                    {"detail": "min_length cannot be greater than max_length"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Prepare response
            results = [obj.to_response() for obj in qs]
            return Response({
                "data": results,
                "count": len(results),
                "filters_applied": filters_applied
            })

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
            obj = get_object_or_404(AnalyzedString, value=string_value)
            return Response(obj.to_response())
        except AnalyzedString.DoesNotExist:
            return Response(
                {"detail": "String does not exist in the system"}, 
                status=status.HTTP_404_NOT_FOUND
            )
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
            obj = AnalyzedString.objects.get(value=string_value)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AnalyzedString.DoesNotExist:
            return Response(
                {"detail": "String does not exist in the system"}, 
                status=status.HTTP_404_NOT_FOUND
            )
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
                {"detail": "Query parameter is required and cannot be empty"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Parse natural language query
            parsed = parse_nl_query(query)
            if not parsed:
                return Response(
                    {
                        "detail": "Could not understand the query",
                        "suggestions": [
                            "Try using simple phrases like 'palindromes', 'strings with 5 words'",
                            "Include specific criteria like 'length greater than 10'",
                            "Specify character content like 'contains the letter a'"
                        ]
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate parsed filters
            if 'word_count' in parsed and (not isinstance(parsed['word_count'], int) or parsed['word_count'] < 0):
                return Response(
                    {"detail": "Invalid word count in query"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'min_length' in parsed and (not isinstance(parsed['min_length'], int) or parsed['min_length'] < 0):
                return Response(
                    {"detail": "Invalid minimum length in query"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'max_length' in parsed and (not isinstance(parsed['max_length'], int) or parsed['max_length'] < 0):
                return Response(
                    {"detail": "Invalid maximum length in query"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'min_length' in parsed and 'max_length' in parsed and parsed['min_length'] > parsed['max_length']:
                return Response(
                    {"detail": "Minimum length cannot be greater than maximum length"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            if 'contains_character' in parsed and len(parsed['contains_character']) != 1:
                return Response(
                    {"detail": "Character filter must be a single character"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Apply filters
            qs = AnalyzedString.objects.all()
            
            if 'is_palindrome' in parsed:
                qs = [obj for obj in qs if obj.properties.get('is_palindrome') == parsed['is_palindrome']]
            if 'word_count' in parsed:
                qs = [obj for obj in qs if obj.properties.get('word_count') == parsed['word_count']]
            if 'min_length' in parsed:
                qs = [obj for obj in qs if obj.properties.get('length', 0) >= parsed['min_length']]
            if 'max_length' in parsed:
                qs = [obj for obj in qs if obj.properties.get('length', 0) <= parsed['max_length']]
            if 'contains_character' in parsed:
                qs = [obj for obj in qs if parsed['contains_character'] in obj.value]

            results = [obj.to_response() for obj in qs]
            
            return Response({
                "data": results,
                "count": len(results),
                "interpreted_query": {
                    "original": query,
                    "parsed_filters": parsed,
                    "applied_criteria": {
                        key: value for key, value in parsed.items() 
                        if key in ['is_palindrome', 'word_count', 'min_length', 'max_length', 'contains_character']
                    }
                }
            })

        except ValueError as e:
            return Response(
                {"detail": f"Invalid query parameter: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"Error processing query: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
