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


def load_yaml_steps(file_path: str) -> List[Dict]:
    """
    Load and extract the first 'teststeps' list from a YAML file.

    :param file_path: Path to the YAML file
    :return: List of step dictionaries
    :raises: RuntimeError if file not found or invalid
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Precondition file not found: {file_path}")

    data = read_yaml(file_path)
    if not data:
        raise RuntimeError(f"Failed to parse or empty YAML file: {file_path}")

    # Find the first 'teststeps' block
    for block in data:
        if isinstance(block, dict) and "teststeps" in block:
            steps = block["teststeps"]
            if isinstance(steps, list):
                return steps
    raise ValueError(f"No 'teststeps' block found in {file_path}")


def load_test_cases() -> List[Tuple[str, List[Dict], str]]:
    """
    Load all test cases from YAML files.

    Each 'teststeps' block in a YAML file is treated as one test case.
    If the first step is a 'presteps' directive, merge the referenced steps at the beginning.

    :return: List of tuples (test_name, merged_steps, source_file)
    """
    testcases = []
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(get_case_path()[0])))  # Project root

    for file_path in get_case_path():
        file_path = os.path.abspath(file_path)
        filename = os.path.basename(file_path).rsplit(".", 1)[0]  # Remove extension safely

        test_data = read_yaml(file_path)
        if not test_data or not isinstance(test_data, list):
            log.warning(f"YAML file is empty or invalid structure: {file_path}")
            continue

        # Process each 'teststeps' block in the file
        for idx, block in enumerate(test_data):
            if not isinstance(block, dict) or "teststeps" not in block:
                continue

            raw_steps = block["teststeps"]
            if not isinstance(raw_steps, list) or len(raw_steps) == 0:
                log.debug(f"Skipping empty teststeps block in {file_path}")
                continue

            # Determine if the first step is a 'presteps' directive
            merged_steps = raw_steps
            has_presteps = (
                    len(raw_steps) > 0 and
                    isinstance(raw_steps[0], dict) and
                    "presteps" in raw_steps[0]
            )

            if has_presteps:
                presteps_ref = raw_steps[0]["presteps"]
                main_steps = raw_steps[1:]

                # Resolve path relative to project root
                presteps_path = os.path.normpath(os.path.join(project_root, presteps_ref))

                log.info(f"🔁 Loading pre-steps from: {presteps_ref}")

                try:
                    presteps = load_yaml_steps(presteps_path)
                    merged_steps = presteps + main_steps
                    log.info(f"✅ Merged {len(presteps)} pre-step(s) into test case")
                except Exception as e:
                    log.error(f"❌ Failed to load pre-steps '{presteps_ref}': {str(e)}")
                    continue  # Skip this test case if pre-steps are missing/broken

            # Generate test name using first actual step (after merge)
            first_step = merged_steps[0] if merged_steps else {"name": "unnamed_step"}
            step_name = first_step.get("name", f"step_1")
            test_name = f"{filename}::case_{idx + 1}_{step_name}"

            testcases.append((test_name, merged_steps, file_path))

    # Final logging
    if not testcases:
        log.warning("No valid test cases loaded from YAML files.")
    else:
        log.info(f"✅ Successfully loaded {len(testcases)} test case(s)")

    return testcases


def load_teststeps():
    """
    Pytest decorator factory to parametrize test cases.
    Loads test cases and returns pytest.mark.parametrize with proper args and IDs.
    """
    cases = load_test_cases()
    return pytest.mark.parametrize(
        "test_name, teststeps, file_path",
        cases,
        ids=[tc[0] for tc in cases]  # Use test_name as display ID in pytest
    )
