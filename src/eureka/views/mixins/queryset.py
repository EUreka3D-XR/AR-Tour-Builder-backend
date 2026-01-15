"""
Mixins for reusable queryset optimization patterns.
These mixins provide common prefetch and annotation logic to avoid code duplication.
"""
from django.db.models import Count, Q, Prefetch
from ...models.tour import Tour
from ...models.poi import POI

class TourPrefetchMixin:
    @staticmethod
    def get_tour_prefetch():
        return Prefetch(
            'tours',
            queryset=Tour.objects.annotate(
                total_pois=Count('pois', distinct=True),
                total_assets=Count('pois__assets', distinct=True)
            )
        )

class POIPrefetchMixin:
    @staticmethod
    def get_poi_prefetch():
        return Prefetch(
            'pois',
            queryset=POI.objects.prefetch_related('assets').annotate(
                stat_image=Count('assets', filter=Q(assets__type__istartswith='image') | Q(assets__type='image')),
                stat_video=Count('assets', filter=Q(assets__type__istartswith='video') | Q(assets__type='video')),
                stat_audio=Count('assets', filter=Q(assets__type__istartswith='audio') | Q(assets__type='audio')),
                stat_model3d=Count('assets', filter=Q(assets__type__istartswith='model') | Q(assets__type='model3d')),
                stat_text=Count('assets', filter=Q(assets__type__istartswith='text') | Q(assets__type='text'))
            ).order_by('order')
        )
