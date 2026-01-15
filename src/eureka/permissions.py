# your_app_name/permissions.py
from rest_framework import permissions
from django.contrib.auth.models import Group


class ReadOnlyPublicAccess(permissions.BasePermission):
    """
    Custom permission to allow read-only access to unauthenticated users,
    while requiring authentication for write operations (POST, PUT, PATCH, DELETE).

    Safe methods (GET, HEAD, OPTIONS) are allowed for everyone.
    Unsafe methods require authentication.
    """
    def has_permission(self, request, view):
        # Allow safe methods (GET, HEAD, OPTIONS) for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # For unsafe methods, require authentication
        return request.user and request.user.is_authenticated

class IsGroupMember(permissions.BasePermission):
    """
    Custom permission to only allow members of a group to access/modify objects.

    For Group objects: checks if user is a member of the group itself
    For other objects (Tour, Project, etc.): checks if user is a member of the object's associated group
    """
    def has_permission(self, request, view):
        # For authenticated users, allow the check to proceed to has_object_permission
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Check if the requesting user is a member of the group
        # Handle different object types

        if isinstance(obj, Group):
            # 'obj' is a Group instance itself
            return obj.user_set.filter(pk=request.user.pk).exists()

        # For objects with a 'group' attribute (like Project)
        if hasattr(obj, 'group'):
            return obj.group.user_set.filter(pk=request.user.pk).exists()

        # For objects with a 'project' attribute (like Tour)
        if hasattr(obj, 'project'):
            return obj.project.group.user_set.filter(pk=request.user.pk).exists()

        # For objects with a 'tour' attribute (like POI)
        if hasattr(obj, 'tour') and hasattr(obj.tour, 'project'):
            return obj.tour.project.group.user_set.filter(pk=request.user.pk).exists()

        # For objects with a 'poi' attribute (like POIAsset)
        if hasattr(obj, 'poi') and hasattr(obj.poi, 'tour') and hasattr(obj.poi.tour, 'project'):
            return obj.poi.tour.project.group.user_set.filter(pk=request.user.pk).exists()

        # If none of the above, deny permission
        return False
    