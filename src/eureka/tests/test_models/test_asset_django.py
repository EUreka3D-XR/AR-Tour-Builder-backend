from django.test import TestCase
from django.contrib.auth import get_user_model
from eureka.models import Project, Asset, AssetType, POI, Tour
import json

User = get_user_model()

class TestAsset(TestCase):
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

    def test_asset_creation(self):
        """Test creating an asset with multilingual content."""
        asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Asset', 'el': 'Δοκιμαστικό Περιεχόμενο'}},
            description={'locales': {'en': 'A test asset', 'el': 'Ένα δοκιμαστικό περιεχόμενο'}},
            type=AssetType.IMAGE,
            url='/test/path/image.jpg'
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
            url='/test/path/image.jpg'
        )
        
        str_repr = str(asset)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['title']['locales']['en'], 'Test Asset')
        self.assertEqual(json_data['type'], AssetType.IMAGE)
        self.assertIsNone(json_data['description'])

    def test_asset_with_poi_reference(self):
        """Test creating an asset that references a POI."""
        tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour'}}
        )
        poi = POI.objects.create(
            tour=tour,
            name={'locales': {'en': 'Test POI'}},
            latitude=37.9838,
            longitude=23.7275,
            order=1
        )
        
        asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'POI Asset'}},
            type=AssetType.IMAGE,
            url='/test/path/image.jpg',
            poi=poi
        )
        
        self.assertEqual(asset.poi, poi)
        
        # Test JSON string representation
        str_repr = str(asset)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['poi_id'], poi.id)

    def test_asset_with_source_asset(self):
        """Test creating an asset that references a source asset."""
        source_asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Source Asset'}},
            type=AssetType.IMAGE,
            url='/test/path/source.jpg'
        )
        
        derived_asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Derived Asset'}},
            type=AssetType.IMAGE,
            url='/test/path/derived.jpg',
            source_asset=source_asset
        )
        
        self.assertEqual(derived_asset.source_asset, source_asset)
        
        # Test JSON string representation
        str_repr = str(derived_asset)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['source_asset_id'], source_asset.id)

    def test_asset_with_real_world_dimensions(self):
        """Test creating an asset with real-world dimensions for map images."""
        asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Map Image'}},
            type=AssetType.IMAGE,
            url='/test/path/map.jpg',
            real_width_meters=100.5,
            real_height_meters=75.25
        )
        
        self.assertEqual(asset.real_width_meters, 100.5)
        self.assertEqual(asset.real_height_meters, 75.25)
        
        # Test JSON string representation
        str_repr = str(asset)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['real_width_meters'], 100.5)
        self.assertEqual(json_data['real_height_meters'], 75.25)

    def test_asset_with_partial_real_world_dimensions(self):
        """Test creating an asset with only one real-world dimension."""
        asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Partial Map'}},
            type=AssetType.IMAGE,
            url='/test/path/partial_map.jpg',
            real_width_meters=50.0
        )
        
        self.assertEqual(asset.real_width_meters, 50.0)
        self.assertIsNone(asset.real_height_meters)
        
        # Test JSON string representation
        str_repr = str(asset)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['real_width_meters'], 50.0)
        self.assertIsNone(json_data['real_height_meters'])

    def test_asset_with_small_3d_object_dimensions(self):
        """Test creating an asset with small real-world dimensions for 3D objects."""
        asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Small 3D Object'}},
            type=AssetType.MODEL3D,
            url='/test/path/small_object.glb',
            real_width_meters=0.025,
            real_height_meters=0.015
        )
        
        self.assertEqual(asset.real_width_meters, 0.025)
        self.assertEqual(asset.real_height_meters, 0.015)
        
        # Test JSON string representation
        str_repr = str(asset)
        json_data = json.loads(str_repr)
        self.assertEqual(json_data['real_width_meters'], 0.025)
        self.assertEqual(json_data['real_height_meters'], 0.015)

    def test_asset_has_real_world_dimensions(self):
        """Test the has_real_world_dimensions helper method."""
        # Asset with both dimensions
        asset_with_both = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Full Map'}},
            type=AssetType.IMAGE,
            url='/test/path/full_map.jpg',
            real_width_meters=100.0,
            real_height_meters=75.0
        )
        self.assertTrue(asset_with_both.has_real_world_dimensions())
        
        # Asset with only width
        asset_with_width = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Width Only'}},
            type=AssetType.IMAGE,
            url='/test/path/width_only.jpg',
            real_width_meters=50.0
        )
        self.assertTrue(asset_with_width.has_real_world_dimensions())
        
        # Asset with no dimensions
        asset_without = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'No Dimensions'}},
            type=AssetType.IMAGE,
            url='/test/path/no_dimensions.jpg'
        )
        self.assertFalse(asset_without.has_real_world_dimensions())

    def test_asset_get_scale_factor(self):
        """Test the get_scale_factor helper method."""
        asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'Scale Test Map'}},
            type=AssetType.IMAGE,
            url='/test/path/scale_test.jpg',
            real_width_meters=100.0,
            real_height_meters=75.0
        )
        
        # Test with 1000x750 pixel image
        scale_factor = asset.get_scale_factor(1000, 750)
        self.assertIsNotNone(scale_factor)
        meters_per_pixel_x, meters_per_pixel_y = scale_factor
        self.assertEqual(meters_per_pixel_x, 0.1)  # 100m / 1000px = 0.1 m/px
        self.assertEqual(meters_per_pixel_y, 0.1)  # 75m / 750px = 0.1 m/px
        
        # Test with asset without dimensions
        asset_no_dim = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'No Dim'}},
            type=AssetType.IMAGE,
            url='/test/path/no_dim.jpg'
        )
        self.assertIsNone(asset_no_dim.get_scale_factor(1000, 750))

    def test_asset_get_gps_bounds(self):
        """Test the get_gps_bounds_from_image_coords helper method."""
        asset = Asset.objects.create(
            project=self.project,
            title={'locales': {'en': 'GPS Test Map'}},
            type=AssetType.IMAGE,
            url='/test/path/gps_test.jpg',
            real_width_meters=100.0,
            real_height_meters=75.0
        )
        
        # Test with image at coordinates (37.9838, 23.7275) - Athens area
        bounds = asset.get_gps_bounds_from_image_coords(1000, 750, 37.9838, 23.7275)
        self.assertIsNotNone(bounds)
        self.assertIn('min_lat', bounds)
        self.assertIn('max_lat', bounds)
        self.assertIn('min_lon', bounds)
        self.assertIn('max_lon', bounds)
        
        # Verify the bounds make sense (top-left corner should be max_lat, min_lon)
        self.assertEqual(bounds['max_lat'], 37.9838)  # Top
        self.assertEqual(bounds['min_lon'], 23.7275)  # Left
        
        # Bottom and right should be calculated
        self.assertLess(bounds['min_lat'], bounds['max_lat'])  # Bottom < Top
        self.assertGreater(bounds['max_lon'], bounds['min_lon'])  # Right > Left

    def test_asset_serializer_corner_coordinates(self):
        """Test that the serializer can calculate real-world dimensions from corner coordinates."""
        from eureka.serializers.asset_serializer import AssetSerializer
        from eureka.models import Tour
        
        # Create a tour and POI
        tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour'}}
        )
        poi = POI.objects.create(
            tour=tour,
            name={'locales': {'en': 'Test POI'}},
            latitude=37.9838,  # Top-left corner
            longitude=23.7275,
            order=1
        )
        
        # Test data with corner coordinates
        asset_data = {
            'project': self.project.id,
            'poi': poi.id,
            'title': {'locales': {'en': 'Map with Corner Coords'}},
            'type': 'image',
            'url': 'http://example.com/test/path/map.jpg',
            'se_corner_lat': 37.9830,
            'se_corner_long': 23.7280
        }
        
        serializer = AssetSerializer(data=asset_data)
        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)
        self.assertTrue(serializer.is_valid())
        
        # Create the asset, passing project and poi as instances
        asset = serializer.save(project=self.project, poi=poi)
        
        # Verify that real-world dimensions were calculated
        self.assertIsNotNone(asset.real_width_meters)
        self.assertIsNotNone(asset.real_height_meters)
        
        # The dimensions should be positive and reasonable
        self.assertGreater(asset.real_width_meters, 0)
        self.assertGreater(asset.real_height_meters, 0)
        
        # For this small area, dimensions should be in the range of tens to hundreds of meters
        self.assertLess(asset.real_width_meters, 1000)  # Less than 1km
        self.assertLess(asset.real_height_meters, 1000)  # Less than 1km 