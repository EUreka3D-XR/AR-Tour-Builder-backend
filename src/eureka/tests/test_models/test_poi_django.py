from django.test import TestCase
from django.contrib.auth import get_user_model
from eureka.models import Project, Tour, POI
import json

User = get_user_model()

class TestPOI(TestCase):
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
        self.tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour'}}
        )

    def test_poi_creation(self):
        """Test creating a POI with multilingual content and coordinates."""
        poi = POI.objects.create(
            tour=self.tour,
            title={'locales': {'en': 'Test POI', 'el': 'Δοκιμαστικό Σημείο'}},
            description={'locales': {'en': 'A test POI', 'el': 'Ένα δοκιμαστικό σημείο'}},
            coordinates={'lat': 37.9838, 'long': 23.7275},
            order=1
        )
        self.assertEqual(poi.title['locales']['en'], 'Test POI')
        self.assertEqual(poi.coordinates['lat'], 37.9838)
        self.assertEqual(poi.coordinates['long'], 23.7275)
        self.assertEqual(poi.tour, self.tour)
        self.assertEqual(poi.order, 1)
        # Test JSON string representation
        str_repr = str(poi)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['title']['locales']['en'], 'Test POI')
        self.assertEqual(json_data['tour_id'], self.tour.id)
        self.assertEqual(json_data['coordinates']['lat'], 37.9838)
        self.assertEqual(json_data['coordinates']['long'], 23.7275)
        self.assertEqual(json_data['order'], 1)

    def test_poi_str_representation(self):
        """Test string representation returns JSON."""
        poi = POI.objects.create(
            tour=self.tour,
            title={'locales': {'en': 'Test POI'}},
            coordinates={'lat': 37.9838, 'long': 23.7275},
            order=1
        )
        str_repr = str(poi)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['title']['locales']['en'], 'Test POI')
        self.assertEqual(json_data['coordinates']['lat'], 37.9838)
        self.assertEqual(json_data['coordinates']['long'], 23.7275)
        self.assertIsNone(json_data['description'])

    def test_poi_order_sequence(self):
        """Test POI order field functionality."""
        poi1 = POI.objects.create(
            tour=self.tour,
            title={'locales': {'en': 'First POI'}},
            coordinates={'lat': 37.9838, 'long': 23.7275},
            order=1
        )
        poi2 = POI.objects.create(
            tour=self.tour,
            title={'locales': {'en': 'Second POI'}},
            coordinates={'lat': 37.9840, 'long': 23.7280},
            order=2
        )
        self.assertEqual(poi1.order, 1)
        self.assertEqual(poi2.order, 2)
        # Test JSON string representation
        str_repr1 = str(poi1)
        json_data1 = json.loads(str_repr1)
        self.assertEqual(json_data1['order'], 1)
        self.assertEqual(json_data1['coordinates']['lat'], 37.9838)
        self.assertEqual(json_data1['coordinates']['long'], 23.7275)
        str_repr2 = str(poi2)
        json_data2 = json.loads(str_repr2)
        self.assertEqual(json_data2['order'], 2)
        self.assertEqual(json_data2['coordinates']['lat'], 37.9840)
        self.assertEqual(json_data2['coordinates']['long'], 23.7280)

    def test_poi_radius_field(self):
        """Test POI radius field with default and custom values."""
        # Test default radius
        poi1 = POI.objects.create(
            tour=self.tour,
            title={'locales': {'en': 'POI with default radius'}},
            coordinates={'lat': 37.9838, 'long': 23.7275},
            order=1
        )
        self.assertEqual(poi1.radius, 20)

        # Test custom radius
        poi2 = POI.objects.create(
            tour=self.tour,
            title={'locales': {'en': 'POI with custom radius'}},
            coordinates={'lat': 37.9840, 'long': 23.7280},
            radius=50,
            order=2
        )
        self.assertEqual(poi2.radius, 50)

        # Test JSON string representation includes radius
        str_repr = str(poi1)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['radius'], 20)

        str_repr2 = str(poi2)
        json_data2 = json.loads(str_repr2)
        self.assertEqual(json_data2['radius'], 50)
