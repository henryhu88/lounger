from lounger.utils.get_configs import config_utils

project_config: dict = config_utils.get_config('test_project')


def get_project_name():
    """
    动态获取项目名称
    :return:
    """
    project_name_list = []
    for project_name in project_config.keys():
        project_name_list.append(project_name)
    return config_utils.get_config('test_project')
