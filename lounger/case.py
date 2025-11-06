from time import sleep
from typing import Dict, Any

import pytest

from lounger.commons.assert_result import api_validate
from lounger.commons.extract import extract_var
from lounger.commons.model import verify_model
from lounger.commons.request import request_client
from lounger.commons.template_engine import template_replace
from lounger.log import log


def execute_teststeps(teststeps: Dict) -> None:
    """
    execute the test steps
    :param teststeps
    """
    test_name = teststeps["name"]
    test_steps = teststeps["steps"]
    file_path = teststeps["file"]

    log.info(f"✅ Starting test case: {test_name}")
    log.info(f"📁 Source file: {file_path}")
    log.info(f"🔧 Contains {len(test_steps)} step(s)")

    for i, step in enumerate(test_steps):
        step_name = step.get("name", f"step_{i + 1}")
        log.info(f"🔹 Executing step {i + 1}/{len(teststeps)}: {step_name}")
        execute_step(step)


def execute_step(case_step: Dict[str, Any]) -> None:
    """
    Execute a test step
    
    :param case_step: Test case step
    :return: None
    :raises Exception: If test case execution fails
    """
    step_name = case_step.get('name')
    log.info(f"Executing test step: {step_name}")

    try:
        # Verify model and replace templates
        validated_case = verify_model(case_step)
        processed_case = template_replace(validated_case)

        # Send request
        resp = request_client.send_request(**processed_case["request"])

        # sleep
        sec = processed_case.get("sleep", 0)
        if sec != 0:
            log.info(f"💤 sleep: {sec}s")
            sleep(sec)

        # Code for variable extraction and API validation is commented out
        extract_var(resp, processed_case.get("extract"))
        api_validate(resp, processed_case.get("validate"))

    except Exception as e:
        pytest.fail(f"❌ Test case execution failed: {str(e)}")
