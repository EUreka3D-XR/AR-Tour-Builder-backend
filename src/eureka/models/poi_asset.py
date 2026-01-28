from django.db import models
from .poi import POI
from .asset import Asset
from .fields import MultilingualTextField, Georeference, LinkedAsset, is_valid_georeference
import json

class POIAsset(models.Model):
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('high', 'High'),
    ]

    AR_PLACEMENT_CHOICES = [
        ('free', 'Free'),
        ('ground', 'Ground'),
    ]

    poi = models.ForeignKey(POI, on_delete=models.CASCADE, related_name='assets')
    source_asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, related_name='poi_assets', null=True, blank=True)
    title = MultilingualTextField()
    description = MultilingualTextField(blank=True, null=True)
    type = models.CharField(max_length=32)
    url = MultilingualTextField()
    priority = models.CharField(max_length=6, choices=PRIORITY_CHOICES, default='normal')
    view_in_ar = models.BooleanField(default=False)
    ar_placement = models.CharField(max_length=6, choices=AR_PLACEMENT_CHOICES, default='free')
    spawn_radius = models.FloatField(default=5)

    # Optional georeference with coordinates
    georeference = Georeference(null=True, blank=True, help_text="Georeference with coordinates (optional)")

    # Optional linked asset with multilingual title and URL
    linked_asset = LinkedAsset(null=True, blank=True, help_text="Multilingual linked asset with title and URL")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_georeferenced(self):
        """Returns True if georeference has valid coordinates with populated lat/long values."""
        return is_valid_georeference(self.georeference)

    def __str__(self):
        return json.dumps({
            "id": self.id,
            "poi_id": self.poi_id,
            "source_asset_id": self.source_asset_id,
            "title": self.title,
            "description": self.description,
            "type": self.type,
            "url": self.url,
            "priority": self.priority,
            "view_in_ar": self.view_in_ar,
            "ar_placement": self.ar_placement,
            "georeference": self.georeference,
            "linked_asset": self.linked_asset,
        }, ensure_ascii=False)
