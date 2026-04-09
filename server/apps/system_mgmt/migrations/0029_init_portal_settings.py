from django.db import migrations


def create_portal_settings(apps, schema_editor):
    SystemSettings = apps.get_model("system_mgmt", "SystemSettings")

    portal_settings = [
        {"key": "portal_name", "value": "BlueKing Lite"},
        {"key": "portal_logo_url", "value": ""},
        {"key": "portal_favicon_url", "value": ""},
        {"key": "watermark_enabled", "value": "0"},
        {"key": "watermark_text", "value": "BlueKing Lite · ${username} · ${date}"},
    ]

    for setting in portal_settings:
        SystemSettings.objects.get_or_create(key=setting["key"], defaults={"value": setting["value"]})


class Migration(migrations.Migration):

    dependencies = [
        ("system_mgmt", "0028_group_allow_inherit_roles"),
    ]

    operations = [
        migrations.RunPython(create_portal_settings, migrations.RunPython.noop),
    ]