from django.test import TestCase
from django.contrib.auth import get_user_model
from eureka.models import Project, Tour, POI
import json

User = get_user_model()

class TestPOI(TestCase):
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
        self.tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour'}}
        )

    def test_poi_creation(self):
        """Test creating a POI with multilingual content and coordinates."""
        poi = POI.objects.create(
            tour=self.tour,
            name={'locales': {'en': 'Test POI', 'el': 'Δοκιμαστικό Σημείο'}},
            description={'locales': {'en': 'A test POI', 'el': 'Ένα δοκιμαστικό σημείο'}},
            latitude=37.9838,
            longitude=23.7275,
            order=1
        )
        
        self.assertEqual(poi.name['locales']['en'], 'Test POI')
        self.assertEqual(poi.latitude, 37.9838)
        self.assertEqual(poi.longitude, 23.7275)
        self.assertEqual(poi.tour, self.tour)
        self.assertEqual(poi.order, 1)
        
        # Test JSON string representation
        str_repr = str(poi)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['name']['locales']['en'], 'Test POI')
        self.assertEqual(json_data['tour_id'], self.tour.id)
        self.assertEqual(json_data['latitude'], 37.9838)
        self.assertEqual(json_data['order'], 1)

    def test_poi_str_representation(self):
        """Test string representation returns JSON."""
        poi = POI.objects.create(
            tour=self.tour,
            name={'locales': {'en': 'Test POI'}},
            latitude=37.9838,
            longitude=23.7275,
            order=1
        )
        
        str_repr = str(poi)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['name']['locales']['en'], 'Test POI')
        self.assertIsNone(json_data['description'])

    def test_poi_order_sequence(self):
        """Test POI order field functionality."""
        poi1 = POI.objects.create(
            tour=self.tour,
            name={'locales': {'en': 'First POI'}},
            latitude=37.9838,
            longitude=23.7275,
            order=1
        )
        poi2 = POI.objects.create(
            tour=self.tour,
            name={'locales': {'en': 'Second POI'}},
            latitude=37.9840,
            longitude=23.7280,
            order=2
        )
        
        self.assertEqual(poi1.order, 1)
        self.assertEqual(poi2.order, 2)
        
        # Test JSON string representation
        str_repr1 = str(poi1)
        json_data1 = json.loads(str_repr1)
        self.assertEqual(json_data1['order'], 1)
        
        str_repr2 = str(poi2)
        json_data2 = json.loads(str_repr2)
        self.assertEqual(json_data2['order'], 2) 