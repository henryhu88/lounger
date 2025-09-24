import os
import pytest

from lounger.commons.case import execute_case
from lounger.commons import get_case_path
from lounger.log import log
from lounger.utils.file_handle import read_yaml


class TestApiFramework:
    log.error("test error")
    pass


def create_func_case(path):
    """
    创建测试用例
    :param path: 用例YAML文件路径
    :return: 执行测试的方法
    """

    @pytest.mark.parametrize('caseinfo', read_yaml(path))
    def func(self, caseinfo):
        log.info(caseinfo['model'])
        execute_case(caseinfo)

    return func


# 动态构建符合Pytest命名规则的测试用例
for file_path in get_case_path():
    file_name = os.path.basename(file_path).replace('.yaml', '')
    setattr(TestApiFramework, f'test_{file_name}', create_func_case(file_path))
