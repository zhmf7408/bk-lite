from rest_framework import viewsets
from rest_framework.decorators import action

from apps.core.utils.web_utils import WebUtils
from apps.log.services.k8s_collect import K8sLogCollectService
from apps.rpc.node_mgmt import NodeMgmt


class K8sCollectViewSet(viewsets.ViewSet):
    @action(methods=["get"], detail=False, url_path="cloud_region_list")
    def cloud_region_list(self, request):
        data = NodeMgmt().cloud_region_list()
        return WebUtils.response_success(data)

    @action(methods=["post"], detail=False, url_path="create_instance")
    def create_instance(self, request):
        data = K8sLogCollectService.create_k8s_collect_instance(request.data)
        return WebUtils.response_success(data)

    @action(methods=["post"], detail=False, url_path="generate_install_command")
    def generate_install_command(self, request):
        command = K8sLogCollectService.generate_install_command(
            request.data.get("instance_id"),
            request.data.get("cloud_region_id"),
        )
        return WebUtils.response_success(command)

    @action(methods=["post"], detail=False, url_path="check_collect_status")
    def check_collect_status(self, request):
        success = K8sLogCollectService.check_collect_status(request.data.get("instance_id"))
        return WebUtils.response_success({"success": success})
