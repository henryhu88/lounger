# 基于平台的 Lounger 测试执行

Lounger
提供了一个强大的基于平台的测试执行框架，能够实现自动化测试用例收集和执行。[platform_running.py](https://github.com/SeldomQA/lounger/blob/main/myapi/platform_running.py)
脚本展示了这一功能，通过自动化整个测试工作流程，从用例收集到执行。

## 概述

基于平台的执行系统通过以下方式简化测试自动化：

- 自动从项目中收集测试用例
- 将收集的用例保存到结构化 JSON 文件中
- 基于收集的信息执行测试
- 提供全面的执行报告

## 核心组件

### 1. 测试用例收集

`get_test_cases()`函数自动发现并收集指定目录内的所有测试用例：

```python
import json

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


if __name__ == "__main__":
    cases_path = "./collected_cases/test_cases_info.json"

    # step1: 收集当前项目下的测试用例
    collected_cases(collect_dir="./", output_path=cases_path)
```

收集到的用例格式如下：

```json
[
  {
    "file": "/Users/channelwill/cwpro/github/lounger/myapi/test_api.py",
    "nodeid": "test_api.py::test_api[test_assert::case_1_step_1]",
    "name": "test_api[test_assert::case_1_step_1]",
    "parent": "test_api.py",
    "description": "\nExecute the 'teststeps' test case in YAML.\n",
    "markers": [
      "parametrize"
    ]
  },
  {
    "file": "/Users/channelwill/cwpro/github/lounger/myapi/test_api.py",
    "nodeid": "test_api.py::test_api[test_sample::case_1_step_1]",
    "name": "test_api[test_sample::case_1_step_1]",
    "parent": "test_api.py",
    "description": "\nExecute the 'teststeps' test case in YAML.\n",
    "markers": [
      "parametrize"
    ]
  },
  ...
]
```

**说明：**

我们可以将收集到的用例，解析为测试平台的目录树。参考 seldom-platform 的实现。
https://github.com/seldomqa/seldom-platform

### 2. 测试执行引擎

[running_cases()](file:///Users/channelwill/cwpro/github/lounger/myapi/platform_running.py#L27-L38) 函数执行先前收集的测试用例：

```python
import pytest

from lounger.log import log


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

    # step2: 执行收集到的测试用例
    running_cases(execute_path=cases_path)
```

**说明：**

- 根据平台中针对用例的勾选，可以有选择的将测试用例重新组装为JSON文件，然后，交由 pytest 执行。
- 使用 `--junit-xml=./reports/result.xml` 生成测试结果，解析之后保存到数据库中，最终，在测试平台中展示。

## 后续

pytest 针对测试用例的解析和执行的核心问题已经解决了，接下来，我们可以执行开发测试平台，将该功能集成到平台中。
