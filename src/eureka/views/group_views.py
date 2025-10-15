from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

from ..serializers import GroupCreateSerializer, GroupMemberManagementSerializer
from ..permissions import IsGroupMember # Your custom permission

@extend_schema(
    description="Create a new group and automatically become its first member.",
    summary="Create Group",
    tags=['Group Management'],
    responses={
        201: OpenApiResponse(
            description="Group created successfully",
            response={
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer', 'description': 'Group ID'},
                    'name': {'type': 'string', 'description': 'Group name'}
                },
                'required': ['id', 'name']
            },
            examples=[
                OpenApiExample('Success', value={'id': 1, 'name': 'My Group'})
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
                OpenApiExample('Bad Request', value={'detail': 'Invalid group data.'})
            ]
        )
    }
)
class GroupCreateView(generics.CreateAPIView):
    """
    Allows any authenticated user to create a new group and automatically become its first member.
    POST /api/groups/
    """
    serializer_class = GroupCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        group = serializer.save() # Create the group
        # Add the creating user to the new group
        self.request.user.groups.add(group)
        # For simplicity, let's assume the first member (creator) is also the admin initially.
        # More complex admin roles might be needed later.

@extend_schema(
    description="Add another user to a group. User must be a member of the group.",
    summary="Add Group Member",
    tags=['Group Management'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'user_identifier': {'type': 'string', 'description': 'User login or email'}
            },
            'required': ['user_identifier']
        }
    },
    responses={
        200: OpenApiResponse(
            description="User added successfully",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Success message'}
                },
                'required': ['detail']
            },
            examples=[
                OpenApiExample('Success', value={'detail': 'User username added to group Group Name.'})
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
                OpenApiExample('Bad Request', value={'detail': 'User is already a member of this group.'})
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
                OpenApiExample('Permission Denied', value={'detail': 'Not a member of this group.'})
            ]
        )
    }
)
class GroupMemberAddView(APIView):
    """
    Allows a group member to add another user to their group.
    POST /api/groups/{pk}/members/add/
    """
    permission_classes = [IsAuthenticated, IsGroupMember] # Custom permission to ensure user is member

    def post(self, request, pk, format=None):
        group = get_object_or_404(Group, pk=pk)
        
        # Use the custom permission's has_object_permission
        self.check_object_permissions(request, group) 

        serializer = GroupMemberManagementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_to_add = serializer.validated_data.get('user_identifier') # type: ignore
        if user_to_add is None:
            return Response({'detail': 'User not found.'}, status=status.HTTP_400_BAD_REQUEST)

        if group.user_set.filter(pk=user_to_add.pk).exists():
            return Response({'detail': 'User is already a member of this group.'}, status=status.HTTP_400_BAD_REQUEST)

        group.user_set.add(user_to_add)
        return Response({'detail': f'User {user_to_add.login} added to group {group.name}.'}, status=status.HTTP_200_OK)

@extend_schema(
    description="Remove a user from a group. User cannot be removed from their personal group.",
    summary="Remove Group Member",
    tags=['Group Management'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'user_identifier': {'type': 'string', 'description': 'User login or email'}
            },
            'required': ['user_identifier']
        }
    },
    responses={
        200: OpenApiResponse(
            description="User removed successfully",
            response={
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'description': 'Success message'}
                },
                'required': ['detail']
            },
            examples=[
                OpenApiExample('Success', value={'detail': 'User username removed from group Group Name.'})
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
                OpenApiExample('Bad Request', value={'detail': 'A user cannot be removed from their personal group.'})
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
                OpenApiExample('Permission Denied', value={'detail': 'Not a member of this group.'})
            ]
        )
    }
)
class GroupMemberRemoveView(APIView):
    """
    Allows a group member to remove another user (or themselves) from their group.
    POST /api/groups/{pk}/members/remove/
    """
    permission_classes = [IsAuthenticated, IsGroupMember] # Custom permission to ensure user is member

    def post(self, request, pk, format=None):
        group = get_object_or_404(Group, pk=pk)

        # Use the custom permission's has_object_permission
        self.check_object_permissions(request, group)

        serializer = GroupMemberManagementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_to_remove = serializer.validated_data['user_identifier'] # type: ignore 

        # CRUCIAL RESTRICTION: Prevent removing a user from their personal group
        if user_to_remove.personal_group == group:
            return Response(
                {'detail': 'A user cannot be removed from their personal group.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not group.user_set.filter(pk=user_to_remove.pk).exists():
            return Response({'detail': 'User is not a member of this group.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # If the user being removed is the last member, add logic here for auto-deletion
        # (though we're handling auto-deletion separately later)

        group.user_set.remove(user_to_remove)
        return Response({'detail': f'User {user_to_remove.login} removed from group {group.name}.'}, status=status.HTTP_200_OK)
