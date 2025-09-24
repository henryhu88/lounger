import csv
from typing import Any, Dict

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


def read_csv(csv_path: str):
    """
    CSV文件读取
    :param csv_path: 文件路径
    :return: 文件数据
    """
    try:
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f, delimiter=","))
    except Exception as e:
        log.error(f"读取csv文件时发生错误: {e}")
        return None


def write_extract(data: Dict):
    """
    数据写入保存
    :param data: 数据
    :return:
    """
    with open("extract.yaml", "a+", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)
