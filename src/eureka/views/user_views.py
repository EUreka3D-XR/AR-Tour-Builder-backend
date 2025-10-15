from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from django.contrib.auth import authenticate, login
from ..models.user import User
from ..serializers import UserSerializer, LoginSerializer, SignupSerializer, CurrentUserSerializer

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

@extend_schema(
    description="Retrieve a list of all active and inactive users in the system.",
    summary="List all Users",
    tags=['User'] 
)
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated] # Ensures only logged-in users can list


# --- New API Views for Authentication ---

@extend_schema(
    request=LoginSerializer,
    responses={
        200: OpenApiResponse(
            description="Login successful",
            response={
                'type': 'object',
                'properties': {
                    'token': {'type': 'string', 'description': 'Authentication token'},
                    'userId': {'type': 'string', 'description': 'User ID'}
                },
                'required': ['token', 'userId']
            },
            examples=[
                OpenApiExample(
                    'Login Success',
                    value={'token': 'abc.def.ghi', 'userId': '12345'},
                    response_only=True,
                    media_type='application/json'
                )
            ]
        ),
        401: OpenApiResponse(
            description="Invalid credentials",
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['error']
            },
            examples=[
                OpenApiExample(
                    'Invalid Credentials',
                    value={'error': 'Invalid credentials'},
                    response_only=True,
                    media_type='application/json'
                )
            ]
        )
    },
    description="Login with email and password to obtain an authentication token and user ID.",
    summary="User Login",
    tags=['User']
)
class LoginView(APIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        if not user.is_active:
            return Response({'error': 'User account is disabled.'}, status=status.HTTP_403_FORBIDDEN)

        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user_id': str(user.id)
        }, status=status.HTTP_200_OK)


@extend_schema(
    request=SignupSerializer,
    responses={
        201: OpenApiResponse(
            description="Signup successful",
            response={
                'type': 'object',
                'properties': {
                    'message': {'type': 'string', 'description': 'Success message'},
                    'userId': {'type': 'string', 'description': 'User ID'},
                    'token': {'type': 'string', 'description': 'Authentication token'}
                },
                'required': ['message', 'userId', 'token']
            },
            examples=[
                OpenApiExample(
                    'Signup Success',
                    value={'message': 'Signup successful', 'userId': '12345', 'token': 'abc.def.ghi'},
                    response_only=True,
                    media_type='application/json'
                )
            ]
        ),
        400: OpenApiResponse(
            description="Invalid request data",
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['error']
            },
            examples=[
                OpenApiExample(
                    'Invalid Request (Passwords)',
                    value={'error': 'Passwords do not match'},
                    response_only=True,
                    media_type='application/json'
                )
            ]
        ),
        409: OpenApiResponse(
            description="Email already in use",
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['error']
            },
            examples=[
                OpenApiExample(
                    'Email Already In Use',
                    value={'error': 'Email already in use'},
                    response_only=True,
                    media_type='application/json'
                )
            ]
        )
    },
    description="Register a new user with username, email, and password.",
    summary="User Signup",
    tags=['User']
)
class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer
    permission_classes = []

    def perform_create(self, serializer):
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        self.headers = self.get_success_headers(serializer.data)
        self.response_data = {
            'message': 'Signup successful',
            'user_id': str(user.id),
            'token': token.key
        }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(self.response_data, status=status.HTTP_201_CREATED, headers=self.headers)


@extend_schema(
    responses={
        200: CurrentUserSerializer,
        401: OpenApiResponse(
            description="Unauthorized access",
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['error']
            },
            examples=[
                OpenApiExample(
                    'Unauthorized Access',
                    value={'error': 'Unauthorized access'},
                    response_only=True,
                    media_type='application/json'
                )
            ]
        )
    },
    description="Retrieve details about the currently authenticated user.",
    summary="Get Current User",
    tags=['User']
)
class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = CurrentUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"error": "Unauthorized access."}, status=status.HTTP_401_UNAUTHORIZED)
        return super().retrieve(request, *args, **kwargs)


@extend_schema(
    request={
        'type': 'object',
        'properties': {
            'id_token': {'type': 'string', 'description': 'OpenID Connect ID token from EGI Check-In'}
        },
        'required': ['id_token']
    },
    responses={
        200: OpenApiResponse(
            description="OIDC authentication successful",
            response={
                'type': 'object',
                'properties': {
                    'token': {'type': 'string', 'description': 'Authentication token'},
                    'user_id': {'type': 'string', 'description': 'User ID'},
                    'user': CurrentUserSerializer
                },
                'required': ['token', 'user_id', 'user']
            },
            examples=[
                OpenApiExample(
                    'OIDC Login Success',
                    value={
                        'token': 'abc123def456',
                        'user_id': '42',
                        'user': {
                            'id': 42,
                            'email': 'user@example.com',
                            'login': 'user',
                            'name': 'John Doe'
                        }
                    },
                    response_only=True,
                    media_type='application/json'
                )
            ]
        ),
        400: OpenApiResponse(
            description="Invalid request or token",
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['error']
            },
            examples=[
                OpenApiExample(
                    'Missing Token',
                    value={'error': 'id_token is required'},
                    response_only=True,
                    media_type='application/json'
                )
            ]
        ),
        401: OpenApiResponse(
            description="Authentication failed",
            response={
                'type': 'object',
                'properties': {
                    'error': {'type': 'string', 'description': 'Error message'}
                },
                'required': ['error']
            },
            examples=[
                OpenApiExample(
                    'Invalid Token',
                    value={'error': 'Invalid or expired token'},
                    response_only=True,
                    media_type='application/json'
                )
            ]
        )
    },
    description="Authenticate using an OpenID Connect ID token from EGI Check-In. "
                "The backend will verify the token, and create or retrieve the user based on their email address. "
                "Returns an authentication token for subsequent API requests.",
    summary="OIDC Login",
    tags=['User']
)
class OIDCLoginView(APIView):
    """
    Authenticate users via OpenID Connect (EGI Check-In).
    Accepts an ID token, verifies it, and returns a Django token for API access.
    """
    permission_classes = []

    def post(self, request, *args, **kwargs):
        id_token = request.data.get('id_token')

        if not id_token:
            return Response(
                {'error': 'id_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate using OIDC backend
        user = authenticate(request=request, id_token=id_token)

        if user is None:
            return Response(
                {'error': 'Invalid or expired token'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'error': 'User account is disabled'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create or get token for the user
        token, created = Token.objects.get_or_create(user=user)

        # Serialize user data
        user_serializer = CurrentUserSerializer(user)

        return Response({
            'token': token.key,
            'user_id': str(user.id),
            'user': user_serializer.data
        }, status=status.HTTP_200_OK)
