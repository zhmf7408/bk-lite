import shlex

from django.utils import timezone

from apps.core.logger import job_logger as logger
from apps.job_mgmt.constants import ExecutionStatus
from apps.job_mgmt.models import Target
from apps.job_mgmt.services import ExecutionTaskBaseService
from apps.rpc.ansible import AnsibleExecutor
from config.components.nats import NATS_NAMESPACE


class PlaybookExecution(ExecutionTaskBaseService):
    def __init__(self, execution_id):
        super().__init__(execution_id, "execute_playbook_task")

    def run(self):
        logger.info(f"[{self.task_name}] 开始执行Playbook任务: execution_id={self.execution_id}")

        execution, target_list = self.prepare_execution()
        if not execution:
            return

        # 检查 Playbook 是否存在
        if not execution.playbook:
            logger.error(f"[{self.task_name}] Playbook 不存在: execution_id={self.execution_id}")
            self.update_execution_status(execution, ExecutionStatus.FAILED, finished_at=timezone.now())
            return

        # 判断是否走 Ansible 路径
        if self._should_use_ansible(execution.target_source, target_list):
            self._run_via_ansible(execution, target_list)
        else:
            error_msg = "Playbook 执行仅支持 Ansible 驱动的目标管理主机"
            logger.warning(f"[{self.task_name}] {error_msg}: execution_id={self.execution_id}")
            execution.execution_results = [self.build_target_failed_result(t, error_msg) for t in target_list]
            execution.save(update_fields=["execution_results", "updated_at"])
            self.update_execution_status(execution, ExecutionStatus.FAILED, finished_at=timezone.now())

    def _run_via_ansible(self, execution, target_list: list):
        """通过 AnsibleExecutor.playbook() 执行 Playbook（异步回调）"""
        try:
            self._execute_playbook_via_ansible(execution, target_list)
            logger.info(f"[{self.task_name}] Ansible Playbook 任务已提交，等待回调: execution_id={self.execution_id}")
        except Exception as e:
            error_msg = f"Ansible Playbook 执行失败: {str(e)}"
            logger.exception(f"[{self.task_name}] {error_msg}")
            self.update_execution_status(execution, ExecutionStatus.FAILED, finished_at=timezone.now())
            execution.execution_results = [self.build_target_failed_result(t, error_msg) for t in target_list]
            execution.save(update_fields=["execution_results", "updated_at"])

    @classmethod
    def _execute_playbook_via_ansible(cls, execution, target_list: list) -> None:
        """
        通过 Ansible 执行 Playbook（异步方式）

        使用 AnsibleExecutor.playbook()，将 Playbook ZIP 文件信息和主机凭据
        传递给远端 Ansible 执行器，结果通过 NATS 回调返回。
        """
        task_name = "execute_playbook_via_ansible"
        playbook = execution.playbook

        # 获取目标 Target 对象
        target_ids = [t.get("target_id") for t in target_list if t.get("target_id")]
        if not target_ids:
            raise ValueError("未找到有效的目标ID")

        targets = list(Target.objects.filter(id__in=target_ids))
        if not targets:
            raise ValueError("未找到有效的目标记录")

        # 按云区域分组，当前仅取第一个云区域
        region_targets = {}
        for target in targets:
            region_id = target.cloud_region_id
            if region_id not in region_targets:
                region_targets[region_id] = []
            region_targets[region_id].append(target)

        if len(region_targets) > 1:
            logger.warning(f"[{task_name}] 检测到多个云区域，当前仅使用第一个云区域执行")

        cloud_region_id = list(region_targets.keys())[0]
        region_target_list = region_targets[cloud_region_id]

        # 获取 Ansible 执行节点
        ansible_node_id = cls._get_ansible_node(cloud_region_id)

        # 构建主机凭据
        host_credentials = cls._build_host_credentials(region_target_list)

        # 构建回调配置
        callback_config = {
            "subject": f"{NATS_NAMESPACE}.ansible_task_callback",
            "timeout": 30,
        }

        # 构建 extra_vars（从 execution.params 和 playbook.params 还原）
        extra_vars = cls._build_extra_vars(execution.params, playbook.params)

        # 构建文件列表（Playbook ZIP 存储在 MinIO）
        files = []
        if playbook.file:
            files.append(
                {
                    "name": playbook.file_name,
                    "file_key": playbook.file_key,
                    "bucket_name": playbook.bucket_name,
                }
            )

        # 调用 AnsibleExecutor.playbook()
        executor = AnsibleExecutor(ansible_node_id)
        result = executor.playbook(
            playbook_path="playbook.yml",
            host_credentials=host_credentials,
            files=files,
            extra_vars=extra_vars,
            callback=callback_config,
            task_id=str(execution.id),
            timeout=execution.timeout,
        )

        logger.info(f"[{task_name}] Ansible Playbook 任务已提交: execution_id={execution.id}, result={result}")

    @staticmethod
    def _build_extra_vars(params_str: str, playbook_params: list) -> dict:
        """
        从执行记录的 params 字符串和 Playbook 参数定义还原 extra_vars 字典

        execution.params 存储的是空格分隔的值字符串（如 "value1 value2"），
        playbook.params 存储的是参数定义列表（如 [{name, default, ...}]）。
        按顺序将值映射回参数名。

        Args:
            params_str: 执行记录的参数字符串
            playbook_params: Playbook 参数定义列表

        Returns:
            dict: {param_name: param_value}
        """
        if not params_str or not playbook_params:
            return {}

        try:
            values = shlex.split(params_str)
        except ValueError:
            values = params_str.split()

        extra_vars = {}
        for i, param_def in enumerate(playbook_params):
            name = param_def.get("name", "")
            if not name:
                continue
            if i < len(values):
                extra_vars[name] = values[i]
            elif param_def.get("default"):
                extra_vars[name] = param_def["default"]

        return extra_vars
