from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import Group
from django_filters.rest_framework import DjangoFilterBackend
from ..models.project import Project
from ..models.asset import Asset
from ..serializers.project_serializer import ProjectSerializer
from ..serializers.asset_serializer import AssetSerializer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import PermissionDenied

@extend_schema(
    methods=['GET'],
    description="List all projects the authenticated user has access to.",
    summary="List Projects",
    tags=['Projects'],
    parameters=[
        OpenApiParameter(name='ordering', description='Order by field (e.g., -created_at)', required=False),
        OpenApiParameter(name='search', description='Search in project title', required=False),
    ],
    responses={
        200: ProjectSerializer(many=True)
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
                'group_id': {'type': 'integer', 'description': 'Group ID where to create the project (optional, defaults to personal group)'}
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
class ProjectListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_groups = self.request.user.groups.all()
        return Project.objects.filter(group__in=user_groups)  # type: ignore[attr-defined]

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
        
        serializer.save(group=group)

@extend_schema(
    description="Retrieve, update, or delete a specific project by ID. Cannot delete projects with existing tours or assets.",
    summary="Project CRUD Operations",
    tags=['Projects'],
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
class ProjectRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Project.objects.all()  # type: ignore[attr-defined]

    def get_queryset(self):
        user_groups = self.request.user.groups.all()
        return Project.objects.filter(group__in=user_groups)  # type: ignore[attr-defined]

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