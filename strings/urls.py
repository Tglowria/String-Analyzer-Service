from django.urls import path
from .views import (
    StringsView, GetSpecificStringView, NaturalLanguageFilterView
)

urlpatterns = [
    # POST /strings (create) and GET /strings (list/filter)
    path('strings', StringsView.as_view(), name='strings'),
    # Natural language filtering
    path('strings/filter-by-natural-language', NaturalLanguageFilterView.as_view(), name='nl_filter'),
    # Get/Delete specific string (combined in one view)
    path('strings/<path:string_value>', GetSpecificStringView.as_view(), name='get_string'),
]
