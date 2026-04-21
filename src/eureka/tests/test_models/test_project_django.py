from django.test import TestCase
from django.contrib.auth import get_user_model
from eureka.models import Project, Tour, POI, Asset, AssetType
from eureka.models.poi_asset import POIAsset

User = get_user_model()

class TestProject(TestCase):
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )

    def test_project_creation(self):
        """Test creating a project with simple text content."""
        project = Project.objects.create(
            title='Test Project',
            description='A test project',
            group=self.user.personal_group
        )
        
        self.assertEqual(project.title, 'Test Project')
        self.assertEqual(project.description, 'A test project')
        self.assertEqual(project.group, self.user.personal_group)
        
        # Test string representation
        str_repr = str(project)
        self.assertIn('Test Project', str_repr)
        self.assertIn(self.user.personal_group.name, str_repr)

    def test_project_str_representation(self):
        """Test string representation."""
        project = Project.objects.create(
            title='Test Project',
            group=self.user.personal_group
        )
        
        str_repr = str(project)
        self.assertIn('Test Project', str_repr)
        self.assertIn(self.user.personal_group.name, str_repr)

    def test_project_without_description(self):
        """Test creating a project without description."""
        project = Project.objects.create(
            title='Test Project',
            group=self.user.personal_group
        )
        self.assertEqual(project.description, {})

        # Test string representation
        str_repr = str(project)
        self.assertIn('Test Project', str_repr)
        self.assertIn(self.user.personal_group.name, str_repr)

    def test_project_deletion_cascades_to_tours_pois_assets_and_poi_assets(self):
        """Deleting a project should cascade-delete its tours, POIs, assets, and POI assets."""
        project = Project.objects.create(
            title='Project To Delete',
            group=self.user.personal_group
        )
        tour = Tour.objects.create(project=project, title={'locales': {'en': 'Tour'}})
        poi = POI.objects.create(tour=tour, title={'locales': {'en': 'POI'}}, coordinates={'lat': 37.9, 'long': 23.7}, order=1)
        asset = Asset.objects.create(project=project, title={'locales': {'en': 'Asset'}}, type=AssetType.IMAGE)
        poi_asset = POIAsset.objects.create(poi=poi, source_asset=asset, type=AssetType.IMAGE)

        project_id = project.id
        tour_id = tour.id
        poi_id = poi.id
        asset_id = asset.id
        poi_asset_id = poi_asset.id

        project.delete()

        self.assertFalse(Project.objects.filter(id=project_id).exists())
        self.assertFalse(Tour.objects.filter(id=tour_id).exists())
        self.assertFalse(POI.objects.filter(id=poi_id).exists())
        self.assertFalse(Asset.objects.filter(id=asset_id).exists())
        self.assertFalse(POIAsset.objects.filter(id=poi_asset_id).exists())

    def test_project_deletion_does_not_affect_other_projects(self):
        """Deleting one project should not affect another project's tours, POIs, assets, or POI assets."""
        second_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            name='Other User'
        )
        project_a = Project.objects.create(title='Project A', group=self.user.personal_group)
        project_b = Project.objects.create(title='Project B', group=second_user.personal_group)

        tour_b = Tour.objects.create(project=project_b, title={'locales': {'en': 'Tour B'}})
        poi_b = POI.objects.create(tour=tour_b, title={'locales': {'en': 'POI B'}}, coordinates={'lat': 37.9, 'long': 23.7}, order=1)
        asset_b = Asset.objects.create(project=project_b, title={'locales': {'en': 'Asset B'}}, type=AssetType.IMAGE)
        poi_asset_b = POIAsset.objects.create(poi=poi_b, source_asset=asset_b, type=AssetType.IMAGE)

        project_a.delete()

        self.assertTrue(Project.objects.filter(id=project_b.id).exists())
        self.assertTrue(Tour.objects.filter(id=tour_b.id).exists())
        self.assertTrue(POI.objects.filter(id=poi_b.id).exists())
        self.assertTrue(Asset.objects.filter(id=asset_b.id).exists())
        self.assertTrue(POIAsset.objects.filter(id=poi_asset_b.id).exists())