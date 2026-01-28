from rest_framework import serializers
from ..models.asset import Asset
from .fields import MultilingualTextField, Georeference

class AssetSerializer(serializers.ModelSerializer):
    """
    Serializer for the Asset model. Handles creation, retrieval, and updates of assets.
    The georeference field is optional and uses the Georeference custom field.
    """
    title = MultilingualTextField(
        help_text="Multilingual title with locales structure"
    )
    description = MultilingualTextField(
        required=False,
        allow_null=True,
        help_text="Multilingual description with locales structure"
    )
    url = MultilingualTextField(
        help_text="Multilingual URL with locales structure"
    )

    georeference = Georeference(
        required=False,
        allow_null=True,
        help_text="Georeference with nested coordinates (optional)"
    )

    # Read-only fields for associations (handled by views)
    project = serializers.PrimaryKeyRelatedField(read_only=True)
    is_georeferenced = serializers.BooleanField(read_only=True)

    class Meta:
        model = Asset
        fields = ['id', 'project', 'type', 'title', 'description', 'url', 'georeference', 'is_georeferenced', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'is_georeferenced'] 