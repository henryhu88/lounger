import re
import threading

import jsonpath


class BrowserConfig:
    """
    Define run browser config
    """
    NAME = None
    REPORT_PATH = None
    REPORT_TITLE = "Lounger Test Report"
    LOG_PATH = None


class Lounger:
    env = None

    _thread_local = threading.local()

    @property
    def action(self):
        """
        playwright locator action
        """
        return getattr(self._thread_local, 'action', None)

    @action.setter
    def action(self, value):
        self._thread_local.action = value


# Assertion types
ASSERT_TYPES: dict = {
    # assertion_type: expects (expected, actual) -> bool
    "contains": lambda expect, actual: expect in actual,  # Assert that actual contains expected
    "equal": lambda expect, actual: expect == actual,  # Assert equality
    "not_equal": lambda expect, actual: expect != actual,  # Assert inequality
    "not_contains": lambda expect, actual: expect not in actual,  # Assert that actual does not contain expected
    "type": lambda expect, actual: type(expect) == type(actual),  # Assert data type match
    "length": lambda expect, actual: int(expect) == len(actual),  # Assert length match
}

# Data extraction methods
EXTRACT_TYPES: dict = {
    # extraction_method: takes (response, expression, index) -> extracted value(s)
    "json": lambda resp, expr, index: jsonpath.jsonpath(resp.json, expr)[index],  # Extract single value via JSONPath
    "text": lambda resp, expr, index: re.findall(expr, resp.text)[index],  # Extract single value via regex/text
    "json_all": lambda resp, expr, index: jsonpath.jsonpath(resp.json, expr),  # Extract multiple values via JSONPath
    "text_all": lambda resp, expr, index: re.findall(expr, resp.text),  # Extract multiple values via regex/text
}
