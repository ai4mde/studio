# Generated by Django 5.0.1 on 2024-01-30 08:20

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("prose", "0002_pipeline_step"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pipeline",
            name="step",
            field=models.SmallIntegerField(default=2),
        ),
    ]
