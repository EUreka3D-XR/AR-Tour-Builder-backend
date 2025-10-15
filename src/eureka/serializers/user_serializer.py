from rest_framework import serializers
from rest_framework.authtoken.models import Token # For login response
from django.contrib.auth import authenticate # For authenticating users
from django.contrib.auth.models import Group
from ..models.user import User # Your custom User model

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'login', 'email', 'name', 'is_active', 'is_staff')


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Accepts either email or login username for authentication.
    """
    username = serializers.CharField(required=True, help_text="Email address or login username") 
    password = serializers.CharField(write_only=True, required=True) 

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        print(f"--- LoginSerializer: Attempting to call authenticate for username: {username} ---")
 
        if username and password:
            # Use Django's authenticate function with your custom User model
            # The EmailBackend will handle both email and login lookups
            user = authenticate(request=self.context.get('request'), username=username, password=password)

            if not user:
                raise serializers.ValidationError('Invalid credentials provided.', code='authorization')
        else:
            raise serializers.ValidationError('Must include "username" and "password".', code='authorization')

        data['user'] = user
        return data

class SignupSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration (signup).
    """
    password = serializers.CharField(write_only=True, required=True) 
    class Meta:
        model = User
        fields = ('login', 'email', 'password', 'name')
        extra_kwargs = {
            'login': {'required': True},
            'email': {'required': True}, 
        }

    def validate(self, data):
        # Check if email or login already exists
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "Email already in use."})
        if User.objects.filter(login=data['login']).exists():
            raise serializers.ValidationError({"login": "Username already in use."})
        return data

    def create(self, validated_data):
        # Create user using your custom user manager's create_user method
        user = User.objects.create_user(
            login=validated_data['login'],
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data.get('name')
        )

        group_name = f"user_{user.login}_personal_group" # Make this robust in production

        # Create the Group
        personal_group = Group.objects.create(name=group_name)

        # Assign this group as the user's personal group
        user.personal_group = personal_group
        user.save() # Save the user to update the personal_group field

        # Add the user to their new personal group
        user.groups.add(personal_group)
        return user

class CurrentUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the currently authenticated user's details.
    """
    user_id = serializers.CharField(source='id')  # Map id to user_id

    class Meta:
        model = User
        fields = ('user_id', 'login', 'email', 'name') 
