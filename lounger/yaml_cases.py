import os
from typing import Any, Optional, List, Tuple, Dict

import pytest
import yaml

from lounger.commons.run_config import get_case_path
from lounger.log import log


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


def load_test_cases() -> List[Tuple[str, List[Dict], str]]:
    """
    Load all YAML files and extract each 'teststeps' block as a single test case.
    Returns: List[(test_name, teststeps_list, source_file)]
    """
    testcases = []
    for file_path in get_case_path():
        file_name = os.path.basename(file_path).replace(".yaml", "")
        test_data = read_yaml(file_path)

        if not test_data:
            log.warning(f"YAML file is empty or failed to parse: {file_path}")
            continue

        # Iterate over each 'teststeps' block (a file can have multiple blocks)
        for idx, block in enumerate(test_data):
            if "teststeps" not in block:
                continue

            teststeps = block["teststeps"]
            if not isinstance(teststeps, list) or len(teststeps) == 0:
                continue

            # Generate test name: filename + case index + first step name
            first_step_name = teststeps[0].get("name", f"step_0")
            test_name = f"{file_name}::case_{idx + 1}_{first_step_name}"

            testcases.append((test_name, teststeps, file_path))

    if not testcases:
        log.warning("No teststeps test cases loaded.")
    else:
        log.info(f"Loaded {len(testcases)} teststeps test cases.")

    return testcases


def load_teststeps():
    return pytest.mark.parametrize(
        "test_name, teststeps, file_path",
        load_test_cases(),
        ids=[tc[0] for tc in load_test_cases()]  # Display clear test names in reports
    )
