from factory.declarations import Sequence, PostGenerationMethodCall, LazyAttribute, Iterator, SubFactory, LazyFunction
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from eureka.models import Project, Asset, Tour, POI, AssetType
from eureka.models.poi_asset import POIAsset
from faker import Faker as FakerInstance
from decimal import Decimal

fake = FakerInstance()
User = get_user_model()

def to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: to_float(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_float(v) for v in value]
    return value

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    username = LazyFunction(lambda: fake.unique.user_name())
    email = LazyFunction(lambda: fake.unique.email())
    password = PostGenerationMethodCall('set_password', 'testpass123')
    name = LazyFunction(lambda: fake.name())

class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project
    
    title = LazyFunction(lambda: {
        'locales': {
            'en': fake.sentence(nb_words=3),
            'el': fake.sentence(nb_words=3)
        }
    })
    description = LazyFunction(lambda: {
        'locales': {
            'en': fake.text(max_nb_chars=200),
            'el': fake.text(max_nb_chars=200)
        }
    })
    group = LazyAttribute(lambda o: UserFactory().personal_group)


class AssetFactory(DjangoModelFactory):
    class Meta:
        model = Asset
    project = SubFactory(ProjectFactory)
    title = LazyFunction(lambda: {
        'locales': {
            'en': fake.sentence(nb_words=2),
            'el': fake.sentence(nb_words=2)
        }
    })
    description = LazyFunction(lambda: {
        'locales': {
            'en': fake.text(max_nb_chars=150),
            'el': fake.text(max_nb_chars=150)
        }
    })
    type = Iterator([AssetType.IMAGE, AssetType.VIDEO, AssetType.AUDIO, AssetType.TEXT, AssetType.MODEL3D])
    url = LazyFunction(lambda: {
        'locales': {
            'en': fake.url(),
            'el': fake.url()
        }
    })

class TourFactory(DjangoModelFactory):
    class Meta:
        model = Tour

    project = SubFactory(ProjectFactory)
    title = LazyFunction(lambda: {
        'locales': {
            'en': fake.sentence(nb_words=2),
            'el': fake.sentence(nb_words=2)
        }
    })
    description = LazyFunction(lambda: {
        'locales': {
            'en': fake.text(max_nb_chars=200),
            'el': fake.text(max_nb_chars=200)
        }
    })
    is_public = False
    # Note: bounding_box is automatically calculated via update_bounding_box() method
    # when POIs are added to the tour

class POIFactory(DjangoModelFactory):
    class Meta:
        model = POI
    tour = SubFactory(TourFactory)
    title = LazyFunction(lambda: {
        'locales': {
            'en': fake.sentence(nb_words=2),
            'el': fake.sentence(nb_words=2)
        }
    })
    description = LazyFunction(lambda: {
        'locales': {
            'en': fake.text(max_nb_chars=150),
            'el': fake.text(max_nb_chars=150)
        }
    })
    coordinates = LazyFunction(lambda: to_float({
        'lat': fake.latitude(),
        'long': fake.longitude()
    }))
    radius = 20
    external_links = LazyFunction(lambda: {
        'locales': {
            'en': [
                {
                    'title': fake.sentence(nb_words=2),
                    'url': fake.url(),
                    'type': 'blog'
                }
            ],
            'el': [
                {
                    'title': fake.sentence(nb_words=2),
                    'url': fake.url(),
                    'type': 'quiz'
                }
            ]
        }
    })
    order = Sequence(lambda n: n + 1)

# POIAssetFactory for POI assets
class POIAssetFactory(DjangoModelFactory):
    class Meta:
        model = POIAsset
    poi = SubFactory(POIFactory)
    source_asset = SubFactory(AssetFactory)
    title = LazyFunction(lambda: {
        'locales': {
            'en': fake.sentence(nb_words=2),
            'el': fake.sentence(nb_words=2)
        }
    })
    description = LazyFunction(lambda: {
        'locales': {
            'en': fake.text(max_nb_chars=150),
            'el': fake.text(max_nb_chars=150)
        }
    })
    type = Iterator(['image', 'video', 'audio', 'text', 'model3d'])
    url = LazyFunction(lambda: {
        'locales': {
            'en': fake.url(),
            'el': fake.url()
        }
    })
    priority = Iterator(['normal', 'high'])
    view_in_ar = False
    ar_placement = Iterator(['free', 'ground'])
    linked_asset = LazyAttribute(lambda obj: {
        'locales': {
            'en': {
                'title': f'{fake.sentence(nb_words=2)} - Audio Guide',
                'url': f'https://example.com/audio/{fake.uuid4()}.mp3'
            },
            'el': {
                'title': f'{fake.sentence(nb_words=2)} - Ηχητικός Οδηγός',
                'url': f'https://example.com/audio/{fake.uuid4()}.mp3'
            }
        }
    } if obj.type == 'model3d' else None)