from rest_framework import serializers
from ..models.poi import POI
from ..models.tour import Tour
from ..models.project import Project
from ..models.poi_asset import POIAsset
from .fields import MultilingualTextField, Coordinates, BoundingBox, ExternalLinks, LinkedAsset
from .user_serializer import UserLiteSerializer


class POIAssetNestedSerializer(serializers.ModelSerializer):
    """
    Nested serializer for POIAsset used in populated project endpoint.
    Includes all asset details without related object IDs.

    Supports locale filtering: if a 'locale' parameter is passed in the serializer context,
    multilingual fields will return just the string/object for that locale.
    """
    title = MultilingualTextField()
    description = MultilingualTextField(required=False, allow_null=True)
    url = MultilingualTextField()
    coordinates = Coordinates(required=False, allow_null=True)
    linked_asset = LinkedAsset(required=False, allow_null=True)
    is_georeferenced = serializers.BooleanField(read_only=True)

    class Meta:
        model = POIAsset
        fields = [
            'id', 'title', 'description', 'type', 'url',
            'priority', 'view_in_ar', 'ar_placement', 'coordinates', 'is_georeferenced', 'linked_asset'
        ]


class POINestedSerializer(serializers.ModelSerializer):
    """
    Nested serializer for POI used in populated project endpoint.
    Includes all POI details and nested assets, plus calculated stats.

    Supports locale filtering: if a 'locale' parameter is passed in the serializer context,
    multilingual fields will return just the string/array for that locale.
    """
    title = MultilingualTextField()
    description = MultilingualTextField(required=False, allow_null=True)
    coordinates = Coordinates(required=False, allow_null=True)
    external_links = ExternalLinks(required=False, allow_null=True)
    assets = serializers.SerializerMethodField(read_only=True)
    stats = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = POI
        fields = [
            'id', 'title', 'description', 'coordinates', 'radius',
            'external_links', 'order', 'stats', 'assets'
        ]

    def get_assets(self, obj):
        """Serialize assets with context (for locale support)"""
        assets = obj.assets.all()
        return POIAssetNestedSerializer(assets, many=True, context=self.context).data

    def get_stats(self, obj):
        """Calculate media statistics for this POI's assets"""
        # Check if stats were already annotated by the viewset for performance
        if hasattr(obj, 'stat_image') and hasattr(obj, 'stat_video') and \
           hasattr(obj, 'stat_audio') and hasattr(obj, 'stat_model3d') and \
           hasattr(obj, 'stat_text'):
            return {
                'image': obj.stat_image or 0,
                'video': obj.stat_video or 0,
                'audio': obj.stat_audio or 0,
                'model3d': obj.stat_model3d or 0,
                'text': obj.stat_text or 0,
            }

        # Fallback: calculate from prefetched assets
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


class TourNestedSerializer(serializers.ModelSerializer):
    """
    Nested serializer for Tour used in populated project endpoint.
    Includes all tour details and nested POIs, plus calculated stats.

    Supports locale filtering: if a 'locale' parameter is passed in the serializer context,
    multilingual fields will return just the string/array for that locale.
    """
    title = MultilingualTextField()
    description = MultilingualTextField(required=False, allow_null=True)
    bounding_box = BoundingBox(required=False, allow_null=True, read_only=True)
    center = Coordinates(required=False, allow_null=True, read_only=True)
    pois = serializers.SerializerMethodField(read_only=True)
    total_pois = serializers.SerializerMethodField(read_only=True)
    total_assets = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tour
        fields = [
            'id', 'title', 'description', 'is_public', 'bounding_box', 'center',
            'distance_meters', 'duration_minutes', 'locales', 'guided',
            'total_pois', 'total_assets', 'pois'
        ]

    def get_pois(self, obj):
        """Serialize POIs with context (for locale support)"""
        pois = obj.pois.all()
        return POINestedSerializer(pois, many=True, context=self.context).data

    def get_total_pois(self, obj):
        """Calculate the total number of POIs in this tour"""
        if hasattr(obj, 'total_pois'):
            return obj.total_pois
        return obj.pois.count()

    def get_total_assets(self, obj):
        """Calculate the total number of POI assets across all POIs in this tour"""
        if hasattr(obj, 'total_assets'):
            return obj.total_assets
        # Use prefetched POIs to calculate
        return sum(poi.assets.count() for poi in obj.pois.all())


class ProjectPopulatedSerializer(serializers.ModelSerializer):
    """
    Specialized serializer for fully populated project data.
    Includes all nested tours, POIs, and assets with calculated statistics.
    Used exclusively by the ProjectPopulatedView endpoint.

    Supports locale filtering: if a 'locale' parameter is passed in the serializer context,
    multilingual fields in nested tours, POIs, and assets will return just the string/array for that locale.
    """
    title = MultilingualTextField()
    description = MultilingualTextField(required=False, allow_null=True)
    center = serializers.SerializerMethodField(read_only=True)
    created_by = UserLiteSerializer(read_only=True)
    tours = serializers.SerializerMethodField(read_only=True)
    total_tours = serializers.SerializerMethodField(read_only=True)
    total_pois = serializers.SerializerMethodField(read_only=True)
    group_members = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'created_by', 'title', 'description', 'created_at', 'updated_at',
            'locales', 'center', 'total_tours', 'total_pois', 'group_members', 'tours'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def get_center(self, obj):
        """Calculate the project's center using the model method"""
        return obj.get_center()

    def get_tours(self, obj):
        """Serialize tours with context (for locale support)"""
        tours = obj.tours.all()
        return TourNestedSerializer(tours, many=True, context=self.context).data

    def get_total_tours(self, obj):
        """Calculate the total number of tours in this project"""
        if hasattr(obj, 'total_tours'):
            return obj.total_tours
        return obj.tours.count()

    def get_total_pois(self, obj):
        """Calculate the total number of POIs across all tours in this project"""
        if hasattr(obj, 'total_pois'):
            return obj.total_pois
        # Use prefetched tours to calculate
        return sum(tour.pois.count() for tour in obj.tours.all())

    def get_group_members(self, obj):
        """Return lightweight list of users who are members of the project's group"""
        members = obj.group.user_set.all().order_by('username')
        return UserLiteSerializer(members, many=True).data
