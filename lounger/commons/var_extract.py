import copy
from typing import Dict, Any, List, Optional, Union, Callable

from lounger.config import EXTRACT_TYPES
from lounger.log import log
from lounger.utils.file_handle import write_extract

def _save_extracted_values(key: str, result: Any) -> None:
    """
    Save extracted values, handling both single values and lists
    
    :param key: Variable name
    :param result: Extracted value or list of values
    :return: None
    """
    if isinstance(result, list):
        for i, item in enumerate(result):
            write_extract({f"{key}_{i}": item})
    else:
        write_extract({key: result})

def extract_value(resp: Any, save_type: str, expr: str, index: Union[int, str]) -> Any:
    """
    Extract value from response
    
    :param resp: Response object
    :param save_type: Extraction type
    :param expr: Extraction expression
    :param index: Index for extraction
    :return: Extracted value
    """
    # Prepare response object
    prepared_resp = copy.deepcopy(resp)
    
    if save_type in EXTRACT_TYPES and prepared_resp is not None:
        # Set method as attribute
        prepared_resp.json = prepared_resp.json()
        index = index if index != "" else 0
        func: Callable = EXTRACT_TYPES.get(save_type)
        return func(prepared_resp, expr, index)
    
    # Return response attribute value directly
    return getattr(prepared_resp, save_type)

def save_var(resp: Any, data: Optional[Dict[str, List[Any]]]) -> None:
    """
    Save API association intermediate variables
    
    :param resp: API response object
    :param data: Extraction parameters
    :return: None
    """
    if not data:
        log.warning("API association variable extraction not set")
        return
    
    for key, value in data.items():
        try:
            save_type, expr, index = value
            log.info(f"API association variable extraction: extraction method={save_type}, extraction expression={expr}")
            
            # Extract value
            result = extract_value(resp, save_type, expr, index)
            
            # Save value
            _save_extracted_values(key, result)
            log.info(f"Variable extraction successful, variable name: {key}, variable value: {result}")
            return
        except Exception as e:
            log.error(f"Failed to extract variable {key}: {e}")
            return
