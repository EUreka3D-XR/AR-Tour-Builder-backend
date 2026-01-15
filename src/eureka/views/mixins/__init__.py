"""
View mixins for reusable functionality across views.
"""
from .locale import LocaleContextMixin
from .queryset import TourPrefetchMixin, POIPrefetchMixin
from .permission import POIAssetPermissionMixin

__all__ = [
    'LocaleContextMixin',
    'TourPrefetchMixin',
    'POIPrefetchMixin',
    'POIAssetPermissionMixin',
]
