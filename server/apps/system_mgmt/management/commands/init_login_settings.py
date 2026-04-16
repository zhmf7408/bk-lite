from django.core.management import BaseCommand

from apps.system_mgmt.models import SystemSettings
from apps.system_mgmt.models.login_module import LoginModule


class Command(BaseCommand):
    help = "初始登陆化设置"

    def handle(self, *args, **options):
        LoginModule.objects.get_or_create(
            is_build_in=True,
            source_type="wechat",
            defaults={
                "name": "微信开放平台",
                "app_id": "",
                "app_secret": "",
                "other_config": {
                    "redirect_uri": "",
                    "callback_url": "",
                },
                "enabled": True,
            },
        )

        SystemSettings.objects.get_or_create(key="login_expired_time", defaults={"value": "24"})
        SystemSettings.objects.get_or_create(key="enable_otp", defaults={"value": "0"})
        SystemSettings.objects.get_or_create(key="portal_name", defaults={"value": "BlueKing Lite"})
        SystemSettings.objects.get_or_create(key="portal_logo_url", defaults={"value": ""})
        SystemSettings.objects.get_or_create(key="portal_favicon_url", defaults={"value": ""})
        SystemSettings.objects.get_or_create(key="watermark_enabled", defaults={"value": "0"})
        SystemSettings.objects.get_or_create(key="watermark_text", defaults={"value": "BlueKing Lite · ${username} · ${date}"})
