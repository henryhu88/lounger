import json

import pytest


class JsonCollector:
    def __init__(self):
        self.test_data = []

    def pytest_collection_modifyitems(self, items):
        """
        Collect test cases and handle parameterized tests by extracting case names
        from parameters and appending them to docstrings.
        """
        # Collect all test case information
        for item in items:
            # Extract basic test case information
            case_info = {
                "file": str(item.fspath),  # File path
                "nodeid": item.nodeid,  # Unique identifier
                "name": item.name,  # Method name
                "parent": item.parent.name,  # Class name or module name
                "description": item.obj.__doc__,  # Docstring (comments)
                "markers": [m.name for m in item.own_markers]  # Decorators/tags
            }
            self.test_data.append(case_info)


def get_test_cases(path):
    collector = JsonCollector()
    # Use --collect-only parameter to prevent test execution
    pytest.main([
        "--collect-only",
        "-W", "ignore::pytest.PytestAssertRewriteWarning",
        path
    ], plugins=[collector])
    return collector.test_data


if __name__ == "__main__":
    cases = get_test_cases("./")
    print(json.dumps(cases, indent=4, ensure_ascii=False))
