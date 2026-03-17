from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0013_alter_system_color_palette'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='settings',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.RemoveField(
            model_name='system',
            name='settings',
        ),
    ]
