from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import migrations, models


INITIAL_GROUPS = []


def add_initial_auth(apps, schema_editor):

    Group = apps.get_model('auth', 'Group')
    User = get_user_model()
    initial_groups = INITIAL_GROUPS

    existing_groups = list(Group.objects.filter(name__in=initial_groups).values_list('name', flat=True))

    Group.objects.bulk_create(
        [Group(name=group_name) for group_name in initial_groups if group_name not in existing_groups]
    )

    if not User.objects.filter(username=settings.INITIAL_ADMIN_USERNAME).exists():
        _ = User.objects.create_superuser(username=settings.INITIAL_ADMIN_USERNAME,
                                          password=settings.INITIAL_ADMIN_PASSWORD,
                                          email=settings.INITIAL_ADMIN_EMAIL)
    else:
        print(f"User with username {settings.INITIAL_ADMIN_USERNAME} already exists.")


def remove_initial_auth(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    User = get_user_model()
    initial_groups = INITIAL_GROUPS

    User.objects.filter(username=settings.INITIAL_ADMIN_USERNAME).delete()
    Group.objects.filter(name__in=initial_groups).delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [migrations.RunPython(add_initial_auth, remove_initial_auth)]
