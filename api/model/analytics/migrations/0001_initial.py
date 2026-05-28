import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserEvent",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("session_id", models.CharField(db_index=True, max_length=64)),
                ("event_type", models.CharField(db_index=True, max_length=64)),
                ("timestamp", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "ordering": ["timestamp"],
            },
        ),
    ]
