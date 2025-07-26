开发指南
========

本文档介绍如何参与 fabik 项目的开发，包括开发环境搭建、代码规范、测试和贡献流程。

开发环境搭建
------------

克隆项目
~~~~~~~~

.. code-block:: bash

    git clone https://github.com/zrong/fabik.git
    cd fabik

安装开发依赖
~~~~~~~~~~~~

.. code-block:: bash

    # 安装项目依赖
    pip install -e .
    
    # 安装开发依赖
    pip install -e .[dev]
    
    # 或者使用 uv（推荐）
    uv sync --group dev

设置开发环境
~~~~~~~~~~~~

.. code-block:: bash

    # 创建开发配置文件
    cp fabik.toml.example fabik.toml
    
    # 设置环境变量
    export FABIK_ENV=development
    
    # 初始化开发数据库（如果需要）
    fabik dev setup

项目结构
--------

.. code-block::

    fabik/
    ├── fabik/                  # 主要源代码
    │   ├── __init__.py
    │   ├── config/            # 配置管理模块
    │   ├── cli/               # 命令行工具
    │   ├── deploy/            # 部署相关功能
    │   ├── crypto/            # 加密工具
    │   └── utils/             # 工具函数
    ├── tests/                 # 测试代码
    │   ├── unit/              # 单元测试
    │   ├── integration/       # 集成测试
    │   └── fixtures/          # 测试数据
    ├── docs/                  # 文档
    ├── examples/              # 示例代码
    ├── scripts/               # 构建脚本
    └── pyproject.toml         # 项目配置

代码规范
--------

代码风格
~~~~~~~~

fabik 项目遵循 PEP 8 代码风格规范，使用以下工具进行代码格式化和检查：

- **Black**: 代码格式化
- **isort**: 导入排序
- **flake8**: 代码风格检查
- **mypy**: 类型检查

.. code-block:: bash

    # 格式化代码
    black fabik/ tests/
    
    # 排序导入
    isort fabik/ tests/
    
    # 检查代码风格
    flake8 fabik/ tests/
    
    # 类型检查
    mypy fabik/

提交规范
~~~~~~~~

提交信息应该遵循以下格式：

.. code-block::

    <type>(<scope>): <subject>
    
    <body>
    
    <footer>

类型（type）包括：

- **feat**: 新功能
- **fix**: 修复 bug
- **docs**: 文档更新
- **style**: 代码格式调整
- **refactor**: 代码重构
- **test**: 测试相关
- **chore**: 构建过程或辅助工具的变动

示例：

.. code-block::

    feat(config): 添加环境变量替换功能
    
    - 支持 ${VAR} 和 ${VAR:default} 语法
    - 添加环境变量验证
    - 更新相关文档
    
    Closes #123

测试
----

运行测试
~~~~~~~~

.. code-block:: bash

    # 运行所有测试
    pytest
    
    # 运行指定测试文件
    pytest tests/test_config.py
    
    # 运行指定测试函数
    pytest tests/test_config.py::test_load_config
    
    # 生成覆盖率报告
    pytest --cov=fabik --cov-report=html

测试分类
~~~~~~~~

- **单元测试**: 测试单个函数或类的功能
- **集成测试**: 测试多个组件的协作
- **端到端测试**: 测试完整的用户场景

编写测试
~~~~~~~~

测试文件应该放在 ``tests/`` 目录下，文件名以 ``test_`` 开头：

.. code-block:: python

    # tests/test_config.py
    import pytest
    from fabik.config import Config
    
    def test_load_config():
        """测试配置加载功能"""
        config = Config.load('tests/fixtures/test.toml')
        assert config.get('project.name') == 'test-project'
    
    def test_environment_config():
        """测试环境配置"""
        config = Config.load('tests/fixtures/test.toml', environment='development')
        assert config.get('debug') is True
    
    @pytest.fixture
    def sample_config():
        """测试配置夹具"""
        return {
            'project': {'name': 'test'},
            'debug': True
        }

文档
----

构建文档
~~~~~~~~

.. code-block:: bash

    # 安装文档依赖
    pip install -e .[doc]
    
    # 构建 HTML 文档
    cd docs
    make html
    
    # 启动文档服务器
    make serve

文档规范
~~~~~~~~

- 使用 reStructuredText 格式
- 每个模块都应该有对应的文档
- API 文档使用 autodoc 自动生成
- 示例代码应该可以运行

调试
----

日志配置
~~~~~~~~

在开发环境中启用详细日志：

.. code-block:: python

    import logging
    
    # 设置日志级别
    logging.basicConfig(level=logging.DEBUG)
    
    # 或者在配置文件中设置
    # [logging]
    # level = "DEBUG"

调试工具
~~~~~~~~

推荐使用以下调试工具：

- **pdb**: Python 内置调试器
- **ipdb**: 增强版调试器
- **pytest-pdb**: 在测试中使用调试器

.. code-block:: python

    # 在代码中设置断点
    import pdb; pdb.set_trace()
    
    # 或者使用 ipdb
    import ipdb; ipdb.set_trace()

性能分析
~~~~~~~~

使用 cProfile 进行性能分析：

.. code-block:: bash

    # 分析脚本性能
    python -m cProfile -o profile.stats script.py
    
    # 查看分析结果
    python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(10)"

发布流程
--------

版本管理
~~~~~~~~

fabik 使用语义化版本控制（SemVer）：

- **主版本号**: 不兼容的 API 修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

发布步骤
~~~~~~~~

1. 更新版本号：

.. code-block:: bash

    # 更新 pyproject.toml 中的版本号
    # 更新 docs/conf.py 中的版本号

2. 更新变更日志：

.. code-block:: bash

    # 在 CHANGELOG.md 中记录变更

3. 创建发布标签：

.. code-block:: bash

    git tag -a v1.0.0 -m "Release version 1.0.0"
    git push origin v1.0.0

4. 构建和发布：

.. code-block:: bash

    # 构建包
    python -m build
    
    # 发布到 PyPI
    python -m twine upload dist/*

持续集成
--------

GitHub Actions
~~~~~~~~~~~~~~

项目使用 GitHub Actions 进行持续集成：

.. code-block:: yaml

    # .github/workflows/test.yml
    name: Test
    
    on: [push, pull_request]
    
    jobs:
      test:
        runs-on: ubuntu-latest
        strategy:
          matrix:
            python-version: [3.9, 3.10, 3.11, 3.12]
        
        steps:
        - uses: actions/checkout@v3
        - name: Set up Python
          uses: actions/setup-python@v3
          with:
            python-version: ${{ matrix.python-version }}
        - name: Install dependencies
          run: |
            pip install -e .[dev]
        - name: Run tests
          run: |
            pytest --cov=fabik

代码质量检查
~~~~~~~~~~~~

.. code-block:: yaml

    # .github/workflows/quality.yml
    name: Code Quality
    
    on: [push, pull_request]
    
    jobs:
      quality:
        runs-on: ubuntu-latest
        steps:
        - uses: actions/checkout@v3
        - name: Set up Python
          uses: actions/setup-python@v3
          with:
            python-version: 3.11
        - name: Install dependencies
          run: |
            pip install black isort flake8 mypy
        - name: Check formatting
          run: |
            black --check fabik/ tests/
            isort --check-only fabik/ tests/
        - name: Lint
          run: |
            flake8 fabik/ tests/
        - name: Type check
          run: |
            mypy fabik/

贡献指南
--------

如何贡献
~~~~~~~~

1. Fork 项目到你的 GitHub 账户
2. 创建功能分支：``git checkout -b feature/new-feature``
3. 提交你的修改：``git commit -am 'Add new feature'``
4. 推送到分支：``git push origin feature/new-feature``
5. 创建 Pull Request

Pull Request 规范
~~~~~~~~~~~~~~~~~

- 提供清晰的标题和描述
- 关联相关的 Issue
- 确保所有测试通过
- 更新相关文档
- 遵循代码规范

问题报告
~~~~~~~~

报告 bug 时请提供：

- 详细的问题描述
- 重现步骤
- 期望的行为
- 实际的行为
- 环境信息（Python 版本、操作系统等）
- 相关的错误日志

功能请求
~~~~~~~~

提出新功能时请说明：

- 功能的用途和价值
- 详细的功能描述
- 可能的实现方案
- 是否愿意参与开发