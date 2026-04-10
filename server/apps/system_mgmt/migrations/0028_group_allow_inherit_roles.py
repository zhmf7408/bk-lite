from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('system_mgmt', '0027_add_userrule_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='allow_inherit_roles',
            field=models.BooleanField(default=False, verbose_name='允许子组织继承角色'),
        ),
    ]
