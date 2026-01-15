from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import Group
from django.db.models import Count, Prefetch
from ..models.project import Project
from ..models.tour import Tour
from ..serializers.project_serializer import ProjectSerializer
from ..serializers.nested_serializers import ProjectPopulatedSerializer
from ..serializers.user_serializer import UserLiteSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import PermissionDenied
from .mixins import LocaleContextMixin, TourPrefetchMixin, POIPrefetchMixin

@extend_schema(
    methods=['GET'],
    description="List all projects the authenticated user has access to. Returns projects with statistics but WITHOUT nested tours array for performance. To get a project with its tours, use the detail endpoint GET /projects/{id}/.",
    summary="List Projects",
    tags=['Projects'],
    parameters=[
        OpenApiParameter(name='ordering', description='Order by field (e.g., -created_at)', required=False),
        OpenApiParameter(name='search', description='Search in project title', required=False),
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el"). Note: Project title and description are not multilingual.',
            required=False,
            type=str
        ),
    ],
    responses={
        200: 'ProjectSerializerLite(many=True)'
    }
)
@extend_schema(
    methods=['POST'],
    description="Create a new project. If group_id is provided and user has access to that group, the project will be created there. Otherwise, it will be created in the user's personal group.",
    summary="Create Project",
    tags=['Projects'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string', 'description': 'Project title'},
                'description': {'type': 'string', 'description': 'Project description (optional)'},
                'group_id': {'type': 'integer', 'description': 'Group ID where to create the project (optional, defaults to personal group)'},
                'locales': {
                    'type': 'array',
                    'items': {'type': 'string'},
                    'description': 'Supported language codes for this project, e.g. ["en", "fr", "it"] (optional)'
                }
            },
            'required': ['title']
        }
    },
    responses={
        201: ProjectSerializer,
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
                OpenApiExample('Invalid Group', value={'detail': 'You do not have access to the specified group.'})
            ]
        )
    }
)
class ProjectListCreateView(TourPrefetchMixin, LocaleContextMixin, generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_groups = self.request.user.groups.all()

        # For list view: only annotate with counts, don't prefetch tours
        # This is much more efficient when fetching multiple projects
        return Project.objects.filter(group__in=user_groups).annotate(  # type: ignore[attr-defined]
            total_tours=Count('tours', distinct=True),
            total_pois=Count('tours__pois', distinct=True)
        )

    def get_serializer_class(self):
        """Use ProjectSerializer without tours field for list view"""
        # Import here to avoid circular dependency
        from ..serializers.project_serializer import ProjectSerializer, ProjectSerializerLite

        # For list view (GET), use lite serializer without tours
        if self.request.method == 'GET':
            return ProjectSerializerLite
        # For create (POST), we'll use the full serializer since we refetch
        return ProjectSerializer

    def perform_create(self, serializer):
        user = self.request.user
        group_id = self.request.data.get('group_id')

        if group_id:
            # Check if user has access to the specified group
            try:
                target_group = Group.objects.get(pk=group_id)
                if target_group not in user.groups.all():
                    raise PermissionDenied('You do not have access to the specified group.')
                group = target_group
            except ObjectDoesNotExist:
                raise PermissionDenied('Group not found.')
        else:
            # Use personal group as default
            group = user.personal_group

        serializer.save(group=group, created_by=user)

    def create(self, request, *args, **kwargs):
        """Override create to return the instance with optimized queryset including tours"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Refetch the created instance with tours prefetch
        user_groups = request.user.groups.all()
        instance = Project.objects.filter(  # type: ignore[attr-defined]
            pk=serializer.instance.pk,
            group__in=user_groups
        ).prefetch_related(self.get_tour_prefetch()).annotate(
            total_tours=Count('tours', distinct=True),
            total_pois=Count('tours__pois', distinct=True)
        ).first()

        # Use the full ProjectSerializer for the response
        from ..serializers.project_serializer import ProjectSerializer
        serializer = ProjectSerializer(instance, context={'request': request})

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

@extend_schema(
    description="Retrieve, update, or delete a specific project by ID. When retrieving, returns the project with an array of its tours (tours include statistics but NOT nested POIs for performance). To get fully populated data, use the /projects/{id}/populated endpoint. Cannot delete projects with existing tours or assets.",
    summary="Project CRUD Operations",
    tags=['Projects'],
    parameters=[
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el"). Note: Project title and description are not multilingual, but tour titles and descriptions are multilingual.',
            required=False,
            type=str
        ),
    ],
    responses={
        200: ProjectSerializer,
        204: OpenApiResponse(
            description="Project deleted successfully",
            response=None
        ),
        400: OpenApiResponse(
            description="Cannot delete project",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['detail']
            },
            examples=[
                OpenApiExample('Cannot Delete', value={'detail': 'Cannot delete a project with existing tours or assets.'})
            ]
        ),
        404: OpenApiResponse(
            description="Project not found",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['detail']
            },
            examples=[
                OpenApiExample('Not Found', value={'detail': 'Project not found.'})
            ]
        )
    }
)
class ProjectRetrieveUpdateDestroyView(TourPrefetchMixin, LocaleContextMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Project.objects.all()  # type: ignore[attr-defined]

    def get_queryset(self):
        user_groups = self.request.user.groups.all()

        # Note: We only prefetch tours without their nested POIs.
        # This keeps the query efficient for the project detail view.
        # If you need fully populated tours with POIs, use the ProjectPopulatedView endpoint instead.
        return Project.objects.filter(group__in=user_groups).prefetch_related(  # type: ignore[attr-defined]
            self.get_tour_prefetch()
        ).annotate(
            total_tours=Count('tours', distinct=True),
            total_pois=Count('tours__pois', distinct=True)
        )

    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        
        # Check if project has associated tours
        if hasattr(project, 'tour_set') and project.tour_set.exists():
            return Response(
                {'detail': 'Cannot delete a project with existing tours.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if project has associated assets
        if hasattr(project, 'asset_set') and project.asset_set.exists():
            return Response(
                {'detail': 'Cannot delete a project with existing assets.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)

@extend_schema(
    description="Move a project to a different group where the user is a member.",
    summary="Move Project to Different Group",
    tags=['Projects'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'group_id': {'type': 'integer', 'description': 'Target group ID'}
            },
            'required': ['group_id']
        }
    },
    responses={
        200: OpenApiResponse(
            description="Project moved successfully",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Success message'}
                },
                'required': ['detail']
            },
            examples=[
                OpenApiExample('Success', value={'detail': 'Project group updated.'})
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
                OpenApiExample('Permission Denied', value={'detail': 'Not a member of the target group.'})
            ]
        ),
        404: OpenApiResponse(
            description="Group not found",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['detail']
            },
            examples=[
                OpenApiExample('Group Not Found', value={'detail': 'Group not found.'})
            ]
        )
    }
)
class ProjectMoveGroupView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        project = Project.objects.get(pk=pk)  # type: ignore[attr-defined]
        group_id = request.data.get('group_id')
        user = request.user
        try:
            target_group = Group.objects.get(pk=group_id)
        except ObjectDoesNotExist:
            return Response({'detail': 'Group not found.'}, status=status.HTTP_404_NOT_FOUND)
        if target_group not in user.groups.all():
            return Response({'detail': 'Not a member of the target group.'}, status=status.HTTP_403_FORBIDDEN)
        project.group = target_group
        project.save()
        return Response({'detail': 'Project group updated.'})

@extend_schema(
    description="Retrieve a fully populated project with all nested tours, POIs, assets, and group members. This endpoint is optimized for fetching complete project data in a single request with all calculated statistics.",
    summary="Get Populated Project",
    tags=['Projects'],
    parameters=[
        OpenApiParameter(
            name='locale',
            description='Language code to filter multilingual fields (e.g., "en", "fr", "el"). If provided, multilingual fields will return just the string for that locale instead of the full multilingual object.',
            required=False,
            type=str
        ),
        OpenApiParameter(
            name='public_only',
            description='If "true", only return public tours (is_public=True). Defaults to false (returns all tours).',
            required=False,
            type=str
        ),
    ],
    responses={
        200: ProjectPopulatedSerializer,
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
                OpenApiExample('Permission Denied', value={'detail': 'You do not have permission to access this project.'})
            ]
        ),
        404: OpenApiResponse(
            description="Project not found",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['detail']
            },
            examples=[
                OpenApiExample('Not Found', value={'detail': 'Not found.'})
            ]
        )
    }
)
class ProjectPopulatedView(POIPrefetchMixin, LocaleContextMixin, generics.RetrieveAPIView):
    """
    Retrieve a fully populated project with all nested data.

    This endpoint returns:
    - Project details with total_tours and total_pois statistics
    - Group members list (users who have access to this project)
    - All tours with total_pois and total_assets statistics
    - All POIs with media stats (image, video, audio, model3d, text counts)
    - All POI assets with complete details

    The endpoint uses optimized queries with prefetch_related and annotations
    to minimize database queries (approximately 5-6 queries total).

    Query parameters:
    - locale: Get just the string for that locale instead of the full multilingual object
    - public_only: If 'true', only return public tours (is_public=True)
    """
    serializer_class = ProjectPopulatedSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Optimize the queryset with prefetch_related and annotations.

        This approach ensures:
        1. All related data is fetched in minimal queries
        2. Statistics are calculated efficiently with annotations
        3. POIs are ordered correctly
        4. Assets are included for each POI
        """
        user_groups = self.request.user.groups.all()

        # Check if we should filter for public tours only
        public_only = self.request.query_params.get('public_only', '').lower() == 'true'

        # Build tour queryset with optional public filter
        tour_queryset = Tour.objects.prefetch_related(self.get_poi_prefetch()).annotate(  # type: ignore[attr-defined]
            total_pois=Count('pois', distinct=True),
            total_assets=Count('pois__assets', distinct=True)
        )

        if public_only:
            tour_queryset = tour_queryset.filter(is_public=True)

        # Create optimized prefetch for tours with POIs
        tour_prefetch = Prefetch(
            'tours',
            queryset=tour_queryset
        )

        # Main queryset with all prefetches and project-level annotations
        return Project.objects.filter(  # type: ignore[attr-defined]
            group__in=user_groups
        ).prefetch_related(
            tour_prefetch,
            'group__user_set'  # Prefetch group members to avoid N+1 queries
        ).annotate(
            total_tours=Count('tours', distinct=True),
            total_pois=Count('tours__pois', distinct=True)
        )

@extend_schema(
    description="Retrieve the list of members for a specific project. Returns all users who are members of the project's group.",
    summary="Get Project Members",
    tags=['Projects'],
    responses={
        200: OpenApiResponse(
            description="List of project members",
            response=UserLiteSerializer(many=True)
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
                OpenApiExample('Permission Denied', value={'detail': 'You do not have permission to access this project.'})
            ]
        ),
        404: OpenApiResponse(
            description="Project not found",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['detail']
            },
            examples=[
                OpenApiExample('Not Found', value={'detail': 'Not found.'})
            ]
        )
    }
)
class ProjectMembersView(generics.GenericAPIView):
    """
    Retrieve the list of members for a specific project.

    This endpoint returns all users who are members of the project's group,
    ordered by username.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserLiteSerializer

    def get(self, request, pk):
        """Get list of members for the specified project"""
        user_groups = request.user.groups.all()

        try:
            project = Project.objects.filter(  # type: ignore[attr-defined]
                pk=pk,
                group__in=user_groups
            ).select_related('group').first()

            if not project:
                return Response(
                    {'detail': 'Not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Get all members of the project's group
            members = project.group.user_set.all().order_by('username')
            serializer = UserLiteSerializer(members, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )