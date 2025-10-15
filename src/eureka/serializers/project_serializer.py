from rest_framework import serializers
from ..models.project import Project

class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for the Project model. Handles creation, retrieval, and updates of projects.
    """
    class Meta:
        model = Project
        fields = ['id', 'group', 'title', 'description'] 