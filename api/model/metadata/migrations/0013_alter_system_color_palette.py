from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0012_system_settings'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE metadata_system ALTER COLUMN color_palette SET DEFAULT '{}'::jsonb, ALTER COLUMN color_palette DROP NOT NULL;",
            reverse_sql="ALTER TABLE metadata_system ALTER COLUMN color_palette SET NOT NULL, ALTER COLUMN color_palette DROP DEFAULT;",
        ),
    ]
