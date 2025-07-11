# Generated by Django 4.2.15 on 2025-07-07 06:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mlops', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnomalyDetectionServing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Created Time')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated Time')),
                ('created_by', models.CharField(default='', max_length=32, verbose_name='Creator')),
                ('updated_by', models.CharField(default='', max_length=32, verbose_name='Updater')),
                ('domain', models.CharField(default='domain.com', max_length=100, verbose_name='Domain')),
                ('updated_by_domain', models.CharField(default='domain.com', max_length=100, verbose_name='updated by domain')),
                ('name', models.CharField(help_text='服务的名称', max_length=100, verbose_name='服务名称')),
                ('description', models.TextField(blank=True, help_text='服务的详细描述', null=True, verbose_name='服务描述')),
                ('model_version', models.CharField(default='latest', help_text='模型版本', max_length=50, verbose_name='模型版本')),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive')], default='active', help_text='服务的当前状态', max_length=20, verbose_name='服务状态')),
                ('anomaly_threshold', models.FloatField(default=0.5, help_text='用于判断异常的阈值', verbose_name='异常阈值')),
                ('anomaly_detection_train_job', models.ForeignKey(help_text='关联的异常检测训练任务模型ID', on_delete=django.db.models.deletion.CASCADE, related_name='servings', to='mlops.anomalydetectiontrainjob', verbose_name='模型ID')),
            ],
            options={
                'verbose_name': '异常检测服务',
                'verbose_name_plural': '异常检测服务',
                'ordering': ['-created_at'],
            },
        ),
    ]
