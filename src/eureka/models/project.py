from django.db import models
from django.contrib.auth.models import Group
from django.conf import settings
from .fields import MultilingualTextField

class Project(models.Model):
    """
    Project model - represents a collection of tours and assets.
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='projects')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_projects', help_text="User who created this project")
    title = MultilingualTextField()  # Multilingual title
    description = MultilingualTextField(blank=True, null=True)  # Multilingual description
    # Add other project-level fields as needed
    locales = models.JSONField(default=list, help_text="Supported language codes for this project, e.g. ['en', 'fr', 'it']")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Project: {self.title} (Group: {self.group.name})"

    def get_center(self, public_only=False):
        """
        Calculate the project's center as the mean of all tour centers.

        Args:
            public_only: If True, only consider public tours when calculating center.

        Returns None if no tours have centers.
        """
        tours = self.tours.filter(is_public=True) if public_only else self.tours.all()
        if not tours.exists():
            return None

        # Collect all valid tour centers
        lat_sum = 0
        long_sum = 0
        valid_count = 0

        for tour in tours:
            if tour.center:
                lat = tour.center.get('lat')
                long = tour.center.get('long')

                if lat is not None and long is not None:
                    lat_sum += lat
                    long_sum += long
                    valid_count += 1

        # Return center if we found valid tour centers
        if valid_count > 0:
            return {
                "lat": lat_sum / valid_count,
                "long": long_sum / valid_count
            }

        return None

    class Meta:
        ordering = ['-id']

    # ... rest of the file remains unchanged ... 