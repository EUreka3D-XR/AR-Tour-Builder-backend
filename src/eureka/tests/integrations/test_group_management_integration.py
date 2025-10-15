from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class TestGroupManagementIntegration(TestCase):
    """
    Integration tests for group management workflow.
    Tests user signup, group creation, user listing, and group member management.
    """
    
    def setUp(self):
        self.client = APIClient()
    
    def test_complete_group_management_workflow(self):
        """
        Test complete workflow: signup 5 users, login as one, create group, 
        list users, add 2 users to the group.
        """
        # Step 1: Sign up 5 generic users
        users_data = [
            {
                'login': 'user1',
                'email': 'user1@example.com',
                'password': 'password123',
                'name': 'User One'
            },
            {
                'login': 'user2',
                'email': 'user2@example.com',
                'password': 'password123',
                'name': 'User Two'
            },
            {
                'login': 'user3',
                'email': 'user3@example.com',
                'password': 'password123',
                'name': 'User Three'
            },
            {
                'login': 'user4',
                'email': 'user4@example.com',
                'password': 'password123',
                'name': 'User Four'
            },
            {
                'login': 'user5',
                'email': 'user5@example.com',
                'password': 'password123',
                'name': 'User Five'
            }
        ]
        
        created_users = []
        for user_data in users_data:
            response = self.client.post('/api/auth/signup/', user_data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn('token', response.data)
            self.assertIn('user_id', response.data)
            created_users.append({
                'data': user_data,
                'user_id': response.data['user_id'],
                'token': response.data['token']
            })
        
        # Step 2: Login as user1 (the group creator)
        login_data = {
            'username': 'user1@example.com',  # Using email
            'password': 'password123'
        }
        
        response = self.client.post('/api/auth/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user_id', response.data)
        
        # Set authentication for user1
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        
        # Step 3: Create a group "Open Air Museum, Paris"
        group_data = {
            'name': 'Open Air Museum, Paris'
        }
        
        response = self.client.post('/api/groups/', group_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['name'], 'Open Air Museum, Paris')
        group_id = response.data['id']
        
        # Step 4: List all users (should be accessible to authenticated users)
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        
        # Verify all 5 users are in the list
        self.assertEqual(len(response.data), 5)
        
        # Check that all our users are present
        user_logins = [user['login'] for user in response.data]
        expected_logins = ['user1', 'user2', 'user3', 'user4', 'user5']
        for login in expected_logins:
            self.assertIn(login, user_logins)
        
        # Step 5: Add user2 and user3 to the group
        # First, get user2's login from the users list
        user2_data = next(user for user in response.data if user['login'] == 'user2')
        user3_data = next(user for user in response.data if user['login'] == 'user3')
        
        # Add user2 to the group
        add_member_data = {
            'user_identifier': 'user2'  # Using login
        }
        
        response = self.client.post(f'/api/groups/{group_id}/members/add/', add_member_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('User user2 added to group Open Air Museum, Paris', response.data['detail'])
        
        # Add user3 to the group
        add_member_data = {
            'user_identifier': 'user3@example.com'  # Using email
        }
        
        response = self.client.post(f'/api/groups/{group_id}/members/add/', add_member_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('User user3 added to group Open Air Museum, Paris', response.data['detail'])
        
        # Step 6: Verify the group members by trying to add them again (should fail)
        add_member_data = {
            'user_identifier': 'user2'
        }
        
        response = self.client.post(f'/api/groups/{group_id}/members/add/', add_member_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('User is already a member of this group', response.data['detail'])
        
        # Step 7: Test that user4 (not in group) cannot add members
        # Login as user4
        login_data = {
            'username': 'user4',
            'password': 'password123'
        }
        
        response = self.client.post('/api/auth/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        
        # Try to add user5 to the group (should fail - user4 is not a member)
        add_member_data = {
            'user_identifier': 'user5'
        }
        
        response = self.client.post(f'/api/groups/{group_id}/members/add/', add_member_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('You do not have permission to perform this action', str(response.data))
    
    def test_group_creation_and_member_management(self):
        """
        Test group creation and member management with edge cases.
        """
        # Step 1: Create a user
        signup_data = {
            'login': 'groupadmin',
            'email': 'groupadmin@example.com',
            'password': 'password123',
            'name': 'Group Admin'
        }
        
        response = self.client.post('/api/auth/signup/', signup_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 2: Login as the user
        login_data = {
            'username': 'groupadmin@example.com',
            'password': 'password123'
        }
        
        response = self.client.post('/api/auth/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        
        # Step 3: Create a group
        group_data = {
            'name': 'Test Group'
        }
        
        response = self.client.post('/api/groups/', group_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        group_id = response.data['id']
        
        # Step 4: Try to add a non-existent user (should fail)
        add_member_data = {
            'user_identifier': 'nonexistentuser'
        }
        
        response = self.client.post(f'/api/groups/{group_id}/members/add/', add_member_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('User with this identifier does not exist', str(response.data))
        
        # Step 5: Try to remove a user that's not in the group (should fail)
        # First create another user
        signup_data = {
            'login': 'outsider',
            'email': 'outsider@example.com',
            'password': 'password123',
            'name': 'Outsider User'
        }
        
        response = self.client.post('/api/auth/signup/', signup_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Try to remove the outsider (should fail)
        remove_member_data = {
            'user_identifier': 'outsider'
        }
        
        response = self.client.post(f'/api/groups/{group_id}/members/remove/', remove_member_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('User is not a member of this group', str(response.data)) 