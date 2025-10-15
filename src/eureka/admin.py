# src/eureka/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django import forms
from .models.user import User

# Custom UserChangeForm for editing an existing user
class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        # Important: Do NOT include 'password' here if you want Django's default 'change password' link
        # The BaseUserAdmin's fieldsets handle how the password field is displayed (as a link).
        fields = ('login', 'email', 'name', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')

    # You generally don't need to override save() for password hashing here.
    # The default behavior of UserChangeForm combined with BaseUserAdmin for AbstractBaseUser
    # is to handle password changes via a dedicated link/form, not direct input on the main form.

# Custom UserCreationForm for adding a new user
class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        # These are the fields for initial user creation.
        # 'password' and 'password2' are handled by the parent UserCreationForm.
        fields = ('login', 'email', 'name') # Non-password fields

    def clean_login(self):
        login = self.cleaned_data['login']
        if User.objects.filter(login=login).exists():
            raise forms.ValidationError("A user with that login already exists.")
        return login

    # The save() method of the parent UserCreationForm inherently calls user.set_password().
    # No explicit override for password hashing is typically needed here.


# Custom UserAdmin for your User model
class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm  # Form used when EDITING an existing user
    add_form = CustomUserCreationForm # Form used when ADDING a new user

    list_display = ('login', 'email', 'name', 'is_staff', 'is_active', 'is_superuser')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'groups')
    search_fields = ('login', 'email', 'name')
    ordering = ('login',)

    # Fieldsets for the CHANGE form (editing an existing user's details).
    # The 'password' entry here tells Django to include the standard password display/link widget.
    fieldsets = (
        (None, {'fields': ('login', 'password')}), # 'password' here is the special field handled by BaseUserAdmin
        ('Personal info', {'fields': ('name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    # add_fieldsets for the ADD form (creating a new user).
    # This explicitly lists 'password' and 'password2' for initial password setting.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('login', 'email', 'name', 'password', 'password2'),
        }),
    )

# Register your CustomUser model with your CustomUserAdmin
admin.site.register(User, CustomUserAdmin)
