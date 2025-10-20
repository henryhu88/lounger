import os
from pathlib import Path
from typing import List, Tuple, Any

from lounger.log import log
from lounger.utils.config_utils import ConfigUtils
from lounger.utils.hot_loads import ExtractVar

CONFIG_FILE = ConfigUtils("config/config.yaml")
TEST_PROJECTS = CONFIG_FILE.get_config("test_project")
BASE_URL = CONFIG_FILE.get_config("base_url")


def global_test_config(key: str) -> Any:
    """
    get global test config
    param: key
    """
    var = ExtractVar()
    value = var.config(key)
    return value


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
    for project_name, project_value in TEST_PROJECTS.items():
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
    return list(CONFIG_FILE.get_config('test_project').keys())


def get_case_path() -> List[str]:
    """
    Get test case paths based on project configuration
    """
    project_name_list = get_project_name()
    log.info(f"project_name_list: {project_name_list}")
    try:
        need_test_projects, skip_test_projects = get_project_config()
        log.info("=== Read Test Configuration ===")
        log.info(f"Running tests: {need_test_projects}")
        log.info(f"Skipped tests: {skip_test_projects}")

        if not need_test_projects:
            log.warning("No projects configured for testing")
            return []

        # Get execute YAML files
        valid_need_projects = [proj for proj in need_test_projects if proj in project_name_list]
        all_paths = _get_specific_test_cases(valid_need_projects, project_name_list)

        # === Sort: global_setup | normal | global_teardown ===
        setup_paths = []
        teardown_paths = []
        normal_paths = []

        for path in all_paths:
            abs_path = os.path.abspath(path)
            norm_path = abs_path.replace("/", os.sep).lower()

            if "global_setup" in norm_path:
                setup_paths.append(abs_path)
            elif "global_teardown" in norm_path:
                teardown_paths.append(abs_path)
            else:
                normal_paths.append(abs_path)

        sorted_paths = setup_paths + normal_paths + teardown_paths

        return sorted_paths
    except Exception as e:
        log.error(f"Failed to get test case paths: {e}")
        return []


def _get_specific_test_cases(
        need_test_projects: List[str], supported_projects: List[str]
) -> List[str]:
    """
    Get test cases for specific projects

    :param need_test_projects: List of projects to test
    :param supported_projects: List of supported projects
    :return: List of test case paths
    """
    case_paths = []

    for project_name in need_test_projects:
        if project_name in supported_projects:
            # Get all test cases under the specified project
            project_cases = [
                str(path.as_posix())
                for path in Path("datas", project_name).rglob("*.yaml")
                if path.stem.startswith("test_") or path.stem.endswith("_test")
            ]

            case_paths.extend(project_cases)

    return case_paths
