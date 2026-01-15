from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group

class UserManager(BaseUserManager):
    def create_user(self, username, email, name=None, password=None):
        if not username:
            raise ValueError('Users must have a username')
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            name=name,
        )

        user.set_password(password)
        user.save(using=self._db)

        # Create and assign the user's private group
        from django.contrib.auth.models import Group
        group_name = f'user_{user.id}_personal'
        group, created = Group.objects.get_or_create(name=group_name)
        user.personal_group = group
        user.save(update_fields=['personal_group'])
        if group not in user.groups.all():
            user.groups.add(group)

        return user

    def create_superuser(self, username, email, password=None, name=None):
        user = self.create_user(
            username=username,
            email=self.normalize_email(email),
            password=password,
            name=name,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=100, blank=True, null=True)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)
    password = models.CharField(max_length=128)  # Handled by AbstractBaseUser
    is_active = models.BooleanField(default=True)  # type: ignore
    is_staff = models.BooleanField(default=False)  # type: ignore
    is_superuser = models.BooleanField(default=False)  # type: ignore

    personal_group = models.OneToOneField(
        Group,
        on_delete=models.SET_NULL, # If the group is deleted, set this field to NULL
        null=True,                 # Allow it to be NULL
        blank=True,                # Allow it to be blank in forms
        related_name='owner_user', # Allows group.owner_user to get the user who owns it
        help_text="The default group owned by this user for personal projects."
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def __str__(self):
        return self.username

    def get_full_name(self):
        return self.name if self.name else self.username

    def get_short_name(self):
        return self.name if self.name else self.username

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Ensure personal group exists and is assigned
        from django.contrib.auth.models import Group
        group_name = f'user_{self.id}_personal'  # type: ignore[attr-defined]
        group, created = Group.objects.get_or_create(name=group_name)
        if self.personal_group != group:
            self.personal_group = group
            super().save(update_fields=['personal_group'])
        if group not in self.groups.all():  # type: ignore[attr-defined]
            self.groups.add(group)  # type: ignore[attr-defined]
