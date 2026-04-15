from django.http import JsonResponse
from django_filters import filters
from django_filters.rest_framework import FilterSet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.decorators.api_permission import HasPermission
from apps.core.utils.viewset_utils import GenericViewSetFun
from apps.system_mgmt.models import Channel, ChannelChoices, User
from apps.system_mgmt.serializers import ChannelSerializer
from apps.system_mgmt.utils.operation_log_utils import log_operation
from apps.system_mgmt.utils.channel_utils import send_by_dingtalk_bot, send_by_feishu_bot, send_by_wecom_bot, send_email


class ChannelFilter(FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")
    channel_type = filters.CharFilter(field_name="channel_type", lookup_expr="exact")


class ChannelViewSet(viewsets.ModelViewSet, GenericViewSetFun):
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    filterset_class = ChannelFilter

    @HasPermission("channel_list-View")
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        _, _, _, query = self.filter_by_group(queryset, request, request.user)
        queryset = queryset.filter(query)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @HasPermission("channel_list-Add")
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)

        # 记录操作日志
        if response.status_code == 201:
            channel_name = response.data.get("name", "")
            channel_type = response.data.get("channel_type", "")
            log_operation(request, "create", "channel", f"新增{channel_type}渠道: {channel_name}")

        return response

    @HasPermission("channel_list-Delete")
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        channel_name = obj.name
        channel_type = obj.channel_type

        response = super().destroy(request, *args, **kwargs)

        # 记录操作日志
        if response.status_code == 204:
            log_operation(request, "delete", "channel", f"删除{channel_type}渠道: {channel_name}")

        return response

    @action(methods=["POST"], detail=True)
    @HasPermission("channel_list-Edit")
    def update_settings(self, request, *args, **kwargs):
        obj: Channel = self.get_object()
        config = request.data["config"]
        if obj.channel_type == "email":
            obj.encrypt_field("smtp_pwd", config)
            config.setdefault("smtp_pwd", obj.config["smtp_pwd"])
        elif obj.channel_type == "enterprise_wechat":
            obj.encrypt_field("secret", config)
            obj.encrypt_field("token", config)
            obj.encrypt_field("aes_key", config)
            config.setdefault("secret", obj.config["secret"])
            config.setdefault("token", obj.config["token"])
            config.setdefault("aes_key", obj.config["aes_key"])
        elif obj.channel_type == "enterprise_wechat_bot":
            obj.encrypt_field("webhook_url", config)
            config.setdefault("webhook_url", obj.config["webhook_url"])
        elif obj.channel_type == "nats":
            # NATS 配置无需加密处理
            pass
        obj.config = config
        obj.save()

        # 记录操作日志
        log_operation(request, "update", "channel", f"编辑{obj.channel_type}渠道: {obj.name}")

        return JsonResponse({"result": True})

    @action(methods=["POST"], detail=False)
    @HasPermission("channel_list-Edit")
    def test_send(self, request, *args, **kwargs):
        channel_type = request.data.get("channel_type")
        config = request.data.get("config") or {}
        channel_name = request.data.get("name") or "Test Channel"

        supported_types = {
            ChannelChoices.EMAIL,
            ChannelChoices.ENTERPRISE_WECHAT_BOT,
            ChannelChoices.FEISHU_BOT,
            ChannelChoices.DINGTALK_BOT,
        }
        if channel_type not in supported_types:
            return Response({"result": False, "message": "Unsupported channel type"}, status=400)

        test_channel = Channel(name=channel_name, channel_type=channel_type, config=config, description="", team=[])
        title = f"[{channel_name}] Test Message"
        receiver_name = request.user.display_name or request.user.username
        content = f"This is a test message from channel '{channel_name}'.<br/>Receiver: {receiver_name}"

        if channel_type == ChannelChoices.EMAIL:
            if not request.user.email:
                return Response({"result": False, "message": "Current user email is empty"}, status=400)
            user_list = User.objects.filter(id=request.user.id)
            result = send_email(test_channel, title, content, user_list)
        elif channel_type == ChannelChoices.ENTERPRISE_WECHAT_BOT:
            result = send_by_wecom_bot(test_channel, content, [receiver_name])
        elif channel_type == ChannelChoices.FEISHU_BOT:
            result = send_by_feishu_bot(test_channel, title, content, [receiver_name])
        else:
            result = send_by_dingtalk_bot(test_channel, title, content, [receiver_name])

        if result.get("result") is False:
            return Response({"result": False, "message": result.get("message") or "Test send failed"}, status=400)

        if channel_type != ChannelChoices.EMAIL:
            if result.get("errcode") not in (None, 0) or result.get("code") not in (None, 0):
                return Response(
                    {
                        "result": False,
                        "message": result.get("errmsg") or result.get("msg") or result.get("message") or "Test send failed",
                    },
                    status=400,
                )

        return Response({"result": True})


class TemplateFilter(FilterSet):
    channel_type = filters.CharFilter(field_name="channel_type", lookup_expr="exact")
    name = filters.CharFilter(field_name="name", lookup_expr="lte")
