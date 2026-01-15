from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from eureka.models import Project, Tour, POI, Asset, AssetType
from eureka.models.poi_asset import POIAsset
import json

User = get_user_model()

class TestPOIAsset(TestCase):
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
            group=self.user.personal_group
        )
        self.tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour'}},
            description={'locales': {'en': 'A test tour'}}
        )
        self.poi = POI.objects.create(
            tour=self.tour,
            title={'locales': {'en': 'Test POI'}},
            description={'locales': {'en': 'A test POI'}},
            coordinates={'lat': 37.9838, 'long': 23.7275},
            radius=10
        )
        self.source_asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Source Asset'}},
            type=AssetType.IMAGE,
            url={'locales': {'en': '/test/path/image.jpg'}}
        )

    def test_poi_asset_creation(self):
        """Test creating a POI asset with basic fields."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Test POI Asset', 'el': 'Δοκιμαστικό POI Asset'}},
            description={'locales': {'en': 'A test POI asset', 'el': 'Ένα δοκιμαστικό POI asset'}},
            type='image',
            url={'locales': {'en': '/test/poi/asset.jpg', 'el': '/test/poi/asset.jpg'}}
        )

        self.assertEqual(poi_asset.title['locales']['en'], 'Test POI Asset')
        self.assertEqual(poi_asset.type, 'image')
        self.assertEqual(poi_asset.poi, self.poi)
        self.assertEqual(poi_asset.source_asset, self.source_asset)

    def test_ar_placement_default_value(self):
        """Test that ar_placement defaults to 'free'."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Test Asset'}},
            type='model3d',
            url={'locales': {'en': '/test/model.glb'}}
        )

        self.assertEqual(poi_asset.ar_placement, 'free')

    def test_ar_placement_free_choice(self):
        """Test creating POI asset with ar_placement='free'."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Free AR Asset'}},
            type='model3d',
            url={'locales': {'en': '/test/model.glb'}},
            ar_placement='free'
        )

        self.assertEqual(poi_asset.ar_placement, 'free')

    def test_ar_placement_ground_choice(self):
        """Test creating POI asset with ar_placement='ground'."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Ground AR Asset'}},
            type='model3d',
            url={'locales': {'en': '/test/model.glb'}},
            ar_placement='ground'
        )

        self.assertEqual(poi_asset.ar_placement, 'ground')

    def test_ar_placement_invalid_choice(self):
        """Test that invalid ar_placement values are rejected."""
        poi_asset = POIAsset(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Invalid AR Asset'}},
            type='model3d',
            url={'locales': {'en': '/test/model.glb'}},
            ar_placement='invalid_value'
        )

        with self.assertRaises(ValidationError):
            poi_asset.full_clean()

    def test_priority_choices(self):
        """Test priority field with valid choices."""
        # Test normal priority (default)
        poi_asset_normal = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Normal Priority'}},
            type='image',
            url={'locales': {'en': '/test/image.jpg'}}
        )
        self.assertEqual(poi_asset_normal.priority, 'normal')

        # Test high priority
        poi_asset_high = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'High Priority'}},
            type='image',
            url={'locales': {'en': '/test/image.jpg'}},
            priority='high'
        )
        self.assertEqual(poi_asset_high.priority, 'high')

    def test_view_in_ar_default(self):
        """Test that view_in_ar defaults to False."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Test Asset'}},
            type='image',
            url={'locales': {'en': '/test/image.jpg'}}
        )

        self.assertFalse(poi_asset.view_in_ar)

    def test_poi_asset_with_coordinates(self):
        """Test creating a POI asset with optional coordinates."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Geolocated POI Asset'}},
            type='image',
            url={'locales': {'en': '/test/image.jpg'}},
            coordinates={'lat': 37.9838, 'long': 23.7275}
        )

        self.assertEqual(poi_asset.coordinates['lat'], 37.9838)
        self.assertEqual(poi_asset.coordinates['long'], 23.7275)

    def test_poi_asset_without_coordinates(self):
        """Test creating a POI asset without coordinates."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Non-geolocated POI Asset'}},
            type='video',
            url={'locales': {'en': '/test/video.mp4'}}
        )

        self.assertIsNone(poi_asset.coordinates)

    def test_is_georeferenced_property_with_coordinates(self):
        """Test is_georeferenced property returns True when coordinates are set."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Geolocated Asset'}},
            type='image',
            url={'locales': {'en': '/test/image.jpg'}},
            coordinates={'lat': 37.9838, 'long': 23.7275}
        )

        self.assertTrue(poi_asset.is_georeferenced)

    def test_is_georeferenced_property_without_coordinates(self):
        """Test is_georeferenced property returns False when coordinates are None."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Non-geolocated Asset'}},
            type='image',
            url={'locales': {'en': '/test/image.jpg'}}
        )

        self.assertFalse(poi_asset.is_georeferenced)

    def test_poi_asset_with_linked_asset(self):
        """Test creating a POI asset with a linked asset."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': '3D Model'}},
            type='model3d',
            url={'locales': {'en': '/test/model.glb'}},
            linked_asset={
                'locales': {
                    'en': {
                        'title': 'Audio Guide',
                        'url': 'https://example.com/audio/guide.mp3'
                    },
                    'el': {
                        'title': 'Ηχητικός Οδηγός',
                        'url': 'https://example.com/audio/guide.mp3'
                    }
                }
            }
        )

        self.assertIsNotNone(poi_asset.linked_asset)
        self.assertEqual(poi_asset.linked_asset['locales']['en']['title'], 'Audio Guide')

    def test_poi_asset_str_representation(self):
        """Test string representation returns JSON."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Test Asset'}},
            type='image',
            url={'locales': {'en': '/test/image.jpg'}},
            priority='high',
            view_in_ar=True,
            ar_placement='ground'
        )

        str_repr = str(poi_asset)
        json_data = json.loads(str_repr)

        self.assertEqual(json_data['title']['locales']['en'], 'Test Asset')
        self.assertEqual(json_data['type'], 'image')
        self.assertEqual(json_data['priority'], 'high')
        self.assertTrue(json_data['view_in_ar'])
        self.assertEqual(json_data['ar_placement'], 'ground')
        self.assertEqual(json_data['poi_id'], self.poi.id)
        self.assertEqual(json_data['source_asset_id'], self.source_asset.id)

    def test_poi_asset_cascade_delete_with_poi(self):
        """Test that POI asset is deleted when associated POI is deleted."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Test Asset'}},
            type='image',
            url={'locales': {'en': '/test/image.jpg'}}
        )

        poi_asset_id = poi_asset.id
        self.poi.delete()

        with self.assertRaises(POIAsset.DoesNotExist):
            POIAsset.objects.get(id=poi_asset_id)

    def test_poi_asset_cascade_delete_with_source_asset(self):
        """Test that POI asset is deleted when source asset is deleted."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Test Asset'}},
            type='image',
            url={'locales': {'en': '/test/image.jpg'}}
        )

        poi_asset_id = poi_asset.id
        self.source_asset.delete()

        with self.assertRaises(POIAsset.DoesNotExist):
            POIAsset.objects.get(id=poi_asset_id)
