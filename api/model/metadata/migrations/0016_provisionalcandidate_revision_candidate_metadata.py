import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("metadata", "0015_systemrevision_revision_origin"),
    ]

    operations = [
        migrations.AlterField(
            model_name="systemrevision",
            name="revision_origin",
            field=models.CharField(
                choices=[
                    ("baseline", "Baseline"),
                    ("human_sync", "Human Sync"),
                    ("ai_refinement", "AI Refinement"),
                ],
                default="baseline",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="systemrevision",
            name="candidate_count",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="systemrevision",
            name="candidate_index",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="ProvisionalCandidate",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ("session_id", models.CharField(max_length=64)),
                ("candidate_index", models.PositiveIntegerField()),
                ("candidate_count", models.PositiveIntegerField()),
                ("process_text", models.TextField()),
                ("pipeline_profile", models.CharField(max_length=64)),
                ("activity_graph", models.JSONField()),
                ("ai4mde_export", models.JSONField()),
                ("topology_artifact", models.JSONField(blank=True, null=True)),
                ("semantic_sketch_plan", models.JSONField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("selected_at", models.DateTimeField(blank=True, null=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="provisional_candidates",
                        to="metadata.project",
                    ),
                ),
                (
                    "selected_system",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="selected_provisional_candidate",
                        to="metadata.system",
                    ),
                ),
            ],
            options={"ordering": ["candidate_index"]},
        ),
        migrations.AddConstraint(
            model_name="provisionalcandidate",
            constraint=models.UniqueConstraint(
                fields=("project", "session_id", "candidate_index"),
                name="unique_provisional_candidate_per_session_index",
            ),
        ),
    ]
