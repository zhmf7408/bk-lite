from django.db import migrations


def backfill_default_cloud_region_service_status(apps, schema_editor):
    CloudRegionService = apps.get_model("node_mgmt", "CloudRegionService")

    CloudRegionService.objects.filter(
        cloud_region_id=1,
        name__in=["stargazer", "nats-executor"],
    ).update(status="normal", deployed_status=2)


class Migration(migrations.Migration):
    dependencies = [
        ("node_mgmt", "0030_optimize_converge_task_indexes"),
    ]

    operations = [
        migrations.RunPython(
            backfill_default_cloud_region_service_status,
            migrations.RunPython.noop,
        ),
    ]
