from django.test import TestCase
from django.contrib.auth import get_user_model
from eureka.models import Project, Tour, POI
import json

User = get_user_model()

class TestTour(TestCase):
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )
        self.project = Project.objects.create(
            title='Test Project',
            group=self.user.personal_group
        )

    def test_tour_creation(self):
        """Test creating a tour with multilingual content."""
        tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour', 'el': 'Δοκιμαστική Περιήγηση'}},
            description={'locales': {'en': 'A test tour', 'el': 'Μια δοκιμαστική περιήγηση'}}
        )

        self.assertEqual(tour.title['locales']['en'], 'Test Tour')
        self.assertEqual(tour.project, self.project)
        self.assertFalse(tour.is_public)

        # Test JSON string representation
        str_repr = str(tour)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['title']['locales']['en'], 'Test Tour')
        self.assertEqual(json_data['project_id'], self.project.id)
        self.assertFalse(json_data['is_public'])

    def test_tour_str_representation(self):
        """Test string representation returns JSON."""
        tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour'}}
        )

        str_repr = str(tour)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['title']['locales']['en'], 'Test Tour')
        self.assertIsNone(json_data['description'])

    def test_tour_distance_and_duration_fields(self):
        """Test that distance_meters and duration_minutes fields are stored and serialized correctly."""
        tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Distance Tour'}},
            distance_meters=9876,
            duration_minutes=123
        )
        self.assertEqual(tour.distance_meters, 9876)
        self.assertEqual(tour.duration_minutes, 123)
        str_repr = str(tour)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['distance_meters'], 9876)
        self.assertEqual(json_data['duration_minutes'], 123)

    def test_tour_bounding_box_calculation(self):
        """Test bounding box calculation with POIs."""
        tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour'}}
        )
        # Create POIs at different coordinates
        poi1 = POI.objects.create(
            tour=tour,
            title={'locales': {'en': 'POI 1'}},
            coordinates={'lat': 37.9838, 'long': 23.7275},
            order=1
        )
        poi2 = POI.objects.create(
            tour=tour,
            title={'locales': {'en': 'POI 2'}},
            coordinates={'lat': 37.9840, 'long': 23.7280},
            order=2
        )
        tour.update_bounding_box()

        # Check the bounding box field
        self.assertIsNotNone(tour.bounding_box)
        self.assertEqual(tour.bounding_box[0]['lat'], 37.9838)
        self.assertEqual(tour.bounding_box[0]['long'], 23.7275)
        self.assertEqual(tour.bounding_box[1]['lat'], 37.9840)
        self.assertEqual(tour.bounding_box[1]['long'], 23.7280)

        # Test JSON string representation
        str_repr = str(tour)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['bounding_box'][0]['lat'], 37.9838)
        self.assertEqual(json_data['bounding_box'][0]['long'], 23.7275)
        self.assertEqual(json_data['bounding_box'][1]['lat'], 37.9840)
        self.assertEqual(json_data['bounding_box'][1]['long'], 23.7280)

    def test_tour_bounding_box_empty(self):
        """Test bounding box calculation with no POIs."""
        tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour'}}
        )
        tour.update_bounding_box()
        self.assertIsNone(tour.bounding_box)

        # Test JSON string representation
        str_repr = str(tour)
        json_data = json.loads(str_repr)
        self.assertIsNone(json_data['bounding_box'])

    def test_tour_public_flag(self):
        """Test tour public flag functionality."""
        tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Public Tour'}},
            is_public=True
        )
        self.assertTrue(tour.is_public)

        # Test JSON string representation
        str_repr = str(tour)
        json_data = json.loads(str_repr)
        self.assertTrue(json_data['is_public'])
