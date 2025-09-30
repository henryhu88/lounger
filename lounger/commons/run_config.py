import glob
from typing import List, Tuple
from pathlib import Path

from lounger.log import log
from lounger.utils.config_utils import ConfigUtils

CONFIG_FILE = ConfigUtils("config/config.yaml")
TEST_PROJECTS = CONFIG_FILE.get_config("test_project")
BASE_URL = CONFIG_FILE.get_config("base_url")


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

        # If all supported projects need to be tested, return all test cases
        if len(need_test_projects) >= len(project_name_list):
            return glob.glob("datas/**/*.yaml", recursive=True)

        case_path = _get_specific_test_cases(need_test_projects, project_name_list)
        return case_path
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
        if project_name in supported_projects and project_name != 'single_file':
            # Get all test cases under the specified project
            project_cases = [
                str(path.as_posix())
                for path in Path("datas", project_name).rglob("*.yaml")
            ]
        else:
            # Custom file or file list
            project_cases = _get_custom_cases(project_name)

        case_paths.extend(project_cases)

    return case_paths


def _get_custom_cases(case_specification: str) -> List[str]:
    """
    Get custom test cases

    :param case_specification: Case specification, can be a single file name or comma-separated file names
    """
    case_paths = []
    case_name = CONFIG_FILE.get_config("test_project", case_specification)

    # Handle multiple files separated by commas
    case_names = [name.strip() for name in case_name.split(",")]

    for case_name in case_names:
        if case_name:  # Ensure it's not empty
            file_cases = glob.glob(f"datas/**/{case_name}.yaml", recursive=True)
            case_paths.extend(file_cases)

    return case_paths
