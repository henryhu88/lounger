## 0.8.0(2026-01-09)

* Web测试：
    * 增加 `playwright` 最新API。
* 接口测试
    * 增加`save_response()` 方法用于保存响应结果。
    * YAML支持`step`关键字用于描述测试步骤。
* 升级 pytest-html 测试库。

## 0.7.3(2025-12-12)

* `HttpRequest` 增加参数。
* `webhook.py` 格式化代码。
* 优化logo的打印方式。

## 0.7.2(2025-12-3)

* 修复bug
* 合并功能

## 0.7.1(2025-12-2)

* 代码优化
* 合并功能

## 0.7.0(2025-11-18)

* YAML API 更新：
    * 支持`centrifuge` 协议，公司内部使用。
    * `commons` 相关代码重构。
    * 测试步骤增加 `prescript` 字段，执行前置脚本。
    * 测试步骤增加 `sleep` 字段，支持用例执行完休眠。
    * 简化`test_api.py`脚本。
    * 增加新的断言类型：`greater`,`greater_equal`, `less`, `less_equal`。
* 使用新的模板
* 移除`jmespath`直接依赖。
* 升级`pytest-req` 到 0.5.0版本。

## 0.6.0(2025-10-23)

* 更新`lounger`命令，创建API测试，直接提供混合示例。
* 调整`YAML`接口测试用例的查找规则。
* 升级`pytest-xhtml>=0.2.0`最新版本。
* 增加`global_test_config()`函数，用于获取`config.yaml`中的配置。

## 0.5.0(2025-10-8)

* 支持YAML编写API测试，提供了一套完整的方案。

## 0.3.0(2025-08-27)

* 使用`pyest-xhtml`替换`pytest-html`报告，现代美观。
* 升级`pytest-playwright>=0.7.0`最新版本。
* 修复: `HTML` 报告无法集成`pytest-req`日志的问题。

## 0.2.0(2024-09-27)

* 增加`HttpRequest`类，支持`API objects`设计模式。
* 增加`BasePage`、`Locator`类，支持`Page objects`设计模式。
* 修复: `python 3.12` 警告：`datetime.utcnow()`废弃。

## 0.1.0(2024-09-13)

* lounger 正式发布
