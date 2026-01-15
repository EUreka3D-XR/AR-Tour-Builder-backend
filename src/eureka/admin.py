# src/eureka/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django import forms
from .models.user import User
from .models.project import Project
from .models.asset import Asset
from .models.tour import Tour
from .models.poi import POI
from .models.poi_asset import POIAsset

# Custom UserChangeForm for editing an existing user
class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        # Important: Do NOT include 'password' here if you want Django's default 'change password' link
        # The BaseUserAdmin's fieldsets handle how the password field is displayed (as a link).
        fields = ('username', 'email', 'name', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')

    # You generally don't need to override save() for password hashing here.
    # The default behavior of UserChangeForm combined with BaseUserAdmin for AbstractBaseUser
    # is to handle password changes via a dedicated link/form, not direct input on the main form.

# Custom UserCreationForm for adding a new user
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        # These are the fields for initial user creation.
        # 'password' and 'password2' are handled by the parent UserCreationForm.
        fields = ('username', 'email', 'name') # Non-password fields

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    # The save() method of the parent UserCreationForm inherently calls user.set_password().
    # No explicit override for password hashing is typically needed here.


# Custom UserAdmin for your User model
class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm  # Form used when EDITING an existing user
    add_form = CustomUserCreationForm # Form used when ADDING a new user

    list_display = ('username', 'email', 'name', 'is_staff', 'is_active', 'is_superuser')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'groups')
    search_fields = ('username', 'email', 'name')
    ordering = ('username',)

    # Fieldsets for the CHANGE form (editing an existing user's details).
    # The 'password' entry here tells Django to include the standard password display/link widget.
    fieldsets = (
        (None, {'fields': ('username', 'password')}), # 'password' here is the special field handled by BaseUserAdmin
        ('Personal info', {'fields': ('name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Group Management', {'fields': ('personal_group',)}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    # add_fieldsets for the ADD form (creating a new user).
    # This explicitly lists 'password' and 'password2' for initial password setting.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('login', 'email', 'name', 'password1', 'password2'),
        }),
    )

# Register your CustomUser model with your CustomUserAdmin
admin.site.register(User, CustomUserAdmin)

# Project Admin
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'group', 'created_at')
    list_filter = ('group', 'created_at')
    search_fields = ('title',)
    ordering = ('-created_at',)

# Asset Admin
@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_title', 'type', 'project', 'created_at')
    list_filter = ('type', 'project', 'created_at')
    search_fields = ('title', 'url')
    ordering = ('-created_at',)

    def get_title(self, obj):
        if isinstance(obj.title, dict) and 'locales' in obj.title:
            # Show English title if available, otherwise first available language
            locales = obj.title['locales']
            return locales.get('en', next(iter(locales.values())) if locales else 'N/A')
        return str(obj.title)
    get_title.short_description = 'Title'

# Tour Admin
@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_title', 'project', 'is_public', 'created_at')
    list_filter = ('is_public', 'project', 'created_at')
    search_fields = ('title',)
    ordering = ('-created_at',)

    def get_title(self, obj):
        if isinstance(obj.title, dict) and 'locales' in obj.title:
            locales = obj.title['locales']
            return locales.get('en', next(iter(locales.values())) if locales else 'N/A')
        return str(obj.title)
    get_title.short_description = 'Title'

# POI Admin
@admin.register(POI)
class POIAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_title', 'tour', 'get_coordinates', 'order')
    list_filter = ('tour', 'order')
    search_fields = ('title',)
    ordering = ('tour', 'order')

    def get_title(self, obj):
        if isinstance(obj.title, dict) and 'locales' in obj.title:
            locales = obj.title['locales']
            return locales.get('en', next(iter(locales.values())) if locales else 'N/A')
        return str(obj.title)
    get_title.short_description = 'Title'

    def get_coordinates(self, obj):
        if obj.coordinates and isinstance(obj.coordinates, dict):
            lat = obj.coordinates.get('lat')
            long = obj.coordinates.get('long')
            if lat is not None and long is not None:
                return f"({lat}, {long})"
        return "N/A"
    get_coordinates.short_description = 'Coordinates'

# POI Asset Admin
@admin.register(POIAsset)
class POIAssetAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_title', 'poi', 'source_asset', 'type', 'priority', 'view_in_ar', 'created_at')
    list_filter = ('type', 'priority', 'view_in_ar', 'created_at')
    search_fields = ('title', 'url')
    ordering = ('-created_at',)

    def get_title(self, obj):
        if isinstance(obj.title, dict) and 'locales' in obj.title:
            locales = obj.title['locales']
            return locales.get('en', next(iter(locales.values())) if locales else 'N/A')
        return str(obj.title)
    get_title.short_description = 'Title'
