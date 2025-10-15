from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from ..models.tour import Tour
from ..models.project import Project
from ..models.poi import POI
from ..serializers.tour_serializer import TourSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from ..permissions import IsGroupMember

@extend_schema(
    methods=['GET'],
    description="List all tours the authenticated user has access to. Supports filtering by project ID.",
    summary="List Tours",
    tags=['Tours'],
    parameters=[
        OpenApiParameter(name='project_id', description='Filter tours by project ID', required=False, type=int),
    ],
    responses={
        200: TourSerializer(many=True)
    }
)
@extend_schema(
    methods=['POST'],
    description="Create a new tour for a project. User must be a member of the project group.",
    summary="Create Tour",
    tags=['Tours'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'title': {'type': 'object', 'description': 'Multilingual title with locales structure'},
                'description': {'type': 'object', 'description': 'Multilingual description with locales structure (optional)'},
                'is_public': {'type': 'boolean', 'description': 'Whether the tour is public (optional, defaults to false)'},
                'project_id': {'type': 'integer', 'description': 'Project ID to create tour for (required)'}
            },
            'required': ['title', 'project_id']
        }
    },
    responses={
        201: TourSerializer,
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
                OpenApiExample('Missing Project', value={'detail': 'project_id is required to create a tour.'})
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
class TourListCreateView(generics.ListCreateAPIView):
    serializer_class = TourSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_groups = user.groups.all()
        
        # Filter by project if specified
        project_id = self.request.query_params.get('project_id')
        if project_id:
            try:
                project = Project.objects.get(pk=project_id)  # type: ignore[attr-defined]
                if project.group not in user_groups:
                    return Tour.objects.none()  # type: ignore[attr-defined]
                return Tour.objects.filter(project=project)  # type: ignore[attr-defined]
            except ObjectDoesNotExist:
                return Tour.objects.none()  # type: ignore[attr-defined]
        
        # Return all tours from user's groups
        return Tour.objects.filter(project__group__in=user_groups)  # type: ignore[attr-defined]

    def perform_create(self, serializer):
        project_id = self.request.data.get('project_id')
        if not project_id:
            raise PermissionDenied('project_id is required to create a tour.')
        
        try:
            project = Project.objects.get(pk=project_id)  # type: ignore[attr-defined]
        except ObjectDoesNotExist:
            raise PermissionDenied('Project not found.')
        
        user = self.request.user
        if project.group not in user.groups.all():
            raise PermissionDenied('Not a member of the project group.')
        
        serializer.save(project=project)

@extend_schema(
    description="Retrieve, update, or delete a specific tour. User must have access to the tour's project. Project association and bounding box coordinates cannot be changed.",
    summary="Tour CRUD Operations",
    tags=['Tours'],
    responses={
        200: TourSerializer,
        204: OpenApiResponse(
            description="Tour deleted successfully",
            response=None
        ),
        400: OpenApiResponse(
            description="Cannot delete tour",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['detail']
            },
            examples=[
                OpenApiExample('Cannot Delete', value={'detail': 'Cannot delete a public tour or tour with POIs.'})
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
                OpenApiExample('Permission Denied', value={'detail': 'Not a member of the project group.'})
            ]
        ),
        404: OpenApiResponse(
            description="Tour not found",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['detail']
            },
            examples=[
                OpenApiExample('Not Found', value={'detail': 'Tour not found.'})
            ]
        )
    }
)
class TourRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = TourSerializer
    permission_classes = [permissions.IsAuthenticated, IsGroupMember]
    queryset = Tour.objects.all()

    def delete(self, request, pk):
        user = request.user
        user_groups = user.groups.all()
        try:
            tour = Tour.objects.get(pk=pk, project__group__in=user_groups)  # type: ignore[attr-defined]
        except ObjectDoesNotExist:
            return Response({'detail': 'Tour not found.'}, status=status.HTTP_404_NOT_FOUND)
        if tour.is_public:
            return Response({'detail': 'Cannot delete a public tour.'}, status=status.HTTP_400_BAD_REQUEST)
        if POI.objects.filter(tour=tour).exists():  # type: ignore[attr-defined]
            return Response({'detail': 'Cannot delete a tour with POIs.'}, status=status.HTTP_400_BAD_REQUEST)
        tour.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@extend_schema(
    description="Retrieve a published tour with all its associated data (POIs, assets, etc.) as a single JSON response.",
    summary="Get Published Tour",
    tags=['Tours'],
    responses={
        200: OpenApiResponse(
            description="Published tour data",
            response={
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer', 'description': 'Tour ID'},
                    'title': {'type': 'object', 'description': 'Multilingual title'},
                    'description': {'type': 'object', 'description': 'Multilingual description'},
                    'is_public': {'type': 'boolean', 'description': 'Public visibility flag'},
                    'min_latitude': {'type': 'number', 'description': 'Minimum latitude'},
                    'max_latitude': {'type': 'number', 'description': 'Maximum latitude'},
                    'min_longitude': {'type': 'number', 'description': 'Minimum longitude'},
                    'max_longitude': {'type': 'number', 'description': 'Maximum longitude'},
                    'pois': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'name': {'type': 'object', 'description': 'Multilingual name'},
                                'description': {'type': 'object', 'description': 'Multilingual description'},
                                'latitude': {'type': 'number'},
                                'longitude': {'type': 'number'},
                                'order': {'type': 'integer'},
                                'assets': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'id': {'type': 'integer'},
                                            'type': {'type': 'string'},
                                            'title': {'type': 'object', 'description': 'Multilingual title'},
                                            'description': {'type': 'object', 'description': 'Multilingual description'},
                                            'url': {'type': 'string'},
                                            'language': {'type': 'string'},
                                            'thumbnail': {'type': 'string'}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    'assets': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'type': {'type': 'string'},
                                'title': {'type': 'object', 'description': 'Multilingual title'},
                                'description': {'type': 'object', 'description': 'Multilingual description'},
                                'url': {'type': 'string'},
                                'language': {'type': 'string'},
                                'thumbnail': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        ),
        404: OpenApiResponse(
            description="Tour not found",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['detail']
            },
            examples=[
                OpenApiExample('Not Found', value={'detail': 'Tour not found.'})
            ]
        )
    }
)
class PublishedTourView(generics.RetrieveAPIView):
    """
    Retrieve a published tour with all its associated data as a single JSON response.
    GET /api/publishedTour/{id}/
    """
    queryset = Tour.objects.all()
    permission_classes = []  # No authentication required for published tours
    
    def retrieve(self, request, *args, **kwargs):
        tour = self.get_object()
        
        # Build the complete tour data structure
        tour_data = {
            'id': tour.id,
            'title': tour.title,
            'description': tour.description,
            'is_public': tour.is_public,
            'min_latitude': float(tour.min_latitude) if tour.min_latitude else None,
            'max_latitude': float(tour.max_latitude) if tour.max_latitude else None,
            'min_longitude': float(tour.min_longitude) if tour.min_longitude else None,
            'max_longitude': float(tour.max_longitude) if tour.max_longitude else None,
            'pois': [],
            'assets': []
        }
        
        # Add POIs with their assets
        for poi in tour.pois.all().order_by('order'):
            poi_data = {
                'id': poi.id,
                'name': poi.name,
                'description': poi.description,
                'latitude': poi.latitude,
                'longitude': poi.longitude,
                'order': poi.order,
                'assets': []
            }
            
            # Add assets associated with this POI
            for asset in poi.assets.all():
                asset_data = {
                    'id': asset.id,
                    'type': asset.type,
                    'title': asset.title,
                    'description': asset.description,
                    'url': asset.url,
                    'language': asset.language,
                    'thumbnail': asset.thumbnail
                }
                poi_data['assets'].append(asset_data)
            
            tour_data['pois'].append(poi_data)
        
        # Add tour-level assets (assets not associated with any POI)
        for asset in tour.assets.all():
            asset_data = {
                'id': asset.id,
                'type': asset.type,
                'title': asset.title,
                'description': asset.description,
                'url': asset.url,
                'language': asset.language,
                'thumbnail': asset.thumbnail
            }
            tour_data['assets'].append(asset_data)
        
        return Response(tour_data) 