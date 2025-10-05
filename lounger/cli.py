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
    create scaffold with specified project name.
    :param project_name:
    :param type:
    :return:
    """
    if os.path.isdir(project_name):
        log.info(f"Folder {project_name} exists, please specify a new folder name.")
        return

    log.info(f"Start to create new test project: {project_name}")
    log.info(f"CWD: {os.getcwd()}\n")

    def create_folder(path):
        os.makedirs(path)
        log.info(f"created folder: {path}")

    def create_file(path, file_content=""):
        with open(path, 'w', encoding="utf-8") as py_file:
            py_file.write(file_content)
        msg = f"created file: {path}"
        log.info(msg)

    current_file = Path(__file__).resolve()

    # create base file
    conftest_path = current_file.parent / "project_temp" / "conftest.py"
    conftest_content = conftest_path.read_text(encoding='utf-8')
    create_folder(project_name)
    create_folder(os.path.join(project_name, "reports"))

    web_ini = '''[pytest]
log_format = %(asctime)s | %(levelname)-8s | %(filename)s | %(message)s
log_date_format = %Y-%m-%d %H:%M:%S
base_url = https://cn.bing.com
addopts = -s --browser=chromium --headed --html=./reports/result.html
'''
    api_ini = '''[pytest]
log_format = %(asctime)s | %(levelname)-8s | %(filename)s | %(message)s
log_date_format = %Y-%m-%d %H:%M:%S
base_url = https://httpbin.org
addopts = -s --html=./reports/result.html
'''

    if type == "api":
        # create api file
        api_case_path = current_file.parent / "project_temp" / "test_api.py"
        content = api_case_path.read_text(encoding='utf-8')
        create_file(os.path.join(project_name, "test_api.py"), content)
        create_file(os.path.join(project_name, "conftest.py"), conftest_content)
        create_file(os.path.join(project_name, "pytest.ini"), api_ini)
    elif type == "web":
        # create web file
        web_case_path = current_file.parent / "project_temp" / "test_web.py"
        content = web_case_path.read_text(encoding='utf-8')
        create_file(os.path.join(project_name, "test_web.py"), content)
        create_file(os.path.join(project_name, "conftest.py"), conftest_content)
        create_file(os.path.join(project_name, "pytest.ini"), web_ini)
    elif type == "yapi":
        # create YAML api file
        create_folder(os.path.join(project_name, "config"))
        create_folder(os.path.join(project_name, "datas"))
        create_folder(os.path.join(project_name, "datas", "setup"))
        create_folder(os.path.join(project_name, "datas", "sample"))
        test_api_path = current_file.parent / "project_temp" / "yapi" / "test_api.py"
        config_path = current_file.parent / "project_temp" / "yapi" / "config" / "config.yaml"
        setup_path = current_file.parent / "project_temp" / "yapi" / "datas" / "setup" / "login.yaml"
        test_case_path = current_file.parent / "project_temp" / "yapi" / "datas" / "sample" / "test_case.yaml"
        test_req_path = current_file.parent / "project_temp" / "yapi" / "datas" / "sample" / "test_req.yaml"
        test_api_content = test_api_path.read_text(encoding='utf-8')
        create_file(os.path.join(project_name, "test_api.py"), test_api_content)
        config_content = config_path.read_text(encoding='utf-8')
        create_file(os.path.join(project_name, "config", "config.yaml"), config_content)
        setup_content = setup_path.read_text(encoding='utf-8')
        create_file(os.path.join(project_name, "datas", "setup", "login.yaml"), setup_content)
        test_case_content = test_case_path.read_text(encoding='utf-8')
        create_file(os.path.join(project_name, "datas", "sample", "test_case.yaml"), test_case_content)
        test_req_content = test_req_path.read_text(encoding='utf-8')
        create_file(os.path.join(project_name, "datas", "sample", "test_req.yaml"), test_req_content)


if __name__ == '__main__':
    main()
