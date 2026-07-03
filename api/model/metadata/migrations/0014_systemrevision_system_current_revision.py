from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0013_systemgenerationartifacts"),
    ]

    operations = [
        migrations.CreateModel(
            name="SystemRevision",
            fields=[
                ("id", models.UUIDField(primary_key=True, default=uuid.uuid4, serialize=False)),
                ("revision_index", models.IntegerField()),
                ("process_text", models.TextField()),
                ("pipeline_profile", models.CharField(max_length=64)),
                ("topology_artifact", models.JSONField(blank=True, null=True)),
                ("semantic_sketch_plan", models.JSONField(blank=True, null=True)),
                ("activity_graph", models.JSONField()),
                ("ai4mde_export", models.JSONField()),
                ("refinement_trace", models.JSONField(blank=True, null=True)),
                ("refinement_instruction", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "parent_revision",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="child_revisions",
                        to="metadata.systemrevision",
                    ),
                ),
                (
                    "system",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="revisions",
                        to="metadata.system",
                    ),
                ),
            ],
            options={
                "ordering": ["revision_index", "created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="systemrevision",
            constraint=models.UniqueConstraint(
                fields=("system", "revision_index"),
                name="unique_revision_index_per_system",
            ),
        ),
        migrations.AddField(
            model_name="system",
            name="current_revision",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="metadata.systemrevision",
            ),
        ),
    ]
