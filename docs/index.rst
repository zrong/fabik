.. FABIK documentation master file, created by
   sphinx-quickstart on Wed Jul 26 12:21:00 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

FABIK 文档
================================

FABIK ``/ˈfæbɪk/`` = Fabric + Click

Fabik 是一个 Python 命令行项目的基础包，封装了命令行项目的常用功能，具体如下：

- 使用 TOML 配置文件解决配置管理问题。
- 多环境配置、默认值替换、环境变量读取和路径管理。
- 配置模板支持。
- 多开发环境支持。
- 使用 Fabric 进行远程项目部署。

fabik 使用的库包括 Fabric/Click/Jinja2/cryptography/python-dotenv/httpx/itdangerous 等。

fabik 的想法来自我之前创建的 `pyape <https://pypi.org/project/pyape/#description>`_ 项目。pyape 是一个 Python Web 服务器开发框架，包含了大量的部署、配置文件处理和命令行管理功能。我将这些功能分离出来创建了 fabik，使其更容易被更多项目直接引用。

有关 pyape 项目的更多信息，请阅读文档：https://pyape.rtfd.io/

项目源代码：https://github.com/zrong/pyape

**FABIK 的特点如下：**

TOML 配置文件管理
------------------

使用 TOML 格式的配置文件，提供清晰、易读的配置管理方案。支持配置文件的层级结构和模板化配置。

多环境配置支持
---------------

可配置多套开发环境，方便同时支持本地开发、测试环境和生产环境部署。不同环境可以有不同的配置参数。

环境变量集成
-------------

支持从环境变量中读取配置值，避免将敏感信息（如密码、API 密钥）直接写入配置文件，提高安全性。

命令行工具集成
---------------

基于 Click 和 Typer 构建强大的命令行界面，提供统一的命令行工具来管理项目的各种操作。

远程部署支持
-------------

集成 Fabric 库，支持远程服务器部署和管理，简化项目的部署流程。

模板系统
---------

基于 Jinja2 的模板系统，支持配置文件模板化，可以根据不同环境生成相应的配置文件。

加密支持
---------

集成 cryptography 库，提供配置文件加密和解密功能，保护敏感配置信息。

HTTP 客户端
------------

集成 httpx 库，提供现代化的 HTTP 客户端功能，支持异步和同步操作。

.. toctree::
   :maxdepth: 2
   :caption: 目录:

   usage
   configuration
   command
   development
   reference


索引和表格
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`