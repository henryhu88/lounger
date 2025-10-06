import base64
from typing import Any

from lounger.log import log
from lounger.utils import cache
from lounger.utils.config_utils import ConfigUtils

config_utils = ConfigUtils("config/config.yaml")
base_config = config_utils.get_config('base_test_config')


class ExtractVar:
    """
    Extract variables
    """

    @staticmethod
    def config(key: str) -> Any:
        """
        Extract from the config file
        :param key:
        """
        try:
            return base_config.get(key)
        except Exception as e:
            log.error(f"getting config error: {e}")
            return None

    @staticmethod
    def extract(key: str) -> Any:
        """
        Extract from the cache
        :param key：
        """
        return cache.get(key)

    @staticmethod
    def base64_encode(text: str):
        """
        base64 encode
        :param text:
        """
        try:
            if isinstance(text, str):
                text = text.encode("utf-8")
            return base64.b64encode(text).decode("utf-8")
        except Exception as e:
            log.error(f"base64 encode error: {e}")
            return None

    @staticmethod
    def base64_decode(text: str):
        """
        base64 decode
        :param text:
        """
        try:
            if isinstance(text, str):
                text = text.encode("utf-8")
            return base64.b64decode(text).decode("utf-8")
        except Exception as e:
            log.error(f"base64 decode error: {e}")
            return None
