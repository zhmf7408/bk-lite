from apps.cmdb.collection.collect_util import timestamp_gt_one_day_ago
from apps.cmdb.collection.plugins.base import BaseCollectionPlugin, bind_collection_mapping
from apps.cmdb.constants.constants import CollectPluginTypes
from apps.core.logger import cmdb_logger as logger


class BaseDBCollectionPlugin(BaseCollectionPlugin):
    supported_task_type = CollectPluginTypes.DB
    metric_names = ()
    field_mapping = {}

    @property
    def _metrics(self):
        if not self.metric_names:
            raise AssertionError(f"{self.__class__.__name__} needs metric_names")
        return list(self.metric_names)

    @property
    def model_field_mapping(self):
        return {self.model_id: bind_collection_mapping(self, self.field_mapping)}

    def format_data(self, data):
        for index_data in data.get("result", []):
            metric_name = index_data["metric"]["__name__"]
            value = index_data["value"]
            _time, value = value[0], value[1]
            if not self.timestamp_gt:
                if timestamp_gt_one_day_ago(_time):
                    break
                self.timestamp_gt = True
            index_dict = dict(
                index_key=metric_name,
                index_value=value,
                **index_data["metric"],
            )
            self.collection_metrics_dict[metric_name].append(index_dict)

    def get_inst_name(self, data):
        return f"{data['ip_addr']}-{self.model_id}-{data['port']}"

    def format_metrics(self):
        for metric_key, metrics in self.collection_metrics_dict.items():
            result = []
            mapping = self.model_field_mapping.get(self.model_id, {})
            for index_data in metrics:
                data = {}
                for field, key_or_func in mapping.items():
                    if isinstance(key_or_func, tuple):
                        try:
                            data[field] = key_or_func[0](index_data[key_or_func[1]])
                        except Exception as exc:  # noqa: BLE001 - 单字段格式化失败不阻断单条数据构建
                            logger.error("数据转换失败 field:%s, value:%s, error:%s", field, index_data.get(key_or_func[1]), exc)
                    elif callable(key_or_func):
                        try:
                            data[field] = key_or_func(index_data)
                        except Exception as exc:  # noqa: BLE001 - 单字段格式化失败不阻断单条数据构建
                            logger.error("数据处理转换失败 field:%s, error:%s", field, exc)
                    else:
                        data[field] = index_data.get(key_or_func, "")
                if data and data.get("inst_name"):
                    result.append(data)
            self.result[self.model_id] = result