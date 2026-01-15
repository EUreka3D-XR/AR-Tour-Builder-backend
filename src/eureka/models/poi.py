from django.db import models
from .tour import Tour
from .fields import MultilingualTextField, Coordinates, ExternalLinks
import json

class POI(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name='pois')
    title = MultilingualTextField()
    description = MultilingualTextField(blank=True, null=True)

    # Geographic coordinates
    coordinates = Coordinates(null=True, blank=True, help_text="Geographic coordinates")
    radius = models.PositiveIntegerField(default=20, help_text="Radius in meters (default: 20)")

    # External links
    external_links = ExternalLinks(blank=True, null=True, help_text="Multilingual external links (quiz/blog)")

    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return json.dumps({
            "id": self.id,
            "tour_id": self.tour_id,
            "title": self.title,
            "description": self.description,
            "coordinates": self.coordinates,
            "radius": self.radius,
            "external_links": self.external_links,
            "order": self.order,
        }, ensure_ascii=False)
