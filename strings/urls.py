from django.urls import path
from .views import (
    StringsView, GetSpecificStringView, NaturalLanguageFilterView, DeleteStringView
)

urlpatterns = [
    path('strings', StringsView.as_view(), name='strings'),
    path('strings/filter-by-natural-language', NaturalLanguageFilterView.as_view(), name='nl_filter'),
    path('strings/<path:string_value>', GetSpecificStringView.as_view(), name='get_string'),
    path('strings/<path:string_value>', DeleteStringView.as_view(), name='delete_string'),
]
