配置
================

.. _fabik_toml:

fabik.toml
-----------------

fabik.toml 是 ``fabik`` 的主配置文件。它应该跟随项目源码一起被提交到 VCS。

由于 TOML 格式的特点，我们可以把所有的配置文件的生成和替换在一个单独的文件中完成，这让我们的配置更容易理解。
感谢 TOML。

关于 TOML 格式的介绍请阅读： https://toml.io/

fabik.toml 的模板：

- `fabik.tpl::FABIK_TOML_SIMPLE_TPL` - 简易模板，适合基本的项目配置
- `fabik.tpl::FABIK_TOML_FULL_TPL` - 全功能模板，适合功能强大的项目配置

完整的 fabik.toml 配置文件保存在 `samples/fabik.toml` 中，欢迎查看。

.. _fabik_toml_substitution:

替换机制
--------------

fabik 在生成配置文件的时候，会读取 ``fabik.toml`` 的所有内容，
根据其中的配置做好值的替换，再写入到具体的配置文件中。

fabik 有两个主要的替换机制。

任何时候都可用的变量
^^^^^^^^^^^^^^^^^^^^^

``NAME/DEPLOY_DIR/WORK_DIR`` 这三个变量在任何时候都可用。关于前两个，
需要在 :ref:`fabik_toml_root` 中进行定义。

``WORK_DIR`` 不需要定义就能使用，它默认指向 fabik 项目的工作文件夹。

从环境变量中获取值
^^^^^^^^^^^^^^^^^^^

为了安全，我们会把敏感的信息写入系统的环境变量中。fabik 可以从环境变量中提取之，在生成配置文件时进行替换。

请阅读 :ref:`fabik_toml_root` 中关于 ``REPLACE_ENVIRON`` 的介绍。


.. _multi_env:

多开发环境支持
---------------------

Web 程序开发的过程中，我们一般会有多套开发环境。例如在本地 ``local`` 环境做调试，
在远程测试 ``test`` 服务器做测试，在正式服 ``prod`` 环境做部署。

fabik 的多开发环境支持，可以支持在 ``fabik.toml`` 中进行多套环境的配置。默认配置会被环境配置中的同名变量直接覆盖。
这种机制减少了配置内容的数量，也方便信息共用。

环境配置以 `ENV.环境名` 开头，后接希望被覆盖的配置名称。

例如，根元素下的 `DEPLOY_DIR` 配置，若希望在 ``prod`` 环境中使用不同的值，可以增加这样的配置： ::

    [ENV.prod]
    DEPLOY_DIR = '/srv/app/{{NAME}}_prod'
    
若希望在 ``local`` 环境中使用调试方式启动 Flask，则可以覆盖默认的 ``FLASK_ENV``： ::

    [ENV.local.'.env']
    FLASK_ENV = 'development'
    FLASK_RUN_PORT = 5001

在开发环境配置中提供的配置，将被 **合并** 进入默认的配置。
合并规则如下：

- 开发环境配置会 **覆盖** 默认配置中的同名参数。
- 开发环境中的新配置，会 **增加** 到默认配置中。
- 若希望在开发环境中 **删除** 某个默认配置，可以将开发环境中的同名变量设置为空值。
  
.. note::

    由于 TOML `自身的规则 <https://github.com/toml-lang/toml/issues/30>`_ 限制，TOML 配置中是没有 **空值** 的概念的。
    若希望将某个值设置为空值，可以使用布尔值或者空对象的方法。

下面是几个关于开发环境替换的例子： ::

    # 正式环境的 uwsgi 使用 4 进程启动
    [ENV.prod.'uwsgi.ini']
    processes = 4

    # 正式环境的数据库使用 DEPLOY_DIR 来定位 
    [ENV.prod.'config.toml'.SQLALCHEMY]
    URI = 'sqlite:///{{DEPLOY_DIR}}/pyape.sqlite'

    # 正式环境的 gunicorn 使用 sock 绑定，并指定 pid 和 log 文件
    [ENV.prod.'gunicorn.conf.py']
    bind = 'unix:{{DEPLOY_DIR}}/gunicorn.sock'
    pidfile = '{{DEPLOY_DIR}}/gunicorn.pid'
    accesslog = '{{DEPLOY_DIR}}/logs/access.log'
    errorlog = '{{DEPLOY_DIR}}/logs/error.log
    
.. _fabik_toml_root:

根元素
-------------

PYE
    **远程服务器专用**。定义 Python 运行时路径，可使用绝对路径。这个配置仅在部署远程服务器时有意义，
    指定的是远程服务器上的 Python 运行时。使用 :ref:`cli_venv` 命令部署远程虚拟环境时，
    会使用这里定义的 Python 运行时。

NAME
    项目名称。 可以用做替换值。
    配置文件中所有包含 ``{{NAME}}`` 的参数都会被这里的值替换。
    
DEPLOY_DIR
    **远程服务器专用**。设定部署在服务器上的文件夹。 可以用做替换值。
    配置文件中所有包含 ``{{DEPLOY_DIR}}`` 的参数都会被这里的值替换。

RSYNC_EXCLUDE
    **远程服务器专用**。这是一个列表，定义在使用 :ref:`cli_fabik_deploy` 命令将本地代码同步到远程服务器时的排除文件。
    详情可参考 `fabric-patchwork.transfers <https://fabric-patchwork.readthedocs.io/en/latest/api/transfers.html#module-patchwork.transfers>`_。
    
REPLACE_ENVIRON
    这是一个列表。定义允许被替换的环境变量的名称。
    若配置文件中包含下面的名称，并使用 ``{{}}`` 包裹，则会被替换成环境变量中的值。

    例如：

    1. 项目 NAME 为 ``fabik``，作为环境变量替换时，会被转换为全大写 ``FABIK``。
    2. 环境变量中包含 ``FABIK_LOCAL_SECRET_KEY``。
    3. 使用 ``--env local`` 生成配置文件时，将替换 ``{{SECRET_KEY}}`` 的值为环境变量中的 ``FABIK_LOCAL_SECRET_KEY``。

    默认提供了四个环境变量替换：

    - ``{{ADMIN_NAME}}`` 管理员帐号
    - ``{{ADMIN_PASSWORD}}`` 管理员密码
    - ``{{SECRET_KEY}}`` flask 框架加密使用
    - ``{{SQLALCHEMY_URI}}`` 数据库地址和密码定义
    
    亦可自行增加环境变量，保证配置文件中的变量名称相同即可。

.. _fabik_toml_fabric:

[FABRIC]
------------

fabik 使用 `Fabric`_ 作为部署工具。在部署时，会直接读取这个段落的配置作为 Fabric 调用的参数。

.. warning::
    强烈建议在本地 ``~/.ssh/config`` 中配置好 host 地址、端口和公钥。
    此处的 host 可以使用配置好的地址，避免真实的地址提交到版本库造成信息泄露。

host
    远程服务器地址。

user
    远程服务器登录用户。


.. _fabik_toml_dotenv:

['.env']
-----------

``.env`` 是环境配置文件，使用 :ref:`cli_fabik_config` 生成配置文件，
或使用 :ref:`cli_fabik_deploy` 进行远程部署时，会自动生成。


.. _pyape_toml_gunicorn_conf_py:

['gunicorn.conf.py']
------------------------

``gunicorn.conf.py`` 是 `Gunicorn`_ 的配置文件。

默认值为： ::

    wsgi_app = 'wsgi:{{NAME}}_app'
    proc_name = '{{NAME}}'
    bind = '127.0.0.1:5001'
    umask = 0
    daemon = true
    capture_output = true

配置中可用的参数，通过阅读 ``samples/gunicorn.conf.py.jinja2`` 源码获取。

.. _fabik_toml_uwsgi_ini:

['uwsgi.ini']
--------------------------

``uwsgi.ini`` 是 `uWSGI`_ 的配置文件。

默认值为： ::

    callable = 'wsgi:{{NAME}}_app'
    processes = 2
    threads = 1
    venv = '%dvenv'
    # 是否切换到后台，本地调试的时候可以设为 False，直接查看控制台输出
    daemonize = true
    # socket 和 http 参数二选一，如果同时选择，以 socket 参数为准
    # 端口转发可能引发 nginx 499 问题（推测是端口转发 limit 没有打开） 
    # 改为使用 sock 文件 （同样需要打开 limit 限制）
    socket = '%d%n.sock'
    # http_socket = '127.0.0.1:5002'
    # http = '127.0.0.1:5002'
    # Stat Server
    stats = '%d%nstats.sock
    
配置中可用的参数，通过阅读 ``samples/uwsgi.ini.jinja2`` 源码获取。


.. _Fabric: https://www.fabfile.org/
.. _Gunicorn: https://gunicorn.org/
.. _uWSGI: https://uwsgi-docs.readthedocs.io/