from rest_framework import serializers
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

User = get_user_model()

class GroupCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new groups.
    """
    class Meta:
        model = Group
        fields = ('id', 'name') # Only name is needed for creation

    def create(self, validated_data):
        # This serializer will be used by the view to create the group.
        # The view will handle adding the creating user to the group.
        return super().create(validated_data)

class GroupMemberManagementSerializer(serializers.Serializer):
    """
    Serializer for adding/removing users from a group.
    Accepts either an email or a username to identify the user.
    """
    user_identifier = serializers.CharField(required=True)

    def validate_user_identifier(self, value):
        # Try to find the user by email or username
        try:
            # Check if it looks like an email first
            if '@' in value and '.' in value:
                user = User.objects.get(email__iexact=value)
            else:
                user = User.objects.get(username__iexact=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this identifier does not exist.")
        return user # Return the User instance if found
