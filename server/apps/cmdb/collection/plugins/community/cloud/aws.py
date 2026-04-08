from apps.cmdb.collection.collect_plugin.aws import AWSCollectMetrics
from apps.cmdb.collection.plugins.base import AutoRegisterCollectionPluginMixin, bind_collection_mapping
from apps.cmdb.constants.constants import CollectPluginTypes


class AWSCloudCollectionPlugin(AutoRegisterCollectionPluginMixin, AWSCollectMetrics):
    supported_task_type = CollectPluginTypes.CLOUD
    supported_model_id = "aws"
    plugin_source = "community"
    priority = 10

    metric_names = [
        "aws_cloudfront_info_gauge",
        "aws_docdb_info_gauge",
        "aws_ec2_info_gauge",
        "aws_eks_info_gauge",
        "aws_elasticache_info_gauge",
        "aws_elb_info_gauge",
        "aws_memdb_info_gauge",
        "aws_msk_info_gauge",
        "aws_rds_info_gauge",
        "aws_s3_bucket_info_gauge",
    ]

    field_mappings = {
        "aws_cloudfront": {
            "inst_name": "inst_name",
            "organization": "organization",
            "resource_name": "resource_name",
            "resource_id": "resource_id",
            "status": "status",
            "domain": "domain",
            "aliase_domain": "aliase_domain",
            "modify_time": "modify_time",
            "price_class": "price_class",
            "http_version": "http_version",
            "ssl_method": "ssl_method",
        },
        "aws_docdb": {
            "inst_name": "inst_name",
            "organization": "organization",
            "resource_name": "resource_name",
            "resource_id": "resource_id",
            "region": "region",
            "status": "status",
            "inst_num": "inst_num",
            "port": "port",
            "engine": "engine",
            "engine_version": "engine_version",
            "parameter_group": "parameter_group",
            "maintenance_window": "maintenance_window",
        },
        "aws_ec2": {
            "inst_name": "inst_name",
            "organization": "organization",
            "resource_name": "resource_name",
            "resource_id": "resource_id",
            "ip_addr": "ip_addr",
            "public_ip": "public_ip",
            "region": "region",
            "zone": "zone",
            "vpc": "vpc",
            "status": "status",
            "instance_type": "instance_type",
            "vcpus": "vcpus",
            "key_name": "key_name",
        },
        "aws_eks": {
            "inst_name": "inst_name",
            "organization": "organization",
            "resource_name": "resource_name",
            "resource_id": "resource_id",
            "region": "region",
            "status": "status",
            "k8s_version": "k8s_version",
        },
        "aws_elasticache": {
            "inst_name": "inst_name",
            "organization": "organization",
            "resource_name": "resource_name",
            "resource_id": "resource_id",
            "region": "region",
            "status": "status",
            "engine": "engine",
            "node_type": "node_type",
            "node_num": "node_num",
            "backup_window": "backup_window",
        },
        "aws_elb": {
            "inst_name": "inst_name",
            "organization": "organization",
            "resource_name": "resource_name",
            "resource_id": "resource_id",
            "region": "region",
            "zone": "zone",
            "vpc": "vpc",
            "scheme": "scheme",
            "status": "status",
            "type": "type",
            "dns_name": "dns_name",
        },
        "aws_memdb": {
            "inst_name": "inst_name",
            "organization": "organization",
            "resource_name": "resource_name",
            "resource_id": "resource_id",
            "region": "region",
            "node_type": "node_type",
            "shards_num": "shards_num",
            "node_num": "node_num",
            "status": "status",
            "engine_version": "engine_version",
            "parameter_group": "parameter_group",
            "endpoint": "endpoint",
            "maintenance_window": "maintenance_window",
        },
        "aws_msk": {
            "inst_name": "inst_name",
            "organization": "organization",
            "resource_name": "resource_name",
            "resource_id": "resource_id",
            "region": "region",
            "node_type": "node_type",
            "node_num": "node_num",
            "node_disk": "node_disk",
            "status": "status",
            "cluster_version": "cluster_version",
        },
        "aws_rds": {
            "inst_name": "inst_name",
            "organization": "organization",
            "resource_name": "resource_name",
            "resource_id": "resource_id",
            "region": "region",
            "zone": "zone",
            "vpc": "vpc",
            "status": "status",
            "instance_type": "instance_type",
            "engine": "engine",
            "engine_version": "engine_version",
            "parameter_group": "parameter_group",
            "endpoint": "endpoint",
            "maintenance_window": "maintenance_window",
            "ca": "ca",
            "ca_start_date": "ca_start_date",
            "ca_end_date": "ca_end_date",
        },
        "aws_s3_bucket": {
            "inst_name": "inst_name",
            "organization": "organization",
            "resource_name": "resource_name",
            "resource_id": "resource_id",
            "region": "region",
            "create_date": "create_date",
        },
    }

    @property
    def _metrics(self):
        return list(self.metric_names)

    @property
    def model_field_mapping(self):
        return {
            model_id: bind_collection_mapping(self, mapping)
            for model_id, mapping in self.field_mappings.items()
        }