from rest_framework import generics, permissions
from rest_framework.throttling import ScopedRateThrottle
from django.db.models import Count, Prefetch, Q
from math import radians, cos, sin, asin, sqrt
from ..models.project import Project
from ..models.tour import Tour
from ..serializers.project_serializer import ProjectSerializerLite
from ..serializers.nested_serializers import ProjectPopulatedSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from .mixins import LocaleContextMixin, POIPrefetchMixin


@extend_schema(
    description="Public endpoint to list projects that contain at least one public tour. Returns projects with statistics but WITHOUT nested tours array for performance. Supports proximity-based ordering when 'order_by=proximity' with lat/long parameters. Anonymous access allowed with throttling (500/hour).",
    summary="List Projects with Public Tours (Public)",
    tags=['Public'],
    parameters=[
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el")',
            required=False,
            type=str
        ),
        OpenApiParameter(
            name='order_by',
            description='Order results by proximity to given coordinates. Use "proximity" to enable proximity-based ordering (requires lat and long parameters).',
            required=False,
            type=str
        ),
        OpenApiParameter(
            name='lat',
            description='Latitude coordinate for proximity-based ordering (required when order_by=proximity)',
            required=False,
            type=OpenApiTypes.FLOAT
        ),
        OpenApiParameter(
            name='long',
            description='Longitude coordinate for proximity-based ordering (required when order_by=proximity)',
            required=False,
            type=OpenApiTypes.FLOAT
        ),
    ],
    responses={
        200: ProjectSerializerLite(many=True)
    }
)
class PublicProjectListView(LocaleContextMixin, generics.ListAPIView):
    """
    Public read-only endpoint to list projects that have at least one public tour.

    Returns only projects containing public tours with statistics (total public tours, total POIs, etc.)
    without nested tours array for performance.

    Supports proximity-based ordering when order_by=proximity parameter is provided
    along with lat and long coordinates.

    Anonymous users can access this endpoint with throttling limits.
    """
    serializer_class = ProjectSerializerLite
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'public_projects'

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the great circle distance in kilometers between two points
        on the earth (specified in decimal degrees) using the Haversine formula.
        """
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        # Radius of earth in kilometers
        r = 6371

        return c * r

    def get_queryset(self):
        """
        Return only projects that have at least one public tour.
        Annotates with counts of public tours and their POIs.
        If order_by=proximity with lat and long parameters, order by distance to given coordinates.
        """
        # Filter projects that have at least one public tour
        # Use Q filter to only count public tours and their POIs
        queryset = Project.objects.filter(  # type: ignore[attr-defined]
            tours__is_public=True
        ).distinct().annotate(
            total_tours=Count('tours', filter=Q(tours__is_public=True), distinct=True),
            total_pois=Count('tours__pois', filter=Q(tours__is_public=True), distinct=True)
        )

        # Check if proximity ordering is requested
        order_by = self.request.query_params.get('order_by', None)

        if order_by == 'proximity':
            # Get lat and long parameters
            try:
                user_lat = self.request.query_params.get('lat', None)
                user_long = self.request.query_params.get('long', None)

                # Only apply proximity ordering if both lat and long are provided
                if user_lat is not None and user_long is not None:
                    user_lat = float(user_lat)
                    user_long = float(user_long)

                    # Fetch all projects with prefetched tours to avoid N+1 queries
                    projects = list(queryset.prefetch_related('tours'))

                    # Calculate distance for each project and attach it
                    for project in projects:
                        # Get project center using only public tours
                        center = project.get_center(public_only=True)

                        if center:
                            project_lat = center['lat']
                            project_long = center['long']
                            project._distance = self.haversine_distance(
                                user_lat, user_long, project_lat, project_long
                            )
                        else:
                            # No valid center, put at the end
                            project._distance = float('inf')

                    # Sort projects by distance
                    projects.sort(key=lambda p: p._distance)

                    # Return as a list (Django will handle it properly)
                    return projects

            except (ValueError, TypeError):
                # If lat/long conversion fails, skip proximity ordering
                pass

        return queryset


@extend_schema(
    description="Public endpoint to retrieve a fully populated project with all nested data. Only returns PUBLIC tours (is_public=True). Anonymous access allowed with throttling (500/hour).",
    summary="Get Populated Project (Public)",
    tags=['Public'],
    parameters=[
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el")',
            required=False,
            type=str
        ),
    ],
    responses={
        200: ProjectPopulatedSerializer
    }
)
class PublicProjectPopulatedView(POIPrefetchMixin, LocaleContextMixin, generics.RetrieveAPIView):
    """
    Public read-only endpoint to retrieve a fully populated project.

    This endpoint returns:
    - Project details with total_tours and total_pois statistics
    - Group members list (users who have access to this project)
    - ONLY PUBLIC tours (is_public=True) with total_pois and total_assets statistics
    - All POIs with media stats (image, video, audio, model3d, text counts)
    - All POI assets with complete details

    Query parameters:
    - locale: Get just the string for that locale instead of the full multilingual object

    Anonymous users can access this endpoint with throttling limits.
    Only public tours are returned.
    """
    serializer_class = ProjectPopulatedSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'public_projects'

    def get_queryset(self):
        """
        Optimize the queryset with prefetch_related and annotations.
        Returns all projects with ONLY public tours.
        """
        # Build tour queryset - only public tours for public endpoint
        tour_queryset = Tour.objects.filter(is_public=True).prefetch_related(
            self.get_poi_prefetch()
        ).annotate(  # type: ignore[attr-defined]
            total_pois=Count('pois', distinct=True),
            total_assets=Count('pois__assets', distinct=True)
        )

        # Create optimized prefetch for tours with POIs
        tour_prefetch = Prefetch(
            'tours',
            queryset=tour_queryset
        )

        # Return all projects with prefetched public tours only
        return Project.objects.prefetch_related(  # type: ignore[attr-defined]
            tour_prefetch,
            'group__user_set'
        ).annotate(
            total_tours=Count('tours', filter=Q(tours__is_public=True), distinct=True),
            total_pois=Count('tours__pois', filter=Q(tours__is_public=True), distinct=True)
        )
