from typing import Dict, Any, Optional

import requests

from lounger.libs import jmespath
from lounger.log import log

# Assertion types
ASSERT_TYPES: dict = {
    # assertion_type: expects (expected, actual) -> bool
    "equal": lambda expect, actual: expect == actual,  # Assert equality
    "not_equal": lambda expect, actual: expect != actual,  # Assert inequality
    "contains": lambda expect, actual: expect in actual,  # Assert that actual contains expected
    "not_contains": lambda expect, actual: expect not in actual,  # Assert that actual does not contain expected
    "type": lambda expect, actual: type(expect) == type(actual),  # Assert data type match
    "length": lambda expect, actual: int(expect) == len(actual),  # Assert length match
}


def _get_actual_value(resp: requests.Response, expr: str):
    """
    Extract the actual value from the API response based on the given expression.

    Supported expression formats:
    - "status_code": returns the HTTP status code (e.g., 200)
    - "headers.<key>": returns the value of the specified response header (e.g., "headers.Content-Type")
    - "body.<jmespath>": treats <jmespath> as a JMESPath expression applied to the JSON response body
    - Any other expression: treated as a JMESPath expression applied directly to the JSON response body
      (equivalent to prepending "body.")

    :param resp: Response object from the API request
    :param expr: Expression string to extract value, e.g.,
                "status_code",
                "headers.Content-Type",
                "body.code", or "data.name"
    """
    if expr == "status_code":
        return resp.status_code
    elif expr.startswith("headers."):
        header_key = expr[8:]
        return resp.headers.get(header_key)
    elif expr.startswith("body."):
        jmes_expr = expr[5:]
        json_data = resp.json()
        return jmespath.jmespath(json_data, jmes_expr)
    else:
        json_data = resp.json()
        return jmespath.jmespath(json_data, expr)


def api_validate(resp: requests.Response, validate_value: Optional[Dict[str, Any]]) -> None:
    """
    Validate API response against the specified assertion rules

    :param resp: Response object from API request
    :param validate_value: Dictionary containing assertion rules, e.g.:
        {
            "equal": [["status_code", 200], ["body.code", 10200]],
            "not_equal": [["body.data.name", "jack"]],
            "contains": [["body.message", "succ"]],
            "not_contains": [["body.message", "access"]]
        }
    """
    if not validate_value:
        return

    for assert_type, assertions in validate_value.items():
        if assert_type not in ASSERT_TYPES:
            log.warning(f"Unsupported assertion type: {assert_type}")
            continue

        if not isinstance(assertions, list):
            log.error(f"Assertion value for '{assert_type}' must be a list of [expr, expected]")
            continue

        for item in assertions:
            if not isinstance(item, list) or len(item) != 2:
                log.error(f"Invalid assertion format: {item}. Expected [expr, expected]")
                continue

            expr, expected = item
            actual = _get_actual_value(resp, expr)
            assert_func = ASSERT_TYPES[assert_type]
            result = assert_func(expected, actual)

            if result:
                if assert_type == "length":
                    log.info(
                        f"[{assert_type}] assertion passed: expr={expr}, expected={expected}, actual_length={len(actual)}")
                else:
                    log.info(f"[{assert_type}] assertion passed: expr={expr}, expected={expected}, actual={actual}")
            else:
                log.error(f"[{assert_type}] assertion failed: expr={expr}, expected={expected}, actual={actual}")
                raise AssertionError(
                    f"[{assert_type}] assertion failed: {expr} → expected {expected}, got {actual}")
