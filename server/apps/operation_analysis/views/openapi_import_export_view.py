# -- coding: utf-8 --
"""
运营分析 YAML 导入导出 Open API

提供面向外部系统的导入导出接口，支持：
- 导出指定对象为 YAML
- 导入预检（检测冲突、缺失配置）
- 导入提交（执行导入）

认证方式：通过 API Token（由 APISecretMiddleware 验证）
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.utils.open_base import OpenAPIViewSet
from apps.core.exceptions.base_app_exception import UnauthorizedException
from apps.core.logger import operation_analysis_logger as logger
from apps.operation_analysis.constants.import_export import (
    ObjectType,
    ConflictAction,
    ConflictReason,
    ImportExportErrorCode,
)
from apps.operation_analysis.serializers.import_export_serializers import (
    ExportRequestSerializer,
    ImportPrecheckRequestSerializer,
    ImportSubmitRequestSerializer,
)
from apps.operation_analysis.services.import_export.export_service import ExportService
from apps.operation_analysis.services.import_export.precheck_service import PrecheckService
from apps.operation_analysis.services.import_export.import_service import ImportService
from apps.operation_analysis.schemas.import_export_schema import YAMLDocument


class OpenImportExportViewSet(OpenAPIViewSet):
    """
    运营分析 YAML 导入导出开放 API 视图集

    提供无需登录的 API 接口，通过 API Token 认证：
    - POST /export - 导出对象为 YAML
    - POST /import/precheck - 导入预检
    - POST /import/submit - 导入提交

    认证方式：
        请求头需包含有效的 API Token（由 APISecretMiddleware 验证）
        Header: Api-Authorization: <api_token>
    """

    def _check_api_auth(self, request):
        if not getattr(request, "api_pass", False):
            logger.warning("Open API request rejected: missing or invalid API token, path=%s", request.path)
            raise UnauthorizedException("缺少有效的 API Token，请在请求头中提供有效的认证信息")

    def _get_groups_from_request(self, request) -> list[int]:
        """从请求中获取组织列表"""
        groups = request.data.get("groups", [])
        if isinstance(groups, list):
            return [int(g) for g in groups if str(g).isdigit()]
        return []

    def _get_username_from_request(self, request) -> str:
        """从请求中获取用户名"""
        if hasattr(request, "user") and hasattr(request.user, "username"):
            return request.user.username
        return request.data.get("operator", "api_user")

    def _convert_ids_to_keys(self, object_type: str, object_ids: list[int]) -> list[str]:
        """将对象 ID 转换为业务键"""
        from apps.operation_analysis.models.models import Dashboard, Topology, Architecture
        from apps.operation_analysis.models.datasource_models import DataSourceAPIModel, NameSpace
        from apps.operation_analysis.constants.import_export import BUSINESS_KEY_SEPARATOR

        keys = []
        if object_type == ObjectType.DASHBOARD.value:
            for obj in Dashboard.objects.filter(id__in=object_ids):
                keys.append(f"{object_type}{BUSINESS_KEY_SEPARATOR}{obj.name}")
        elif object_type == ObjectType.TOPOLOGY.value:
            for obj in Topology.objects.filter(id__in=object_ids):
                keys.append(f"{object_type}{BUSINESS_KEY_SEPARATOR}{obj.name}")
        elif object_type == ObjectType.ARCHITECTURE.value:
            for obj in Architecture.objects.filter(id__in=object_ids):
                keys.append(f"{object_type}{BUSINESS_KEY_SEPARATOR}{obj.name}")
        elif object_type == ObjectType.DATASOURCE.value:
            for obj in DataSourceAPIModel.objects.filter(id__in=object_ids):
                keys.append(f"{obj.name}{BUSINESS_KEY_SEPARATOR}{obj.rest_api}")
        elif object_type == ObjectType.NAMESPACE.value:
            for obj in NameSpace.objects.filter(id__in=object_ids):
                keys.append(obj.name)
        return keys

    def _parse_yaml_to_document(self, yaml_content: str) -> YAMLDocument:
        import yaml as pyyaml

        data = pyyaml.safe_load(yaml_content)
        return YAMLDocument(**data)

    def _validate_conflict_decisions(self, conflicts: list[dict], conflict_decisions: dict[str, str]) -> list[dict]:
        errors = []
        for conflict in conflicts:
            if conflict["reason"] != ConflictReason.NO_PERMISSION_CONFLICT:
                continue
            object_key = conflict["object_key"]
            action = conflict_decisions.get(object_key, ConflictAction.RENAME.value)
            if action != ConflictAction.RENAME.value:
                errors.append(
                    {
                        "code": ImportExportErrorCode.IMPORT_PERMISSION_DENIED,
                        "message": f"对象 '{object_key}' 在其他组织中已存在，只能选择重命名",
                        "object_key": object_key,
                        "object_type": conflict["object_type"],
                    }
                )
        return errors

    @action(detail=False, methods=["post"], url_path="export")
    def export_objects(self, request):
        """
        导出对象为 YAML

        API: POST /open_api/import_export/export

        Request Headers:
            Authorization (str, required): API Token 认证

        Request Body:
            {
                "scope": "single",  # 导出范围: "single" | "cascade"
                "object_type": "dashboard",  # 对象类型: "dashboard" | "topology" | "architecture" | "datasource" | "namespace"
                "object_ids": [1, 2, 3],  # 要导出的对象 ID 列表
                "groups": [1]  # 可选，组织 ID 列表
            }

        Response (200 OK):
            {
                "yaml_content": "version: '1.0'\\n...",  # 导出的 YAML 内容
                "exported_objects": [  # 已导出的对象列表
                    {
                        "object_type": "dashboard",
                        "object_key": "dashboard::my-dashboard",
                        "name": "my-dashboard"
                    }
                ],
                "warnings": []  # 警告信息
            }

        Response (401 Unauthorized):
            {
                "success": False,
                "code": "UNAUTHORIZED",
                "message": "缺少有效的 API Token"
            }
        """
        self._check_api_auth(request)

        serializer = ExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        scope = data["scope"]
        object_type = data["object_type"]
        object_ids = data["object_ids"]

        groups = self._get_groups_from_request(request)
        organization_id = groups[0] if groups else 0

        object_keys = self._convert_ids_to_keys(object_type, object_ids)

        logger.info(
            "Open API export request: object_type=%s, object_ids=%s, organization_id=%s",
            object_type,
            object_ids,
            organization_id,
        )

        result = ExportService.export_objects(
            scope_type=scope,
            object_types=[object_type],
            object_keys=object_keys,
            organization_id=organization_id,
        )

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="import/precheck")
    def import_precheck(self, request):
        """
        导入预检

        API: POST /open_api/import_export/import/precheck

        Request Headers:
            Authorization (str, required): API Token 认证

        Request Body:
            {
                "yaml_content": "version: '1.0'\\n...",  # YAML 内容
                "target_directory_id": 1,  # 可选，目标目录 ID（仅对画布类对象有效）
                "groups": [1]  # 可选，组织 ID 列表，用于检测跨组织冲突
            }

        Response (200 OK):
            {
                "valid": true,  # 预检是否通过
                "errors": [],  # 错误列表
                "warnings": [],  # 警告列表
                "conflicts": [  # 冲突列表
                    {
                        "object_type": "dashboard",
                        "object_key": "dashboard::my-dashboard",
                        "name": "my-dashboard",
                        "reason": "NAME_CONFLICT",  # 冲突原因
                        "existing_id": 123,  # 已存在对象的 ID
                        "available_actions": ["overwrite", "rename", "skip"]  # 可选的冲突处理方式
                    }
                ],
                "objects": [  # 待导入对象列表
                    {
                        "object_type": "dashboard",
                        "object_key": "dashboard::my-dashboard",
                        "name": "my-dashboard",
                        "has_conflict": true,
                        "status": "pending"
                    }
                ],
                "secret_fields": [  # 需要补充的敏感字段
                    {
                        "object_key": "datasource::my-ds::http://api.example.com",
                        "field": "password",
                        "required": true
                    }
                ]
            }

        Response (401 Unauthorized):
            认证失败
        """
        self._check_api_auth(request)

        serializer = ImportPrecheckRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        yaml_content = data["yaml_content"]
        target_directory_id = data.get("target_directory_id")

        groups = self._get_groups_from_request(request)
        current_team = groups[0] if groups else None

        logger.info(
            "Open API import precheck request: yaml_size=%d, target_directory_id=%s, current_team=%s",
            len(yaml_content),
            target_directory_id,
            current_team,
        )

        result = PrecheckService.precheck(
            yaml_content=yaml_content,
            target_directory_id=target_directory_id,
            current_team=current_team,
        )

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="import/submit")
    def import_submit(self, request):
        """
        导入提交

        API: POST /open_api/import_export/import/submit

        Request Headers:
            Authorization (str, required): API Token 认证

        Request Body:
            {
                "yaml_content": "version: '1.0'\\n...",  # YAML 内容
                "target_directory_id": 1,  # 可选，目标目录 ID
                "conflict_decisions": [  # 冲突决策列表
                    {
                        "object_key": "dashboard::my-dashboard",
                        "action": "overwrite"  # "overwrite" | "rename" | "skip"
                    }
                ],
                "secret_supplements": [  # 敏感字段补充
                    {
                        "object_key": "datasource::my-ds::http://api.example.com",
                        "field": "password",
                        "value": "secret123"
                    }
                ],
                "groups": [1],  # 组织 ID 列表
                "operator": "api_user"  # 可选，操作者用户名
            }

        Response (200 OK):
            {
                "success": true,
                "summary": {  # 导入汇总
                    "total": 5,
                    "created": 3,
                    "overwritten": 1,
                    "renamed": 0,
                    "skipped": 1,
                    "failed": 0
                },
                "results": [  # 各对象导入结果
                    {
                        "object_type": "dashboard",
                        "object_key": "dashboard::my-dashboard",
                        "name": "my-dashboard",
                        "action": "created",  # "created" | "overwritten" | "renamed" | "skipped" | "failed"
                        "new_id": 456,  # 新对象 ID（如果创建/覆盖）
                        "new_name": null,  # 新名称（如果重命名）
                        "error": null  # 错误信息（如果失败）
                    }
                ],
                "errors": []  # 全局错误
            }

        Response (400 Bad Request):
            {
                "success": false,
                "errors": [...],
                "message": "预检失败，无法执行导入"
            }

        Response (401 Unauthorized):
            认证失败
        """
        self._check_api_auth(request)

        serializer = ImportSubmitRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        yaml_content = data["yaml_content"]
        target_directory_id = data.get("target_directory_id")
        conflict_decisions_list = data.get("conflict_decisions", [])
        secret_supplements_list = data.get("secret_supplements", [])

        groups = self._get_groups_from_request(request)
        current_team = groups[0] if groups else None
        username = self._get_username_from_request(request)

        logger.info(
            "Open API import submit request: yaml_size=%d, target_directory_id=%s, groups=%s, operator=%s",
            len(yaml_content),
            target_directory_id,
            groups,
            username,
        )

        precheck_result = PrecheckService.precheck(
            yaml_content=yaml_content,
            target_directory_id=target_directory_id,
            current_team=current_team,
        )

        if not precheck_result["valid"]:
            return Response(
                {
                    "success": False,
                    "errors": precheck_result["errors"],
                    "message": "预检失败，无法执行导入",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        conflict_decisions = {item["object_key"]: item["action"] for item in conflict_decisions_list}

        invalid_decisions = self._validate_conflict_decisions(precheck_result["conflicts"], conflict_decisions)
        if invalid_decisions:
            return Response(
                {
                    "success": False,
                    "errors": invalid_decisions,
                    "message": "冲突决策无效",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        secret_supplements = {}
        for item in secret_supplements_list:
            key = item["object_key"]
            if key not in secret_supplements:
                secret_supplements[key] = {}
            secret_supplements[key][item["field"]] = item["value"]

        doc = self._parse_yaml_to_document(yaml_content)

        import_service = ImportService(
            doc=doc,
            target_directory_id=target_directory_id,
            conflict_decisions=conflict_decisions,
            secret_supplements=secret_supplements,
            created_by=username,
            updated_by=username,
            groups=groups,
        )

        result = import_service.execute()

        return Response(result, status=status.HTTP_200_OK)
