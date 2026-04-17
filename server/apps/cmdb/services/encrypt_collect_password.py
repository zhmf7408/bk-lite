# -- coding: utf-8 --
# @File: encrypt_collect_password.py
# @Time: 2025/12/10 10:53
# @Author: windyzhao

from apps.cmdb.services.collect_object_tree import get_collect_object_meta


def get_collect_model_passwords(collect_model_id, driver_type=None):
    """
    获取采集模型所需的加密密码字典 从COLLECT_OBJ_TREE的encrypted_fields字段中提取
    :param collect_model_id: 采集模型名称
    :return: 加密密码字典
    """
    collect_object_meta = get_collect_object_meta(collect_model_id, driver_type=driver_type)
    return collect_object_meta.get("encrypted_fields", [])
