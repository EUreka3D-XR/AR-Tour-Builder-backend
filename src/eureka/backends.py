# src/eureka/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.conf import settings
import jwt
from jwt import PyJWKClient
from typing import Optional

class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in using their email address.
    Falls back to login field if no user is found with the provided email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        print(f"--- EmailBackend: Attempting authentication for username: {username} ---")
        UserModel = get_user_model()
        
        # First, try to find user by email
        try:
            user = UserModel.objects.get(email=username)
            print("--- EmailBackend: User found by email. ---")
        except UserModel.DoesNotExist:
            print("--- EmailBackend: No user found with that email, trying login field. ---")
            # Fallback: try to find user by login field
            try:
                user = UserModel.objects.get(login=username)
                print("--- EmailBackend: User found by login. ---")
            except UserModel.DoesNotExist:
                print("--- EmailBackend: No user found with that email or login. ---")
                return None

        # If a user is found, check their password and ensure they are active
        if user.check_password(password) and self.user_can_authenticate(user):
            print("--- EmailBackend: Authentication SUCCESS. ---")
            return user
        print("--- EmailBackend: Password mismatch or user not allowed to authenticate. ---")
        return None # Password mismatch or user cannot authenticate

    def get_user(self, user_id):
        """
        Required by Django's authentication system to retrieve a user by their ID.
        """
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None


class OIDCAuthenticationBackend(ModelBackend):
    """
    OpenID Connect authentication backend for EGI Check-In.
    Validates ID tokens and creates/retrieves users based on email.
    """

    def __init__(self):
        super().__init__()
        self.jwks_client = None
        self._init_jwks_client()

    def _init_jwks_client(self):
        """Initialize JWKS client for token verification."""
        if not hasattr(settings, 'OIDC_JWKS_URI'):
            return

        try:
            self.jwks_client = PyJWKClient(settings.OIDC_JWKS_URI)
        except Exception as e:
            print(f"Warning: Could not initialize JWKS client: {e}")

    def authenticate(self, request, id_token=None, **kwargs):
        """
        Authenticate a user using an OpenID Connect ID token.

        Args:
            request: The HTTP request
            id_token: The ID token from the OIDC provider

        Returns:
            User instance if authentication succeeds, None otherwise
        """
        if not id_token:
            return None

        print(f"--- OIDCAuthenticationBackend: Attempting OIDC authentication ---")

        # Verify and decode the token
        decoded_token = self._verify_token(id_token)
        if not decoded_token:
            print("--- OIDCAuthenticationBackend: Token verification failed ---")
            return None

        # Extract user information from token
        email = decoded_token.get('email')
        if not email:
            print("--- OIDCAuthenticationBackend: No email in token ---")
            return None

        # Get or create user based on email
        user = self._get_or_create_user(decoded_token)

        if user and self.user_can_authenticate(user):
            print(f"--- OIDCAuthenticationBackend: Authentication SUCCESS for {email} ---")
            return user

        print("--- OIDCAuthenticationBackend: User cannot authenticate ---")
        return None

    def _verify_token(self, id_token: str) -> Optional[dict]:
        """
        Verify the ID token signature and claims.

        Args:
            id_token: The ID token to verify

        Returns:
            Decoded token claims if valid, None otherwise
        """
        if not self.jwks_client:
            self._init_jwks_client()
            if not self.jwks_client:
                print("--- OIDCAuthenticationBackend: JWKS client not initialized ---")
                return None

        try:
            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(id_token)

            # Decode and verify token
            decoded = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=['RS256'],
                issuer=settings.OIDC_ISSUER,
                audience=getattr(settings, 'OIDC_CLIENT_ID', None),
                options={
                    'verify_exp': True,
                    'verify_iss': True,
                    'verify_aud': bool(getattr(settings, 'OIDC_CLIENT_ID', None))
                }
            )

            print(f"--- OIDCAuthenticationBackend: Token verified for {decoded.get('email')} ---")
            return decoded

        except jwt.ExpiredSignatureError:
            print("--- OIDCAuthenticationBackend: Token has expired ---")
            return None
        except jwt.InvalidTokenError as e:
            print(f"--- OIDCAuthenticationBackend: Invalid token: {e} ---")
            return None
        except Exception as e:
            print(f"--- OIDCAuthenticationBackend: Token verification error: {e} ---")
            return None

    def _get_or_create_user(self, decoded_token: dict):
        """
        Get or create a user based on the decoded token claims.
        Uses email as the unique identifier.

        Args:
            decoded_token: The decoded ID token claims

        Returns:
            User instance or None
        """
        UserModel = get_user_model()
        email = decoded_token.get('email')

        if not email:
            return None

        try:
            # Try to find existing user by email
            user = UserModel.objects.get(email=email)
            print(f"--- OIDCAuthenticationBackend: Found existing user for {email} ---")

            # Update user information from token if needed
            self._update_user_from_token(user, decoded_token)

            return user

        except UserModel.DoesNotExist:
            # Create new user
            print(f"--- OIDCAuthenticationBackend: Creating new user for {email} ---")

            # Extract user information from token
            name = decoded_token.get('name', '')
            given_name = decoded_token.get('given_name', '')
            family_name = decoded_token.get('family_name', '')

            # Use name from token, or construct from given/family name
            full_name = name or f"{given_name} {family_name}".strip()

            # Generate login from email (part before @)
            login = email.split('@')[0]

            # Ensure login is unique
            original_login = login
            counter = 1
            while UserModel.objects.filter(login=login).exists():
                login = f"{original_login}{counter}"
                counter += 1

            # Create user without password (OIDC users don't need one)
            user = UserModel.objects.create_user(
                login=login,
                email=email,
                name=full_name or login,
                password=None  # No password for OIDC users
            )

            # Set unusable password to prevent password-based login
            user.set_unusable_password()
            user.save()

            print(f"--- OIDCAuthenticationBackend: Created user {login} ({email}) ---")
            return user

    def _update_user_from_token(self, user, decoded_token: dict):
        """
        Update user information from the token if it has changed.

        Args:
            user: The user instance
            decoded_token: The decoded ID token claims
        """
        updated = False

        # Update name if provided in token and different
        name = decoded_token.get('name', '')
        if name and user.name != name:
            user.name = name
            updated = True

        if updated:
            user.save()
            print(f"--- OIDCAuthenticationBackend: Updated user info for {user.email} ---")
