配置管理
========

fabik 提供了强大的配置管理功能，支持 TOML 格式的配置文件、多环境配置、环境变量替换等特性。

配置文件格式
------------

fabik 使用 TOML 格式的配置文件，默认文件名为 ``fabik.toml``。

基本结构
~~~~~~~~

.. code-block:: toml

    [project]
    name = "my-project"
    version = "1.0.0"
    description = "项目描述"
    
    [database]
    host = "localhost"
    port = 5432
    name = "mydb"
    
    [logging]
    level = "INFO"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

多环境配置
----------

fabik 支持为不同环境设置不同的配置参数：

.. code-block:: toml

    [environments.development]
    debug = true
    database_host = "localhost"
    database_port = 5432
    log_level = "DEBUG"
    
    [environments.testing]
    debug = true
    database_host = "test-db"
    database_port = 5432
    log_level = "INFO"
    
    [environments.production]
    debug = false
    database_host = "${DB_HOST}"
    database_port = "${DB_PORT}"
    log_level = "WARNING"

环境变量替换
------------

fabik 支持在配置文件中使用环境变量，格式为 ``${VARIABLE_NAME}``：

.. code-block:: toml

    [database]
    host = "${DATABASE_HOST}"
    port = "${DATABASE_PORT}"
    username = "${DATABASE_USER}"
    password = "${DATABASE_PASSWORD}"

如果环境变量不存在，可以提供默认值：

.. code-block:: toml

    [database]
    host = "${DATABASE_HOST:localhost}"
    port = "${DATABASE_PORT:5432}"

配置文件模板
------------

fabik 支持使用 Jinja2 模板语法创建配置文件模板：

.. code-block:: toml

    [project]
    name = "{{ project_name }}"
    version = "{{ version }}"
    
    {% if environment == "development" %}
    [database]
    host = "localhost"
    port = 5432
    {% else %}
    [database]
    host = "{{ database_host }}"
    port = {{ database_port }}
    {% endif %}

配置加载
--------

在 Python 代码中加载配置：

.. code-block:: python

    from fabik import Config
    
    # 加载默认配置文件
    config = Config.load()
    
    # 加载指定配置文件
    config = Config.load('custom.toml')
    
    # 指定环境
    config = Config.load('fabik.toml', environment='production')

配置访问
--------

访问配置值：

.. code-block:: python

    # 获取配置值
    project_name = config.get('project.name')
    database_host = config.get('database.host')
    
    # 提供默认值
    debug = config.get('debug', False)
    
    # 获取环境特定配置
    env_config = config.get_environment('production')

配置验证
--------

fabik 支持配置验证，确保配置文件的正确性：

.. code-block:: python

    from fabik import Config, ConfigSchema
    
    # 定义配置模式
    schema = ConfigSchema({
        'project.name': str,
        'project.version': str,
        'database.host': str,
        'database.port': int,
    })
    
    # 验证配置
    config = Config.load('fabik.toml')
    schema.validate(config)

配置文件示例
------------

完整的配置文件示例：

.. code-block:: toml

    [project]
    name = "fabik-example"
    version = "1.0.0"
    description = "fabik 示例项目"
    author = "zrong"
    
    [database]
    driver = "postgresql"
    host = "${DATABASE_HOST:localhost}"
    port = "${DATABASE_PORT:5432}"
    name = "${DATABASE_NAME:fabik_db}"
    username = "${DATABASE_USER:fabik}"
    password = "${DATABASE_PASSWORD}"
    
    [redis]
    host = "${REDIS_HOST:localhost}"
    port = "${REDIS_PORT:6379}"
    db = "${REDIS_DB:0}"
    
    [logging]
    level = "${LOG_LEVEL:INFO}"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file = "logs/app.log"
    
    [environments.development]
    debug = true
    database_host = "localhost"
    redis_host = "localhost"
    log_level = "DEBUG"
    
    [environments.testing]
    debug = true
    database_host = "test-db"
    redis_host = "test-redis"
    log_level = "INFO"
    
    [environments.production]
    debug = false
    database_host = "${PROD_DB_HOST}"
    redis_host = "${PROD_REDIS_HOST}"
    log_level = "WARNING"
    
    [deployment]
    remote_host = "${DEPLOY_HOST}"
    remote_user = "${DEPLOY_USER}"
    remote_path = "/opt/fabik-app"
    
    [security]
    secret_key = "${SECRET_KEY}"
    encryption_key = "${ENCRYPTION_KEY}"