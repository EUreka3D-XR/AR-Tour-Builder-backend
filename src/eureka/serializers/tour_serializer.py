from rest_framework import serializers
from ..models.tour import Tour
from ..models.poi import POI
from ..models.poi_asset import POIAsset
from .fields import MultilingualTextField, BoundingBox, Coordinates
from .poi_serializer import POISerializer

class TourStatsBaseSerializer(serializers.ModelSerializer):
    title = MultilingualTextField(help_text="Multilingual title with locales structure")
    description = MultilingualTextField(required=False, allow_null=True, help_text="Multilingual description with locales structure")
    bounding_box = BoundingBox(required=False, allow_null=True, read_only=True, help_text="Geographic bounding box as array of [southwest, northeast] coordinates")
    center = Coordinates(required=False, allow_null=True, read_only=True, help_text="Geographic center point of the tour")
    total_pois = serializers.SerializerMethodField(read_only=True)
    total_assets = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tour
        fields = [
            'id', 'project', 'title', 'description', 'is_public',
            'bounding_box', 'center', 'distance_meters', 'duration_minutes', 'locales', 'guided',
            'total_pois', 'total_assets', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'project', 'bounding_box', 'center', 'created_at', 'updated_at'
        ]

    def get_total_pois(self, obj):
        if hasattr(obj, 'total_pois'):
            return obj.total_pois
        return obj.pois.count()

    def get_total_assets(self, obj):
        if hasattr(obj, 'total_assets'):
            return obj.total_assets
        return POIAsset.objects.filter(poi__tour=obj).count()

class TourSerializerLite(TourStatsBaseSerializer):
    """
    Lightweight serializer for the Tour model without nested POIs.
    Used when tours are embedded in other serializers (e.g., ProjectSerializer)
    to avoid N+1 query problems.
    """
    # Meta is inherited from TourStatsBaseSerializer
    pass

class TourSerializer(TourStatsBaseSerializer):
    """
    Serializer for the Tour model. Handles creation, retrieval, and updates of tours.
    Includes calculated statistics for POIs and POI assets, and an array of POIs with their assets.
    The bounding_box field uses the BoundingBox custom field.

    When updating, you can provide a 'pois' field with an array of POI IDs to reorder them.
    The order of each POI will be updated based on its index in the array.
    """
    pois = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="Array of POI IDs to set the order. POIs will be ordered by their position in this array."
    )

    class Meta(TourStatsBaseSerializer.Meta):
        fields = TourStatsBaseSerializer.Meta.fields + ['pois']
        read_only_fields = TourStatsBaseSerializer.Meta.read_only_fields

    def to_representation(self, instance):
        """
        Override to_representation to show POI objects when reading,
        while accepting POI IDs when writing.
        """
        representation = super().to_representation(instance)
        # Add the full POI objects for reading
        representation['pois'] = POISerializer(
            instance.pois.all().order_by('order'),
            many=True,
            context=self.context
        ).data
        return representation

    def create(self, validated_data):
        """
        Override create to populate empty locales list with project's locales.
        """
        # Check if locales is an empty list and populate it with project's locales
        if 'locales' in validated_data and validated_data['locales'] == []:
            project = validated_data.get('project')
            if project and project.locales:
                validated_data['locales'] = project.locales

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Override update to handle POI reordering and empty locales population.
        If 'pois' is provided, update the order of each POI based on its index.
        If 'locales' is an empty list, populate it with the project's locales.
        """
        # Check if locales is an empty list and populate it with project's locales
        if 'locales' in validated_data and validated_data['locales'] == []:
            if instance.project and instance.project.locales:
                validated_data['locales'] = instance.project.locales

        poi_ids = validated_data.pop('pois', None)

        # Update tour fields
        instance = super().update(instance, validated_data)

        # Handle POI reordering if provided
        if poi_ids is not None:
            # Validate that all POI IDs belong to this tour
            tour_poi_ids = set(instance.pois.values_list('id', flat=True))
            provided_poi_ids = set(poi_ids)

            # Check if all provided IDs belong to this tour
            invalid_ids = provided_poi_ids - tour_poi_ids
            if invalid_ids:
                raise serializers.ValidationError({
                    'pois': f'The following POI IDs do not belong to this tour: {list(invalid_ids)}'
                })
        
            # Check if all tour POIs are included in the reordering
            missing_ids = tour_poi_ids - provided_poi_ids
            if missing_ids:
                raise serializers.ValidationError({
                    'pois': f'All POIs must be included in the reordering. Missing POI IDs: {list(missing_ids)}'
                })
            
            # Check for duplicate ids in the pois ids list
            if len(poi_ids) != len(set(poi_ids)):
                raise serializers.ValidationError({
                    'pois': 'Duplicate POI IDs are not allowed in the reordering array.'
                })

            # Update the order of each POI based on its index
            for index, poi_id in enumerate(poi_ids):
                POI.objects.filter(id=poi_id, tour=instance).update(order=index)

        return instance
