from django.db import models
from django.contrib.auth.models import Group

class Project(models.Model):
    """
    Project model - represents a collection of tours and assets.
    
    Note: Project is not an end-user facing structure. It serves as an organizational
    container for tours and assets within a group. Since it's not displayed to end users,
    it doesn't need multilingual support and uses simple text fields instead of JSONField.
    """
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=255)  # Simple text field - not multilingual
    description = models.TextField(blank=True, null=True)  # Simple text field - not multilingual
    # Add other project-level fields as needed

    def __str__(self):
        return f"Project: {self.title} (Group: {self.group.name})"

    class Meta:
        ordering = ['-id']

    # ... rest of the file remains unchanged ... 