# Generated by Django 5.0.1 on 2024-01-17 18:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("metadata", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Diagram",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("type", models.CharField()),
                ("name", models.CharField()),
                ("description", models.TextField(blank=True)),
                (
                    "system",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="metadata.system",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Edge",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("data", models.JSONField()),
                (
                    "diagram",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="diagram.diagram",
                    ),
                ),
                (
                    "rel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="metadata.relation",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Node",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("data", models.JSONField()),
                (
                    "cls",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="metadata.classifier",
                    ),
                ),
                (
                    "diagram",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="diagram.diagram",
                    ),
                ),
            ],
        ),
    ]