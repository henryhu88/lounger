from typing import Dict, Any

from lounger.commons.all_request import request_client
from lounger.commons.assert_result import api_validate
from lounger.commons.model import verify_model
from lounger.commons.template import template_replace
from lounger.commons.var_extract import save_var
from lounger.log import log


def execute_case(case_step: Dict[str, Any]) -> None:
    """
    Execute a test case
    
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

        # Code for variable extraction and API validation is commented out
        save_var(resp, processed_case.get("extract"))
        api_validate(resp, processed_case.get("validate"))

    except Exception as e:
        log.error(f"Test case execution failed: {e}")
        raise
