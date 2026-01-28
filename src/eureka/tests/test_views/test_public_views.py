from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from eureka.models import Project, Tour, POI
from eureka.models.poi_asset import POIAsset


User = get_user_model()


class TestPublicProjectListView(TestCase):
    """Test public project list endpoint filtering"""

    def setUp(self):
        """Set up test data"""
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            name='User One'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123',
            name='User Two'
        )

        # Create projects
        self.project_with_public_tour = Project.objects.create(
            title={'locales': {'en': 'Project With Public Tour'}},
            description={'locales': {'en': 'Has public tours'}},
            group=self.user1.personal_group,
            locales=['en']
        )

        self.project_with_only_private_tours = Project.objects.create(
            title={'locales': {'en': 'Project With Only Private Tours'}},
            description={'locales': {'en': 'Has only private tours'}},
            group=self.user1.personal_group,
            locales=['en']
        )

        self.project_with_no_tours = Project.objects.create(
            title={'locales': {'en': 'Project With No Tours'}},
            description={'locales': {'en': 'Has no tours'}},
            group=self.user2.personal_group,
            locales=['en']
        )

        self.project_with_mixed_tours = Project.objects.create(
            title={'locales': {'en': 'Project With Mixed Tours'}},
            description={'locales': {'en': 'Has both public and private tours'}},
            group=self.user2.personal_group,
            locales=['en']
        )

        # Create tours
        self.public_tour_1 = Tour.objects.create(
            project=self.project_with_public_tour,
            title={'locales': {'en': 'Public Tour 1'}},
            description={'locales': {'en': 'A public tour'}},
            locales=['en'],
            is_public=True,
            center={'lat': 40.7128, 'long': -74.0060}
        )

        self.private_tour_1 = Tour.objects.create(
            project=self.project_with_only_private_tours,
            title={'locales': {'en': 'Private Tour 1'}},
            description={'locales': {'en': 'A private tour'}},
            locales=['en'],
            is_public=False
        )

        self.private_tour_2 = Tour.objects.create(
            project=self.project_with_only_private_tours,
            title={'locales': {'en': 'Private Tour 2'}},
            description={'locales': {'en': 'Another private tour'}},
            locales=['en'],
            is_public=False
        )

        self.public_tour_2 = Tour.objects.create(
            project=self.project_with_mixed_tours,
            title={'locales': {'en': 'Public Tour 2'}},
            description={'locales': {'en': 'A public tour in mixed project'}},
            locales=['en'],
            is_public=True,
            center={'lat': 51.5074, 'long': -0.1278}
        )

        self.private_tour_3 = Tour.objects.create(
            project=self.project_with_mixed_tours,
            title={'locales': {'en': 'Private Tour 3'}},
            description={'locales': {'en': 'A private tour in mixed project'}},
            locales=['en'],
            is_public=False
        )

        self.client = APIClient()

    def test_public_project_list_only_returns_projects_with_public_tours(self):
        """
        Test that the public project list endpoint only returns projects
        that have at least one public tour.
        """
        response = self.client.get('/api/public/projects')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should only return 2 projects (those with public tours)
        self.assertEqual(len(response.data), 2)

        # Extract project IDs from response
        returned_project_ids = [project['id'] for project in response.data]

        # Should include projects with public tours
        self.assertIn(self.project_with_public_tour.id, returned_project_ids)
        self.assertIn(self.project_with_mixed_tours.id, returned_project_ids)

        # Should NOT include projects without public tours
        self.assertNotIn(self.project_with_only_private_tours.id, returned_project_ids)
        self.assertNotIn(self.project_with_no_tours.id, returned_project_ids)

    def test_public_project_list_total_tours_count_only_public(self):
        """
        Test that total_tours count only includes public tours.
        """
        response = self.client.get('/api/public/projects')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Find the mixed project in response
        mixed_project_data = None
        for project in response.data:
            if project['id'] == self.project_with_mixed_tours.id:
                mixed_project_data = project
                break

        self.assertIsNotNone(mixed_project_data)
        # Should only count public tour, not the private one
        self.assertEqual(mixed_project_data['total_tours'], 1)

    def test_public_project_list_unauthenticated_access(self):
        """
        Test that unauthenticated users can access the public project list.
        """
        # Don't authenticate
        response = self.client.get('/api/public/projects')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_public_project_list_proximity_ordering_uses_public_tours_only(self):
        """
        Test that proximity ordering is based on public tour centers only.
        """
        # Query from a location closer to project_with_mixed_tours (London)
        # New York: 40.7128, -74.0060
        # London: 51.5074, -0.1278
        # Query point closer to London
        response = self.client.get(
            '/api/public/projects',
            {'order_by': 'proximity', 'lat': 51.0, 'long': 0.0}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        # The project with mixed tours (London location) should come first
        self.assertEqual(response.data[0]['id'], self.project_with_mixed_tours.id)


class TestPublicProjectPopulatedView(TestCase):
    """Test public project populated endpoint filtering"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )

        self.project = Project.objects.create(
            title={'locales': {'en': 'Test Project'}},
            description={'locales': {'en': 'A test project'}},
            group=self.user.personal_group,
            locales=['en']
        )

        # Create public and private tours
        self.public_tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Public Tour'}},
            description={'locales': {'en': 'A public tour'}},
            locales=['en'],
            is_public=True
        )

        self.private_tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Private Tour'}},
            description={'locales': {'en': 'A private tour'}},
            locales=['en'],
            is_public=False
        )

        self.client = APIClient()

    def test_public_project_populated_only_returns_public_tours(self):
        """
        Test that the public project populated endpoint only returns public tours.
        """
        response = self.client.get(f'/api/public/projects/{self.project.id}/populated')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should only return 1 tour (the public one)
        self.assertEqual(len(response.data['tours']), 1)
        self.assertEqual(response.data['tours'][0]['id'], self.public_tour.id)
        self.assertTrue(response.data['tours'][0]['is_public'])

        # total_tours should only count public tours
        self.assertEqual(response.data['total_tours'], 1)

    def test_public_project_populated_includes_new_fields(self):
        """
        Test that the public project populated endpoint includes ar_placement,
        is_georeferenced for POI assets, and guided for tours.
        """
        # Create a POI with an asset
        poi = POI.objects.create(
            tour=self.public_tour,
            title={'locales': {'en': 'Test POI'}},
            description={'locales': {'en': 'A test POI'}},
            coordinates={'lat': 40.7128, 'long': -74.0060},
            radius=100,
            order=0
        )

        # Create a POI asset with ar_placement and coordinates (is_georeferenced)
        poi_asset = POIAsset.objects.create(
            poi=poi,
            title={'locales': {'en': 'Test Asset'}},
            description={'locales': {'en': 'A test asset'}},
            type='image',
            url={'locales': {'en': 'https://example.com/image.jpg'}},
            priority='high',
            view_in_ar=True,
            ar_placement='ground',
            georeference = {'coordinates': {'lat': 40.7128, 'long': -74.0060}}
        )

        # Update tour to have guided=True
        self.public_tour.guided = True
        self.public_tour.save()

        response = self.client.get(f'/api/public/projects/{self.project.id}/populated')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that tours include 'guided' field
        tour_data = response.data['tours'][0]
        self.assertIn('guided', tour_data)
        self.assertTrue(tour_data['guided'])

        # Check that POI assets include 'ar_placement' and 'is_georeferenced'
        poi_data = tour_data['pois'][0]
        asset_data = poi_data['assets'][0]

        self.assertIn('ar_placement', asset_data)
        self.assertEqual(asset_data['ar_placement'], 'ground')

        self.assertIn('is_georeferenced', asset_data)
        self.assertTrue(asset_data['is_georeferenced'])

    def test_public_project_populated_is_georeferenced_false_when_no_coordinates(self):
        """
        Test that is_georeferenced is False when POI asset has no coordinates.
        """
        # Create a POI
        poi = POI.objects.create(
            tour=self.public_tour,
            title={'locales': {'en': 'Test POI'}},
            description={'locales': {'en': 'A test POI'}},
            coordinates={'lat': 40.7128, 'long': -74.0060},
            radius=100,
            order=0
        )

        # Create a POI asset without georeference
        poi_asset = POIAsset.objects.create(
            poi=poi,
            title={'locales': {'en': 'Test Asset'}},
            description={'locales': {'en': 'A test asset'}},
            type='text',
            url={'locales': {'en': 'https://example.com/text.txt'}},
            priority='normal',
            view_in_ar=False,
            ar_placement='free'
            # No georeference provided
        )

        response = self.client.get(f'/api/public/projects/{self.project.id}/populated')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that is_georeferenced is False
        poi_data = response.data['tours'][0]['pois'][0]
        asset_data = poi_data['assets'][0]

        self.assertIn('is_georeferenced', asset_data)
        self.assertFalse(asset_data['is_georeferenced'])
