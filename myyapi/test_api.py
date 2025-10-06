# test_api.py
from typing import List, Dict

from lounger.case import execute_case
from lounger.log import log
from lounger.yaml_cases import load_teststeps


@load_teststeps()
def test_api(test_name: str, teststeps: List[Dict], file_path: str):
    """
    Execute a test case defined by a 'teststeps' block.
    """
    log.info(f"✅ Starting test case: {test_name}")
    log.info(f"📁 Source file: {file_path}")
    log.info(f"🔧 Contains {len(teststeps)} step(s)")

    for i, step in enumerate(teststeps):
        step_name = step.get("name", f"step_{i + 1}")
        log.info(f"🔹 Executing step {i + 1}/{len(teststeps)}: {step_name}")
        execute_case(step)
