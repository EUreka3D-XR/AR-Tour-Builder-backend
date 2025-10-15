from rest_framework import serializers
from ..models.poi import POI
from .fields import MultilingualTextField

class POISerializer(serializers.ModelSerializer):
    """
    Serializer for the POI model. Handles creation, retrieval, and updates of Points of Interest.
    """
    name = MultilingualTextField(
        help_text="Multilingual name with locales structure"
    )
    description = MultilingualTextField(
        required=False,
        allow_null=True,
        help_text="Multilingual description with locales structure"
    )

    class Meta:
        model = POI
        fields = ['id', 'tour', 'name', 'description', 'latitude', 'longitude', 'order']
        read_only_fields = ['tour']  # Prevent moving between tours 