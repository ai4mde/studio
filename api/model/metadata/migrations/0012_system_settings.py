from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0011_classifier_project_alter_classifier_system'),
    ]

    operations = [
        migrations.AddField(
            model_name='system',
            name='settings',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
