from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from eureka.models.poi_asset import POIAsset
from eureka.models.poi import POI
from eureka.models.asset import Asset
from eureka.serializers.poi_asset_serializer import POIAssetSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from .mixins import LocaleContextMixin, POIAssetPermissionMixin

@extend_schema(
    methods=['GET'],
    description="List all POI assets the authenticated user has access to. Supports filtering by POI.",
    summary="List POI Assets",
    tags=['POI Assets'],
    parameters=[
        OpenApiParameter(name='poi_id', description='Filter POI assets by POI ID', required=False, type=int),
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el"). If provided, multilingual fields will return just the string for that locale instead of the full multilingual object.',
            required=False,
            type=str
        ),
    ],
    responses={
        200: POIAssetSerializer(many=True)
    }
)
@extend_schema(
    methods=['POST'],
    description="Create a new POI asset. Two modes: (1) From existing asset template - provide source_asset_id to copy fields. (2) From scratch - provide title, type, url to create both POI asset and source asset.",
    summary="Create POI Asset",
    tags=['POI Assets'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'poi_id': {'type': 'integer', 'description': 'POI ID to create asset for (required)'},
                'source_asset_id': {'type': 'integer', 'description': 'Source asset ID to use as template (optional - if not provided, creates new asset)'},
                'title': {'type': 'object', 'description': 'Multilingual title (optional if source_asset_id provided, required otherwise)'},
                'description': {'type': 'object', 'description': 'Multilingual description (optional)'},
                'type': {'type': 'string', 'description': 'Asset type (optional if source_asset_id provided, required otherwise)'},
                'url': {'type': 'string', 'description': 'Asset URL (optional if source_asset_id provided, required otherwise)'},
                'priority': {'type': 'string', 'description': 'Priority: normal or high (default: normal)'},
                'view_in_ar': {'type': 'boolean', 'description': 'Whether to view in AR (default: false)'},
                'ar_placement': {'type': 'string', 'description': 'AR placement mode: free or ground (default: free)', 'enum': ['free', 'ground']},
            },
            'required': ['poi_id']
        }
    },
    responses={
        201: POIAssetSerializer,
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
class POIAssetListCreateView(LocaleContextMixin, generics.ListCreateAPIView):
    serializer_class = POIAssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_groups = user.groups.all()

        # Filter POI assets by user's accessible projects
        queryset = POIAsset.objects.filter(poi__tour__project__group__in=user_groups)

        poi_id = self.request.query_params.get('poi_id')
        if poi_id:
            queryset = queryset.filter(poi_id=poi_id)

        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        user = self.request.user
        poi_id = self.request.data.get('poi_id')
        source_asset_id = self.request.data.get('source_asset_id')

        if not poi_id:
            raise PermissionDenied('poi_id is required to create a POI asset.')

        try:
            poi = POI.objects.get(pk=poi_id)  # type: ignore[attr-defined]
        except ObjectDoesNotExist:
            raise PermissionDenied('POI not found.')

        # Check user has access to the POI's project
        if poi.tour.project.group not in user.groups.all():
            raise PermissionDenied('Not a member of the POI project group.')

        validated_data = serializer.validated_data

        # Use transaction to ensure atomicity
        with transaction.atomic():
            # If priority is 'high', demote all other POI assets of the same POI
            if validated_data.get('priority') == 'high':
                POIAsset.objects.filter(  # type: ignore[attr-defined]
                    poi=poi,
                    priority='high'
                ).update(priority='normal')

            # Case 1: Creating POI asset from an existing source asset
            if source_asset_id:
                try:
                    source_asset = Asset.objects.get(pk=source_asset_id)  # type: ignore[attr-defined]
                except ObjectDoesNotExist:
                    raise PermissionDenied('Source asset not found.')

                # Ensure source asset belongs to the same project as the POI
                if source_asset.project != poi.tour.project:
                    raise PermissionDenied('Source asset must belong to the same project as the POI.')

                # Copy fields from source asset if not provided
                if 'title' not in validated_data:
                    validated_data['title'] = source_asset.title
                if 'description' not in validated_data:
                    validated_data['description'] = source_asset.description
                if 'type' not in validated_data:
                    validated_data['type'] = source_asset.type
                if 'url' not in validated_data:
                    validated_data['url'] = source_asset.url

                serializer.save(poi=poi, source_asset=source_asset)

            # Case 2: Creating POI asset from scratch (no source asset provided)
            else:
                # Validate required fields when creating from scratch
                if 'title' not in validated_data:
                    raise PermissionDenied('title is required when creating POI asset without source_asset_id.')
                if 'type' not in validated_data:
                    raise PermissionDenied('type is required when creating POI asset without source_asset_id.')
                if 'url' not in validated_data:
                    raise PermissionDenied('url is required when creating POI asset without source_asset_id.')

                # Create a new Asset as the source
                new_asset = Asset.objects.create(  # type: ignore[attr-defined]
                    project=poi.tour.project,
                    title=validated_data['title'],
                    description=validated_data.get('description'),
                    type=validated_data['type'],
                    url=validated_data['url']
                )

                # Save POI asset with the newly created source asset
                serializer.save(poi=poi, source_asset=new_asset)

@extend_schema(
    description="Retrieve, update, or delete a specific POI asset. User must have access to the POI's project.",
    summary="POI Asset CRUD Operations",
    tags=['POI Assets'],
    parameters=[
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el"). If provided, multilingual fields will return just the string for that locale instead of the full multilingual object.',
            required=False,
            type=str
        ),
    ],
    responses={
        200: POIAssetSerializer,
        204: OpenApiResponse(
            description="POI Asset deleted successfully",
            response=None
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
class POIAssetRetrieveUpdateDestroyView(LocaleContextMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = POIAssetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        user_groups = user.groups.all()
        # Include POI assets from projects that user has access to
        return POIAsset.objects.filter(
            poi__tour__project__group__in=user_groups
        )  # type: ignore[attr-defined]

    def perform_update(self, serializer):
        validated_data = serializer.validated_data
        poi_asset = self.get_object()

        # Use transaction to ensure atomicity
        with transaction.atomic():
            # If priority is being set to 'high', demote all other POI assets of the same POI
            if validated_data.get('priority') == 'high':
                POIAsset.objects.filter(  # type: ignore[attr-defined]
                    poi=poi_asset.poi,
                    priority='high'
                ).exclude(pk=poi_asset.pk).update(priority='normal')

            serializer.save()

@extend_schema(
    methods=['POST'],
    description="Set a POI asset as primary (priority='high'). Automatically demotes all other POI assets of the same POI to priority='normal'. Only one POI asset can be primary per POI.",
    summary="Set POI Asset as Primary",
    tags=['POI Assets'],
    parameters=[
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el"). If provided, multilingual fields will return just the string for that locale instead of the full multilingual object.',
            required=False,
            type=str
        ),
    ],
    responses={
        200: POIAssetSerializer,
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
            description="POI Asset not found",
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
class POIAssetSetPrimaryView(POIAssetPermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        # Get POI asset and check permissions
        poi_asset, error_response = self.get_poi_asset_with_permission_check(request, pk)
        if error_response:
            return error_response

        # Use transaction to ensure atomicity
        with transaction.atomic():
            # Demote all other POI assets of the same POI from 'high' to 'normal'
            POIAsset.objects.filter(  # type: ignore[attr-defined]
                poi=poi_asset.poi,
                priority='high'
            ).exclude(pk=pk).update(priority='normal')

            # Set this POI asset as primary
            poi_asset.priority = 'high'
            poi_asset.save()

        # Return the updated POI asset
        context = self.build_serializer_context(request)
        serializer = POIAssetSerializer(poi_asset, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)

@extend_schema(
    methods=['POST'],
    description="Unset a POI asset as primary by setting its priority to 'normal'. Does not modify any other POI assets.",
    summary="Unset POI Asset as Primary",
    tags=['POI Assets'],
    parameters=[
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el"). If provided, multilingual fields will return just the string for that locale instead of the full multilingual object.',
            required=False,
            type=str
        ),
    ],
    responses={
        200: POIAssetSerializer,
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
            description="POI Asset not found",
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
class POIAssetUnsetPrimaryView(POIAssetPermissionMixin, APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        # Get POI asset and check permissions
        poi_asset, error_response = self.get_poi_asset_with_permission_check(request, pk)
        if error_response:
            return error_response

        # Set priority to normal (no mutations to other POI assets)
        with transaction.atomic():
            poi_asset.priority = 'normal'
            poi_asset.save()

        # Return the updated POI asset
        context = self.build_serializer_context(request)
        serializer = POIAssetSerializer(poi_asset, context=context)
        return Response(serializer.data, status=status.HTTP_200_OK)
