"""
lounger CLI
"""
import os
from pathlib import Path

import click
from pytest_req.log import log

from lounger import __version__


@click.command()
@click.version_option(version=__version__, help="Show version.")
@click.option("-pw", "--project-web", help="Create an web automation test project.")
@click.option("-pa", "--project-api", help="Create an api automation test project.")
@click.option("-ya", "--yaml-api", help="Create an YAML api automation test project.")
def main(project_web, project_api, yaml_api):
    """
    lounger CLI.
    """

    if project_web:
        create_scaffold(project_web, "web")
        return 0

    if project_api:
        create_scaffold(project_api, "api")
        return 0

    if yaml_api:
        create_scaffold(yaml_api, "yapi")
        return 0

    return None


def create_scaffold(project_name: str, type: str) -> None:
    """
    Create a project scaffold with the specified name and type.

    :param project_name: Name of the project (folder)
    :param type: Project type, one of "api", "web", "yapi"
    """
    project_root = Path(project_name)

    # Check if project already exists
    if project_root.exists():
        log.info(f"Folder {project_name} already exists. Please specify a new folder name.")
        return

    log.info(f"Start to create new test project: {project_name}")
    log.info(f"CWD: {os.getcwd()}\n")

    # Shared paths
    current_file = Path(__file__).resolve()
    template_base = current_file.parent / "project_temp"

    # Ensure project root exists
    project_root.mkdir(parents=True, exist_ok=True)

    # Create reports folder
    (project_root / "reports").mkdir(exist_ok=True)
    log.info("📁 created folder: reports")

    # Define pytest.ini content
    ini_content = {
        "api": '''[pytest]
log_format = %(asctime)s | %(levelname)-8s | %(filename)s | %(message)s
log_date_format = %Y-%m-%d %H:%M:%S
base_url = https://httpbin.org
addopts = -s --html=./reports/result.html
''',
        "web": '''[pytest]
log_format = %(asctime)s | %(levelname)-8s | %(filename)s | %(message)s
log_date_format = %Y-%m-%d %H:%M:%S
base_url = https://cn.bing.com
addopts = -s --browser=chromium --headed --html=./reports/result.html
'''
    }

    # Write pytest.ini
    if type == "api" or type == "web":
        content = ini_content[type]
        (project_root / "pytest.ini").write_text(content, encoding="utf-8")
        log.info("📄 created file: pytest.ini")

    # Define file mappings: (source, destination relative to project_root)
    file_mappings = []

    # Add conftest.py (shared)
    conftest_src = template_base / "conftest.py"
    file_mappings.append((conftest_src, "conftest.py"))

    if type == "api":
        file_mappings.append((template_base / "test_api.py", "test_api.py"))

    elif type == "web":
        file_mappings.append((template_base / "test_web.py", "test_web.py"))

    elif type == "yapi":
        # Main test file and config
        file_mappings.extend([
            (template_base / "yapi" / "test_api.py", "test_api.py"),
            (template_base / "yapi" / "config" / "config.yaml", "config/config.yaml"),
            (template_base / "yapi" / "datas" / "setup" / "login.yaml", "datas/setup/login.yaml"),
            (template_base / "yapi" / "datas" / "sample" / "test_case.yaml", "datas/sample/test_case.yaml"),
            (template_base / "yapi" / "datas" / "sample" / "test_req.yaml", "datas/sample/test_req.yaml"),
        ])
    else:
        log.error(f"Unsupported project type: {type}. Choose from 'api', 'web', 'yapi'.")
        return

    # Copy all template files
    for src_path, dest_rel in file_mappings:
        try:
            content = src_path.read_text(encoding="utf-8")
            dest_path = project_root / dest_rel

            # Ensure parent dir exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            dest_path.write_text(content, encoding="utf-8")
            log.info(f"📄 created file: {dest_rel}")
        except Exception as e:
            log.error(f"Failed to create {dest_rel}: {e}")

    log.info(f"🎉 Project '{project_name}' created successfully.")
    log.info(f"👉 Go to the project folder and run 'pytest' to start testing.")


if __name__ == '__main__':
    main()
