from django.test import TestCase
from django.contrib.auth import get_user_model
from eureka.models import Project, Asset, AssetType
import json

User = get_user_model()

class TestAsset(TestCase):
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

    def test_asset_creation(self):
        """Test creating an asset with multilingual content."""
        asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Asset', 'el': 'Δοκιμαστικό Περιεχόμενο'}},
            description={'locales': {'en': 'A test asset', 'el': 'Ένα δοκιμαστικό περιεχόμενο'}},
            type=AssetType.IMAGE,
            url={'locales': {'en': '/test/path/image.jpg', 'el': '/test/path/image.jpg'}}
        )

        self.assertEqual(asset.title['locales']['en'], 'Test Asset')
        self.assertEqual(asset.type, AssetType.IMAGE)
        self.assertEqual(asset.project, self.project)

        # Test JSON string representation
        str_repr = str(asset)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['title']['locales']['en'], 'Test Asset')
        self.assertEqual(json_data['project_id'], self.project.id)
        self.assertEqual(json_data['type'], AssetType.IMAGE)

    def test_asset_str_representation(self):
        """Test string representation returns JSON."""
        asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Asset'}},
            type=AssetType.IMAGE,
            url={'locales': {'en': '/test/path/image.jpg'}}
        )

        str_repr = str(asset)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['title']['locales']['en'], 'Test Asset')
        self.assertEqual(json_data['type'], AssetType.IMAGE)
        self.assertIsNone(json_data['description'])

    def test_asset_with_georeference(self):
        """Test creating an asset with optional georeference."""
        asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Geolocated Asset'}},
            type=AssetType.IMAGE,
            url={'locales': {'en': '/test/path/image.jpg'}},
            georeference={'coordinates': {'lat': 37.9838, 'long': 23.7275}}
        )

        self.assertEqual(asset.georeference['coordinates']['lat'], 37.9838)
        self.assertEqual(asset.georeference['coordinates']['long'], 23.7275)

        # Test JSON string representation
        str_repr = str(asset)
        json_data = json.loads(str_repr)
        self.assertIsNotNone(json_data['georeference'])
        self.assertEqual(json_data['georeference']['coordinates']['lat'], 37.9838)
        self.assertEqual(json_data['georeference']['coordinates']['long'], 23.7275)

    def test_asset_without_georeference(self):
        """Test creating an asset without georeference."""
        asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Non-geolocated Asset'}},
            type=AssetType.VIDEO,
            url={'locales': {'en': '/test/path/video.mp4'}}
        )

        self.assertIsNone(asset.georeference)

        # Test JSON string representation
        str_repr = str(asset)
        json_data = json.loads(str_repr)
        self.assertIsNone(json_data['georeference'])

    def test_is_georeferenced_property_with_georeference(self):
        """Test is_georeferenced property returns True when georeference is set."""
        asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Geolocated Asset'}},
            type=AssetType.IMAGE,
            url={'locales': {'en': '/test/path/image.jpg'}},
            georeference={'coordinates': {'lat': 37.9838, 'long': 23.7275}}
        )

        self.assertTrue(asset.is_georeferenced)

    def test_is_georeferenced_property_without_georeference(self):
        """Test is_georeferenced property returns False when georeference is None."""
        asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Non-geolocated Asset'}},
            type=AssetType.IMAGE,
            url={'locales': {'en': '/test/path/image.jpg'}}
        )

        self.assertFalse(asset.is_georeferenced)
