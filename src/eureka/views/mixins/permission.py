"""
Mixins for permission checking and object retrieval.
"""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from eureka.models.poi_asset import POIAsset


class POIAssetPermissionMixin:
    """
    Mixin to handle POI asset retrieval with permission checking.

    Provides a method to retrieve a POI asset by primary key and verify
    that the requesting user has access to the project that contains it.
    """

    def get_poi_asset_with_permission_check(self, request, pk):
        """
        Retrieve a POI asset and verify user has permission to access it.

        Args:
            request: The HTTP request object containing the authenticated user
            pk: Primary key of the POI asset to retrieve

        Returns:
            tuple: (poi_asset, error_response)
                - If successful: (POIAsset instance, None)
                - If failed: (None, Response with error details)

        Raises:
            PermissionDenied: If user is not a member of the POI asset's project group
        """
        user_groups = request.user.groups.all()

        try:
            poi_asset = POIAsset.objects.select_related(
                'poi__tour__project__group'
            ).get(pk=pk)
        except ObjectDoesNotExist:
            return None, Response(
                {'detail': 'POI Asset not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if poi_asset.poi.tour.project.group not in user_groups:
            raise PermissionDenied('Not a member of the POI asset project group.')

        return poi_asset, None

    def build_serializer_context(self, request):
        """
        Build serializer context with request and optional locale parameter.

        Args:
            request: The HTTP request object

        Returns:
            dict: Context dictionary for serializer
        """
        context = {'request': request}
        locale = request.query_params.get('locale')
        if locale:
            context['locale'] = locale
        return context
