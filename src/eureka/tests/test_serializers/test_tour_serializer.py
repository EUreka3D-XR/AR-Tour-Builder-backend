from django.test import TestCase
from django.contrib.auth import get_user_model
from eureka.models import Project, Tour
from eureka.serializers.tour_serializer import TourSerializer

User = get_user_model()
class TestTourSerializer(TestCase):
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.project = Project.objects.create(
            title={'locales': {'en': 'Test Project'}},
            group=self.user.personal_group,
            locales=['en', 'fr', 'el']
        )

    def test_create_tour_with_empty_locales_populates_from_project(self):
        """Test that creating a tour with empty locales list populates it with project's locales."""
        data = {
            'title': {'locales': {'en': 'Test Tour'}},
            'description': {'locales': {'en': 'A test tour'}},
            'locales': []
        }

        serializer = TourSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Save the tour with the project
        tour = serializer.save(project=self.project)

        # Check that locales were populated from the project
        self.assertEqual(tour.locales, ['en', 'fr', 'el'])

    def test_create_tour_with_specific_locales_keeps_them(self):
        """Test that creating a tour with specific locales keeps those locales."""
        data = {
            'title': {'locales': {'en': 'Test Tour'}},
            'description': {'locales': {'en': 'A test tour'}},
            'locales': ['en', 'it']
        }

        serializer = TourSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Save the tour with the project
        tour = serializer.save(project=self.project)

        # Check that locales were NOT overridden
        self.assertEqual(tour.locales, ['en', 'it'])

    def test_create_tour_without_locales_field_uses_default(self):
        """Test that creating a tour without locales field uses model default (empty list)."""
        data = {
            'title': {'locales': {'en': 'Test Tour'}},
            'description': {'locales': {'en': 'A test tour'}}
        }

        serializer = TourSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Save the tour with the project
        tour = serializer.save(project=self.project)

        # Check that locales use the model default (empty list)
        self.assertEqual(tour.locales, [])

    def test_create_tour_with_empty_locales_and_project_without_locales(self):
        """Test that empty locales stay empty if project has no locales."""
        project_no_locales = Project.objects.create(
            title={'locales': {'en': 'Project No Locales'}},
            group=self.user.personal_group,
            locales=[]
        )

        data = {
            'title': {'locales': {'en': 'Test Tour'}},
            'locales': []
        }

        serializer = TourSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Save the tour with the project that has no locales
        tour = serializer.save(project=project_no_locales)

        # Check that locales remain empty
        self.assertEqual(tour.locales, [])

    def test_update_tour_with_empty_locales_populates_from_project(self):
        """Test that updating a tour with empty locales list populates it with project's locales."""
        # Create a tour with specific locales
        tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour'}},
            locales=['en', 'it']
        )

        # Update with empty locales
        data = {
            'title': {'locales': {'en': 'Updated Tour'}},
            'locales': []
        }

        serializer = TourSerializer(tour, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

        # Save the update
        updated_tour = serializer.save()

        # Check that locales were populated from the project
        self.assertEqual(updated_tour.locales, ['en', 'fr', 'el'])

    def test_update_tour_with_specific_locales_keeps_them(self):
        """Test that updating a tour with specific locales keeps those locales."""
        # Create a tour with some locales
        tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour'}},
            locales=['en', 'fr']
        )

        # Update with different specific locales
        data = {
            'locales': ['en', 'de']
        }

        serializer = TourSerializer(tour, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

        # Save the update
        updated_tour = serializer.save()

        # Check that locales were NOT overridden
        self.assertEqual(updated_tour.locales, ['en', 'de'])

    def test_update_tour_with_empty_locales_and_project_without_locales(self):
        """Test that empty locales stay empty on update if project has no locales."""
        project_no_locales = Project.objects.create(
            title={'locales': {'en': 'Project No Locales'}},
            group=self.user.personal_group,
            locales=[]
        )

        tour = Tour.objects.create(
            project=project_no_locales,
            title={'locales': {'en': 'Test Tour'}},
            locales=['en']
        )

        # Update with empty locales
        data = {
            'locales': []
        }

        serializer = TourSerializer(tour, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

        # Save the update
        updated_tour = serializer.save()

        # Check that locales remain empty
        self.assertEqual(updated_tour.locales, [])
