import os
import pytest
from typing import Any, Optional, List, Tuple
import yaml

from lounger.log import log
from lounger.commons.run_config import get_case_path


def read_yaml(yaml_path: str, key: Optional[str] = None) -> Any:
    """
    Read a YAML file and return its content.

    :param yaml_path: Path to the YAML file
    :param key: Optional key to extract a specific node
    """
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if key is None:
                return data
            return data.get(key) if isinstance(data, dict) else None
    except Exception as e:
        log.error(f"Error occurred while reading YAML file: {e}")
        return None


def load_test_file() -> List[Tuple[str, str]]:
    """
    load all YAML file
    """
    cases = []
    for file_path in get_case_path():
        file_name = os.path.basename(file_path).replace('.yaml', '')
        cases.append((f"test_{file_name}", file_path))

    return cases


def load_cases():
    return pytest.mark.parametrize("test_name,file_path", load_test_file())
