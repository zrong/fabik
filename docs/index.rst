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

fabik 的想法来自我之前创建的 `pyape <https://github.com/zrong/pyape>`_ 项目。pyape 是一个 Python Web 服务器开发框架，包含了大量的部署、配置文件处理和命令行管理功能。我将这些功能分离出来创建了 fabik，使其更容易被更多项目直接引用。

现在，一部分 pyape 功能被移到 fabik 中，fabik 作为 pyape 的核心依赖包继续更新和维护。

**FABIK 的特点如下：**

TOML 配置文件管理
------------------

使用 TOML 格式的配置文件，提供清晰、易读的配置管理方案。支持配置文件的层级结构和模板化配置。

基于 Jinja2 的模板系统，支持配置文件模板化，可以根据不同环境生成相应的配置文件。

支持从 fabik.toml 直接生成配置文件，也支持基于 tpls 文件夹中先获取模板，再对配置模版进行替换，并生成最终的配置文件。

使用 python-dotenv 库来加载 .env 文件中的环境变量，以支持从环境变量中获取配置信息。

多环境配置支持
---------------

可配置多套开发环境，方便同时支持本地开发、局域网开发、互联网测试和正式服部署。

详细说明请阅读： :ref:`multi_env`。

环境变量集成替换支持
------------------

fabik 的配置文件模版机制支持从环境变量中获取实际值，这样可以避免将敏感信息写入配置文件提交到 CVS 造成安全隐患。

详细说明请阅读： :ref:`fabik_toml_substitution`。

命令行工具集成
---------------

基于 Click 和 Typer 构建强大的命令行界面，提供统一的命令行工具来管理项目的各种操作。

远程部署支持
-------------

集成 `Fabric`_ 库，支持远程服务器部署和管理，简化项目的部署流程。


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
  

.. _Fabric: https://www.fabfile.org/