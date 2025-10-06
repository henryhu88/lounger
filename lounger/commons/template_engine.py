import re
from typing import Dict, Any

from lounger.log import log
from lounger.utils import cache
from lounger.utils.hot_loads import ExtractVar

# Precompile regex pattern for performance
TEMPLATE_PATTERN = re.compile(r"\$\{(.*?)\((.*?)\)}")


def _render_value(value: str) -> Any:
    """
    Process a single string value. If it's a template expression, execute it
    and return the result with its original type.
    If not a template, return the value as-is.

    :param value: The input value (should be a string)
    """
    if not isinstance(value, str) or "${" not in value or "}" not in value:
        return value

    # Only match complete template expressions like ${func(args)}
    match = TEMPLATE_PATTERN.fullmatch(value.strip())
    if not match:
        return value

    func_name, func_args = match.groups()
    extract_var = ExtractVar()

    if not hasattr(extract_var, func_name):
        log.warning(f"Function '{func_name}' not found")
        return value

    method = getattr(extract_var, func_name)

    try:
        # Parse arguments (supports $var syntax for cache lookup)
        if not func_args.strip():
            args = []
        else:
            raw_args = [arg.strip() for arg in func_args.split(",")]
            args = []
            for arg in raw_args:
                if arg.startswith("$") and len(arg) > 1:
                    var_value = cache.get(arg[1:])
                    args.append(var_value)
                else:
                    args.append(arg)

        result = method(*args) if args else method()
        log.info(f"Template replaced: {value} → {result} (type: {type(result).__name__})")
        return result

    except Exception as e:
        log.error(f"Failed to execute {value}: {e}")
        return value


def template_replace(case_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively traverse the test case data and replace template expressions
    (e.g., ${config(username)}, ${extract(token)}) with their evaluated values,
    preserving the original data types (e.g., int, bool, str).

    :param case_info: The test case data (dict)
    """

    def _walk(obj):
        if isinstance(obj, dict):
            return {k: _walk(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [_walk(item) for item in obj]
        elif isinstance(obj, str):
            return _render_value(obj)
        else:
            return obj

    return _walk(case_info)
