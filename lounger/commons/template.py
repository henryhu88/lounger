import json
import re
from typing import Dict, Any

from lounger.log import log
from lounger.utils.hot_loads import ExtractVar

# Precompile regex pattern for performance
TEMPLATE_PATTERN = re.compile(r"\$\{(.*?)\((.*?)\)}")


def template_replace(case_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scan test case data and process templates that need to be replaced
    
    :param case_info: Test case data
    """
    case_info_str = json.dumps(case_info, ensure_ascii=False)

    # Return original case_info if no template expressions need to be replaced
    if "${" not in case_info_str or "}" not in case_info_str:
        return case_info

    matches = TEMPLATE_PATTERN.findall(case_info_str)
    extract_var = ExtractVar()

    if not matches:
        return case_info

    for func_name, func_args in matches:
        old_value = f"${{{func_name}({func_args})}}"

        # Check if method exists
        if not hasattr(extract_var, func_name):
            log.warning(f"Method {func_name} does not exist, please check method name")
            continue

        # Get method and execute with appropriate arguments
        method = getattr(extract_var, func_name)

        try:
            if not func_args:  # No arguments
                new_value = method()
            else:
                if "," in func_args:  # Multiple arguments
                    new_value = method(*[arg.strip() for arg in func_args.split(",")])
                else:  # Single argument
                    new_value = method(func_args)

            # Convert to string for replacement
            new_value_str = str(new_value)

            log.info(f"Template replacement needed for {old_value}, replacing with: {new_value_str}")
            case_info_str = case_info_str.replace(old_value, new_value_str)
        except Exception as e:
            log.error(f"Error executing method {func_name} with args {func_args}: {e}")

    new_case_info = json.loads(case_info_str)
    return new_case_info
