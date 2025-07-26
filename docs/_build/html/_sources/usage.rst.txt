使用说明
========

安装
----

使用 pip 安装 fabik：

.. code-block:: bash

    pip install fabik

或者从源代码安装：

.. code-block:: bash

    git clone https://github.com/zrong/fabik.git
    cd fabik
    pip install -e .

快速开始
--------

1. 创建项目配置文件
~~~~~~~~~~~~~~~~~~~

fabik 使用 TOML 格式的配置文件。在项目根目录创建 ``fabik.toml`` 文件：

.. code-block:: toml

    [project]
    name = "my-project"
    version = "1.0.0"
    
    [environments.development]
    debug = true
    database_url = "sqlite:///dev.db"
    
    [environments.production]
    debug = false
    database_url = "${DATABASE_URL}"

2. 使用命令行工具
~~~~~~~~~~~~~~~~~

fabik 提供了丰富的命令行工具：

.. code-block:: bash

    # 查看配置
    fabik config show
    
    # 切换环境
    fabik env set production
    
    # 部署到远程服务器
    fabik deploy

3. 在代码中使用
~~~~~~~~~~~~~~~

.. code-block:: python

    from fabik import Config
    
    # 加载配置
    config = Config.load('fabik.toml')
    
    # 获取配置值
    debug = config.get('debug', False)
    database_url = config.get('database_url')

基本概念
--------

配置文件
~~~~~~~~

fabik 使用 TOML 格式的配置文件，支持：

- 层级配置结构
- 环境变量替换
- 多环境配置
- 配置模板

环境管理
~~~~~~~~

fabik 支持多环境配置，可以为不同的部署环境（开发、测试、生产）设置不同的配置参数。

命令行工具
~~~~~~~~~~

fabik 提供统一的命令行界面，集成了项目管理的各种常用操作。

远程部署
~~~~~~~~

基于 Fabric 的远程部署功能，支持自动化部署到远程服务器。