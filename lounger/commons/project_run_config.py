from lounger.utils.get_configs import config_utils

from typing import List, Tuple, Dict, Any

from lounger.utils.get_configs import ConfigUtils

config_utils = ConfigUtils("config/config.yaml")
project_config = config_utils.get_config("test_project")

def get_project_config() -> Tuple[List[str], List[str]]:
    """
    Get project run configuration to determine which projects need to be tested
    
    :return: Tuple containing two lists: projects to test and projects to skip
    """
    # Store projects that need to be tested
    need_test_projects: List[str] = []
    # Store projects that don't need to be tested
    skip_test_projects: List[str] = []

    # Determine which projects need to be tested
    for project_name, project_value in project_config.items():
        # Single project execution
        if project_name == "single_file" and project_value:
            need_test_projects.append(project_name)
        # Multi-project execution
        else:
            if project_value:
                need_test_projects.append(project_name)
            else:
                skip_test_projects.append(project_name)
    
    return need_test_projects, skip_test_projects



def get_project_name() -> List[str]:
    """
    Get list of project names from the test project configuration.
    
    :return: List of project names
    """
    # Extract project names from the test project configuration keys
    return list(config_utils.get_config('test_project').keys())
