"""
URL configuration for eureka project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from .views import *
from .views.user_views import OIDCLoginView
from .views.project_views import (
    ProjectListCreateView, ProjectRetrieveUpdateDestroyView, ProjectMoveGroupView, ProjectPopulatedView, ProjectMembersView
)
from .views.public_views import PublicProjectListView, PublicProjectPopulatedView
from .views.tour_views import TourListCreateView, TourRetrieveUpdateView, PublishTourView, UnpublishTourView, PublishedTourView
from .views.asset_views import AssetListCreateView, AssetRetrieveUpdateDestroyView
from .views.poi_views import POIListCreateView, POIRetrieveUpdateDestroyView
from .views.poi_asset_views import POIAssetListCreateView, POIAssetRetrieveUpdateDestroyView, POIAssetSetPrimaryView, POIAssetUnsetPrimaryView
from .views.example_views import ExampleFileView

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Authentication & User Management
    
    path('api/auth/login', LoginView.as_view(), name='auth-login'),
    path('api/auth/oidc/login', OIDCLoginView.as_view(), name='auth-oidc-login'),
    path('api/auth/signup', SignupView.as_view(), name='auth-signup'),
    path('api/auth/logout', LogoutView.as_view(), name='auth-logout'),
    path('api/auth/me', CurrentUserView.as_view(), name='auth-me'),
    path('api/users', UserListView.as_view(), name='user-list'),

    # Group Management
    path('api/groups', GroupCreateView.as_view(), name='group-create'),
    path('api/groups/<int:pk>/members', GroupMemberListView.as_view(), name='group-member-list'),
    path('api/groups/<int:pk>/members/add', GroupMemberAddView.as_view(), name='group-member-add'),
    path('api/groups/<int:pk>/members/remove', GroupMemberRemoveView.as_view(), name='group-member-remove'),

    # Public Projects (Anonymous access with throttling)
    path('api/public/projects', PublicProjectListView.as_view(), name='public-project-list'),
    path('api/public/projects/<int:pk>/populated', PublicProjectPopulatedView.as_view(), name='public-project-populated'),

    # Projects
    path('api/projects', ProjectListCreateView.as_view(), name='project-list-create'),
    path('api/projects/<int:pk>', ProjectRetrieveUpdateDestroyView.as_view(), name='project-detail'),
    path('api/projects/<int:pk>/populated', ProjectPopulatedView.as_view(), name='project-populated'),
    path('api/projects/<int:pk>/move_group', ProjectMoveGroupView.as_view(), name='project-move-group'),
    path('api/projects/<int:pk>/members', ProjectMembersView.as_view(), name='project-members'),

    # Assets
    path('api/assets', AssetListCreateView.as_view(), name='asset-list-create'),
    path('api/assets/<int:pk>', AssetRetrieveUpdateDestroyView.as_view(), name='asset-detail'),

    # Tours
    path('api/tours', TourListCreateView.as_view(), name='tour-list-create'),
    path('api/tours/<int:pk>', TourRetrieveUpdateView.as_view(), name='tour-detail'),
    path('api/tours/<int:pk>/publish', PublishTourView.as_view(), name='tour-publish'),
    path('api/tours/<int:pk>/unpublish', UnpublishTourView.as_view(), name='tour-unpublish'),
    path('api/publishedTour/<int:pk>', PublishedTourView.as_view(), name='published-tour'),

    # POIs
    path('api/pois', POIListCreateView.as_view(), name='poi-list-create'),
    path('api/pois/<int:pk>', POIRetrieveUpdateDestroyView.as_view(), name='poi-detail'),

    # POI Assets
    path('api/poi-assets', POIAssetListCreateView.as_view(), name='poi-asset-list-create'),
    path('api/poi-assets/<int:pk>', POIAssetRetrieveUpdateDestroyView.as_view(), name='poi-asset-detail'),
    path('api/poi-assets/<int:pk>/set-primary', POIAssetSetPrimaryView.as_view(), name='poi-asset-set-primary'),
    path('api/poi-assets/<int:pk>/unset-primary', POIAssetUnsetPrimaryView.as_view(), name='poi-asset-unset-primary'),

    # Example Files
    path('api/examples/<path:file_path>', ExampleFileView.as_view(), name='example-file'),
]
