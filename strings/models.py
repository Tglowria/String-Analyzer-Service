from django.db import models
from django.utils import timezone

class AnalyzedString(models.Model):
    """
    id: sha256 hash (hex) of the string (primary key)
    value: the original string
    properties: JSON containing computed properties
    created_at: UTC timestamp when saved
    """
    id = models.CharField(max_length=64, primary_key=True)  # sha256 hex
    value = models.TextField()
    properties = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)

    def to_response(self):
        # Return dictionary in the exact shape required by spec
        return {
            "id": self.id,
            "value": self.value,
            "properties": self.properties,
            "created_at": self.created_at.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        }

    def __str__(self):
        return f"{self.id} - {self.value[:50]}"
