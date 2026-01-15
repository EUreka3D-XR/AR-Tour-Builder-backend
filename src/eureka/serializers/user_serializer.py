from rest_framework import serializers
from rest_framework.authtoken.models import Token # For login response
from django.contrib.auth import authenticate # For authenticating users
from ..models.user import User # Your custom User model

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'name', 'is_active', 'is_staff')

class UserLiteSerializer(serializers.ModelSerializer):
    """Lightweight user serializer for nested member lists"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'name')


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    Accepts either email or username for authentication.
    """
    login = serializers.CharField(required=True, help_text="Email address or username")
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        login = data.get('login')
        password = data.get('password')
        print(f"--- LoginSerializer: Attempting to call authenticate for login: {login} ---")

        if login and password:
            # Use Django's authenticate function with your custom User model
            # The EmailBackend will handle both email and username lookups
            user = authenticate(request=self.context.get('request'), username=login, password=password)

            if not user:
                raise serializers.ValidationError('Invalid credentials provided.', code='authorization')
        else:
            raise serializers.ValidationError('Must include "login" and "password".', code='authorization')

        data['user'] = user
        return data

class SignupSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration (signup).
    """
    password = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'name')
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
        }

    def validate(self, data):
        # Check if email or username already exists
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "Email already in use."})
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({"username": "Username already in use."})
        return data

    def create(self, validated_data):
        # Create user using your custom user manager's create_user method
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data.get('name')
        )

        # Note: personal_group is now created in the User model's save method
        # So we don't need to create it here anymore
        return user

class CurrentUserSerializer(serializers.ModelSerializer):
    """
    Serializer for the currently authenticated user's details.
    """
    user_id = serializers.CharField(source='id')  # Map id to user_id

    class Meta:
        model = User
        fields = ('user_id', 'username', 'email', 'name') 
