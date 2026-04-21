from rest_framework import serializers
from ..models.poi import POI
from ..serializers.poi_asset_serializer import POIAssetSerializer
from .fields import MultilingualTextField, Coordinates, ExternalLinks

class POISerializer(serializers.ModelSerializer):
    """
    Serializer for the POI model. Handles creation, retrieval, and updates of Points of Interest.
    Includes calculated media statistics for assets.

    The coordinates field uses the Coordinates custom field.
    """
    title = MultilingualTextField(
        help_text="Multilingual title with locales structure"
    )
    description = MultilingualTextField(
        required=False,
        allow_null=True,
        help_text="Multilingual description with locales structure"
    )

    coordinates = Coordinates(
        required=False,
        allow_null=True,
        help_text="Geographic coordinates with lat and long"
    )

    external_links = ExternalLinks(
        required=False,
        allow_null=True,
        help_text="Multilingual external links (quiz/blog)"
    )

    assets = serializers.SerializerMethodField(read_only=True)
    stats = serializers.SerializerMethodField(read_only=True)
    thumbnail_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = POI
        fields = ['id', 'tour', 'title', 'description', 'coordinates', 'radius', 'external_links', 'thumbnail', 'thumbnail_url', 'order', 'stats', 'assets', 'created_at', 'updated_at']
        read_only_fields = ['tour', 'order', 'thumbnail_url', 'created_at', 'updated_at']

    def get_thumbnail_url(self, obj):
        """Generate the public URL for the thumbnail image if it exists."""
        if not obj.thumbnail:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/images/{obj.thumbnail.id}')
        return f'/api/images/{obj.thumbnail.id}'

    def get_assets(self, obj):
        """Serialize assets with context (for locale support)"""
        assets = obj.assets.all()
        return POIAssetSerializer(assets, many=True, context=self.context).data

    def get_stats(self, obj):
        """Calculate media statistics for this POI's assets"""
        # Check if stats were already annotated by the viewset for performance
        if hasattr(obj, 'stat_image') and hasattr(obj, 'stat_video') and hasattr(obj, 'stat_audio') and hasattr(obj, 'stat_model3d') and hasattr(obj, 'stat_text'):
            return {
                'image': obj.stat_image or 0,
                'video': obj.stat_video or 0,
                'audio': obj.stat_audio or 0,
                'model3d': obj.stat_model3d or 0,
                'text': obj.stat_text or 0,
            }

        # Fallback: calculate from database
        assets = obj.assets.all()
        stats = {
            'image': 0,
            'video': 0,
            'audio': 0,
            'model3d': 0,
            'text': 0,
        }

        for asset in assets:
            asset_type = asset.type.lower()
            # Map asset types to stats categories
            if asset_type.startswith('image') or asset_type == 'image':
                stats['image'] += 1
            elif asset_type.startswith('video') or asset_type == 'video':
                stats['video'] += 1
            elif asset_type.startswith('audio') or asset_type == 'audio':
                stats['audio'] += 1
            elif asset_type.startswith('model') or asset_type == 'model3d':
                stats['model3d'] += 1
            elif asset_type.startswith('text') or asset_type == 'text':
                stats['text'] += 1

        return stats
