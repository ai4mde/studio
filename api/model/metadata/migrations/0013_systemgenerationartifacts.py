from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0012_remove_release_diagrams_remove_release_interfaces_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="SystemGenerationArtifacts",
            fields=[
                (
                    "system",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name="generation_artifacts",
                        serialize=False,
                        to="metadata.system",
                    ),
                ),
                ("process_text", models.TextField()),
                ("pipeline_profile", models.CharField(max_length=64)),
                ("topology_artifact", models.JSONField()),
                ("semantic_sketch_plan", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
