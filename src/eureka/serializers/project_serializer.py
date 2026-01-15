from rest_framework import serializers
from ..models.project import Project
from ..models.poi import POI
from .tour_serializer import TourSerializerLite
from .user_serializer import UserLiteSerializer
from .fields import MultilingualTextField

class ProjectStatsBaseSerializer(serializers.ModelSerializer):
    title = MultilingualTextField()
    description = MultilingualTextField(required=False, allow_null=True)
    center = serializers.SerializerMethodField(read_only=True)
    total_tours = serializers.SerializerMethodField(read_only=True)
    total_pois = serializers.SerializerMethodField(read_only=True)
    total_members = serializers.SerializerMethodField(read_only=True)
    created_by = UserLiteSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'group', 'created_by', 'title', 'description', 'locales', 'center', 'total_tours', 'total_pois', 'total_members', 'created_at', 'updated_at']
        read_only_fields = ['group', 'created_by', 'created_at', 'updated_at']

    def get_center(self, obj):
        """Calculate the project's center using the model method"""
        return obj.get_center()

    def get_total_tours(self, obj):
        if hasattr(obj, 'total_tours'):
            return obj.total_tours
        return obj.tours.count()

    def get_total_pois(self, obj):
        if hasattr(obj, 'total_pois'):
            return obj.total_pois
        return POI.objects.filter(tour__project=obj).count()

    def get_total_members(self, obj):
        """Return count of users who are members of the project's group"""
        return obj.group.user_set.count()

class ProjectSerializerLite(ProjectStatsBaseSerializer):
    """
    Lightweight serializer for the Project model without nested tours or members.
    Used for list views to avoid performance issues when fetching multiple projects.
    Only includes statistics (total_tours, total_pois, total_members).
    """
    # Meta is inherited from ProjectStatsBaseSerializer
    pass

class ProjectSerializer(ProjectStatsBaseSerializer):
    """
    Serializer for the Project model. Handles creation, retrieval, and updates of projects.
    Includes calculated statistics, an array of tours (without nested POIs), and group members.
    """
    tours = TourSerializerLite(many=True, read_only=True)
    group_members = serializers.SerializerMethodField(read_only=True)

    class Meta(ProjectStatsBaseSerializer.Meta):
        fields = ProjectStatsBaseSerializer.Meta.fields + ['group_members', 'tours']
        read_only_fields = ProjectStatsBaseSerializer.Meta.read_only_fields

    def get_group_members(self, obj):
        """Return lightweight list of users who are members of the project's group"""
        members = obj.group.user_set.all().order_by('username')
        return UserLiteSerializer(members, many=True).data