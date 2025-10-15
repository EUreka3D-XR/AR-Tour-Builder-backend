from rest_framework import serializers
from ..models.asset import Asset
from .fields import MultilingualTextField

class AssetSerializer(serializers.ModelSerializer):
    """
    Serializer for the Asset model. Handles creation, retrieval, and updates of assets.
    """
    title = MultilingualTextField(
        help_text="Multilingual title with locales structure"
    )
    description = MultilingualTextField(
        required=False,
        allow_null=True,
        help_text="Multilingual description with locales structure"
    )
    
    # Read-only fields for associations (handled by views)
    tour = serializers.PrimaryKeyRelatedField(read_only=True)
    poi = serializers.PrimaryKeyRelatedField(read_only=True)
    project = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Asset
        fields = ['id', 'project', 'tour', 'poi', 'type', 'title', 'description', 'url', 'language', 'thumbnail', 'thumbnail_data', 'source_asset']
        read_only_fields = ['source_asset']

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data) 