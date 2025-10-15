from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from eureka.models.project import Project
from eureka.models.tour import Tour
from eureka.models.poi import POI
from eureka.models.asset import Asset
from django.contrib.auth.models import Group

User = get_user_model()


class AssetTourIntegrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.user1 = User.objects.create_user(
            login='user1',
            email='user1@example.com',
            password='testpass123',
            name='User One'
        )
        
        self.user2 = User.objects.create_user(
            login='user2',
            email='user2@example.com',
            password='testpass123',
            name='User Two'
        )
        
        # Create group and add users
        self.group = Group.objects.create(name='Test Group')
        self.group.user_set.add(self.user1, self.user2)
        
        # Create project
        self.project = Project.objects.create(
            title="Test Project",
            description="Test project description",
            group=self.group
        )
        
        # Create tour
        self.tour = Tour.objects.create(
            title={"locales": {"en": "Test Tour"}},
            description={"locales": {"en": "Test tour description"}},
            project=self.project
        )
        
        # Create POI
        self.poi = POI.objects.create(
            name={"locales": {"en": "Test POI"}},
            description={"locales": {"en": "Test POI description"}},
            tour=self.tour,
            latitude=40.7128,
            longitude=-74.0060,
            order=1
        )

    def test_create_asset_for_tour(self):
        """Test creating an asset directly associated with a tour"""
        self.client.force_authenticate(user=self.user1)
        
        asset_data = {
            'title': {"locales": {"en": "Tour Background Map"}},
            'description': {"locales": {"en": "Background map for the tour"}},
            'url': 'https://example.com/map.jpg',
            'type': 'image',
            'language': 'en',
            'tour_id': self.tour.id
        }
        
        response = self.client.post(reverse('asset-list-create'), asset_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        asset = Asset.objects.get(id=response.data['id'])
        self.assertEqual(asset.tour, self.tour)
        self.assertEqual(asset.project, self.project)
        self.assertEqual(asset.poi, None)

    def test_create_asset_for_tour_with_meters(self):
        """Test creating an asset for tour with explicit meter dimensions"""
        self.client.force_authenticate(user=self.user1)
        
        asset_data = {
            'title': {"locales": {"en": "Tour Background Map"}},
            'description': {"locales": {"en": "Background map for the tour"}},
            'url': 'https://example.com/map.jpg',
            'type': 'image',
            'language': 'en',
            'tour_id': self.tour.id
        }
        
        response = self.client.post(reverse('asset-list-create'), asset_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        asset = Asset.objects.get(id=response.data['id'])
        self.assertEqual(asset.tour, self.tour)
        self.assertEqual(asset.project, self.project)

    def test_list_assets_by_tour(self):
        """Test listing assets filtered by tour"""
        # Create assets for different contexts
        asset1 = Asset.objects.create(
            title='Project Asset',
            description='Asset for project',
            url='https://example.com/project.jpg',
            type='image',
            language='en',
            project=self.project
        )
        
        asset2 = Asset.objects.create(
            title='Tour Asset',
            description='Asset for tour',
            url='https://example.com/tour.jpg',
            type='image',
            language='en',
            project=self.project,
            tour=self.tour
        )
        
        asset3 = Asset.objects.create(
            title='POI Asset',
            description='Asset for POI',
            url='https://example.com/poi.jpg',
            type='image',
            language='en',
            project=self.project,
            poi=self.poi
        )
        
        self.client.force_authenticate(user=self.user1)
        
        # Test filtering by tour
        response = self.client.get(f"{reverse('asset-list-create')}?tour_id={self.tour.id}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], asset2.id)

    def test_list_assets_by_poi(self):
        """Test listing assets filtered by POI"""
        # Create assets
        asset1 = Asset.objects.create(
            title='Project Asset',
            description='Asset for project',
            url='https://example.com/project.jpg',
            type='image',
            language='en',
            project=self.project
        )
        
        asset2 = Asset.objects.create(
            title='POI Asset',
            description='Asset for POI',
            url='https://example.com/poi.jpg',
            type='image',
            language='en',
            project=self.project,
            poi=self.poi
        )
        
        self.client.force_authenticate(user=self.user1)
        
        # Test filtering by POI
        response = self.client.get(f"{reverse('asset-list-create')}?poi_id={self.poi.id}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], asset2.id)

    def test_create_asset_multiple_targets_error(self):
        """Test that specifying multiple target IDs raises an error"""
        self.client.force_authenticate(user=self.user1)
        
        asset_data = {
            'title': {"locales": {"en": "Test Asset"}},
            'description': {"locales": {"en": "Test description"}},
            'url': 'https://example.com/test.jpg',
            'type': 'image',
            'language': 'en',
            'project_id': self.project.id,
            'tour_id': self.tour.id
        }
        
        response = self.client.post(reverse('asset-list-create'), asset_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Cannot specify multiple target IDs', response.data['detail'])

    def test_create_asset_no_target_error(self):
        """Test that not specifying any target ID raises an error"""
        self.client.force_authenticate(user=self.user1)
        
        asset_data = {
            'title': {"locales": {"en": "Test Asset"}},
            'description': {"locales": {"en": "Test description"}},
            'url': 'https://example.com/test.jpg',
            'type': 'image',
            'language': 'en'
        }
        
        response = self.client.post(reverse('asset-list-create'), asset_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Exactly one of project_id, tour_id, or poi_id is required', response.data['detail'])

    def test_create_asset_for_tour_unauthorized(self):
        """Test that non-member cannot create asset for tour"""
        # Create another user not in the group
        other_user = User.objects.create_user(
            login='otheruser',
            email='other@example.com',
            password='testpass123',
            name='Other User'
        )
        
        self.client.force_authenticate(user=other_user)
        
        asset_data = {
            'title': {"locales": {"en": "Tour Background Map"}},
            'description': {"locales": {"en": "Background map for the tour"}},
            'url': 'https://example.com/map.jpg',
            'type': 'image',
            'language': 'en',
            'tour_id': self.tour.id
        }
        
        response = self.client.post(reverse('asset-list-create'), asset_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Not a member of the tour project group', response.data['detail'])

    def test_asset_serializer_tour_association(self):
        """Test that the serializer correctly handles tour association"""
        from eureka.serializers.asset_serializer import AssetSerializer
        
        # Test creating asset with tour
        data = {
            'title': 'Test Asset',
            'description': 'Test description',
            'url': 'https://example.com/test.jpg',
            'type': 'image',
            'language': 'en'
        }
        
        serializer = AssetSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        asset = serializer.save(project=self.project, tour=self.tour)
        self.assertEqual(asset.tour, self.tour)
        self.assertEqual(asset.project, self.project)
        self.assertIsNone(asset.poi)

    def test_asset_serializer_poi_association(self):
        """Test that the serializer correctly handles POI association"""
        from eureka.serializers.asset_serializer import AssetSerializer
        
        # Test creating asset with POI
        data = {
            'title': 'Test Asset',
            'description': 'Test description',
            'url': 'https://example.com/test.jpg',
            'type': 'image',
            'language': 'en'
        }
        
        serializer = AssetSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        asset = serializer.save(project=self.project, poi=self.poi)
        self.assertEqual(asset.poi, self.poi)
        self.assertEqual(asset.project, self.project)
        self.assertIsNone(asset.tour)

    def test_asset_serializer_project_association(self):
        """Test that the serializer correctly handles project association"""
        from eureka.serializers.asset_serializer import AssetSerializer
        
        # Test creating asset with project only
        data = {
            'title': 'Test Asset',
            'description': 'Test description',
            'url': 'https://example.com/test.jpg',
            'type': 'image',
            'language': 'en'
        }
        
        serializer = AssetSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        asset = serializer.save(project=self.project)
        self.assertEqual(asset.project, self.project)
        self.assertIsNone(asset.tour)
        self.assertIsNone(asset.poi)

    def test_published_tour_endpoint(self):
        """Test that the published tour endpoint returns complete tour data"""
        # Create some assets for the tour and POI
        tour_asset = Asset.objects.create(
            title={"locales": {"en": "Tour Background"}},
            description={"locales": {"en": "Background for the tour"}},
            url='https://example.com/tour-bg.jpg',
            type='image',
            language='en',
            project=self.project,
            tour=self.tour
        )
        
        poi_asset = Asset.objects.create(
            title={"locales": {"en": "POI Image"}},
            description={"locales": {"en": "Image for the POI"}},
            url='https://example.com/poi-image.jpg',
            type='image',
            language='en',
            project=self.project,
            poi=self.poi
        )
        
        # Test the published tour endpoint
        response = self.client.get(f'/api/publishedTour/{self.tour.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify the response structure
        data = response.data
        self.assertEqual(data['id'], self.tour.id)
        self.assertEqual(data['title'], self.tour.title)
        self.assertEqual(data['description'], self.tour.description)
        self.assertEqual(data['is_public'], self.tour.is_public)
        
        # Verify POIs are included
        self.assertEqual(len(data['pois']), 1)
        poi_data = data['pois'][0]
        self.assertEqual(poi_data['id'], self.poi.id)
        self.assertEqual(poi_data['name'], self.poi.name)
        self.assertEqual(poi_data['latitude'], self.poi.latitude)
        self.assertEqual(poi_data['longitude'], self.poi.longitude)
        self.assertEqual(poi_data['order'], self.poi.order)
        
        # Verify POI assets are included
        self.assertEqual(len(poi_data['assets']), 1)
        poi_asset_data = poi_data['assets'][0]
        self.assertEqual(poi_asset_data['id'], poi_asset.id)
        self.assertEqual(poi_asset_data['title'], poi_asset.title)
        self.assertEqual(poi_asset_data['url'], poi_asset.url)
        
        # Verify tour-level assets are included
        self.assertEqual(len(data['assets']), 1)
        tour_asset_data = data['assets'][0]
        self.assertEqual(tour_asset_data['id'], tour_asset.id)
        self.assertEqual(tour_asset_data['title'], tour_asset.title)
        self.assertEqual(tour_asset_data['url'], tour_asset.url) 