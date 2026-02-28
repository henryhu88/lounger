"""
function: 该脚本支持平台化运行
参考：https://seldomqa.github.io/platform/platform.html
"""

import json

import pytest

from lounger.log import log
from lounger.utils.collect import get_test_cases


def collected_cases(collect_dir: str, output_path: str):
    """
    收集测试用例保存到指定文件
    """
    # Collect test case information
    cases = get_test_cases(collect_dir)

    # Write to JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cases, f, indent=4, ensure_ascii=False)

    log.info(f"Test cases collected and saved to: {output_path}")


def running_cases(execute_path: str):
    """
    收集测试用例保存到指定文件
    """
    log.info(f"✓ Executing test cases from: {execute_path}")
    pytest.main([
        "--run-json",
        execute_path,
        "--junit-xml=./reports/result.xml",
        "-W",
        "ignore::pytest.PytestAssertRewriteWarning"
    ])


if __name__ == "__main__":
    cases_path = "./collected_cases/test_cases_info.json"

    # step1: 收集当前项目下的测试用例
    collected_cases(collect_dir="./", output_path=cases_path)

    # step2: 执行收集到的测试用例
    running_cases(execute_path=cases_path)
