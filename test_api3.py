# test_api.py
from typing import List, Dict

import pytest

from lounger.commons.case import execute_case
from lounger.log import log
from lounger.yaml_cases import load_teststeps


@load_teststeps()
def test_api_case(test_name: str, teststeps: List[Dict], file_path: str):
    """
    Execute a test case defined by a 'teststeps' block (multiple steps in sequence).
    Steps share context (e.g., extracted variables).
    """
    log.info(f"✅ Starting test case: {test_name}")
    log.info(f"📁 Source file: {file_path}")
    log.info(f"🔧 Contains {len(teststeps)} step(s)")

    try:
        for i, step in enumerate(teststeps):
            step_name = step.get("name", f"step_{i + 1}")
            log.info(f"🔹 Executing step {i + 1}/{len(teststeps)}: {step_name}")
            execute_case(step)
    except Exception as e:
        pytest.fail(f"❌ Test case execution failed: {str(e)}")
