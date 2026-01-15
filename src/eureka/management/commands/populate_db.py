from django.core.management.base import BaseCommand
from eureka.tests.factories import (
    UserFactory, ProjectFactory, TourFactory, POIFactory, 
    AssetFactory, POIAssetFactory
)

class Command(BaseCommand):
    help = 'Populate database with mock data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            from django.contrib.auth import get_user_model
            from eureka.models import Project, Tour, POI, Asset
            from eureka.models.poi_asset import POIAsset
            User = get_user_model()
            
            POIAsset.objects.all().delete()
            Asset.objects.all().delete()
            POI.objects.all().delete()
            Tour.objects.all().delete()
            Project.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS('Data cleared!'))

        self.stdout.write('Creating mock data...')
        
        # Create users
        user1 = UserFactory(email='demo@example.com', username='demo')
        user2 = UserFactory(email='user2@example.com', username='user2')
        
        # Create projects
        project1 = ProjectFactory(
            title={'locales': {'en': 'Paris Tour', 'fr': 'Visite de Paris', 'it': 'Tour di Parigi'}},
            description={'locales': {'en': 'Explore historic Paris', 'fr': 'Découvrez Paris historique', 'it': 'Esplora la Parigi storica'}},
            locales=['en', 'fr', 'it'],
            group=user1.personal_group
        )
        
        project2 = ProjectFactory(
            title={'locales': {'en': 'Rome Tour', 'it': 'Tour di Roma'}},
            description={'locales': {'en': 'Discover ancient Rome', 'it': 'Scopri la Roma antica'}},
            locales=['en', 'it'],
            group=user1.personal_group
        )
        
        # Create tours for project 1
        tour1 = TourFactory(
            project=project1,
            title={'locales': {'en': 'Historic Paris', 'fr': 'Paris Historique', 'it': 'Parigi Storica'}},
            description={'locales': {'en': 'A walk through history', 'fr': 'Une promenade à travers l\'histoire', 'it': 'Una passeggiata nella storia'}},
            locales=['en', 'fr', 'it'],
            distance_meters=5000,
            duration_minutes=120
        )
        
        tour2 = TourFactory(
            project=project1,
            title={'locales': {'en': 'Modern Paris', 'fr': 'Paris Moderne', 'it': 'Parigi Moderna'}},
            description={'locales': {'en': 'Contemporary art and architecture', 'fr': 'Art et architecture contemporains', 'it': 'Arte e architettura contemporanea'}},
            locales=['en', 'fr', 'it'],
            distance_meters=3000,
            duration_minutes=90
        )
        
        # Create POIs for tour 1
        poi1 = POIFactory(
            tour=tour1,
            title={'locales': {'en': 'Eiffel Tower', 'fr': 'Tour Eiffel', 'it': 'Torre Eiffel'}},
            description={'locales': {'en': 'Iconic iron tower', 'fr': 'Tour emblématique en fer', 'it': 'Torre iconica in ferro'}},
            order=1
        )
        
        poi2 = POIFactory(
            tour=tour1,
            title={'locales': {'en': 'Louvre Museum', 'fr': 'Musée du Louvre', 'it': 'Museo del Louvre'}},
            description={'locales': {'en': 'World famous museum', 'fr': 'Musée de renommée mondiale', 'it': 'Museo di fama mondiale'}},
            order=2
        )
        
        poi3 = POIFactory(
            tour=tour1,
            title={'locales': {'en': 'Notre-Dame', 'fr': 'Notre-Dame', 'it': 'Notre-Dame'}},
            description={'locales': {'en': 'Gothic cathedral', 'fr': 'Cathédrale gothique', 'it': 'Cattedrale gotica'}},
            order=3
        )
        
        # Create POIs for tour 2
        poi4 = POIFactory(
            tour=tour2,
            title={'locales': {'en': 'Centre Pompidou', 'fr': 'Centre Pompidou', 'it': 'Centro Pompidou'}},
            description={'locales': {'en': 'Modern art museum', 'fr': 'Musée d\'art moderne', 'it': 'Museo di arte moderna'}},
            order=1
        )
        
        # Create project assets
        asset1 = AssetFactory(
            project=project1,
            title={'locales': {'en': 'Paris Map', 'fr': 'Carte de Paris', 'it': 'Mappa di Parigi'}},
            description={'locales': {'en': 'Interactive city map', 'fr': 'Carte interactive de la ville', 'it': 'Mappa interattiva della città'}},
            url={'locales': {'en': 'https://example.com/map.jpg', 'fr': 'https://example.com/map.jpg', 'it': 'https://example.com/map.jpg'}},
            type='image'
        )
        
        asset2 = AssetFactory(
            project=project1,
            title={'locales': {'en': 'Audio Guide', 'fr': 'Guide Audio', 'it': 'Guida Audio'}},
            url={'locales': {'en': 'https://example.com/audio.mp3', 'fr': 'https://example.com/audio.mp3', 'it': 'https://example.com/audio.mp3'}},
            type='audio'
        )
        
        # Create POI assets
        poi_asset1 = POIAssetFactory(
            poi=poi1,
            title={'locales': {'en': 'Eiffel Tower Photo', 'fr': 'Photo Tour Eiffel', 'it': 'Foto Torre Eiffel'}},
            description={'locales': {'en': 'Stunning view from below', 'fr': 'Vue imprenable d\'en bas', 'it': 'Vista mozzafiato dal basso'}},
            url={'locales': {'en': 'https://example.com/eiffel-en.jpg', 'fr': 'https://example.com/eiffel-fr.jpg', 'it': 'https://example.com/eiffel-it.jpg'}},
            type='image',
            priority='high',
            view_in_ar=True
        )
        
        poi_asset2 = POIAssetFactory(
            poi=poi1,
            title={'locales': {'en': 'History Video', 'fr': 'Vidéo Historique', 'it': 'Video Storico'}},
            url={'locales': {'en': 'https://example.com/history-en.mp4', 'fr': 'https://example.com/history-fr.mp4', 'it': 'https://example.com/history-it.mp4'}},
            type='video',
            priority='normal',
            view_in_ar=False
        )
        
        poi_asset3 = POIAssetFactory(
            poi=poi2,
            title={'locales': {'en': 'Louvre Entrance', 'fr': 'Entrée du Louvre', 'it': 'Ingresso del Louvre'}},
            description={'locales': {'en': 'Main entrance photo', 'fr': 'Photo de l\'entrée principale', 'it': 'Foto dell\'ingresso principale'}},
            url={'locales': {'en': 'https://example.com/louvre-en.jpg', 'fr': 'https://example.com/louvre-fr.jpg', 'it': 'https://example.com/louvre-it.jpg'}},
            type='image',
            priority='high',
            view_in_ar=True
        )
        
        poi_asset4 = POIAssetFactory(
            poi=poi3,
            title={'locales': {'en': 'Cathedral Interior', 'fr': 'Intérieur de la Cathédrale', 'it': 'Interno della Cattedrale'}},
            url={'locales': {'en': 'https://example.com/notre-dame-en.jpg', 'fr': 'https://example.com/notre-dame-fr.jpg', 'it': 'https://example.com/notre-dame-it.jpg'}},
            type='image',
            priority='normal',
            view_in_ar=False
        )
        
        poi_asset5 = POIAssetFactory(
            poi=poi4,
            title={'locales': {'en': 'Modern Art', 'fr': 'Art Moderne', 'it': 'Arte Moderna'}},
            url={'locales': {'en': 'https://example.com/pompidou-en.jpg', 'fr': 'https://example.com/pompidou-fr.jpg', 'it': 'https://example.com/pompidou-it.jpg'}},
            type='image',
            priority='high',
            view_in_ar=True
        )
        
        # Create tour for project 2
        tour3 = TourFactory(
            project=project2,
            title={'locales': {'en': 'Ancient Rome', 'it': 'Roma Antica'}},
            description={'locales': {'en': 'Visit ancient landmarks', 'it': 'Visita i monumenti antichi'}},
            locales=['en', 'it'],
            distance_meters=4000,
            duration_minutes=100
        )
        
        poi5 = POIFactory(
            tour=tour3,
            title={'locales': {'en': 'Colosseum', 'it': 'Colosseo'}},
            description={'locales': {'en': 'Ancient amphitheater', 'it': 'Anfiteatro antico'}},
            order=1
        )
        
        poi_asset6 = POIAssetFactory(
            poi=poi5,
            title={'locales': {'en': 'Colosseum View', 'it': 'Vista del Colosseo'}},
            url={'locales': {'en': 'https://example.com/colosseum-en.jpg', 'it': 'https://example.com/colosseum-it.jpg'}},
            type='image',
            priority='high',
            view_in_ar=True
        )
        
        # Assign all superusers to all user groups (personal groups)
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        User = get_user_model()

        superusers = User.objects.filter(is_superuser=True)
        all_groups = Group.objects.all()

        for superuser in superusers:
            existing_group_ids = set(superuser.groups.values_list('id', flat=True))
            new_groups = [group for group in all_groups if group.id not in existing_group_ids]
            if new_groups:
                superuser.groups.add(*new_groups)
            self.stdout.write(f'Assigned superuser {superuser.username} to all {all_groups.count()} groups')

        self.stdout.write(self.style.SUCCESS('\n=== Mock data created successfully! ===\n'))
        self.stdout.write(f'Users: {user1.email}, {user2.email}')
        self.stdout.write(f'Password for all users: testpass123')
        self.stdout.write(f'\nProjects: {project1.id} (Paris), {project2.id} (Rome)')
        self.stdout.write(f'Tours: {tour1.id} (Historic Paris), {tour2.id} (Modern Paris), {tour3.id} (Ancient Rome)')
        self.stdout.write(f'POIs: {poi1.id}, {poi2.id}, {poi3.id}, {poi4.id}, {poi5.id}')
        self.stdout.write(f'Project Assets: {asset1.id}, {asset2.id}')
        self.stdout.write(f'POI Assets: {poi_asset1.id}, {poi_asset2.id}, {poi_asset3.id}, {poi_asset4.id}, {poi_asset5.id}, {poi_asset6.id}')
        self.stdout.write(self.style.SUCCESS('\nYou can now test the API with these data!'))
        self.stdout.write(self.style.WARNING('\nTest the locale parameter:'))
        self.stdout.write(f'  Without locale: GET /api/poi-assets/{poi_asset1.id}/')
        self.stdout.write(f'  With locale:    GET /api/poi-assets/{poi_asset1.id}/?locale=en')
        self.stdout.write(f'  With locale:    GET /api/poi-assets/{poi_asset1.id}/?locale=fr')
