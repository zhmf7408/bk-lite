from django.core.management import BaseCommand
from apps.cmdb.services.model import ModelManage
from apps.core.logger import cmdb_logger as logger
from apps.cmdb.model_migrate.migrete_service import ModelMigrate


class Command(BaseCommand):
    help = "初始化模型"

    def handle(self, *args, **options):
        migrator = ModelMigrate()

        # 模型初始化
        logger.info("初始化模型！")
        result = migrator.main()
        ModelManage._apply_model_config_post_import_extras(migrator.model_config)
        logger.info("初始化模型完成！")
        logger.debug(result)
