from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.fields import empty

from apps.system_mgmt.models import User


class UsernameSerializer(serializers.ModelSerializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)
        user_list = User.objects.all().values("username", "display_name", "domain")
        self.user_map = {}
        for i in user_list:
            self.user_map[f"{i['username']}@{i['domain']}"] = i["display_name"]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        if "created_by" in list(response.keys()):
            username = f"{response['created_by']}@{response.get('domain', 'domain.com')}"
            response["created_by"] = self.user_map.get(username, response["created_by"])
        if "updated_by" in list(response.keys()):
            username = f"{response['updated_by']}@{response.get('updated_by_domain', 'domain.com')}"
            response["updated_by"] = self.user_map.get(username, response["updated_by"])
        return response


class I18nSerializer(UsernameSerializer):
    def to_representation(self, instance):
        response = super().to_representation(instance)
        if "is_build_in" in list(response.keys()):
            for key in response.keys():
                if isinstance(response[key], str):
                    response[key] = _(response[key])
        return response


class TeamSerializer(I18nSerializer):
    team_name = serializers.SerializerMethodField()

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)
        request = self.context["request"]
        groups = request.user.group_list
        self.group_map = {i["id"]: i["name"] for i in groups}

    def get_team_name(self, instance):
        return [self.group_map.get(i) for i in instance.team if i in self.group_map]


class AuthSerializer(UsernameSerializer):
    permissions = serializers.SerializerMethodField()

    def __init__(self, instance=None, data=empty, **kwargs):
        super().__init__(instance=instance, data=data, **kwargs)
        request = self.context["request"]
        self.rule_map = {}

        # 获取当前应用名称
        app_name = self._get_app_name()

        if hasattr(self, "permission_key") and app_name:
            # 获取应用下的规则
            app_name_map = {"system_mgmt": "system-manager", "node_mgmt": "node", "console_mgmt": "ops-console"}
            app_name = app_name_map.get(app_name, app_name)
            app_rules = request.user.rules.get(app_name, {})
            guest_rules_map = app_rules.get("guest", {})
            normal_rules_map = app_rules.get("normal", {})
            if "." in self.permission_key:
                keys = self.permission_key.split(".", 1)
                guest_rules = guest_rules_map.get(keys[0], {})
                normal_rules = normal_rules_map.get(keys[0], {})
                if isinstance(guest_rules, dict) and len(keys) > 1:
                    guest_rules = guest_rules.get(keys[1], [])
                if isinstance(normal_rules, dict) and len(keys) > 1:
                    normal_rules = normal_rules.get(keys[1], [])
            else:
                guest_rules = guest_rules_map.get(self.permission_key, [])
                normal_rules = normal_rules_map.get(self.permission_key, [])
            # 合并规则
            rules = guest_rules + normal_rules
            self.rule_map = {int(i["id"]): i["permission"] for i in rules if int(i["id"]) > 0}

    def _get_app_name(self):
        """获取当前序列化器所属的应用名称"""
        module_path = self.__class__.__module__
        if "apps." in module_path:
            # 从模块路径中提取应用名称，如 apps.opspilot.serializers -> opspilot
            parts = module_path.split(".")
            if len(parts) >= 2 and parts[0] == "apps":
                return parts[1]
        return None

    def get_permissions(self, instance):
        return self.rule_map.get(instance.id, ["View", "Operate"])
