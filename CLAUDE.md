# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在处理本代码库时提供指导。

## 项目概述

**fabik** (/ˈfæbɪk/) 是一个 Python CLI 基础包，提供以下功能：
- 支持多环境的 TOML 配置
- 基于模板的配置生成，支持环境变量替换
- 通过 Fabric 进行远程部署
- HTTP 客户端封装（同步/异步）
- 日志工具

## 快速开始

```bash
# 安装依赖
uv sync

# 运行 CLI
uv run fabik --help

# 初始化项目
uv run fabik init

# 运行测试
uv run pytest
```

## 开发命令

| 任务 | 命令 |
|------|---------|
| 安装依赖 | `uv sync` |
| 添加包 | `uv add package` |
| 添加开发包 | `uv add --dev package` |
| 运行 CLI | `uv run fabik` |
| 运行测试 | `uv run pytest` |
| 运行特定测试 | `uv run pytest tests/test_main.py::TestMainInit::test_init_new_config_file` |
| 覆盖率 | `uv run pytest --cov=fabik` |

## 架构

### 核心组件
- **GlobalState** (`fabik.cmd`): CLI 状态管理
- **FabikConfig** (`fabik.conf`): TOML 配置解析器
- **ConfigReplacer** (`fabik.conf`): 基于模板的配置生成器
- **HTTPxMixIn** (`fabik.http`): HTTP 客户端封装

### 命令结构
- 命令在 `cmd.py` 中定义（无装饰器）
- 命令通过 typer 在 `cli.py` 中注册
- 子命令: `fabik conf tpl|make`

## 配置

### fabik.toml
```toml
NAME = "project-name"
PYE = "python3"
DEPLOY_DIR = "/srv/app/{NAME}"

[PATH]
work_dir = "/abs/path"
tpl_dir = "{work_dir}/tpls"

[ENV.local]
# 环境覆盖配置
```

### 环境变量
格式: `{PROJECT}_{ENV}_{KEY}`
示例: `FABIK_LOCAL_ADMIN_NAME`

## 关键模式

### 添加命令
1. 在 `cmd.py` 中定义回调函数
2. 使用 typer 在 `cli.py` 中注册
3. 将单元测试按照模块划分功能,例如 `main_init` 在 `tests/test_main.py` 中定义, `conf_*` 在 `tests/test_conf.py` 中定义, `gen_*` 在 `tests/test_gen.py` 中定义.

### 模板系统
- 模板位于 `tpls/` 目录
- 使用 Jinja2 语法，支持环境变量替换
- 使用 `fabik conf tpl` 生成配置

### 测试
- 测试使用 `tests/fabik.toml` 配置
- 固定装置在 `conftest.py` 中
- 使用 pytest-mock 进行模拟

## 文件结构
```
fabik/
├── cli.py          # 命令注册
├── cmd.py          # 命令实现
├── conf.py         # 配置管理
├── http.py         # HTTP 客户端
├── deploy/         # 部署模块
└── util/           # 工具类
```

## 引用规则文件

项目使用 Cursor 规则文件来指导开发，这些文件包含了项目特定的编码规范和最佳实践：

- [项目结构规则](.cursor/rules/project-structure.mdc)
- [Pytest 规则](.cursor/rules/pytest.mdc)
- [Python 编码风格规则](.cursor/rules/python-style.mdc)
- [Typer CLI 规范](.cursor/rules/typer.mdc)