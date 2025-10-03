import copy
from typing import Dict, Any, Optional

from lounger.libs import jmespath
from lounger.log import log
from lounger.utils.cache import cache


def _save_extracted_values(key: str, result: Any) -> None:
    """
    Save extracted values, handling both single values and lists
    
    :param key: Variable name
    :param result: Extracted value or list of values
    """
    if isinstance(result, list):
        for i, item in enumerate(result):
            cache.set()
            cache.set({f"{key}_{i}": item})
    else:
        cache.set({key: result})


def extract_value(resp: Any, expr: str) -> Any:
    """
    Extract value from response
    
    :param resp: Response object
    :param expr: Extraction expression
    """
    # Prepare response object
    prepared_resp = copy.deepcopy(resp)

    if prepared_resp is not None:
        # Set method as attribute
        try:
            resp_json = prepared_resp.json()
            value = jmespath.jmespath(resp_json, expr)
            return value
        except ValueError as e:
            log.error(f"The response is not a valid JSON: {e}")
            return None

    return None


def save_var(resp: Any, data: Optional[Dict[str, str]]) -> None:
    """
    Save API association intermediate variables
    
    :param resp: API response object
    :param data: Extraction parameters
    """
    if not data:
        log.warning("API association variable extraction not set")
        return

    for key, value in data.items():
        # Extract value
        result = extract_value(resp, value)
        if result is None:
            log.warning(f"Extracted variable is None: expression={value}")
            continue

        # Save value
        _save_extracted_values(key, result)
