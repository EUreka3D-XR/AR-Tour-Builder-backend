from django.db import models


class Image(models.Model):
    """
    Simple image storage using PostgreSQL blob storage.
    Images are publicly accessible for reading.
    """
    # Binary data stored directly in PostgreSQL
    data = models.BinaryField()

    # Content type (e.g., 'image/jpeg', 'image/png')
    content_type = models.CharField(max_length=100)

    # Original filename (optional, for reference)
    filename = models.CharField(max_length=255, blank=True)

    # Optional external URL/filepath for future MinIO integration
    external_url = models.CharField(max_length=500, blank=True, null=True)

    # File size in bytes
    size = models.IntegerField()

    # User who uploaded the image
    uploaded_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Image {self.id} - {self.filename or 'untitled'}"
