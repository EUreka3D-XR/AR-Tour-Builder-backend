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
    Falls back to username field if no user is found with the provided email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        print(f"--- EmailBackend: Attempting authentication for username: {username} ---")
        UserModel = get_user_model()

        # First, try to find user by email
        try:
            user = UserModel.objects.get(email=username)
            print("--- EmailBackend: User found by email. ---")
        except UserModel.DoesNotExist:
            print("--- EmailBackend: No user found with that email, trying username field. ---")
            # Fallback: try to find user by username field
            try:
                user = UserModel.objects.get(username=username)
                print("--- EmailBackend: User found by username. ---")
            except UserModel.DoesNotExist:
                print("--- EmailBackend: No user found with that email or username. ---")
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

    def authenticate(self, request, id_token=None, userinfo=None, **kwargs):
        """
        Authenticate a user using an OpenID Connect ID token and UserInfo profile.

        Args:
            request: The HTTP request
            id_token: The ID token from the OIDC provider
            userinfo: The UserInfo profile fetched using the access_token

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

        # Extract user information from token or userinfo
        email = decoded_token.get('email') or (userinfo and userinfo.get('email'))
        if not email:
            print("--- OIDCAuthenticationBackend: No email in token or userinfo. Cannot login. ---")
            return None

        # Entitlement gate: if EGI_ENTITLEMENT is configured, the user must hold it
        required_entitlement = getattr(settings, 'EGI_ENTITLEMENT', '')
        if required_entitlement:
            entitlements = (userinfo or {}).get('eduperson_entitlement', [])
            if isinstance(entitlements, str):
                entitlements = [entitlements]
            if not any(required_entitlement in ent for ent in entitlements):
                print(
                    f"--- OIDCAuthenticationBackend: Access denied for {email}. "
                    f"Required entitlement '{required_entitlement}' not found in {entitlements} ---"
                )
                return None

        # Get or create user based on email and process entitlements
        user = self._get_or_create_user(decoded_token, userinfo)

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

    def _get_or_create_user(self, decoded_token: dict, userinfo: dict = None):
        """
        Get or create a user based on the decoded token claims and UserInfo.
        Uses email as the unique identifier.

        Args:
            decoded_token: The decoded ID token claims
            userinfo: The UserInfo profile containing entitlements

        Returns:
            User instance or None
        """
        UserModel = get_user_model()
        email = decoded_token.get('email') or (userinfo and userinfo.get('email'))

        if not email:
            return None

        try:
            # Try to find existing user by email
            user = UserModel.objects.get(email=email)
            print(f"--- OIDCAuthenticationBackend: Found existing user for {email} ---")

            # Update user information from token if needed
            self._update_user_from_token(user, decoded_token, userinfo)

            return user

        except UserModel.DoesNotExist:
            # Create new user
            print(f"--- OIDCAuthenticationBackend: Creating new user for {email} ---")

            # Extract user information from token or userinfo
            name = decoded_token.get('name') or (userinfo and userinfo.get('name', ''))
            given_name = decoded_token.get('given_name') or (userinfo and userinfo.get('given_name', ''))
            family_name = decoded_token.get('family_name') or (userinfo and userinfo.get('family_name', ''))

            # Use name from token, or construct from given/family name
            full_name = name or f"{given_name} {family_name}".strip()

            # Generate login from email (part before @)
            login = email.split('@')[0]

            # Ensure login is unique
            original_login = login
            counter = 1
            while UserModel.objects.filter(username=login).exists():
                login = f"{original_login}{counter}"
                counter += 1

            # Create user without password (OIDC users don't need one)
            # We map login -> username for the custom user model kwargs
            user = UserModel.objects.create_user(
                username=login,
                email=email,
                name=full_name or login,
                password=None  # No password for OIDC users
            )

            # Set unusable password to prevent password-based login
            user.set_unusable_password()
            user.save()

            print(f"--- OIDCAuthenticationBackend: Created user {login} ({email}) ---")

            # Process entitlements immediately after creation
            self._update_user_from_token(user, decoded_token, userinfo)

            return user

    def _update_user_from_token(self, user, decoded_token: dict, userinfo: dict = None):
        """
        Update user information from the token and apply entitlements from UserInfo.

        Args:
            user: The user instance
            decoded_token: The decoded ID token claims
            userinfo: The UserInfo profile containing entitlements
        """
        updated = False

        # Update name if provided in token/userinfo and different
        name = decoded_token.get('name') or (userinfo and userinfo.get('name', ''))
        if name and user.name != name:
            user.name = name
            updated = True


        # Auto-grant admin rights if the user's email is explicitly listed in settings.ADMIN_EMAILS
        is_hardcoded_admin = user.email in getattr(settings, 'ADMIN_EMAILS', [])

        # Final Privilege Determination
        should_be_admin = is_hardcoded_admin
        should_be_staff = should_be_admin

        if should_be_admin and not user.is_superuser:
            user.is_superuser = True
            user.is_staff = True
            updated = True
        elif should_be_staff and not user.is_staff:
            user.is_staff = True
            updated = True
        
        # Note: If you want to automatically REVOKE admin privileges when an email 
        # is removed from the settings list, you could add:
        # elif not should_be_admin and user.is_superuser: user.is_superuser = False; updated = True...

        if updated:
            user.save()
            print(f"--- OIDCAuthenticationBackend: Updated user info for {user.email} ---")
