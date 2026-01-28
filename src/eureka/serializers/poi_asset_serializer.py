from rest_framework import serializers
from eureka.models.poi_asset import POIAsset
from .fields import MultilingualTextField, Georeference, LinkedAsset

class POIAssetSerializer(serializers.ModelSerializer):
    """
    Serializer for the POIAsset model. Handles creation, retrieval, and updates of POI assets.
    The georeference field is optional and uses the Georeference custom field.
    The ar_placement field specifies the AR placement mode ('free' or 'ground', default: 'free').
    Supports locale filtering: if a 'locale' parameter is passed in the context,
    multilingual fields (title, description, url, linked_asset) will return just the string/object for that locale.
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

    linked_asset = LinkedAsset(
        required=False,
        allow_null=True,
        help_text="Multilingual linked asset with title and URL structure"
    )

    # Read-only fields for associations (handled by views)
    poi = serializers.PrimaryKeyRelatedField(read_only=True)
    source_asset = serializers.PrimaryKeyRelatedField(read_only=True)
    is_georeferenced = serializers.BooleanField(read_only=True)

    class Meta:
        model = POIAsset
        fields = [
            'id', 'poi', 'source_asset', 'title', 'description', 'type', 'url', 'priority', 'view_in_ar', 'ar_placement', 'spawn_radius', 'georeference', 'is_georeferenced', 'linked_asset', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_georeferenced']
