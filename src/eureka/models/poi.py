from django.db import models
from .tour import Tour
import json

class POI(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='pois')
    name = models.JSONField()
    description = models.JSONField(blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    order = models.PositiveIntegerField()
    # ... other fields as needed ... 

    def __str__(self):
        return json.dumps({
            "id": self.id,
            "tour_id": self.tour_id,
            "name": self.name,
            "description": self.description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "order": self.order,
        }, ensure_ascii=False) 