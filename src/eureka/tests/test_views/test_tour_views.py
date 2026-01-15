from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from eureka.models import Project, Tour

User = get_user_model()


class TestTourViews(TestCase):
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.client.force_authenticate(user=self.user)

        self.project = Project.objects.create(
            title={'locales': {'en': 'Test Project'}},
            group=self.user.personal_group,
            locales=['en', 'fr', 'el']
        )

    def test_create_tour_with_empty_locales_via_api(self):
        """Test that creating a tour via API with empty locales populates it with project's locales."""
        data = {
            'title': {'locales': {'en': 'API Test Tour'}},
            'description': {'locales': {'en': 'A test tour via API'}},
            'project_id': self.project.id,
            'locales': []
        }

        response = self.client.post(reverse('tour-list-create'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['locales'], ['en', 'fr', 'el'])

        # Verify it was saved to the database correctly
        tour = Tour.objects.get(id=response.data['id'])
        self.assertEqual(tour.locales, ['en', 'fr', 'el'])

    def test_create_tour_with_specific_locales_via_api(self):
        """Test that creating a tour via API with specific locales keeps those locales."""
        data = {
            'title': {'locales': {'en': 'API Test Tour'}},
            'description': {'locales': {'en': 'A test tour via API'}},
            'project_id': self.project.id,
            'locales': ['en', 'de']
        }

        response = self.client.post(reverse('tour-list-create'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['locales'], ['en', 'de'])

        # Verify it was saved to the database correctly
        tour = Tour.objects.get(id=response.data['id'])
        self.assertEqual(tour.locales, ['en', 'de'])

    def test_create_tour_without_locales_field_via_api(self):
        """Test that creating a tour via API without locales field uses default (empty list)."""
        data = {
            'title': {'locales': {'en': 'API Test Tour'}},
            'description': {'locales': {'en': 'A test tour via API'}},
            'project_id': self.project.id
        }

        response = self.client.post(reverse('tour-list-create'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['locales'], [])

        # Verify it was saved to the database correctly
        tour = Tour.objects.get(id=response.data['id'])
        self.assertEqual(tour.locales, [])

    def test_create_tour_with_empty_locales_project_has_empty_locales(self):
        """Test that empty locales stay empty if project has no locales."""
        project_no_locales = Project.objects.create(
            title={'locales': {'en': 'Project No Locales'}},
            group=self.user.personal_group,
            locales=[]
        )

        data = {
            'title': {'locales': {'en': 'API Test Tour'}},
            'project_id': project_no_locales.id,
            'locales': []
        }

        response = self.client.post(reverse('tour-list-create'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['locales'], [])

        # Verify it was saved to the database correctly
        tour = Tour.objects.get(id=response.data['id'])
        self.assertEqual(tour.locales, [])

    def test_update_tour_with_empty_locales_via_api(self):
        """Test that updating a tour via API with empty locales populates it with project's locales."""
        # Create a tour with specific locales
        tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Original Tour'}},
            locales=['en', 'it']
        )

        data = {
            'title': {'locales': {'en': 'Updated Tour'}},
            'locales': []
        }

        response = self.client.patch(
            reverse('tour-detail', kwargs={'pk': tour.id}),
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['locales'], ['en', 'fr', 'el'])

        # Verify it was saved to the database correctly
        tour.refresh_from_db()
        self.assertEqual(tour.locales, ['en', 'fr', 'el'])

    def test_update_tour_with_specific_locales_via_api(self):
        """Test that updating a tour via API with specific locales keeps those locales."""
        # Create a tour
        tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Original Tour'}},
            locales=['en', 'fr']
        )

        data = {
            'locales': ['en', 'de', 'es']
        }

        response = self.client.patch(
            reverse('tour-detail', kwargs={'pk': tour.id}),
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['locales'], ['en', 'de', 'es'])

        # Verify it was saved to the database correctly
        tour.refresh_from_db()
        self.assertEqual(tour.locales, ['en', 'de', 'es'])

    def test_update_tour_with_empty_locales_project_has_empty_locales_via_api(self):
        """Test that empty locales stay empty on update if project has no locales."""
        project_no_locales = Project.objects.create(
            title={'locales': {'en': 'Project No Locales'}},
            group=self.user.personal_group,
            locales=[]
        )

        tour = Tour.objects.create(
            project=project_no_locales,
            title={'locales': {'en': 'Original Tour'}},
            locales=['en']
        )

        data = {
            'locales': []
        }

        response = self.client.patch(
            reverse('tour-detail', kwargs={'pk': tour.id}),
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['locales'], [])

        # Verify it was saved to the database correctly
        tour.refresh_from_db()
        self.assertEqual(tour.locales, [])
