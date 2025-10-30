from typing import Dict, Any

import requests
from pytest_req.plugin import Session

from lounger.log import log
from lounger.utils.config_utils import ConfigUtils


class RequestClient:
    """
    HTTP client wrapper for handling API request
    """

    def __init__(self):
        """
        Initialize the HTTP client with base URL
        """
        config_file = ConfigUtils("config/config.yaml")
        base_url = config_file.get_config("base_url")
        self._session = Session(base_url)

    @staticmethod
    def _files_load(files_dict: Dict[str, str]) -> Dict[str, Any]:
        """
        Process file upload parameters
        
        :param files_dict: File upload parameters dictionary
        :return: Processed file upload parameters
        :raises Exception: If file processing fails
        """
        files = {}
        try:
            for file_name, file_path in files_dict.items():
                files[file_name] = open(file_path, "rb")
            return files
        except Exception as e:
            log.error(f"File upload parameters processing failed: {e}")
            raise e

    def send_request(self, **kwargs: Dict[str, Any]) -> requests.Response:
        """
        Unified API request handler
        
        :param kwargs: Parameters for API request
        :return: Response object
        :raises Exception: If API request fails
        :raises NotImplementedError: If HTTP method is not supported
        """
        try:
            # Process files if present
            if "files" in kwargs:
                kwargs["files"] = self._files_load(kwargs["files"])

            # Add content type for JSON requests
            if "json" in kwargs:
                kwargs['headers'] = kwargs.get('headers') or {}
                kwargs['headers'].setdefault('Content-Type', 'application/json')

            # Get method and URL
            method = kwargs.pop("method", "GET").upper()
            url = kwargs.pop("url", "")

            # Send request based on method
            method_handlers = {
                "GET": self._session.get,
                "POST": self._session.post,
                "PUT": self._session.put,
                "DELETE": self._session.delete
            }

            if method not in method_handlers:
                raise NotImplementedError(f"Only supported methods: {', '.join(method_handlers.keys())}")

            resp = method_handlers[method](url, **kwargs)

            # Content type handling (commented out but kept for reference)
            # content_type = resp.headers.get("Content-Type", "")

            return resp
        except Exception as e:
            log.error(f"API request failed: {e}")
            raise e


# Create a singleton instance of the request client
request_client = RequestClient()
