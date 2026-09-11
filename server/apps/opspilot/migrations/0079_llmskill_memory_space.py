import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("opspilot", "0078_llmskill_force_wiki_grounded"),
    ]

    operations = [
        migrations.AddField(
            model_name="llmskill",
            name="memory_space",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="llm_skills",
                to="opspilot.memoryspace",
                verbose_name="记忆空间",
            ),
        ),
        migrations.AddField(
            model_name="llmskill",
            name="memory_write_rounds",
            field=models.PositiveIntegerField(default=10, verbose_name="记忆写入轮次"),
        ),
    ]
