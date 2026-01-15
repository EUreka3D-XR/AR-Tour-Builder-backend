from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class TestAuthIntegration(TestCase):
    """
    Integration tests for authentication flow including signup and login.
    Tests both email and login-based authentication.
    """
    
    def setUp(self):
        self.client = APIClient()
    
    def test_signup_and_login_with_email(self):
        """
        Test complete flow: signup with login/email/name, then login with email.
        """
        # Step 1: User signup
        signup_data = {
            'username': 'testuser123',
            'email': 'testuser123@example.com',
            'password': 'securepassword123',
            'name': 'Test User'
        }
        
        response = self.client.post('/api/auth/signup', signup_data)
        print(f"Signup response status: {response.status_code}")
        print(f"Signup response data: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user_id', response.data)
        self.assertEqual(response.data['message'], 'Signup successful')
        
        # Step 2: Login with email
        login_data = {
            'login': 'testuser123@example.com',  # Using email
            'password': 'securepassword123'
        }
        
        response = self.client.post('/api/auth/login', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user_id', response.data)
        
        # Step 3: Verify we can access protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        response = self.client.get('/api/auth/me')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'testuser123@example.com')
        self.assertEqual(response.data['username'], 'testuser123')
        self.assertEqual(response.data['name'], 'Test User')
    
    def test_signup_and_login_with_login(self):
        """
        Test complete flow: signup with login/email/name, then login with login username.
        """
        # Step 1: User signup
        signup_data = {
            'username': 'anotheruser456',
            'email': 'anotheruser456@example.com',
            'password': 'securepassword456',
            'name': 'Another User'
        }
        
        response = self.client.post('/api/auth/signup', signup_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user_id', response.data)
        
        # Step 2: Login with login username
        login_data = {
            'login': 'anotheruser456',  # Using username
            'password': 'securepassword456'
        }
        
        response = self.client.post('/api/auth/login', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user_id', response.data)
        
        # Step 3: Verify we can access protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        response = self.client.get('/api/auth/me')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'anotheruser456@example.com')
        self.assertEqual(response.data['username'], 'anotheruser456')
        self.assertEqual(response.data['name'], 'Another User')
    
    def test_login_fails_with_wrong_credentials(self):
        """
        Test that login fails with incorrect credentials.
        """
        # Step 1: Create a user
        signup_data = {
            'username': 'testuser789',
            'email': 'testuser789@example.com',
            'password': 'correctpassword',
            'name': 'Test User 789'
        }
        
        response = self.client.post('/api/auth/signup', signup_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 2: Try to login with wrong password
        login_data = {
            'login': 'testuser789@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post('/api/auth/login', login_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid credentials provided', str(response.data))
        
        # Step 3: Try to login with non-existent email
        login_data = {
            'login': 'nonexistent@example.com',
            'password': 'anypassword'
        }
        
        response = self.client.post('/api/auth/login', login_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid credentials provided', str(response.data))
        
        # Step 4: Try to login with non-existent login
        login_data = {
            'login': 'nonexistentuser',
            'password': 'anypassword'
        }
        
        response = self.client.post('/api/auth/login', login_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid credentials provided', str(response.data))
    
    def test_signup_validation_errors(self):
        """
        Test signup validation errors for duplicate email/login.
        """
        # Step 1: Create first user
        signup_data = {
            'username': 'duplicateuser',
            'email': 'duplicate@example.com',
            'password': 'password123',
            'name': 'Duplicate User'
        }
        
        response = self.client.post('/api/auth/signup', signup_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 2: Try to create user with same email
        signup_data = {
            'username': 'differentuser',
            'email': 'duplicate@example.com',  # Same email
            'password': 'password123',
            'name': 'Different User'
        }
        
        response = self.client.post('/api/auth/signup', signup_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user with this email address already exists.', str(response.data))
        
        # Step 3: Try to create user with same login
        signup_data = {
            'username': 'duplicateuser',  # Same login
            'email': 'different@example.com',
            'password': 'password123',
            'name': 'Different User'
        }
        
        response = self.client.post('/api/auth/signup', signup_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user with this username already exists.', str(response.data))

    def test_logout_deletes_token(self):
        """
        Test that logout deletes the user's token from the database.
        """
        # Step 1: User signup
        signup_data = {
            'username': 'logoutuser',
            'email': 'logoutuser@example.com',
            'password': 'password123',
            'name': 'Logout User'
        }

        response = self.client.post('/api/auth/signup', signup_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        token = response.data['token']

        # Step 2: Verify token works
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        response = self.client.get('/api/auth/me')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Step 3: Logout
        response = self.client.post('/api/auth/logout')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Logout successful')

        # Step 4: Verify token no longer works
        response = self.client.get('/api/auth/me')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Step 5: Verify logout endpoint also returns 401 with invalid token
        response = self.client.post('/api/auth/logout')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_authentication(self):
        """
        Test that logout fails when not authenticated.
        """
        self.client.credentials()  # Clear any credentials
        response = self.client.post('/api/auth/logout')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) 