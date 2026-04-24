from django.utils.timezone import now

from apps.cmdb.models.collect_model import CollectModels
from apps.cmdb.services.config_file_service import ConfigFileService
from apps.core.logger import cmdb_logger as logger


class ConfigFileCollect(object):
    """配置文件采集状态查询类。"""

    def __init__(self, task_id: int):
        self.task = CollectModels.objects.get(id=task_id)
        self.params = dict(self.task.params or {})
        self.file_path = self.params.get("config_file_path", "")
        self.version = now().strftime("%Y-%m-%dT%H:%M:%S")

    def __call__(self):
        logger.info(
            "[ConfigFileCollect] 查询最新采集状态 task_id=%s, path=%s, instance=%s",
            self.task.id,
            self.file_path,
            self.task.instances,
        )
        return ConfigFileService.build_pending_result(self.task)
