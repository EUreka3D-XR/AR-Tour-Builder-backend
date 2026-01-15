from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from eureka.models.project import Project
from eureka.models.asset import Asset
from django.contrib.auth.models import Group

User = get_user_model()


class AssetIntegrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            name='User One'
        )

        self.user2 = User.objects.create_user(
            username='user2',
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

    def test_create_asset_for_project(self):
        """Test creating an asset for a project"""
        self.client.force_authenticate(user=self.user1)

        asset_data = {
            'title': {"locales": {"en": "Project Asset"}},
            'description': {"locales": {"en": "Asset for project"}},
            'url': 'https://example.com/asset.jpg',
            'type': 'image',
            'project_id': self.project.id
        }

        response = self.client.post(reverse('asset-list-create'), asset_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        asset = Asset.objects.get(id=response.data['id'])
        self.assertEqual(asset.project, self.project)

    def test_list_assets_by_project(self):
        """Test listing assets filtered by project"""
        # Create assets for the project
        asset1 = Asset.objects.create(
            title={'locales': {'en': 'Project Asset 1'}},
            description={'locales': {'en': 'Asset for project'}},
            url='https://example.com/project1.jpg',
            type='image',
            project=self.project
        )

        asset2 = Asset.objects.create(
            title={'locales': {'en': 'Project Asset 2'}},
            description={'locales': {'en': 'Asset for project'}},
            url='https://example.com/project2.jpg',
            type='image',
            project=self.project
        )

        self.client.force_authenticate(user=self.user1)

        # Test filtering by project
        response = self.client.get(f"{reverse('asset-list-create')}?project_id={self.project.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_create_asset_no_project_error(self):
        """Test that not specifying project_id raises an error"""
        self.client.force_authenticate(user=self.user1)

        asset_data = {
            'title': {"locales": {"en": "Test Asset"}},
            'description': {"locales": {"en": "Test description"}},
            'url': 'https://example.com/test.jpg',
            'type': 'image'
        }

        response = self.client.post(reverse('asset-list-create'), asset_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('project_id is required', response.data['detail'])

    def test_create_asset_unauthorized(self):
        """Test that non-member cannot create asset for project"""
        # Create another user not in the group
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            name='Other User'
        )

        self.client.force_authenticate(user=other_user)

        asset_data = {
            'title': {"locales": {"en": "Project Asset"}},
            'description': {"locales": {"en": "Asset for project"}},
            'url': 'https://example.com/asset.jpg',
            'type': 'image',
            'project_id': self.project.id
        }

        response = self.client.post(reverse('asset-list-create'), asset_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Not a member of the project group', response.data['detail'])

    def test_asset_serializer_project_association(self):
        """Test that the serializer correctly handles project association"""
        from eureka.serializers.asset_serializer import AssetSerializer

        # Test creating asset with project only
        data = {
            'title': {'locales': {'en': 'Test Asset'}},
            'description': {'locales': {'en': 'Test description'}},
            'url': 'https://example.com/test.jpg',
            'type': 'image'
        }

        serializer = AssetSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        asset = serializer.save(project=self.project)
        self.assertEqual(asset.project, self.project)
