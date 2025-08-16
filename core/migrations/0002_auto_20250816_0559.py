from django.db import migrations
import os


def create_admin(apps, schema_editor):
    # Get your custom User model from the "users" app
    User = apps.get_model("users", "User")

    username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
    email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
    password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "AdminPass123!")

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )


def delete_admin(apps, schema_editor):
    User = apps.get_model("users", "User")
    username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
    User.objects.filter(username=username).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),  # make sure this matches your first migration
    ]

    operations = [
        migrations.RunPython(create_admin, delete_admin),
    ]
