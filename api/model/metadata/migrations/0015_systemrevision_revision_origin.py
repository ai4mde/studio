from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0014_systemrevision_system_current_revision"),
    ]

    operations = [
        migrations.AddField(
            model_name="systemrevision",
            name="revision_origin",
            field=models.CharField(
                choices=[
                    ("baseline", "Baseline"),
                    ("ai_refinement", "AI Refinement"),
                ],
                default="baseline",
                max_length=32,
            ),
        ),
    ]
