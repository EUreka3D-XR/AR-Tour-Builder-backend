from rest_framework import serializers
from ..models.tour import Tour
from .fields import MultilingualTextField

class TourSerializer(serializers.ModelSerializer):
    """
    Serializer for the Tour model. Handles creation, retrieval, and updates of tours.
    """
    title = MultilingualTextField(
        help_text="Multilingual title with locales structure"
    )
    description = MultilingualTextField(
        required=False,
        allow_null=True,
        help_text="Multilingual description with locales structure"
    )

    class Meta:
        model = Tour
        fields = ['id', 'project', 'title', 'description', 'is_public', 'min_latitude', 'max_latitude', 'min_longitude', 'max_longitude']
        read_only_fields = ['project', 'min_latitude', 'max_latitude', 'min_longitude', 'max_longitude']  # Prevent moving between projects and manual bounding box editing 