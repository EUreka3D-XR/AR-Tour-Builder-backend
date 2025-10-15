from .user_views import UserListView, LoginView, SignupView, CurrentUserView
from .group_views import GroupCreateView, GroupMemberAddView, GroupMemberRemoveView
from .project_views import (
    ProjectListCreateView, ProjectRetrieveUpdateDestroyView, ProjectMoveGroupView
)
from .tour_views import TourListCreateView, TourRetrieveUpdateView
from .poi_views import POICreateView, POIRetrieveUpdateDestroyView