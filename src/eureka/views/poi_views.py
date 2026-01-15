from rest_framework import status, permissions, generics, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q, Max, F
from django.db import transaction
from ..models.asset import Asset
from ..models.poi import POI
from ..models.tour import Tour
from ..serializers.poi_serializer import POISerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework.exceptions import PermissionDenied
from ..serializers.asset_serializer import AssetSerializer
from .mixins import LocaleContextMixin

@extend_schema(
    methods=['GET'],
    description="List all POIs the authenticated user has access to. Supports filtering by tour ID.",
    summary="List POIs",
    tags=['Points of Interest'],
    parameters=[
        OpenApiParameter(name='tour_id', description='Filter POIs by tour ID', required=False, type=int),
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el"). If provided, multilingual fields will return just the string for that locale instead of the full multilingual object.',
            required=False,
            type=str
        ),
    ],
    responses={
        200: POISerializer(many=True)
    }
)
@extend_schema(
    methods=['POST'],
    description="Create a new Point of Interest (POI) for a tour. User must be in the project's group.",
    summary="Create POI",
    tags=['Points of Interest'],
    parameters=[
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el"). If provided, multilingual fields will return just the string for that locale instead of the full multilingual object.',
            required=False,
            type=str
        ),
    ],
    responses={
        201: POISerializer,
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
        )
    }
)
class POIListCreateView(LocaleContextMixin, generics.ListCreateAPIView):
    serializer_class = POISerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_groups = user.groups.all()

        # Filter by tour if specified
        tour_id = self.request.query_params.get('tour_id')

        # Base queryset with permissions and annotations
        queryset = POI.objects.filter(tour__project__group__in=user_groups).annotate(  # type: ignore[attr-defined]
            stat_image=Count('assets', filter=Q(assets__type__istartswith='image') | Q(assets__type='image')),
            stat_video=Count('assets', filter=Q(assets__type__istartswith='video') | Q(assets__type='video')),
            stat_audio=Count('assets', filter=Q(assets__type__istartswith='audio') | Q(assets__type='audio')),
            stat_model3d=Count('assets', filter=Q(assets__type__istartswith='model') | Q(assets__type='model3d')),
            stat_text=Count('assets', filter=Q(assets__type__istartswith='text') | Q(assets__type='text'))
        ).order_by('tour', 'order')

        if tour_id:
            queryset = queryset.filter(tour_id=tour_id)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        tour_id = self.request.data.get('tour_id')
        if not tour_id:
            raise serializers.ValidationError({'tour_id': 'This field is required.'})

        try:
            tour = Tour.objects.get(pk=tour_id)
        except Tour.DoesNotExist:
            raise serializers.ValidationError({'tour_id': 'Invalid tour ID.'})

        project = tour.project
        if project.group not in user.groups.all():
            raise PermissionDenied('Not a member of the project group.')

        # Use transaction with select_for_update to prevent race conditions
        # when multiple POIs are created concurrently for the same tour
        with transaction.atomic():
            # Lock the tour to prevent concurrent order calculation
            Tour.objects.select_for_update().get(pk=tour_id)

            # Calculate the next order value for this tour
            max_order = POI.objects.filter(tour=tour).aggregate(Max('order'))['order__max']  # type: ignore[attr-defined]
            next_order = (max_order or 0) + 1

            serializer.save(tour=tour, order=next_order)

@extend_schema(
    description="Retrieve, update, or delete a specific POI. User must have access to the tour's project. Tour association cannot be changed.",
    summary="POI CRUD Operations",
    tags=['Points of Interest'],
    parameters=[
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el"). If provided, multilingual fields will return just the string for that locale instead of the full multilingual object.',
            required=False,
            type=str
        ),
    ]
)
class POIRetrieveUpdateDestroyView(LocaleContextMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = POISerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = POI.objects.all()  # type: ignore[attr-defined]

    def get_queryset(self):
        user = self.request.user
        # Only allow access to POIs in tours the user has access to
        # Annotate with media stats for better performance
        return POI.objects.filter(tour__project__group__in=user.groups.all()).annotate(  # type: ignore[attr-defined]
            stat_image=Count('assets', filter=Q(assets__type__istartswith='image') | Q(assets__type='image')),
            stat_video=Count('assets', filter=Q(assets__type__istartswith='video') | Q(assets__type='video')),
            stat_audio=Count('assets', filter=Q(assets__type__istartswith='audio') | Q(assets__type='audio')),
            stat_model3d=Count('assets', filter=Q(assets__type__istartswith='model') | Q(assets__type='model3d')),
            stat_text=Count('assets', filter=Q(assets__type__istartswith='text') | Q(assets__type='text'))
        )

    def perform_destroy(self, instance):
        tour = instance.tour
        deleted_order = instance.order

        # Delete the POI first
        instance.delete()

        # Efficiently update orders of subsequent POIs in a single query
        POI.objects.filter(  # type: ignore[attr-defined]
            tour=tour,
            order__gt=deleted_order
        ).update(order=F('order') - 1)

@extend_schema(
    description="Create an Asset for a POI by copying from either a project Asset or another Asset (with poi set).",
    summary="Create Tour Asset for POI",
    tags=['Tour Assets'],
    parameters=[
        OpenApiParameter(name='poi_id', description='ID of the POI', required=True, type=int),
        OpenApiParameter(name='asset_id', description='ID of the source Asset (project asset)', required=False, type=int),
        OpenApiParameter(name='source_tourasset_id', description='ID of the source Asset (previously TourAsset)', required=False, type=int),
    ],
    responses={
        201: OpenApiResponse(
            description="Asset created successfully",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Success message'},
                    'asset_id': {'type': 'integer', 'description': 'Created asset ID'}
                },
                'required': ['detail', 'asset_id']
            },
            examples=[
                OpenApiExample('Success', value={'detail': 'Asset created.', 'asset_id': 123})
            ]
        ),
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
                OpenApiExample('Bad Request', value={'detail': 'Must provide poi_id and either asset_id or source_tourasset_id.'})
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
            description="Not found",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['detail']
            },
            examples=[
                OpenApiExample('Not Found', value={'detail': 'POI not found.'})
            ]
        )
    }
)
class TourAssetCreateForPOIView(APIView):
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        poi_id = request.query_params.get('poi_id')
        asset_id = request.query_params.get('asset_id')
        source_tourasset_id = request.query_params.get('source_tourasset_id')

        if not poi_id or (not asset_id and not source_tourasset_id):
            return Response({'detail': 'Must provide poi_id and either asset_id or source_tourasset_id.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            poi = POI.objects.get(pk=poi_id)  # type: ignore[attr-defined]
        except ObjectDoesNotExist:
            return Response({'detail': 'POI not found.'}, status=status.HTTP_404_NOT_FOUND)

        tour = poi.tour
        project = tour.project
        if project.group not in user.groups.all():
            raise PermissionDenied('Not a member of the project group.')

        # Determine the source and copy fields
        if asset_id:
            try:
                source = Asset.objects.get(pk=asset_id)  # type: ignore[attr-defined]
                source_type = 'asset'
            except ObjectDoesNotExist:
                return Response({'detail': 'Asset not found.'}, status=status.HTTP_404_NOT_FOUND)
        elif source_tourasset_id:
            try:
                source = Asset.objects.get(pk=source_tourasset_id)  # type: ignore[attr-defined]
                source_type = 'tourasset'
            except ObjectDoesNotExist:
                return Response({'detail': 'Source Asset not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'detail': 'Must provide either asset_id or source_tourasset_id.'}, status=status.HTTP_400_BAD_REQUEST)

        # Copy fields from the source
        asset = Asset.objects.create(  # type: ignore[attr-defined]
            poi=poi,
            project=source.project,
            type=source.type,
            title=source.title,
            description=source.description,
            url=source.url,
            language=source.language,
            thumbnail=source.thumbnail,
            source_asset=source if source_type == 'asset' else source.source_asset or source
        )

        return Response({'detail': 'Asset created.', 'asset_id': asset.id}, status=status.HTTP_201_CREATED) 