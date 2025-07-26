命令行工具
==========

fabik 提供了丰富的命令行工具，帮助开发者管理项目配置、环境切换和远程部署等操作。

基本用法
--------

安装 fabik 后，可以在命令行中使用 ``fabik`` 命令：

.. code-block:: bash

    fabik --help

配置管理命令
------------

查看配置
~~~~~~~~

.. code-block:: bash

    # 显示当前配置
    fabik config show
    
    # 显示指定环境的配置
    fabik config show --env production
    
    # 显示配置文件路径
    fabik config path

验证配置
~~~~~~~~

.. code-block:: bash

    # 验证配置文件语法
    fabik config validate
    
    # 验证指定配置文件
    fabik config validate --file custom.toml

生成配置模板
~~~~~~~~~~~~

.. code-block:: bash

    # 生成默认配置模板
    fabik config init
    
    # 生成指定类型的配置模板
    fabik config init --template web
    fabik config init --template api
    fabik config init --template cli

环境管理命令
------------

查看环境
~~~~~~~~

.. code-block:: bash

    # 列出所有可用环境
    fabik env list
    
    # 显示当前环境
    fabik env current

切换环境
~~~~~~~~

.. code-block:: bash

    # 切换到指定环境
    fabik env set development
    fabik env set production
    
    # 临时使用指定环境执行命令
    fabik env use testing -- fabik config show

创建环境
~~~~~~~~

.. code-block:: bash

    # 创建新环境
    fabik env create staging
    
    # 基于现有环境创建新环境
    fabik env create staging --from production

部署命令
--------

本地部署
~~~~~~~~

.. code-block:: bash

    # 构建项目
    fabik deploy build
    
    # 运行测试
    fabik deploy test
    
    # 打包项目
    fabik deploy package

远程部署
~~~~~~~~

.. code-block:: bash

    # 部署到远程服务器
    fabik deploy remote
    
    # 部署到指定环境
    fabik deploy remote --env production
    
    # 部署指定版本
    fabik deploy remote --version 1.2.0

服务器管理
~~~~~~~~~~

.. code-block:: bash

    # 检查远程服务器状态
    fabik server status
    
    # 重启远程服务
    fabik server restart
    
    # 查看远程日志
    fabik server logs
    
    # 执行远程命令
    fabik server exec "ps aux | grep python"

项目管理命令
------------

初始化项目
~~~~~~~~~~

.. code-block:: bash

    # 初始化新项目
    fabik project init
    
    # 使用指定模板初始化项目
    fabik project init --template web
    
    # 在指定目录初始化项目
    fabik project init --path /path/to/project

项目信息
~~~~~~~~

.. code-block:: bash

    # 显示项目信息
    fabik project info
    
    # 显示项目依赖
    fabik project deps
    
    # 检查项目健康状态
    fabik project health

开发工具命令
------------

代码格式化
~~~~~~~~~~

.. code-block:: bash

    # 格式化代码
    fabik dev format
    
    # 检查代码风格
    fabik dev lint
    
    # 运行类型检查
    fabik dev typecheck

测试命令
~~~~~~~~

.. code-block:: bash

    # 运行所有测试
    fabik dev test
    
    # 运行指定测试文件
    fabik dev test tests/test_config.py
    
    # 运行测试并生成覆盖率报告
    fabik dev test --coverage

文档命令
~~~~~~~~

.. code-block:: bash

    # 构建文档
    fabik dev docs build
    
    # 启动文档服务器
    fabik dev docs serve
    
    # 清理文档构建文件
    fabik dev docs clean

加密工具命令
------------

加密配置
~~~~~~~~

.. code-block:: bash

    # 加密配置文件
    fabik crypto encrypt config.toml
    
    # 解密配置文件
    fabik crypto decrypt config.toml.enc
    
    # 生成加密密钥
    fabik crypto keygen

密钥管理
~~~~~~~~

.. code-block:: bash

    # 设置加密密钥
    fabik crypto setkey
    
    # 验证密钥
    fabik crypto verify
    
    # 轮换密钥
    fabik crypto rotate

实用工具命令
------------

模板管理
~~~~~~~~

.. code-block:: bash

    # 列出可用模板
    fabik template list
    
    # 渲染模板
    fabik template render template.j2 --output result.txt
    
    # 创建自定义模板
    fabik template create mytemplate

文件操作
~~~~~~~~

.. code-block:: bash

    # 复制文件到远程服务器
    fabik file upload local.txt remote:/path/to/file.txt
    
    # 从远程服务器下载文件
    fabik file download remote:/path/to/file.txt local.txt
    
    # 同步目录
    fabik file sync local_dir/ remote:/path/to/dir/

配置文件示例
------------

为了使用这些命令，需要在项目根目录创建 ``fabik.toml`` 配置文件：

.. code-block:: toml

    [project]
    name = "my-project"
    version = "1.0.0"
    
    [environments.development]
    debug = true
    
    [environments.production]
    debug = false
    
    [deployment]
    remote_host = "example.com"
    remote_user = "deploy"
    remote_path = "/opt/my-project"
    
    [commands]
    build = "python setup.py build"
    test = "pytest"
    format = "black ."
    lint = "flake8"

自定义命令
----------

fabik 支持在配置文件中定义自定义命令：

.. code-block:: toml

    [commands]
    hello = "echo 'Hello, World!'"
    setup = ["pip install -r requirements.txt", "python setup.py develop"]
    clean = "rm -rf build/ dist/ *.egg-info/"

然后可以通过命令行执行：

.. code-block:: bash

    fabik run hello
    fabik run setup
    fabik run clean

命令别名
--------

可以为常用命令创建别名：

.. code-block:: toml

    [aliases]
    d = "deploy"
    t = "dev test"
    f = "dev format"
    l = "dev lint"

使用别名：

.. code-block:: bash

    fabik d  # 等同于 fabik deploy
    fabik t  # 等同于 fabik dev test
    fabik f  # 等同于 fabik dev format