from django.db import models
from .project import Project
from .fields import MultilingualTextField, BoundingBox, Coordinates
import json

class Tour(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tours')
    title = MultilingualTextField()
    description = MultilingualTextField(blank=True, null=True)
    is_public = models.BooleanField(default=False)  # type: ignore

    # Geographical bounding box and center
    bounding_box = BoundingBox(null=True, blank=True, help_text="Geographic bounding box of the tour")
    center = Coordinates(null=True, blank=True, help_text="Geographic center of the tour")

    # Tour properties
    distance_meters = models.PositiveIntegerField(null=True, blank=True, help_text="Total distance of the tour in meters")
    duration_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Estimated duration of the tour in minutes")
    locales = models.JSONField(default=list, help_text="Supported language codes for this tour, e.g. ['en', 'fr', 'it']")
    guided = models.BooleanField(default=False, help_text="Whether this tour is guided")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_bounding_box(self):
        """
        Calculate and update the tour's bounding box and center based on all POIs in the tour using their coordinates.
        """
        pois = self.pois.all()  # type: ignore[attr-defined]
        if not pois.exists():
            # No POIs, clear the bounding box and center
            self.bounding_box = None
            self.center = None
            self.save()
            return

        # Collect all valid coordinates from POIs
        min_lat = None
        max_lat = None
        min_long = None
        max_long = None
        lat_sum = 0
        long_sum = 0
        valid_count = 0

        for poi in pois:
            if poi.coordinates:
                lat = poi.coordinates.get('lat')
                long = poi.coordinates.get('long')

                if lat is not None and long is not None:
                    if min_lat is None or lat < min_lat:
                        min_lat = lat
                    if max_lat is None or lat > max_lat:
                        max_lat = lat
                    if min_long is None or long < min_long:
                        min_long = long
                    if max_long is None or long > max_long:
                        max_long = long

                    # Accumulate for center calculation
                    lat_sum += lat
                    long_sum += long
                    valid_count += 1

        # Set bounding box and center if we found valid coordinates
        if all([min_lat is not None, min_long is not None, max_lat is not None, max_long is not None]):
            self.bounding_box = [
                {"lat": min_lat, "long": min_long},
                {"lat": max_lat, "long": max_long}
            ]
            # Calculate center as the mean of all POI coordinates
            self.center = {
                "lat": lat_sum / valid_count,
                "long": long_sum / valid_count
            }
        else:
            self.bounding_box = None
            self.center = None

        self.save()

    def __str__(self):
        return json.dumps({
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "description": self.description,
            "is_public": self.is_public,
            "bounding_box": self.bounding_box,
            "distance_meters": self.distance_meters,
            "duration_minutes": self.duration_minutes,
            "locales": self.locales,
            "guided": self.guided,
        }, ensure_ascii=False)
