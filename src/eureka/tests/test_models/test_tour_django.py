from django.test import TestCase
from django.contrib.auth import get_user_model
from eureka.models import Project, Tour, POI
import json

User = get_user_model()

class TestTour(TestCase):
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            login='testuser',
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

    def test_tour_bounding_box_calculation(self):
        """Test bounding box calculation with POIs."""
        tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour'}}
        )
        
        # Create POIs at different coordinates
        poi1 = POI.objects.create(
            tour=tour,
            name={'locales': {'en': 'POI 1'}},
            latitude=37.9838,
            longitude=23.7275,
            order=1
        )
        poi2 = POI.objects.create(
            tour=tour,
            name={'locales': {'en': 'POI 2'}},
            latitude=37.9840,
            longitude=23.7280,
            order=2
        )
        
        tour.update_bounding_box()
        
        self.assertEqual(float(tour.min_latitude), 37.9838)
        self.assertEqual(float(tour.max_latitude), 37.9840)
        self.assertEqual(float(tour.min_longitude), 23.7275)
        self.assertEqual(float(tour.max_longitude), 23.7280)
        
        # Test JSON string representation
        str_repr = str(tour)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['min_latitude'], 37.9838)
        self.assertEqual(json_data['max_latitude'], 37.9840)

    def test_tour_bounding_box_empty(self):
        """Test bounding box calculation with no POIs."""
        tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour'}}
        )
        
        tour.update_bounding_box()
        
        self.assertIsNone(tour.min_latitude)
        self.assertIsNone(tour.max_latitude)
        self.assertIsNone(tour.min_longitude)
        self.assertIsNone(tour.max_longitude)
        
        # Test JSON string representation
        str_repr = str(tour)
        json_data = json.loads(str_repr)
        self.assertIsNone(json_data['min_latitude'])
        self.assertIsNone(json_data['max_latitude'])

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