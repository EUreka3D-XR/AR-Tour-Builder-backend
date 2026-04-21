from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class TestProjectMemberIntegration(TestCase):
    """
    Integration tests for project member management workflow.
    Verifies that each project gets its own group on creation and that
    members can be added/removed per project independently.
    """

    def setUp(self):
        self.client = APIClient()

        for user_data in [
            {'username': 'curator', 'email': 'curator@example.com', 'password': 'pass123', 'name': 'Curator'},
            {'username': 'alice', 'email': 'alice@example.com', 'password': 'pass123', 'name': 'Alice'},
            {'username': 'bob', 'email': 'bob@example.com', 'password': 'pass123', 'name': 'Bob'},
        ]:
            self.client.post('/api/auth/signup', user_data, format='json')

        response = self.client.post('/api/auth/login', {'login': 'curator@example.com', 'password': 'pass123'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")

    def _create_project(self, title):
        return self.client.post('/api/projects', {'title': title}, format='json')

    def test_project_creation_auto_creates_group_and_adds_creator(self):
        """Creating a project should auto-create a unique group with the creator as member."""
        response = self._create_project('Project A')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project_id = response.data['id']

        response = self.client.get(f'/api/projects/{project_id}/members')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = [m['username'] for m in response.data]
        self.assertIn('curator', usernames)

    def test_two_projects_have_different_groups(self):
        """Each project should have its own isolated group."""
        r1 = self._create_project('Project A')
        r2 = self._create_project('Project B')
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)

        self.assertNotEqual(r1.data['group'], r2.data['group'])

    def test_adding_member_to_one_project_does_not_affect_other(self):
        """Adding a member to project A should not give them access to project B."""
        r1 = self._create_project('Project A')
        r2 = self._create_project('Project B')
        project_a_id = r1.data['id']
        project_b_id = r2.data['id']

        response = self.client.post(
            f'/api/projects/{project_a_id}/members/add',
            {'user_identifier': 'alice'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f'/api/projects/{project_a_id}/members')
        self.assertIn('alice', [m['username'] for m in response.data])

        response = self.client.get(f'/api/projects/{project_b_id}/members')
        self.assertNotIn('alice', [m['username'] for m in response.data])

    def test_add_member_by_email(self):
        """Members can be added using email as identifier."""
        r = self._create_project('Project A')
        project_id = r.data['id']

        response = self.client.post(
            f'/api/projects/{project_id}/members/add',
            {'user_identifier': 'alice@example.com'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f'/api/projects/{project_id}/members')
        self.assertIn('alice', [m['username'] for m in response.data])

    def test_add_duplicate_member_returns_400(self):
        """Adding an already-existing member should return 400."""
        r = self._create_project('Project A')
        project_id = r.data['id']

        self.client.post(f'/api/projects/{project_id}/members/add', {'user_identifier': 'alice'}, format='json')
        response = self.client.post(f'/api/projects/{project_id}/members/add', {'user_identifier': 'alice'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_member(self):
        """A member can be removed from a project."""
        r = self._create_project('Project A')
        project_id = r.data['id']

        self.client.post(f'/api/projects/{project_id}/members/add', {'user_identifier': 'alice'}, format='json')
        response = self.client.post(f'/api/projects/{project_id}/members/remove', {'user_identifier': 'alice'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(f'/api/projects/{project_id}/members')
        self.assertNotIn('alice', [m['username'] for m in response.data])

    def test_remove_nonmember_returns_400(self):
        """Removing a user who is not a member should return 400."""
        r = self._create_project('Project A')
        project_id = r.data['id']

        response = self.client.post(f'/api/projects/{project_id}/members/remove', {'user_identifier': 'alice'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_member_cannot_add_to_project(self):
        """A user not in the project cannot add members to it."""
        r = self._create_project('Project A')
        project_id = r.data['id']

        response = self.client.post('/api/auth/login', {'login': 'alice@example.com', 'password': 'pass123'}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")

        response = self.client.post(f'/api/projects/{project_id}/members/add', {'user_identifier': 'bob'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
