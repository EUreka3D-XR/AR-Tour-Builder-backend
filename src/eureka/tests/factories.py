from factory.declarations import Sequence, PostGenerationMethodCall, LazyAttribute, Iterator, SubFactory
from factory.faker import Faker
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from eureka.models import Project, Asset, Tour, POI, AssetType

User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    login = Sequence(lambda n: f'user{n}')
    email = Sequence(lambda n: f'user{n}@example.com')
    password = PostGenerationMethodCall('set_password', 'testpass123')
    name = Faker('name')

class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project
    
    title = LazyAttribute(lambda o: {
        'locales': {
            'en': Faker('sentence', nb_words=3).evaluate(o, None, extra={}),
            'el': Faker('sentence', nb_words=3).evaluate(o, None, extra={})
        }
    })
    description = LazyAttribute(lambda o: {
        'locales': {
            'en': Faker('text', max_nb_chars=200).evaluate(o, None, extra={}),
            'el': Faker('text', max_nb_chars=200).evaluate(o, None, extra={})
        }
    })
    group = LazyAttribute(lambda o: UserFactory().personal_group)

class AssetFactory(DjangoModelFactory):
    class Meta:
        model = Asset
    
    project = SubFactory(ProjectFactory)
    title = LazyAttribute(lambda o: {
        'locales': {
            'en': Faker('sentence', nb_words=2).evaluate(o, None, extra={}),
            'el': Faker('sentence', nb_words=2).evaluate(o, None, extra={})
        }
    })
    description = LazyAttribute(lambda o: {
        'locales': {
            'en': Faker('text', max_nb_chars=150).evaluate(o, None, extra={}),
            'el': Faker('text', max_nb_chars=150).evaluate(o, None, extra={})
        }
    })
    type = Iterator([AssetType.IMAGE, AssetType.VIDEO, AssetType.AUDIO, AssetType.TEXT])
    url = Faker('url')

class TourFactory(DjangoModelFactory):
    class Meta:
        model = Tour
    
    project = SubFactory(ProjectFactory)
    title = LazyAttribute(lambda o: {
        'locales': {
            'en': Faker('sentence', nb_words=2).evaluate(o, None, extra={}),
            'el': Faker('sentence', nb_words=2).evaluate(o, None, extra={})
        }
    })
    description = LazyAttribute(lambda o: {
        'locales': {
            'en': Faker('text', max_nb_chars=200).evaluate(o, None, extra={}),
            'el': Faker('text', max_nb_chars=200).evaluate(o, None, extra={})
        }
    })
    is_public = False

class POIFactory(DjangoModelFactory):
    class Meta:
        model = POI
    
    tour = SubFactory(TourFactory)
    name = LazyAttribute(lambda o: {
        'locales': {
            'en': Faker('sentence', nb_words=2).evaluate(o, None, extra={}),
            'el': Faker('sentence', nb_words=2).evaluate(o, None, extra={})
        }
    })
    description = LazyAttribute(lambda o: {
        'locales': {
            'en': Faker('text', max_nb_chars=150).evaluate(o, None, extra={}),
            'el': Faker('text', max_nb_chars=150).evaluate(o, None, extra={})
        }
    })
    latitude = Faker('latitude')
    longitude = Faker('longitude')
    order = Sequence(lambda n: n + 1) 