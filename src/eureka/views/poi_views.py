from rest_framework import status, permissions, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import ObjectDoesNotExist
from ..models.tour import Tour
from ..models.asset import Asset
from ..models.poi import POI
from ..serializers.poi_serializer import POISerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework.exceptions import PermissionDenied
from ..serializers.asset_serializer import AssetSerializer

@extend_schema(
    description="Create a new Point of Interest (POI) for a tour. User must be in the project's group.",
    summary="Create POI",
    tags=['Points of Interest']
)
class POICreateView(generics.CreateAPIView):
    serializer_class = POISerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        tour = serializer.validated_data['tour']
        project = tour.project
        if project.group not in user.groups.all():
            raise PermissionDenied('Not a member of the project group.')
        serializer.save()

@extend_schema(
    description="Retrieve, update, or delete a specific POI. User must have access to the tour's project. Tour association cannot be changed.",
    summary="POI CRUD Operations",
    tags=['Points of Interest']
)
class POIRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = POISerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = POI.objects.all()  # type: ignore[attr-defined]

    def get_queryset(self):
        user = self.request.user
        # Only allow access to POIs in tours the user has access to
        return POI.objects.filter(tour__project__group__in=user.groups.all())  # type: ignore[attr-defined]

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