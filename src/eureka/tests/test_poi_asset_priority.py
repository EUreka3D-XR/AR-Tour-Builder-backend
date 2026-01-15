from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from eureka.models.project import Project
from eureka.models.tour import Tour
from eureka.models.poi import POI
from eureka.models.poi_asset import POIAsset
from eureka.models.asset import Asset
from django.contrib.auth.models import Group

User = get_user_model()


class POIAssetPriorityTest(TestCase):
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

        # Create group and add user1
        self.group = Group.objects.create(name='Test Group')
        self.group.user_set.add(self.user1)

        # Create project
        self.project = Project.objects.create(
            title="Test Project",
            description="Test project description",
            group=self.group
        )

        # Create tour
        self.tour = Tour.objects.create(
            title={'locales': {'en': 'Test Tour'}},
            description={'locales': {'en': 'Test tour description'}},
            project=self.project
        )

        # Create POI
        self.poi = POI.objects.create(
            title={'locales': {'en': 'Test POI'}},
            description={'locales': {'en': 'Test POI description'}},
            tour=self.tour,
            order=1
        )

        # Create source assets
        self.asset1 = Asset.objects.create(
            title={'locales': {'en': 'Asset 1'}},
            description={'locales': {'en': 'Asset 1 description'}},
            url='https://example.com/asset1.jpg',
            type='image',
            project=self.project
        )

        self.asset2 = Asset.objects.create(
            title={'locales': {'en': 'Asset 2'}},
            description={'locales': {'en': 'Asset 2 description'}},
            url='https://example.com/asset2.jpg',
            type='image',
            project=self.project
        )

        self.asset3 = Asset.objects.create(
            title={'locales': {'en': 'Asset 3'}},
            description={'locales': {'en': 'Asset 3 description'}},
            url='https://example.com/asset3.jpg',
            type='image',
            project=self.project
        )

        # Create POI assets
        self.poi_asset1 = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.asset1,
            title={'locales': {'en': 'POI Asset 1'}},
            description={'locales': {'en': 'POI Asset 1 description'}},
            type='image',
            url={'locales': {'en': 'https://example.com/poi_asset1.jpg'}},
            priority='normal'
        )

        self.poi_asset2 = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.asset2,
            title={'locales': {'en': 'POI Asset 2'}},
            description={'locales': {'en': 'POI Asset 2 description'}},
            type='image',
            url={'locales': {'en': 'https://example.com/poi_asset2.jpg'}},
            priority='normal'
        )

        self.poi_asset3 = POIAsset.objects.create(
            poi=self.poi,
            source_asset=self.asset3,
            title={'locales': {'en': 'POI Asset 3'}},
            description={'locales': {'en': 'POI Asset 3 description'}},
            type='image',
            url={'locales': {'en': 'https://example.com/poi_asset3.jpg'}},
            priority='normal'
        )

    def test_set_primary_success(self):
        """Test setting a POI asset as primary successfully"""
        self.client.force_authenticate(user=self.user1)

        response = self.client.post(
            reverse('poi-asset-set-primary', kwargs={'pk': self.poi_asset1.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['priority'], 'high')

        # Verify the asset was updated in the database
        self.poi_asset1.refresh_from_db()
        self.assertEqual(self.poi_asset1.priority, 'high')

    def test_set_primary_demotes_others(self):
        """Test that setting a POI asset as primary demotes other high-priority assets"""
        # First set poi_asset1 as primary
        self.poi_asset1.priority = 'high'
        self.poi_asset1.save()

        # Also set poi_asset2 as high (simulating multiple high-priority assets)
        self.poi_asset2.priority = 'high'
        self.poi_asset2.save()

        self.client.force_authenticate(user=self.user1)

        # Now set poi_asset3 as primary
        response = self.client.post(
            reverse('poi-asset-set-primary', kwargs={'pk': self.poi_asset3.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['priority'], 'high')

        # Verify poi_asset3 is now high priority
        self.poi_asset3.refresh_from_db()
        self.assertEqual(self.poi_asset3.priority, 'high')

        # Verify poi_asset1 and poi_asset2 were demoted to normal
        self.poi_asset1.refresh_from_db()
        self.poi_asset2.refresh_from_db()
        self.assertEqual(self.poi_asset1.priority, 'normal')
        self.assertEqual(self.poi_asset2.priority, 'normal')

    def test_set_primary_same_asset_twice(self):
        """Test setting the same asset as primary twice works correctly"""
        self.client.force_authenticate(user=self.user1)

        # Set as primary first time
        response1 = self.client.post(
            reverse('poi-asset-set-primary', kwargs={'pk': self.poi_asset1.id})
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Set as primary second time
        response2 = self.client.post(
            reverse('poi-asset-set-primary', kwargs={'pk': self.poi_asset1.id})
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['priority'], 'high')

        # Verify it's still high priority
        self.poi_asset1.refresh_from_db()
        self.assertEqual(self.poi_asset1.priority, 'high')

    def test_set_primary_unauthorized(self):
        """Test that non-member cannot set POI asset as primary"""
        self.client.force_authenticate(user=self.user2)

        response = self.client.post(
            reverse('poi-asset-set-primary', kwargs={'pk': self.poi_asset1.id})
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Not a member of the POI asset project group', response.data['detail'])

    def test_set_primary_not_found(self):
        """Test setting non-existent POI asset as primary"""
        self.client.force_authenticate(user=self.user1)

        response = self.client.post(
            reverse('poi-asset-set-primary', kwargs={'pk': 99999})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('POI Asset not found', response.data['detail'])

    def test_unset_primary_success(self):
        """Test unsetting a POI asset as primary successfully"""
        # First set as primary
        self.poi_asset1.priority = 'high'
        self.poi_asset1.save()

        self.client.force_authenticate(user=self.user1)

        response = self.client.post(
            reverse('poi-asset-unset-primary', kwargs={'pk': self.poi_asset1.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['priority'], 'normal')

        # Verify the asset was updated in the database
        self.poi_asset1.refresh_from_db()
        self.assertEqual(self.poi_asset1.priority, 'normal')

    def test_unset_primary_no_side_effects(self):
        """Test that unsetting primary does not affect other POI assets"""
        # Set poi_asset1 as primary
        self.poi_asset1.priority = 'high'
        self.poi_asset1.save()

        # Set poi_asset2 as high too (for testing purposes)
        self.poi_asset2.priority = 'high'
        self.poi_asset2.save()

        self.client.force_authenticate(user=self.user1)

        # Unset poi_asset1
        response = self.client.post(
            reverse('poi-asset-unset-primary', kwargs={'pk': self.poi_asset1.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['priority'], 'normal')

        # Verify poi_asset1 is now normal
        self.poi_asset1.refresh_from_db()
        self.assertEqual(self.poi_asset1.priority, 'normal')

        # Verify poi_asset2 is still high (no side effects)
        self.poi_asset2.refresh_from_db()
        self.assertEqual(self.poi_asset2.priority, 'high')

        # Verify poi_asset3 is still normal
        self.poi_asset3.refresh_from_db()
        self.assertEqual(self.poi_asset3.priority, 'normal')

    def test_unset_primary_unauthorized(self):
        """Test that non-member cannot unset POI asset as primary"""
        self.poi_asset1.priority = 'high'
        self.poi_asset1.save()

        self.client.force_authenticate(user=self.user2)

        response = self.client.post(
            reverse('poi-asset-unset-primary', kwargs={'pk': self.poi_asset1.id})
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Not a member of the POI asset project group', response.data['detail'])

    def test_unset_primary_not_found(self):
        """Test unsetting non-existent POI asset as primary"""
        self.client.force_authenticate(user=self.user1)

        response = self.client.post(
            reverse('poi-asset-unset-primary', kwargs={'pk': 99999})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('POI Asset not found', response.data['detail'])

    def test_unset_primary_already_normal(self):
        """Test unsetting a POI asset that is already normal priority"""
        # poi_asset1 is already normal priority from setUp
        self.client.force_authenticate(user=self.user1)

        response = self.client.post(
            reverse('poi-asset-unset-primary', kwargs={'pk': self.poi_asset1.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['priority'], 'normal')

        # Verify it's still normal
        self.poi_asset1.refresh_from_db()
        self.assertEqual(self.poi_asset1.priority, 'normal')

    def test_set_unset_primary_workflow(self):
        """Test complete workflow of setting and unsetting primary"""
        self.client.force_authenticate(user=self.user1)

        # Set poi_asset1 as primary
        response1 = self.client.post(
            reverse('poi-asset-set-primary', kwargs={'pk': self.poi_asset1.id})
        )
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data['priority'], 'high')

        # Set poi_asset2 as primary (should demote poi_asset1)
        response2 = self.client.post(
            reverse('poi-asset-set-primary', kwargs={'pk': self.poi_asset2.id})
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['priority'], 'high')

        # Verify poi_asset1 was demoted
        self.poi_asset1.refresh_from_db()
        self.assertEqual(self.poi_asset1.priority, 'normal')

        # Unset poi_asset2
        response3 = self.client.post(
            reverse('poi-asset-unset-primary', kwargs={'pk': self.poi_asset2.id})
        )
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.assertEqual(response3.data['priority'], 'normal')

        # Verify all are now normal
        self.poi_asset1.refresh_from_db()
        self.poi_asset2.refresh_from_db()
        self.poi_asset3.refresh_from_db()
        self.assertEqual(self.poi_asset1.priority, 'normal')
        self.assertEqual(self.poi_asset2.priority, 'normal')
        self.assertEqual(self.poi_asset3.priority, 'normal')

    def test_create_poi_asset_with_high_priority_demotes_others(self):
        """Test creating a POI asset with priority='high' demotes other high-priority assets"""
        # Set poi_asset1 as high priority
        self.poi_asset1.priority = 'high'
        self.poi_asset1.save()

        self.client.force_authenticate(user=self.user1)

        # Create new POI asset with priority='high'
        new_asset_data = {
            'poi_id': self.poi.id,
            'title': {'locales': {'en': 'New POI Asset'}},
            'description': {'locales': {'en': 'New POI Asset description'}},
            'type': 'image',
            'url': 'https://example.com/new_asset.jpg',
            'priority': 'high'
        }

        response = self.client.post(
            reverse('poi-asset-list-create'),
            new_asset_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['priority'], 'high')

        # Verify poi_asset1 was demoted
        self.poi_asset1.refresh_from_db()
        self.assertEqual(self.poi_asset1.priority, 'normal')

        # Verify other assets remain normal
        self.poi_asset2.refresh_from_db()
        self.poi_asset3.refresh_from_db()
        self.assertEqual(self.poi_asset2.priority, 'normal')
        self.assertEqual(self.poi_asset3.priority, 'normal')

    def test_create_poi_asset_with_normal_priority_no_side_effects(self):
        """Test creating a POI asset with priority='normal' doesn't affect other assets"""
        # Set poi_asset1 as high priority
        self.poi_asset1.priority = 'high'
        self.poi_asset1.save()

        self.client.force_authenticate(user=self.user1)

        # Create new POI asset with priority='normal' (default)
        new_asset_data = {
            'poi_id': self.poi.id,
            'title': {'locales': {'en': 'New POI Asset'}},
            'description': {'locales': {'en': 'New POI Asset description'}},
            'type': 'image',
            'url': 'https://example.com/new_asset.jpg',
            'priority': 'normal'
        }

        response = self.client.post(
            reverse('poi-asset-list-create'),
            new_asset_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['priority'], 'normal')

        # Verify poi_asset1 is still high priority
        self.poi_asset1.refresh_from_db()
        self.assertEqual(self.poi_asset1.priority, 'high')

    def test_update_poi_asset_to_high_priority_demotes_others(self):
        """Test updating a POI asset to priority='high' demotes other high-priority assets"""
        # Set poi_asset1 as high priority
        self.poi_asset1.priority = 'high'
        self.poi_asset1.save()

        self.client.force_authenticate(user=self.user1)

        # Update poi_asset2 to priority='high'
        update_data = {
            'priority': 'high'
        }

        response = self.client.patch(
            reverse('poi-asset-detail', kwargs={'pk': self.poi_asset2.id}),
            update_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['priority'], 'high')

        # Verify poi_asset2 is now high priority
        self.poi_asset2.refresh_from_db()
        self.assertEqual(self.poi_asset2.priority, 'high')

        # Verify poi_asset1 was demoted
        self.poi_asset1.refresh_from_db()
        self.assertEqual(self.poi_asset1.priority, 'normal')

        # Verify poi_asset3 remains normal
        self.poi_asset3.refresh_from_db()
        self.assertEqual(self.poi_asset3.priority, 'normal')

    def test_update_poi_asset_to_normal_priority_no_side_effects(self):
        """Test updating a POI asset to priority='normal' doesn't affect other assets"""
        # Set both poi_asset1 and poi_asset2 as high priority
        self.poi_asset1.priority = 'high'
        self.poi_asset1.save()
        self.poi_asset2.priority = 'high'
        self.poi_asset2.save()

        self.client.force_authenticate(user=self.user1)

        # Update poi_asset1 to priority='normal'
        update_data = {
            'priority': 'normal'
        }

        response = self.client.patch(
            reverse('poi-asset-detail', kwargs={'pk': self.poi_asset1.id}),
            update_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['priority'], 'normal')

        # Verify poi_asset1 is now normal
        self.poi_asset1.refresh_from_db()
        self.assertEqual(self.poi_asset1.priority, 'normal')

        # Verify poi_asset2 is still high priority (no side effects)
        self.poi_asset2.refresh_from_db()
        self.assertEqual(self.poi_asset2.priority, 'high')

    def test_update_poi_asset_other_fields_preserves_priority_logic(self):
        """Test updating other fields while setting priority='high' still demotes others"""
        # Set poi_asset1 as high priority
        self.poi_asset1.priority = 'high'
        self.poi_asset1.save()

        self.client.force_authenticate(user=self.user1)

        # Update poi_asset2 with new title and priority='high'
        update_data = {
            'title': {'locales': {'en': 'Updated Title'}},
            'priority': 'high'
        }

        response = self.client.patch(
            reverse('poi-asset-detail', kwargs={'pk': self.poi_asset2.id}),
            update_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['priority'], 'high')
        self.assertEqual(response.data['title']['locales']['en'], 'Updated Title')

        # Verify poi_asset2 is now high priority
        self.poi_asset2.refresh_from_db()
        self.assertEqual(self.poi_asset2.priority, 'high')

        # Verify poi_asset1 was demoted
        self.poi_asset1.refresh_from_db()
        self.assertEqual(self.poi_asset1.priority, 'normal')
