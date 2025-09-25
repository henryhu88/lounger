import logging
from typing import Dict, Any, List, Optional

import requests

from lounger.commons.var_extract import extract_value
from lounger.config import ASSERT_TYPES

logger = logging.getLogger(__name__)


def api_validate(resp: requests.Response, validate_value: Optional[Dict[str, Any]]) -> None:
    """
    Validate API response against the specified assertion rules
    
    :param resp: Response object from API request
    :param validate_value: Dictionary containing assertion rules
    """
    if not validate_value:
        logger.warning("No assertions configured")
        return

    for assert_type, assert_value in validate_value.items():
        logger.info(f"Performing [{assert_type}] assertion...")
        try:
            if assert_type in ASSERT_TYPES:
                # Check if it's a multi-level assertion
                if (assert_value is not None and
                        isinstance(assert_value, list) and
                        all(isinstance(item, list) and len(item) == 4 for item in assert_value)):
                    for assert_data in assert_value:
                        assert_handle(resp, assert_type, assert_data)
                else:
                    # Single-level assertion
                    assert_handle(resp, assert_type, assert_value)
            else:
                logger.warning(f"Unsupported assertion type: {assert_type}")
        except Exception as e:
            logger.error(f"Assertion failed: {e}")
            raise


def assert_handle(resp: requests.Response, assert_type: str, assert_value: List[Any]) -> None:
    """
    Handle individual assertion checks
    
    :param resp: API response object
    :param assert_type: Type of assertion to perform
    :param assert_value: Assertion parameters
    """
    if len(assert_value) == 4:  # Check if assertion parameters are complete
        expect, value_type, expr, index = assert_value
        index = 0 if index == "" else index  # Default to 0 if index is empty
        logger.info(f"Extracting assertion variable: extraction method={value_type}, extraction expression={expr}")

        actual = extract_value(resp, value_type, expr, index)
        assert_func = ASSERT_TYPES.get(assert_type)

        if not assert_func:
            logger.warning(f"Assertion function not found for type: {assert_type}")
            return

        result = assert_func(expect, actual)
        if not result:
            logger.error(f"{assert_type} assertion failed, expected={expect}, actual={actual}")
        else:
            if assert_type == 'length':
                logger.info(f"{assert_type} assertion passed, expected={expect}, actual_length={len(actual)}")
            else:
                logger.info(f"{assert_type} assertion passed, expected={expect}, actual={actual}")
    else:
        logger.warning(f"{assert_type} assertion parameters missing, please check: {assert_value}")
