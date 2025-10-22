from django.db import models
from django.utils import timezone

class AnalyzedString(models.Model):
    """
    Model for storing analyzed strings and their properties.
    """
    id = models.AutoField(primary_key=True)
    value = models.TextField(unique=True)
    properties = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)

    def to_response(self):
        """Convert model instance to API response format"""
        return {
            "value": self.value,
            "properties": self.properties,
            "created_at": self.created_at.replace(microsecond=0).isoformat() + "Z"
        }

    def __str__(self):
        return f"{self.value[:50]}"
