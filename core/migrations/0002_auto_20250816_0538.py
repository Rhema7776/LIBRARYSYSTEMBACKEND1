from django.db import migrations

def create_superuser(apps, schema_editor):
    User = apps.get_model("auth", "User")  # use "users", "CustomUser" if you have a custom model
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="AdminPassword123"
        )

class Migration(migrations.Migration):

    dependencies = [
        ("users", "0001_initial"),  # change to your last migration
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]
