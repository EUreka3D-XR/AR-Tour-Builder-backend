# your_app_name/permissions.py
from rest_framework import permissions
from django.contrib.auth.models import Group

class IsGroupMember(permissions.BasePermission):
    """
    Custom permission to only allow members of a group to access/modify its members.
    Assumes the group ID is passed in the URL (e.g., /groups/{group_id}/...).
    """
    def has_permission(self, request, view):
        # Object-level permission is more appropriate here,
        # but we use has_permission to fetch the group first.
        group_id = view.kwargs.get('pk') # Or whatever your URLConf names the ID parameter
        if not group_id:
            return False # No group ID provided

        try:
            group = Group.objects.get(pk=group_id)
        except Group.DoesNotExist:
            # The group doesn't exist, so permission cannot be granted
            return False

        # Store the group object on the view for easier access in has_object_permission
        view.group_object = group
        return request.user.is_authenticated # Only authenticated users can check group membership

    def has_object_permission(self, request, view, obj):
        # Check if the requesting user is a member of the group
        # 'obj' here would be the Group instance itself (from get_object in views)
        return obj.user_set.filter(pk=request.user.pk).exists()
    