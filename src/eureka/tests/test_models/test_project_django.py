from django.test import TestCase
from django.contrib.auth import get_user_model
from eureka.models import Project

User = get_user_model()

class TestProject(TestCase):
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            login='testuser',
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
        self.assertIsNone(project.description)
        
        # Test string representation
        str_repr = str(project)
        self.assertIn('Test Project', str_repr)
        self.assertIn(self.user.personal_group.name, str_repr) 