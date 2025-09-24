from typing import Dict, Any, Optional
import yaml

from lounger.log import log

class ConfigUtils:
    """
    Configuration utility class for loading and accessing YAML configuration files.
    This is a general-purpose class that requires configuration file path and config node to be passed explicitly.
    """

    def __init__(self, config_file_path: str):
        """
        Initialize the ConfigUtils with the path to the YAML configuration file.
        
        :param config_file_path: Path to the YAML configuration file
        :raises FileNotFoundError: If the configuration file does not exist
        """
        self.config_file_path = config_file_path
        # Verify the file exists during initialization
        try:
            with open(self.config_file_path, 'r', encoding='utf-8'):
                pass
        except FileNotFoundError:
            log.error(f"Configuration file not found: {self.config_file_path}")
            raise

    def _get_config_file_data(self) -> Dict[str, Any]:
        """
        Get configuration file data.
        
        :return: Dictionary containing the configuration file data
        :raises Exception: If there's an error loading the configuration file
        """
        try:
            with open(self.config_file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data is None:
                    log.warning(f"Configuration file is empty: {self.config_file_path}")
                    return {}
                return data
        except Exception as e:
            log.error(f"Failed to load configuration file {self.config_file_path}: {e}")
            raise

    def get_config(self, config_node: str, config_key: Optional[str] = None) -> Any:
        """
        Get configuration from the specified node or from a specific key within the node.
        
        :param config_node: Name of the configuration node
        :param config_key: Optional key within the configuration node
        :return: Configuration data for the node or specific key
        """
        try:
            config_data = self._get_config_file_data()
            
            if config_node not in config_data:
                log.warning(f"Configuration node '{config_node}' not found")
                raise KeyError(f"Configuration node '{config_node}' not found")
            
            if config_key is not None:
                if config_key not in config_data[config_node]:
                    log.warning(f"Configuration key '{config_key}' not found in node '{config_node}'")
                    raise KeyError(f"Configuration key '{config_key}' not found in node '{config_node}'")
                return config_data[config_node][config_key]
            
            return config_data[config_node]
        except Exception as e:
            log.error(f"Failed to get configuration: {e}")
            raise e


# Default instance using the standard configuration file path
config_utils = ConfigUtils("config/config.yaml")
