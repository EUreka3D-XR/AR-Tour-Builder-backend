from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from ..models.project import Project
from ..models.asset import Asset
from ..serializers.asset_serializer import AssetSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ObjectDoesNotExist
from .mixins import LocaleContextMixin

@extend_schema(
    methods=['GET'],
    description="List all assets the authenticated user has access to. Supports filtering by project and type.",
    summary="List Assets",
    tags=['Assets'],
    parameters=[
        OpenApiParameter(name='project_id', description='Filter assets by project ID', required=False, type=int),
        OpenApiParameter(name='type', description='Filter by asset type (e.g., image, video)', required=False),
        OpenApiParameter(name='ordering', description='Order by field (default: -created_at)', required=False),
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el"). If provided, multilingual fields will return just the string for that locale instead of the full multilingual object.',
            required=False,
            type=str
        ),
    ],
    responses={
        200: AssetSerializer(many=True)
    }
)
@extend_schema(
    methods=['POST'],
    description="Create a new asset. Specify project_id.",
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
                'project_id': {'type': 'integer', 'description': 'Project ID to create asset for'},
            },
            'required': ['title', 'url', 'type']
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
                OpenApiExample('Project Not Found', value={'detail': 'Project not found.'})
            ]
        )
    }
)
class AssetListCreateView(LocaleContextMixin, generics.ListCreateAPIView):
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        user_groups = user.groups.all()
        
        # Filter by project if specified
        project_id = self.request.query_params.get('project_id')
        
        if project_id:
            try:
                project = Project.objects.get(pk=project_id)  # type: ignore[attr-defined]
                if project.group not in user_groups:
                    return Asset.objects.none()  # type: ignore[attr-defined]
                queryset = Asset.objects.filter(project=project)  # type: ignore[attr-defined]
            except ObjectDoesNotExist:
                return Asset.objects.none()  # type: ignore[attr-defined]
        else:
            # Return all assets from user's groups
            queryset = Asset.objects.filter(project__group__in=user_groups)  # type: ignore[attr-defined]
        
        # Filter by type (exact or general prefix)
        asset_type = self.request.query_params.get('type')
        if asset_type:
            queryset = queryset.filter(type__startswith=asset_type)
        
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user
        project_id = self.request.data.get('project_id')

        if not project_id:
            raise PermissionDenied('project_id is required to create an asset.')

        try:
            project = Project.objects.get(pk=project_id)  # type: ignore[attr-defined]
        except ObjectDoesNotExist:
            raise PermissionDenied('Project not found.')

        if project.group not in user.groups.all():
            raise PermissionDenied('Not a member of the project group.')

        serializer.save(project=project)

@extend_schema(
    description="Retrieve, update, or delete a specific asset. User must have access to the asset's project. Project associations cannot be changed.",
    summary="Asset CRUD Operations",
    tags=['Assets'],
    parameters=[
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el"). If provided, multilingual fields will return just the string for that locale instead of the full multilingual object.',
            required=False,
            type=str
        ),
    ],
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
class AssetRetrieveUpdateDestroyView(LocaleContextMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_groups = user.groups.all()
        # Include assets from projects and tours that user has access to
        return Asset.objects.filter(
            project__group__in=user_groups
        )  # type: ignore[attr-defined]
