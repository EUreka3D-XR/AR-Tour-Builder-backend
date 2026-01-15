import pytest  # type: ignore

@pytest.fixture
def user():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(  # type: ignore
        username='testuser',
        email='test@example.com',
        password='testpass123',
        name='Test User'
    )
    return user

@pytest.fixture
def another_user():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(  # type: ignore
        username='anotheruser',
        email='another@example.com',
        password='testpass123',
        name='Another User'
    )
    return user

@pytest.fixture
def project(user):
    from eureka.models import Project
    return Project.objects.create(  # type: ignore
        title='Test Project',
        description='A test project',
        group=user.personal_group,
        locales=['en', 'fr', 'it']
    )

@pytest.fixture
def asset(project):
    from eureka.models import Asset, AssetType
    return Asset.objects.create(  # type: ignore
        project=project,
        title={'locales': {'en': 'Test Asset', 'el': 'Δοκιμαστικό Περιεχόμενο'}},
        description={'locales': {'en': 'A test asset', 'el': 'Ένα δοκιμαστικό περιεχόμενο'}},
        type=AssetType.IMAGE,
        url='/test/path/image.jpg'
    )

@pytest.fixture
def tour(project):
    from eureka.models import Tour
    return Tour.objects.create(  # type: ignore
        project=project,
        title={'locales': {'en': 'Test Tour', 'el': 'Δοκιμαστική Περιήγηση'}},
        description={'locales': {'en': 'A test tour', 'el': 'Μια δοκιμαστική περιήγηση'}},
        locales=['en', 'fr', 'it'],
        distance_meters=1234,
        duration_minutes=56
    )

@pytest.fixture
def poi(tour):
    from eureka.models import POI
    return POI.objects.create(  # type: ignore
        tour=tour,
        title={'locales': {'en': 'Test POI', 'el': 'Δοκιμαστικό Σημείο'}},
        description={'locales': {'en': 'A test POI', 'el': 'Ένα δοκιμαστικό σημείο'}},
        coordinates={'lat': 37.9838, 'long': 23.7275},
        order=1
    )

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()