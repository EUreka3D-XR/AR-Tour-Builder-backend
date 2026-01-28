from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count
from ..models.tour import Tour
from ..models.project import Project
from ..models.poi import POI
from ..serializers.tour_serializer import TourSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from ..permissions import IsGroupMember
from .mixins import LocaleContextMixin, POIPrefetchMixin

@extend_schema(
    methods=['GET'],
    description="List all tours the authenticated user has access to. Supports filtering by project ID.",
    summary="List Tours",
    tags=['Tours'],
    parameters=[
        OpenApiParameter(name='project_id', description='Filter tours by project ID', required=False, type=int),
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el"). If provided, multilingual fields will return just the string for that locale instead of the full multilingual object.',
            required=False,
            type=str
        ),
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
                'project_id': {'type': 'integer', 'description': 'Project ID to create tour for (required)'},
                'distance_meters': {'type': 'integer', 'description': 'Total distance of the tour in meters (optional)'},
                'duration_minutes': {'type': 'integer', 'description': 'Estimated duration of the tour in minutes (optional)'},
                'locales': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Supported language codes for this tour, e.g. ["en", "fr", "it"] (optional)'}
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
class TourListCreateView(POIPrefetchMixin, LocaleContextMixin, generics.ListCreateAPIView):
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
                # Annotate with counts and prefetch POIs for better performance
                return Tour.objects.filter(project=project).prefetch_related(  # type: ignore[attr-defined]
                    self.get_poi_prefetch()
                ).annotate(
                    total_pois=Count('pois', distinct=True),
                    total_assets=Count('pois__assets', distinct=True)
                )
            except ObjectDoesNotExist:
                return Tour.objects.none()  # type: ignore[attr-defined]

        # Return all tours from user's groups with prefetch and annotations
        return Tour.objects.filter(project__group__in=user_groups).prefetch_related(  # type: ignore[attr-defined]
            self.get_poi_prefetch()
        ).annotate(
            total_pois=Count('pois', distinct=True),
            total_assets=Count('pois__assets', distinct=True)
        )

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

    def create(self, request, *args, **kwargs):
        """Override create to return the instance with optimized queryset"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Refetch the created instance directly, since permission was already checked
        instance = Tour.objects.get(pk=serializer.instance.pk)
        serializer = self.get_serializer(instance)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

@extend_schema(
    description="Retrieve, update, or delete a specific tour. When retrieving, returns the tour with an array of its POIs (POIs are populated with their assets). User must have access to the tour's project. Project association and bounding box cannot be changed.",
    summary="Tour CRUD Operations",
    tags=['Tours'],
    parameters=[
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el"). If provided, multilingual fields will return just the string for that locale instead of the full multilingual object.',
            required=False,
            type=str
        ),
    ],
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
class TourRetrieveUpdateView(POIPrefetchMixin, LocaleContextMixin, generics.RetrieveUpdateAPIView):
    serializer_class = TourSerializer
    permission_classes = [permissions.IsAuthenticated, IsGroupMember]

    def get_queryset(self):
        # Annotate with counts and prefetch POIs for better performance
        return Tour.objects.all().prefetch_related(  # type: ignore[attr-defined]
            self.get_poi_prefetch()
        ).annotate(
            total_pois=Count('pois', distinct=True),
            total_assets=Count('pois__assets', distinct=True)
        )

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

class SetTourPublicStatusView(LocaleContextMixin, APIView):
    """Base view for changing tour publication status."""
    serializer_class = TourSerializer
    permission_classes = [permissions.IsAuthenticated]
    is_public = None  # To be set by subclasses
    action_name = None  # To be set by subclasses
    
    def post(self, request, pk):
        user = request.user
        user_groups = user.groups.all()
        
        try:
            tour = Tour.objects.get(pk=pk)  # type: ignore[attr-defined]
        except Tour.DoesNotExist:
            return Response(
                {'detail': 'Tour not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check permission: user must be a member of the project's group
        if not tour.project.group in user_groups:
            return Response(
                {'detail': 'You do not have permission to publish this tour.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Set tour publication status
        tour.is_public = self.is_public
        tour.save()
        
        # Return updated tour data
        context = {'request': request}
        locale = request.query_params.get('locale')
        if locale:
            context['locale'] = locale
        serializer = TourSerializer(tour, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(
    description="Publish a tour by setting is_public=True. User must be a member of the project group.",
    summary="Publish Tour",
    tags=['Tours'],
    request=None,
    responses={
        200: TourSerializer,
        403: OpenApiResponse(
            description="Permission denied",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['detail']
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
            }
        )
    }
)
class PublishTourView(SetTourPublicStatusView):
    is_public = True
    action_name = 'publish'

@extend_schema(
    description="Unpublish a tour by setting is_public=False. User must be a member of the project group.",
    summary="Unpublish Tour",
    tags=['Tours'],
    request=None,
    responses={
        200: TourSerializer,
        403: OpenApiResponse(
            description="Permission denied",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['detail']
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
            }
        )
    }
)
class UnpublishTourView(SetTourPublicStatusView):
    is_public = False
    action_name = 'unpublish'

@extend_schema(
    description="Retrieve a published tour with all its associated data (POIs, assets, etc.) as a single JSON response.",
    summary="Get Published Tour",
    tags=['Tours'],
    parameters=[
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el"). If provided, multilingual fields will return just the string for that locale instead of the full multilingual object.',
            required=False,
            type=str
        ),
    ],
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
                    'bounding_box': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'lat': {'type': 'number', 'description': 'Latitude'},
                                'long': {'type': 'number', 'description': 'Longitude'}
                            }
                        },
                        'description': 'Bounding box as [southwest, northeast] coordinates'
                    },
                    'distance_meters': {'type': 'integer', 'description': 'Total distance of the tour in meters'},
                    'duration_minutes': {'type': 'integer', 'description': 'Estimated duration of the tour in minutes'},
                    'locales': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Supported language codes for this tour, e.g. ["en", "fr", "it"]'},
                    'pois': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'title': {'type': 'object', 'description': 'Multilingual title'},
                                'description': {'type': 'object', 'description': 'Multilingual description'},
                                'coordinates': {
                                    'type': 'object',
                                    'properties': {
                                        'lat': {'type': 'number', 'description': 'Latitude'},
                                        'long': {'type': 'number', 'description': 'Longitude'}
                                    },
                                    'description': 'Coordinates object with lat/long'
                                },
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

    Supports locale filtering: pass a 'locale' query parameter to get just the string
    for that locale instead of the full multilingual object.
    """
    queryset = Tour.objects.all()
    permission_classes = []  # No authentication required for published tours

    def _filter_multilingual_field(self, field_value, locale):
        """
        Helper to filter multilingual field based on locale.
        Returns the string for the locale if locale is provided, otherwise the full object.
        Falls back to 'en' if the requested locale doesn't exist.
        """
        if locale and isinstance(field_value, dict) and 'locales' in field_value:
            locales = field_value['locales']
            return locales.get(locale, locales.get('en', ''))
        return field_value

    def _filter_external_links(self, links_value, locale):
        """
        Helper to filter external links based on locale.
        Returns the array for the locale if locale is provided, otherwise the full object.
        Falls back to 'en' if the requested locale doesn't exist.
        """
        if locale and isinstance(links_value, dict) and 'locales' in links_value:
            locales = links_value['locales']
            return locales.get(locale, locales.get('en', []))
        return links_value

    def _filter_linked_asset(self, linked_asset_value, locale):
        """
        Helper to filter linked asset based on locale.
        Returns the title and url strings for the locale if locale is provided, otherwise the full object.
        Falls back to 'en' if the requested locale doesn't exist.

        Input structure:
        {
            "title": {"locales": {"en": "...", "el": "..."}},
            "url": {"locales": {"en": "...", "el": "..."}}
        }

        Output when locale is provided:
        {
            "title": "...",
            "url": "..."
        }
        """
        if not linked_asset_value or not isinstance(linked_asset_value, dict):
            return linked_asset_value

        if locale:
            result = {}
            for field in ['title', 'url']:
                if field in linked_asset_value and isinstance(linked_asset_value[field], dict):
                    locales = linked_asset_value[field].get('locales', {})
                    result[field] = locales.get(locale, locales.get('en', ''))
                else:
                    result[field] = ''
            return result

        return linked_asset_value

    def retrieve(self, request, *args, **kwargs):
        tour = self.get_object()
        locale = request.query_params.get('locale')

        # Build the complete tour data structure
        tour_data = {
            'id': tour.id,
            'title': self._filter_multilingual_field(tour.title, locale),
            'description': self._filter_multilingual_field(tour.description, locale),
            'is_public': tour.is_public,
            'bounding_box': tour.bounding_box,
            'distance_meters': tour.distance_meters,
            'duration_minutes': tour.duration_minutes,
            'locales': tour.locales,
            'guided': tour.guided,
            'pois': [],
        }
        # Add POIs with their POI assets
        for poi in tour.pois.all().order_by('order'):
            poi_data = {
                'id': poi.id,
                'title': self._filter_multilingual_field(poi.title, locale),
                'description': self._filter_multilingual_field(poi.description, locale),
                'coordinates': poi.coordinates,
                'radius': poi.radius,
                'external_links': self._filter_external_links(poi.external_links, locale),
                'order': poi.order,
                'assets': []
            }
            # Add POI assets associated with this POI
            for asset in poi.assets.all():
                asset_data = {
                    'id': asset.id,
                    'type': asset.type,
                    'title': self._filter_multilingual_field(asset.title, locale),
                    'description': self._filter_multilingual_field(asset.description, locale),
                    'url': self._filter_multilingual_field(asset.url, locale),
                    'priority': asset.priority,
                    'view_in_ar': asset.view_in_ar,
                    'georeference': asset.georeference,
                    'linked_asset': self._filter_linked_asset(asset.linked_asset, locale)
                }
                poi_data['assets'].append(asset_data)
            tour_data['pois'].append(poi_data)
        return Response(tour_data)