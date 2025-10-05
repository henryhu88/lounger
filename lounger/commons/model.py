from dataclasses import dataclass
from typing import Dict, Any, Optional

from lounger.log import log


@dataclass
class Model:
    """Data model for test cases"""

    name: str
    request: Dict[str, Any]
    extract: Optional[Dict[str, Any]] = None
    validate: Optional[Dict[str, Any]] = None


def verify_model(case_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify that case information matches the Model structure
    
    :param case_info: Case information to verify
    :return: Verified case information
    :raises Exception: If case information doesn't match the Model structure
    """
    try:
        Model(**case_info)
        return case_info
    except Exception as e:
        log.error(f"Data model verification failed: {e}")
        raise
