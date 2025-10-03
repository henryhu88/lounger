from typing import Dict, Any

import pytest

from lounger.commons.all_request import request_client
from lounger.commons.model import verify_model
from lounger.commons.template_replace import replace_template
from lounger.commons.var_extract import save_var
from lounger.log import log


def execute_case(caseinfo: Dict[str, Any]) -> None:
    """
    Execute a test case
    
    :param caseinfo: Test case data
    :return: None
    :raises Exception: If test case execution fails
    """
    model = caseinfo.get('model')
    title = caseinfo.get('title')
    log.info(f"Executing test case: {model}==>{title}")

    try:
        if not caseinfo.get("skip", False):
            # Verify model and replace templates
            validated_case = verify_model(caseinfo)
            processed_case = replace_template(validated_case)

            # Send request
            resp = request_client.send_request(**processed_case["request"])

            # Code for variable extraction and API validation is commented out
            save_var(resp, processed_case.get("extract"))
            # api_validate(resp, processed_case.get("validate"))
        else:
            log.warning(f"Skipping test case: {model}==>{title}")
            pytest.skip(f"Test case skipped: {model}==>{title}")
    except Exception as e:
        log.error(f"Test case execution failed: {e}")
        raise
