from django.urls import path
from .views import (
    CreateStringView, GetSpecificStringView, ListStringsView,
    NaturalLanguageFilterView, DeleteStringView
)

urlpatterns = [
    path('strings', CreateStringView.as_view(), name='create_string'),            # POST /strings
    path('strings', ListStringsView.as_view(), name='list_strings'),             # GET /strings
    path('strings/filter-by-natural-language', NaturalLanguageFilterView.as_view(), name='nl_filter'),
    # Get/Delete specific string by exact value (URL path captures everything)
    path('strings/<path:string_value>', GetSpecificStringView.as_view(), name='get_string'),
    path('strings/<path:string_value>', DeleteStringView.as_view(), name='delete_string'),
]
