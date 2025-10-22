from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import AnalyzedString
from .utils import compute_properties, parse_nl_query

class StringsView(APIView):
    """Handle POST /strings (create) and GET /strings (list/filter)"""
    
    def post(self, request):
        """Create a new analyzed string"""
        if 'value' not in request.data:
            return Response({"detail": "Missing 'value' field"}, status=status.HTTP_400_BAD_REQUEST)
        
        value = request.data['value']
        
        if not isinstance(value, str):
            return Response({"detail": "'value' must be a string"}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        # Calculate properties first to avoid DB write if there's an error
        try:
            properties = compute_properties(value)
            sha = properties['sha256_hash']  # Get hash from properties
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if AnalyzedString.objects.filter(pk=sha).exists():
            return Response({"detail": "String already exists"}, status=status.HTTP_409_CONFLICT)

        try:
            obj = AnalyzedString.objects.create(
                id=sha,
                value=value,
                properties=properties,
                created_at=timezone.now()
            )
            return Response(obj.to_response(), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetSpecificStringView(APIView):
    def get(self, request, string_value):
        # string_value is URL-decoded by Django; find the object by exact value
        obj = get_object_or_404(AnalyzedString, value=string_value)
        return Response(obj.to_response())


class DeleteStringView(APIView):
    def delete(self, request, string_value):
        try:
            obj = AnalyzedString.objects.get(value=string_value)
        except AnalyzedString.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


    def get(self, request):
        qs = AnalyzedString.objects.all()

        # Parse filters from query params
        is_palindrome = request.query_params.get('is_palindrome')
        min_length = request.query_params.get('min_length')
        max_length = request.query_params.get('max_length')
        word_count = request.query_params.get('word_count')
        contains_character = request.query_params.get('contains_character')

        try:
            if is_palindrome is not None:
                if is_palindrome.lower() not in ('true', 'false'):
                    raise ValueError("is_palindrome must be true/false")
                flag = is_palindrome.lower() == 'true'
                qs = [obj for obj in qs if obj.properties.get('is_palindrome') == flag]

            if min_length is not None:
                mn = int(min_length)
                qs = [obj for obj in qs if obj.properties.get('length', 0) >= mn]

            if max_length is not None:
                mx = int(max_length)
                qs = [obj for obj in qs if obj.properties.get('length', 0) <= mx]

            if word_count is not None:
                wc = int(word_count)
                qs = [obj for obj in qs if obj.properties.get('word_count') == wc]

            if contains_character is not None:
                if len(contains_character) != 1:
                    return Response({"detail": "contains_character must be a single character"}, status=status.HTTP_400_BAD_REQUEST)
                ch = contains_character
                qs = [obj for obj in qs if ch in obj.value]
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # If qs is a QuerySet convert to list early; we used in-memory lists for JSONField lookups
        if hasattr(qs, '__iter__') and not hasattr(qs, 'filter'):
            results = [obj.to_response() for obj in qs]
            count = len(results)
        else:
            results = [obj.to_response() for obj in qs]
            count = len(results)

        filters_applied = {}
        if is_palindrome is not None: filters_applied['is_palindrome'] = is_palindrome.lower() == 'true'
        if min_length is not None: filters_applied['min_length'] = int(min_length)
        if max_length is not None: filters_applied['max_length'] = int(max_length)
        if word_count is not None: filters_applied['word_count'] = int(word_count)
        if contains_character is not None: filters_applied['contains_character'] = contains_character

        return Response({
            "data": results,
            "count": count,
            "filters_applied": filters_applied
        })





class NaturalLanguageFilterView(APIView):
    def get(self, request):
        q = request.query_params.get('query', '')
        try:
            parsed = parse_nl_query(q)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # convert parsed filters into a query by reusing logic from ListStringsView
        # Build a pseudo-request for ListStringsView
        fake_request = request
        # apply parsed filters by filtering queryset directly
        qs = AnalyzedString.objects.all()
        # apply possible parsed filters:
        if 'is_palindrome' in parsed:
            qs = [obj for obj in qs if obj.properties.get('is_palindrome') == parsed['is_palindrome']]
        if 'word_count' in parsed:
            wc = parsed['word_count']
            qs = [obj for obj in qs if obj.properties.get('word_count') == wc]
        if 'min_length' in parsed:
            mn = parsed['min_length']
            qs = [obj for obj in qs if obj.properties.get('length', 0) >= mn]
        if 'max_length' in parsed:
            mx = parsed['max_length']
            qs = [obj for obj in qs if obj.properties.get('length', 0) <= mx]
        if 'contains_character' in parsed:
            ch = parsed['contains_character']
            qs = [obj for obj in qs if ch in obj.value]

        results = [obj.to_response() for obj in qs]
        return Response({
            "data": results,
            "count": len(results),
            "interpreted_query": {
                "original": q,
                "parsed_filters": parsed
            }
        })
