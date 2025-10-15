# The model classes in this file have been split into separate files for clarity.
# See project.py, asset.py, tour.py, and poi.py in the same directory. 

from django.db import models
from .project import Project
import json

class Tour(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tours')
    title = models.JSONField()
    description = models.JSONField(blank=True, null=True)
    is_public = models.BooleanField(default=False)  # type: ignore
    
    # Geographical bounding box
    min_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    max_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    min_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    max_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    def update_bounding_box(self):
        """
        Calculate and update the tour's bounding box based on all POIs in the tour.
        """
        pois = self.pois.all()  # type: ignore[attr-defined]
        
        if not pois.exists():
            # No POIs, clear the bounding box
            self.min_latitude = None
            self.max_latitude = None
            self.min_longitude = None
            self.max_longitude = None
            self.save()
            return
        
        # Initialize with the first POI's coordinates
        first_poi = pois.first()
        min_lat = max_lat = first_poi.latitude
        min_lon = max_lon = first_poi.longitude
        
        # Find min/max coordinates across all POIs
        for poi in pois:
            min_lat = min(min_lat, poi.latitude)
            max_lat = max(max_lat, poi.latitude)
            min_lon = min(min_lon, poi.longitude)
            max_lon = max(max_lon, poi.longitude)
        
        # Update the tour's bounding box
        self.min_latitude = min_lat
        self.max_latitude = max_lat
        self.min_longitude = min_lon
        self.max_longitude = max_lon
        self.save()

    def __str__(self):
        return json.dumps({
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "description": self.description,
            "is_public": self.is_public,
            "min_latitude": float(self.min_latitude) if self.min_latitude is not None else None,
            "max_latitude": float(self.max_latitude) if self.max_latitude is not None else None,
            "min_longitude": float(self.min_longitude) if self.min_longitude is not None else None,
            "max_longitude": float(self.max_longitude) if self.max_longitude is not None else None,
        }, ensure_ascii=False)
    # ... other fields as needed ... 