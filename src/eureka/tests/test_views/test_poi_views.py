from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from concurrent.futures import ThreadPoolExecutor, as_completed
from eureka.models import POI, Project, Tour


User = get_user_model()


class TestPOIConcurrentCreation(TransactionTestCase):
    """Test concurrent POI creation to verify race condition fix"""

    def setUp(self):
        """Set up test data"""
        # Create user with personal group
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )

        # Create project
        self.project = Project.objects.create(
            title={'locales': {'en': 'Test Project'}},
            description={'locales': {'en': 'A test project'}},
            group=self.user.personal_group,
            locales=['en']
        )

        # Create tour
        self.tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour'}},
            description={'locales': {'en': 'A test tour'}},
            locales=['en'],
            distance_meters=1000,
            duration_minutes=30
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_concurrent_poi_creation_no_duplicate_orders(self):
        """
        Test that concurrent POI creation doesn't result in duplicate order values.
        This verifies the race condition fix using select_for_update().
        """
        num_concurrent_requests = 10

        def create_poi(index):
            """Helper function to create a POI via API"""
            client = APIClient()
            client.force_authenticate(user=self.user)

            data = {
                'tour_id': self.tour.id,
                'title': {'locales': {'en': f'POI {index}'}},
                'description': {'locales': {'en': f'Description {index}'}},
                'coordinates': {'lat': 37.9838, 'long': 23.7275}
            }

            response = client.post('/api/pois', data, format='json')
            return response.status_code, response.data if response.status_code == 201 else None

        # Execute concurrent POI creations
        with ThreadPoolExecutor(max_workers=num_concurrent_requests) as executor:
            futures = [executor.submit(create_poi, i) for i in range(num_concurrent_requests)]
            results = [future.result() for future in as_completed(futures)]

        # Verify all requests succeeded
        successful_creates = [r for r in results if r[0] == 201]
        self.assertEqual(len(successful_creates), num_concurrent_requests,
                        "All concurrent POI creation requests should succeed")

        # Verify no duplicate order values
        pois = POI.objects.filter(tour=self.tour).order_by('order')
        order_values = [poi.order for poi in pois]

        # Check that all order values are unique
        self.assertEqual(len(order_values), len(set(order_values)),
                        "Order values should be unique (no duplicates)")

        # Check that order values are sequential starting from 1
        expected_orders = list(range(1, num_concurrent_requests + 1))
        self.assertEqual(sorted(order_values), expected_orders,
                        f"Order values should be sequential from 1 to {num_concurrent_requests}")

    def test_sequential_poi_creation_maintains_order(self):
        """
        Test that sequential POI creation still works correctly.
        This is a baseline test to ensure the fix doesn't break normal operation.
        """
        num_pois = 5

        for i in range(num_pois):
            data = {
                'tour_id': self.tour.id,
                'title': {'locales': {'en': f'POI {i}'}},
                'description': {'locales': {'en': f'Description {i}'}},
                'coordinates': {'lat': 37.9838, 'long': 23.7275}
            }

            response = self.client.post('/api/pois', data, format='json')
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data['order'], i + 1)

        # Verify all POIs have correct sequential orders
        pois = POI.objects.filter(tour=self.tour).order_by('order')
        order_values = [poi.order for poi in pois]
        expected_orders = list(range(1, num_pois + 1))

        self.assertEqual(order_values, expected_orders,
                        f"Order values should be sequential from 1 to {num_pois}")


class TestPOIDeletion(TransactionTestCase):
    """Test POI deletion and order updates"""

    def setUp(self):
        """Set up test data"""
        # Create user with personal group
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User'
        )

        # Create project
        self.project = Project.objects.create(
            title={'locales': {'en': 'Test Project'}},
            description={'locales': {'en': 'A test project'}},
            group=self.user.personal_group,
            locales=['en']
        )

        # Create tour
        self.tour = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour'}},
            description={'locales': {'en': 'A test tour'}},
            locales=['en'],
            distance_meters=1000,
            duration_minutes=30
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_delete_poi_updates_subsequent_orders(self):
        """
        Test that when a POI is deleted, all subsequent POIs in the same tour
        have their order decremented by 1.
        """
        # Create 5 POIs with sequential orders
        pois = []
        for i in range(1, 6):
            poi = POI.objects.create(
                tour=self.tour,
                title={'locales': {'en': f'POI {i}'}},
                description={'locales': {'en': f'Description {i}'}},
                coordinates={'lat': 37.9838, 'long': 23.7275},
                order=i
            )
            pois.append(poi)

        # Verify initial orders
        initial_orders = [poi.order for poi in POI.objects.filter(tour=self.tour).order_by('order')]
        self.assertEqual(initial_orders, [1, 2, 3, 4, 5])

        # Delete the middle POI (order=3)
        response = self.client.delete(f'/api/pois/{pois[2].id}')
        self.assertEqual(response.status_code, 204)

        # Verify POI was deleted
        self.assertFalse(POI.objects.filter(id=pois[2].id).exists())

        # Verify remaining POIs have correct orders
        remaining_pois = POI.objects.filter(tour=self.tour).order_by('order')
        remaining_orders = [poi.order for poi in remaining_pois]

        # Orders should be: 1, 2, 3, 4 (the original 4 and 5 became 3 and 4)
        self.assertEqual(remaining_orders, [1, 2, 3, 4],
                        "Subsequent POIs should have their orders decremented after deletion")

        # Verify the correct POIs remain
        remaining_titles = [poi.title['locales']['en'] for poi in remaining_pois]
        self.assertEqual(remaining_titles, ['POI 1', 'POI 2', 'POI 4', 'POI 5'])

    def test_delete_first_poi_updates_all_orders(self):
        """
        Test that deleting the first POI updates all subsequent POIs.
        """
        # Create 4 POIs
        pois = []
        for i in range(1, 5):
            poi = POI.objects.create(
                tour=self.tour,
                title={'locales': {'en': f'POI {i}'}},
                description={'locales': {'en': f'Description {i}'}},
                coordinates={'lat': 37.9838, 'long': 23.7275},
                order=i
            )
            pois.append(poi)

        # Delete the first POI (order=1)
        response = self.client.delete(f'/api/pois/{pois[0].id}')
        self.assertEqual(response.status_code, 204)

        # Verify remaining POIs have correct orders starting from 1
        remaining_pois = POI.objects.filter(tour=self.tour).order_by('order')
        remaining_orders = [poi.order for poi in remaining_pois]

        self.assertEqual(remaining_orders, [1, 2, 3],
                        "All POIs should be decremented when first POI is deleted")

        remaining_titles = [poi.title['locales']['en'] for poi in remaining_pois]
        self.assertEqual(remaining_titles, ['POI 2', 'POI 3', 'POI 4'])

    def test_delete_last_poi_no_order_updates(self):
        """
        Test that deleting the last POI doesn't affect other POI orders.
        """
        # Create 3 POIs
        pois = []
        for i in range(1, 4):
            poi = POI.objects.create(
                tour=self.tour,
                title={'locales': {'en': f'POI {i}'}},
                description={'locales': {'en': f'Description {i}'}},
                coordinates={'lat': 37.9838, 'long': 23.7275},
                order=i
            )
            pois.append(poi)

        # Delete the last POI (order=3)
        response = self.client.delete(f'/api/pois/{pois[2].id}')
        self.assertEqual(response.status_code, 204)

        # Verify remaining POIs have unchanged orders
        remaining_pois = POI.objects.filter(tour=self.tour).order_by('order')
        remaining_orders = [poi.order for poi in remaining_pois]

        self.assertEqual(remaining_orders, [1, 2],
                        "Previous POI orders should remain unchanged when last POI is deleted")

        remaining_titles = [poi.title['locales']['en'] for poi in remaining_pois]
        self.assertEqual(remaining_titles, ['POI 1', 'POI 2'])

    def test_delete_poi_only_affects_same_tour(self):
        """
        Test that deleting a POI only affects POIs in the same tour,
        not POIs in other tours.
        """
        # Create another tour
        tour2 = Tour.objects.create(
            project=self.project,
            title={'locales': {'en': 'Test Tour 2'}},
            description={'locales': {'en': 'Another test tour'}},
            locales=['en'],
            distance_meters=2000,
            duration_minutes=45
        )

        # Create POIs for both tours
        tour1_pois = []
        tour2_pois = []

        for i in range(1, 4):
            poi1 = POI.objects.create(
                tour=self.tour,
                title={'locales': {'en': f'Tour1 POI {i}'}},
                coordinates={'lat': 37.9838, 'long': 23.7275},
                order=i
            )
            tour1_pois.append(poi1)

            poi2 = POI.objects.create(
                tour=tour2,
                title={'locales': {'en': f'Tour2 POI {i}'}},
                coordinates={'lat': 37.9840, 'long': 23.7280},
                order=i
            )
            tour2_pois.append(poi2)

        # Delete a POI from tour1 (order=2)
        response = self.client.delete(f'/api/pois/{tour1_pois[1].id}')
        self.assertEqual(response.status_code, 204)

        # Verify tour1 POIs are updated
        tour1_orders = [poi.order for poi in POI.objects.filter(tour=self.tour).order_by('order')]
        self.assertEqual(tour1_orders, [1, 2])

        # Verify tour2 POIs are NOT affected
        tour2_orders = [poi.order for poi in POI.objects.filter(tour=tour2).order_by('order')]
        self.assertEqual(tour2_orders, [1, 2, 3],
                        "POIs in other tours should not be affected by deletion")

    def test_delete_only_poi_in_tour(self):
        """
        Test that deleting the only POI in a tour works correctly.
        """
        # Create a single POI
        poi = POI.objects.create(
            tour=self.tour,
            title={'locales': {'en': 'Only POI'}},
            coordinates={'lat': 37.9838, 'long': 23.7275},
            order=1
        )

        # Delete the POI
        response = self.client.delete(f'/api/pois/{poi.id}')
        self.assertEqual(response.status_code, 204)

        # Verify no POIs remain for this tour
        remaining_count = POI.objects.filter(tour=self.tour).count()
        self.assertEqual(remaining_count, 0,
                        "No POIs should remain after deleting the only POI")
