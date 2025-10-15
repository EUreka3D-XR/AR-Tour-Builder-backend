from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from ..models.project import Project
from ..models.asset import Asset
from ..models.poi import POI
from ..models.tour import Tour
from ..serializers.asset_serializer import AssetSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

@extend_schema(
    methods=['GET'],
    description="List all assets the authenticated user has access to. Supports filtering by project, tour, language, and type.",
    summary="List Assets",
    tags=['Assets'],
    parameters=[
        OpenApiParameter(name='project_id', description='Filter assets by project ID', required=False, type=int),
        OpenApiParameter(name='tour_id', description='Filter assets by tour ID', required=False, type=int),
        OpenApiParameter(name='poi_id', description='Filter assets by POI ID', required=False, type=int),
        OpenApiParameter(name='language', description='Filter by language code', required=False),
        OpenApiParameter(name='type', description='Filter by asset type (e.g., image, video)', required=False),
        OpenApiParameter(name='ordering', description='Order by field (default: -created_at)', required=False),
    ],
    responses={
        200: AssetSerializer(many=True)
    }
)
@extend_schema(
    methods=['POST'],
    description="Create a new asset. Specify one of: project_id, tour_id, or poi_id. For POI assets, source_asset_id is required.",
    summary="Create Asset",
    tags=['Assets'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string', 'description': 'Asset title'},
                'description': {'type': 'string', 'description': 'Asset description (optional)'},
                'url': {'type': 'string', 'description': 'Asset URL'},
                'type': {'type': 'string', 'description': 'Asset type (e.g., image, video, audio)'},
                'language': {'type': 'string', 'description': 'Language code'},
                'project_id': {'type': 'integer', 'description': 'Project ID to create asset for'},
                'tour_id': {'type': 'integer', 'description': 'Tour ID to create asset for'},
                'poi_id': {'type': 'integer', 'description': 'POI ID to create asset for'},
                'source_asset_id': {'type': 'integer', 'description': 'Source asset ID to copy from (required when creating for POI)'},
                'real_width_meters': {'type': 'number', 'description': 'Real-world width in meters (for map images and 3D objects)'},
                'real_height_meters': {'type': 'number', 'description': 'Real-world height in meters (for map images and 3D objects)'},
                'se_corner_lat': {'type': 'number', 'description': 'Southeast corner latitude for map alignment (alternative to real_width_meters/real_height_meters)'},
                'se_corner_long': {'type': 'number', 'description': 'Southeast corner longitude for map alignment (alternative to real_width_meters/real_height_meters)'}
            },
            'required': ['title', 'url', 'type', 'language']
        }
    },
    responses={
        201: AssetSerializer,
        400: OpenApiResponse(
            description="Bad request",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['detail']
            },
            examples=[
                OpenApiExample('Missing Required', value={'detail': 'Exactly one of project_id, tour_id, or poi_id is required to create an asset.'}),
                OpenApiExample('Multiple Specified', value={'detail': 'Cannot specify multiple target IDs. Choose only one of project_id, tour_id, or poi_id.'}),
                OpenApiExample('Missing Source', value={'detail': 'source_asset_id is required when creating asset for POI.'}),
                OpenApiExample('Source Not Found', value={'detail': 'Source asset not found.'}),
                OpenApiExample('Invalid Source', value={'detail': 'Source asset must be from the same project.'}),
                OpenApiExample('Tour Not Found', value={'detail': 'Tour not found.'}),
                OpenApiExample('POI Not Found', value={'detail': 'POI not found.'}),
                OpenApiExample('Project Not Found', value={'detail': 'Project not found.'})
            ]
        ),
        403: OpenApiResponse(
            description="Permission denied",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['detail']
            },
            examples=[
                OpenApiExample('Not Member', value={'detail': 'Not a member of the project group.'}),
                OpenApiExample('Tour Not Found', value={'detail': 'Tour not found.'}),
                OpenApiExample('POI Not Found', value={'detail': 'POI not found.'}),
                OpenApiExample('Project Not Found', value={'detail': 'Project not found.'})
            ]
        )
    }
)
class AssetListCreateView(generics.ListCreateAPIView):
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['language']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        user_groups = user.groups.all()
        
        # Filter by project if specified
        project_id = self.request.query_params.get('project_id')
        tour_id = self.request.query_params.get('tour_id')
        poi_id = self.request.query_params.get('poi_id')
        
        if project_id:
            try:
                project = Project.objects.get(pk=project_id)  # type: ignore[attr-defined]
                if project.group not in user_groups:
                    return Asset.objects.none()  # type: ignore[attr-defined]
                queryset = Asset.objects.filter(project=project)  # type: ignore[attr-defined]
            except ObjectDoesNotExist:
                return Asset.objects.none()  # type: ignore[attr-defined]
        elif tour_id:
            try:
                tour = Tour.objects.get(pk=tour_id)  # type: ignore[attr-defined]
                if tour.project.group not in user_groups:
                    return Asset.objects.none()  # type: ignore[attr-defined]
                queryset = Asset.objects.filter(tour=tour)  # type: ignore[attr-defined]
            except ObjectDoesNotExist:
                return Asset.objects.none()  # type: ignore[attr-defined]
        elif poi_id:
            try:
                poi = POI.objects.get(pk=poi_id)  # type: ignore[attr-defined]
                if poi.tour.project.group not in user_groups:
                    return Asset.objects.none()  # type: ignore[attr-defined]
                queryset = Asset.objects.filter(poi=poi)  # type: ignore[attr-defined]
            except ObjectDoesNotExist:
                return Asset.objects.none()  # type: ignore[attr-defined]
        else:
            # Return all assets from user's groups
            queryset = Asset.objects.filter(project__group__in=user_groups)  # type: ignore[attr-defined]
        
        # Filter by type (exact or general prefix)
        asset_type = self.request.query_params.get('type')
        if asset_type:
            queryset = queryset.filter(type__startswith=asset_type)
        
        # Filter by language (handled by filterset_fields, but keep for explicitness)
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language=language)
        
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user
        project_id = self.request.data.get('project_id')
        tour_id = self.request.data.get('tour_id')
        poi_id = self.request.data.get('poi_id')
        source_asset_id = self.request.data.get('source_asset_id')
        
        # Count how many target IDs are provided
        target_count = sum(1 for x in [project_id, tour_id, poi_id] if x)
        
        if target_count == 0:
            raise PermissionDenied('Exactly one of project_id, tour_id, or poi_id is required to create an asset.')
        
        if target_count > 1:
            raise PermissionDenied('Cannot specify multiple target IDs. Choose only one of project_id, tour_id, or poi_id.')
        
        if poi_id:
            # Create asset for POI - requires source asset to copy from
            if not source_asset_id:
                raise PermissionDenied('source_asset_id is required when creating asset for POI.')
            
            try:
                poi = POI.objects.get(pk=poi_id)  # type: ignore[attr-defined]
                tour = poi.tour
                project = tour.project
                
                if project.group not in user.groups.all():
                    raise PermissionDenied('Not a member of the POI project group.')
                
                # Get the source asset
                try:
                    source_asset = Asset.objects.get(pk=source_asset_id)  # type: ignore[attr-defined]
                except ObjectDoesNotExist:
                    raise PermissionDenied('Source asset not found.')
                
                # Verify source asset is from the same project
                if source_asset.project != project:
                    raise PermissionDenied('Source asset must be from the same project.')
                
                # Copy fields from source asset
                asset_data = serializer.validated_data.copy()
                asset_data.update({
                    'project': project,
                    'poi': poi,
                    'type': source_asset.type,
                    'title': source_asset.title,
                    'description': source_asset.description,
                    'url': source_asset.url,
                    'language': source_asset.language,
                    'thumbnail': source_asset.thumbnail,
                    'source_asset': source_asset
                })
                
                serializer.save(**asset_data)
                
            except ObjectDoesNotExist:
                raise PermissionDenied('POI not found.')
        
        elif tour_id:
            # Create asset for tour
            if source_asset_id:
                raise PermissionDenied('source_asset_id should not be provided when creating asset for tour.')
            
            try:
                tour = Tour.objects.get(pk=tour_id)  # type: ignore[attr-defined]
                project = tour.project
            except ObjectDoesNotExist:
                raise PermissionDenied('Tour not found.')
            
            if project.group not in user.groups.all():
                raise PermissionDenied('Not a member of the tour project group.')
            
            serializer.save(project=project, tour=tour)
        
        else:
            # Create fresh asset for project
            if source_asset_id:
                raise PermissionDenied('source_asset_id should not be provided when creating asset for project.')
            
            try:
                project = Project.objects.get(pk=project_id)  # type: ignore[attr-defined]
            except ObjectDoesNotExist:
                raise PermissionDenied('Project not found.')
            
            if project.group not in user.groups.all():
                raise PermissionDenied('Not a member of the project group.')
            
            serializer.save(project=project)

@extend_schema(
    description="Retrieve, update, or delete a specific asset. User must have access to the asset's project. Project and POI associations cannot be changed.",
    summary="Asset CRUD Operations",
    tags=['Assets'],
    responses={
        200: AssetSerializer,
        204: OpenApiResponse(
            description="Asset deleted successfully",
            response=None
        ),
        400: OpenApiResponse(
            description="Bad request",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['detail']
            }
        ),
        403: OpenApiResponse(
            description="Permission denied",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['detail']
            }
        )
    }
)
class AssetRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_groups = user.groups.all()
        # Include assets from projects and tours that user has access to
        return Asset.objects.filter(
            models.Q(project__group__in=user_groups) | 
            models.Q(tour__project__group__in=user_groups) |
            models.Q(poi__tour__project__group__in=user_groups)
        )  # type: ignore[attr-defined] 