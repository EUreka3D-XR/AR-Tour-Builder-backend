from django.db import models
from .poi import POI
from .project import Project
from .fields import MultilingualTextField, Georeference, is_valid_georeference
import json


class AssetType(models.TextChoices):
    # General types
    IMAGE = 'image', 'Image'
    VIDEO = 'video', 'Video'
    AUDIO = 'audio', 'Audio'
    TEXT = 'text', 'Text'
    MODEL3D = 'model3d', '3D Model'
    OTHER = 'other', 'Other'
    # Concrete image types
    PNG = 'image/png', 'PNG Image'
    JPEG = 'image/jpeg', 'JPEG Image'
    SVG = 'image/svg+xml', 'SVG Image'
    # Concrete video types
    MP4 = 'video/mp4', 'MP4 Video'
    WEBM = 'video/webm', 'WebM Video'
    # Concrete audio types
    MP3 = 'audio/mpeg', 'MP3 Audio'
    WAV = 'audio/wav', 'WAV Audio'
    OGG = 'audio/ogg', 'OGG Audio'
    # Concrete 3D model types
    GLB = 'model/gltf-binary', 'glTF Binary (GLB)'
    GLTF = 'model/gltf+json', 'glTF (GLTF)'
    FBX = 'model/fbx', 'FBX Model'
    OBJ = 'model/obj', 'OBJ Model'
    # Concrete text types
    PLAIN = 'text/plain', 'Plain Text'
    HTML = 'text/html', 'HTML Document'
    MARKDOWN = 'text/markdown', 'Markdown Document'


class Asset(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='assets')
    type = models.CharField(max_length=32, choices=AssetType.choices)
    title = MultilingualTextField()
    description = MultilingualTextField(blank=True, null=True)
    url = MultilingualTextField(blank=True, null=True)

    # Optional georeference with coordinates
    georeference = Georeference(null=True, blank=True, help_text="Georeference with coordinates (optional)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_georeferenced(self):
        """Returns True if georeference has valid coordinates with populated lat/long values."""
        return is_valid_georeference(self.georeference)

    def __str__(self):
        return json.dumps({
            "id": self.id,
            "project_id": self.project_id,
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "georeference": self.georeference,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }, ensure_ascii=False) 