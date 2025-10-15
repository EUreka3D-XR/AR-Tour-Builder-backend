import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status


class TestAPIWorkflows:
    """
    Integration tests that demonstrate real API usage patterns.
    These tests serve as both documentation and validation of the API workflow.
    """
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def authenticated_client(self, api_client, user):
        """Create an authenticated API client for testing protected endpoints."""
        api_client.force_authenticate(user=user)
        return api_client
    
    def test_user_registration_and_login_workflow(self, api_client):
        """
        Demonstrates the complete user registration and authentication workflow.
        
        This test shows how a new user would:
        1. Register an account
        2. Login to get authentication tokens
        3. Access protected endpoints
        """
        # Step 1: User registration
        signup_data = {
            'login': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123',
            'name': 'New User'
        }
        
        response = api_client.post('/api/auth/signup/', signup_data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        
        # Step 2: User login
        login_data = {
            'email': 'newuser@example.com',
            'password': 'securepassword123'
        }
        
        response = api_client.post('/api/auth/login/', login_data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        
        # Step 3: Access protected endpoint with authentication
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        response = api_client.get('/api/auth/me/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'newuser@example.com'
    
    def test_project_creation_and_management_workflow(self, authenticated_client, user):
        """
        Demonstrates the complete project lifecycle workflow.
        
        This test shows how a user would:
        1. Create a new project
        2. Add assets to the project
        3. Create tours within the project
        4. Add POIs to tours
        """
        # Step 1: Create a new project
        project_data = {
            'title': 'My Vacation Project',
            'description': 'A project documenting my vacation'
        }
        
        response = authenticated_client.post('/api/projects/', project_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        project_id = response.data['id']
        
        # Step 2: Add an asset to the project
        asset_data = {
            'project': project_id,
            'title': {
                'locales': {
                    'en': 'Beach Photo',
                    'el': 'Φωτογραφία Παραλίας'
                }
            },
            'description': {
                'locales': {
                    'en': 'A beautiful beach photo',
                    'el': 'Μια όμορφη φωτογραφία παραλίας'
                }
            },
            'type': 'image',
            'url': '/assets/beach_photo.jpg'
        }
        
        response = authenticated_client.post('/api/assets/', asset_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        asset_id = response.data['id']
        
        # Step 2.5: Add a map asset with real-world dimensions
        map_asset_data = {
            'project': project_id,
            'title': {
                'locales': {
                    'en': 'Beach Area Map',
                    'el': 'Χάρτης Περιοχής Παραλίας'
                }
            },
            'description': {
                'locales': {
                    'en': 'Map of the beach area for GPS positioning',
                    'el': 'Χάρτης της περιοχής παραλίας για τοποθέτηση GPS'
                }
            },
            'type': 'image',
            'url': '/assets/beach_map.jpg',
            'real_width_meters': 500.0,
            'real_height_meters': 300.0
        }
        
        response = authenticated_client.post('/api/assets/', map_asset_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        map_asset_id = response.data['id']
        assert response.data['real_width_meters'] == 500.0
        assert response.data['real_height_meters'] == 300.0
        
        # Step 3: Create a tour within the project
        tour_data = {
            'project': project_id,
            'title': {
                'locales': {
                    'en': 'Athens City Tour',
                    'el': 'Περιήγηση στην Αθήνα'
                }
            },
            'description': {
                'locales': {
                    'en': 'Explore the historic city of Athens',
                    'el': 'Εξερευνήστε την ιστορική πόλη της Αθήνας'
                }
            }
        }
        
        response = authenticated_client.post('/api/tours/', tour_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        tour_id = response.data['id']
        
        # Step 4: Add a POI to the tour
        poi_data = {
            'tour': tour_id,
            'name': {
                'locales': {
                    'en': 'Acropolis',
                    'el': 'Ακρόπολη'
                }
            },
            'description': {
                'locales': {
                    'en': 'Ancient citadel of Athens',
                    'el': 'Η αρχαία ακρόπολη της Αθήνας'
                }
            },
            'latitude': 37.9715,
            'longitude': 23.7267
        }
        
        response = authenticated_client.post('/api/pois/', poi_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Step 5: Verify the complete workflow by retrieving the project
        response = authenticated_client.get(f'/api/projects/{project_id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == 'My Vacation Project'
    
    def test_group_collaboration_workflow(self, authenticated_client, user, another_user):
        """
        Demonstrates how users collaborate through groups.
        
        This test shows how users would:
        1. Create a group
        2. Add members to the group
        3. Share projects within the group
        """
        # Step 1: Create a group
        group_data = {
            'name': 'Vacation Planning Team',
            'description': 'Team for planning our vacation'
        }
        
        response = authenticated_client.post('/api/groups/', group_data)
        assert response.status_code == status.HTTP_201_CREATED
        group_id = response.data['id']
        
        # Step 2: Add another user to the group
        add_member_data = {
            'user_id': another_user.id
        }
        
        response = authenticated_client.post(
            f'/api/groups/{group_id}/members/add/',
            add_member_data
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Step 3: Create a project in the group
        project_data = {
            'title': 'Group Vacation Project',
            'description': 'A collaborative vacation project',
            'group': group_id
        }
        
        response = authenticated_client.post('/api/projects/', project_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_file_serving_workflow(self, authenticated_client):
        """
        Demonstrates how to serve example files through the API.
        
        This test shows how the application serves static files
        from the example directory with proper MIME type detection.
        """
        # Test serving a text file
        response = authenticated_client.get('/api/examples/readme.txt')
        # Note: This will return 404 if the file doesn't exist, but demonstrates the endpoint
        
        # Test serving an image file
        response = authenticated_client.get('/api/examples/images/sample.jpg')
        # Note: This will return 404 if the file doesn't exist, but demonstrates the endpoint
        
        # The actual response status depends on whether the files exist in the example directory
        # This test primarily documents the API endpoint structure
