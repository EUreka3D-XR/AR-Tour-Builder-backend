import uuid
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction
from eureka.models import Project


class Command(BaseCommand):
    help = (
        'Migrate projects that share a personal group to their own dedicated groups. '
        'All current members of the personal group are copied to the new project group. '
        'Run with --dry-run first to preview changes.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('--- DRY RUN — no changes will be saved ---\n'))

        # Find all projects whose group is a personal group (owner_user is set)
        projects = Project.objects.select_related('group').prefetch_related(  # type: ignore[attr-defined]
            'group__user_set', 'group__owner_user'
        ).filter(group__owner_user__isnull=False)

        if not projects.exists():
            self.stdout.write(self.style.SUCCESS('No projects on personal groups found. Nothing to do.'))
            return

        self.stdout.write(f'Found {projects.count()} project(s) on personal groups:\n')

        with transaction.atomic():
            for project in projects:
                personal_group = project.group
                curator = personal_group.owner_user  # reverse OneToOne from User.personal_group
                current_members = list(personal_group.user_set.all())

                self.stdout.write(
                    f'  Project {project.id} "{project.title}" '
                    f'(personal group of: {curator.username}, '
                    f'members: {[u.username for u in current_members]})'
                )

                if not dry_run:
                    new_group = Group.objects.create(name=f'project_{uuid.uuid4().hex[:12]}')
                    # Copy all current personal group members into the new group
                    new_group.user_set.set(current_members)
                    # Ensure curator is in the new group and has it in their groups
                    if curator not in current_members:
                        new_group.user_set.add(curator)
                    curator.groups.add(new_group)

                    project.group = new_group
                    project.save()

                    self.stdout.write(self.style.SUCCESS(
                        f'    → new group {new_group.id} created, '
                        f'{new_group.user_set.count()} member(s) copied, project reassigned.'
                    ))
                else:
                    self.stdout.write(
                        f'    → would create new group, copy {len(current_members)} member(s), reassign project.'
                    )

            if dry_run:
                transaction.set_rollback(True)

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\nDone. All affected projects now have dedicated groups.'))
        else:
            self.stdout.write(self.style.WARNING('\nDry run complete. Run without --dry-run to apply.'))
