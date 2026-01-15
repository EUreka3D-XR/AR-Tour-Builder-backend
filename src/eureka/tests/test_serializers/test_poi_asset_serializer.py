from django.test import TestCase
from django.contrib.auth import get_user_model
from eureka.models import Project, Tour, POI, Asset, AssetType
from eureka.models.poi_asset import POIAsset
from eureka.serializers.poi_asset_serializer import POIAssetSerializer

User = get_user_model()

class TestPOIAssetSerializer(TestCase):
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

    def test_serializer_includes_ar_placement_field(self):
        """Test that the serializer includes ar_placement field."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Test Asset'}},
            type='model3d',
            url={'locales': {'en': '/test/model.glb'}},
            ar_placement='ground'
        )

        serializer = POIAssetSerializer(poi_asset)
        data = serializer.data

        self.assertIn('ar_placement', data)
        self.assertEqual(data['ar_placement'], 'ground')

    def test_serializer_ar_placement_default_value(self):
        """Test that serializer returns default 'free' for ar_placement."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Test Asset'}},
            type='model3d',
            url={'locales': {'en': '/test/model.glb'}}
        )

        serializer = POIAssetSerializer(poi_asset)
        data = serializer.data

        self.assertEqual(data['ar_placement'], 'free')

    def test_serializer_includes_is_georeferenced_field(self):
        """Test that the serializer includes is_georeferenced computed field."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Test Asset'}},
            type='image',
            url={'locales': {'en': '/test/image.jpg'}},
            coordinates={'lat': 37.9838, 'long': 23.7275}
        )

        serializer = POIAssetSerializer(poi_asset)
        data = serializer.data

        self.assertIn('is_georeferenced', data)
        self.assertTrue(data['is_georeferenced'])

    def test_serializer_is_georeferenced_false(self):
        """Test that is_georeferenced is False when coordinates are None."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Test Asset'}},
            type='image',
            url={'locales': {'en': '/test/image.jpg'}}
        )

        serializer = POIAssetSerializer(poi_asset)
        data = serializer.data

        self.assertFalse(data['is_georeferenced'])

    def test_serializer_deserialization_with_ar_placement(self):
        """Test deserializing data with ar_placement field."""
        data = {
            'title': {'locales': {'en': 'New Asset'}},
            'type': 'model3d',
            'url': {'locales': {'en': '/test/model.glb'}},
            'ar_placement': 'ground',
            'view_in_ar': True,
            'priority': 'high'
        }

        serializer = POIAssetSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['ar_placement'], 'ground')

    def test_serializer_validation_invalid_ar_placement(self):
        """Test that serializer rejects invalid ar_placement values."""
        data = {
            'title': {'locales': {'en': 'New Asset'}},
            'type': 'model3d',
            'url': {'locales': {'en': '/test/model.glb'}},
            'ar_placement': 'invalid_choice'
        }

        serializer = POIAssetSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('ar_placement', serializer.errors)

    def test_serializer_all_fields_present(self):
        """Test that all expected fields are present in serialized data."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Complete Asset'}},
            description={'locales': {'en': 'Complete description'}},
            type='model3d',
            url={'locales': {'en': '/test/model.glb'}},
            priority='high',
            view_in_ar=True,
            ar_placement='ground',
            coordinates={'lat': 37.9838, 'long': 23.7275},
            linked_asset={
                'locales': {
                    'en': {
                        'title': 'Audio Guide',
                        'url': 'https://example.com/audio/guide.mp3'
                    }
                }
            }
        )

        serializer = POIAssetSerializer(poi_asset)
        data = serializer.data

        expected_fields = [
            'id', 'poi', 'source_asset', 'title', 'description', 'type',
            'url', 'priority', 'view_in_ar', 'ar_placement', 'coordinates',
            'is_georeferenced', 'linked_asset', 'created_at', 'updated_at'
        ]

        for field in expected_fields:
            self.assertIn(field, data, f"Field '{field}' is missing from serialized data")

    def test_serializer_read_only_fields(self):
        """Test that read-only fields cannot be updated via serializer."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Test Asset'}},
            type='image',
            url={'locales': {'en': '/test/image.jpg'}}
        )

        # Try to update read-only field
        data = {
            'title': {'locales': {'en': 'Updated Asset'}},
            'is_georeferenced': True  # This is read-only
        }

        serializer = POIAssetSerializer(poi_asset, data=data, partial=True)
        self.assertTrue(serializer.is_valid())

        # is_georeferenced should still be False (not updated from input)
        updated_asset = serializer.save()
        self.assertFalse(updated_asset.is_georeferenced)

    def test_serializer_with_locale_context(self):
        """Test serializer with locale context for multilingual fields."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'English Title', 'el': 'Ελληνικός Τίτλος'}},
            type='image',
            url={'locales': {'en': '/test/image-en.jpg', 'el': '/test/image-el.jpg'}}
        )

        # Test with English locale
        serializer = POIAssetSerializer(poi_asset, context={'locale': 'en'})
        data = serializer.data

        # When locale is provided, multilingual fields should return just the string
        self.assertEqual(data['title'], 'English Title')
        self.assertEqual(data['url'], '/test/image-en.jpg')

    def test_serializer_update_ar_placement(self):
        """Test updating ar_placement via serializer."""
        poi_asset = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.source_asset,
            title={'locales': {'en': 'Test Asset'}},
            type='model3d',
            url={'locales': {'en': '/test/model.glb'}},
            ar_placement='free'
        )

        data = {'ar_placement': 'ground'}
        serializer = POIAssetSerializer(poi_asset, data=data, partial=True)

        self.assertTrue(serializer.is_valid())
        updated_asset = serializer.save()
        self.assertEqual(updated_asset.ar_placement, 'ground')
