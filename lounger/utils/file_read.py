from typing import Any

import yaml

from lounger.log import log


def read_yaml(yaml_path: str, key=None) -> Any:
    """
    读取yaml文件
    :param yaml_path: yaml文件路径
    :param key: 节点名称
    :return: 节点数据
    """
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            if key is None:
                return yaml.safe_load(f)
            return yaml.safe_load(f)[key]
    except Exception as e:
        log.error(f"读取yaml文件时发生错误: {e}")
        return None
