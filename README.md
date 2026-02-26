# lounger

Next generation automated testing framework.

## feature

🌟 支持`web`/`api`测试。

🌟 提供脚手架生成自动化项目。

🌟 更好用的数据驱动。

🌟 支持数据库操作。

🌟 已经配置好的测试报告（包含截图、日志）。

🌟 天然支持`API objects`、`Page objects`设计模式。

## framework

lounger不是一个从零开始的自动化测试框架，建立在`pytest`生态的基础上，提供更加简单、方便的使用体验。

![](./images/framework_0.9.0.png)

## Install

* pip安装。

```shell
$ pip install lounger
```

* 体验最新的项目代码。

```shell
$ pip install -U git+https://github.com/SeldomQA/lounger.git@main
```

## scaffold

lounger提供了脚手架，直接创建项目和使用。

```shell
$ lounger --help

Usage: lounger [OPTIONS]

  lounger CLI.

Options:
  --version                Show version.
  -pw, --project-web TEXT  Create an Web automation test project.
  -pa, --project-api TEXT  Create an API automation test project.
  --help                   Show this message and exit.
```

### Web自动化项目

* 首先，请安装测试浏览器（至少一款）。
    ```shell
    $ playwright install chromium[可选]
    $ playwright install firefox[可选]
    $ playwright install webkit[可选]
    ```

* 创建web自动化测试项目。
    ```shell
    $ lounger --project-web myweb
    ```

* 运行项目
    ```shell
    $ cd myweb
    $ pytest
    ```

### API自动化项目

* 创建api自动化测试项目。
    ```shell
    $ lounger --project-api myapi
    ```
  > 注：项目包含通过YAML管理API测试用例，编写规范参考下面的文档。

* 运行测试
    ```shell
    $ cd myapi
    $ pytest
    ```

### 测试报告

* lounger集成`pytest-xhtml`，直接生成测试报告。
  ![](./images/result_0.4.0.png)

## 项目&文档&示例

1. 如何进行Web自动化测试？👉 [阅读文档](./myweb)
2. 如何进行API自动化测试？👉 [阅读文档](./myapi)
3. 框架集成了哪些功能？ [测试示例](./tests)

## 对比

* seldom VS lounger 👉[详细对比](./seldom_vs_lounger.md)
