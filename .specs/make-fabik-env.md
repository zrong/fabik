# fabik 环境配置增强实现计划

## 概述

为了增强 fabik 项目的配置文件替换功能，需要引入 `.fabik.env` 环境配置文件，实现双配置文件架构（`fabik.toml` + `.fabik.env`），并调整相关的读取和验证逻辑。

## 任务分解

### 调整后的重点修改

#### 1. ConfigReplacer 类的结构调整
- `fabik_conf` 属性重命名为 `fabik_conf_data`
- 新增 `fabik_env_data` 属性用于存储 `.fabik.env` 的数据
- `fabik_name` 在类初始化时固化，优先级：环境配置 > TOML 配置 > 默认值

#### 2. FabikConfig 环境变量处理规则
- 仅将 `.fabik.env` 中**不以项目名称值开头**的变量并入 `root_data`
  - 项目名称值指的是 NAME 配置项的实际值（如 "fabik"）
  - 例：如果 NAME="myapp"，则不将 MYAPP_* 变量并入 root_data
- 保持以项目名称开头的变量作为环境变量单独处理（如 `FABIK_LOCAL_*` 等）
- 环境配置优先级高于 TOML 配置

#### 3. 所有 ConfigReplacer 创建处调整
- 更新所有创建 `ConfigReplacer` 实例的地方
- 传递 `fabik_env_data` 参数
- 确保参数顺序正确

### 原计划任务

### 1. 文件路径生成方法调整

**影响文件**: `fabik/conf.py`

**修改内容**:
- 为 `FabikConfig` 类添加 `gen_fabik_env` 静态方法，类似于 `gen_fabik_toml`
- 生成 `.fabik.env` 文件的绝对路径
- 确保环境文件路径与 TOML 文件位于同一目录

**实现要点**:
```python
@staticmethod
def gen_fabik_env(*, work_dir: Path | str | None = None) -> Path:
    """生成 .fabik.env 配置文件路径。"""
    work_dir = FabikConfig.gen_work_dir(work_dir)
    env_file = work_dir.joinpath(FABIK_ENV_FILE)
    return env_file.resolve().absolute()
```

### 2. 文件存在性检查扩展

**影响文件**: `fabik/conf.py`

**修改内容**:
- 扩展 `file_exists` 属性，检查两个配置文件是否都存在
- 添加 `env_file_exists` 属性，专门检查 `.fabik.env` 文件
- 添加 `both_files_exist` 属性，检查两个文件是否同时存在

**实现要点**:
```python
@property
def env_file_exists(self) -> bool:
    """返回环境配置文件 .fabik.env 是否存在。"""
    return self.fabik_env is not None and self.fabik_env.exists()

@property  
def both_files_exist(self) -> bool:
    """返回两个配置文件是否都存在。"""
    return self.file_exists and self.env_file_exists
```

### 3. 环境配置加载方法

**影响文件**: `fabik/conf.py`

**修改内容**:
- 添加 `load_env_data` 方法，用于加载和解析 `.fabik.env` 文件
- 使用 `dotenv_values` 读取环境配置文件
- 处理文件不存在的异常情况

**实现要点**:
```python
def load_env_data(self) -> dict[str, Any]:
    """获取环境配置文件 .fabik.env 并进行简单的检测"""
    if self.env_data is None:
        if self.fabik_env is None:
            raise ConfigError(
                err_type=FileNotFoundError(),
                err_msg=f"{FABIK_ENV_FILE} not found.",
            )
        try:
            # 使用 dotenv_values 读取 .env 格式文件
            raw_env_data = dotenv_values(self.fabik_env)
            # 过滤掉 None 值
            self.env_data = {k: v for k, v in raw_env_data.items() if v is not None}
        except Exception as e:
            raise ConfigError(
                err_type=e,
                err_msg=f"Load {self.fabik_env} error: {e}",
            )
    return self.env_data
```

### 4. 初始化方法调整

**影响文件**: `fabik/conf.py`

**修改内容**:
- 在 `FabikConfig.__init__` 方法中初始化 `fabik_env` 路径
- 确保 `fabik_toml` 和 `fabik_env` 路径都被正确设置

**实现要点**:
```python
def __init__(self, work_dir: Path | str | None = None, cfg: dict | Path | str | None = None):
    # ... 现有代码 ...
    if isinstance(cfg, dict):
        self.root_data = cfg
    else:
        self.fabik_toml = FabikConfig.gen_fabik_toml(work_dir=work_dir, conf_file=cfg)
        # 新增：同时初始化环境文件路径
        self.fabik_env = FabikConfig.gen_fabik_env(work_dir=work_dir)
```

### 5. 配置读取逻辑增强

**影响文件**: `fabik/conf.py`

**修改内容**:
- 修改 `load_root_data` 方法，确保同时加载两个配置文件
- 将 `.fabik.env` 中不以 NAME 开头的变量并入到 `root_data` 中
- 环境文件中的变量优先级高于 TOML 文件中的同名变量
- 处理两个文件必须同时存在的验证逻辑

**实现要点**:
```python
def load_root_data(self) -> dict[str, Any]:
    """获取主配置文件并合并环境配置"""
    if self.root_data is None:
        # 检查两个文件必须同时存在
        if not self.both_files_exist:
            missing_files = []
            if not self.file_exists:
                missing_files.append(FABIK_TOML_FILE)
            if not self.env_file_exists:
                missing_files.append(FABIK_ENV_FILE)
            raise ConfigError(
                err_type=FileNotFoundError(),
                err_msg=f"Required config files not found: {', '.join(missing_files)}",
            )
        
        # 加载 TOML 配置
        # ... 现有 TOML 加载逻辑 ...
        
        # 加载环境配置
        env_data = self.load_env_data()
        
        # 获取项目名称（优先从环境配置获取）
        project_name = env_data.get('NAME', self.root_data.get('NAME', 'fabik'))
        
        # 将不以项目名称值开头的环境变量并入 root_data
        if env_data:
            name_prefix = f"{project_name.upper()}_"
            non_name_vars = {k: v for k, v in env_data.items() 
                           if not k.startswith(name_prefix) and k != 'NAME'}
            
            # 合并配置：环境配置覆盖 TOML 配置中的同名键
            self.root_data = merge_dict(self.root_data, non_name_vars)
    
    return self.root_data
```

### 6. ConfigReplacer 类调整

**影响文件**: `fabik/conf.py`

**修改内容**:
- 在类初始化时固化 `fabik_name` 变量值
- `fabik_conf` 属性改名为 `fabik_conf_data`
- 新增 `fabik_env_data` 属性，用于存储 `.fabik.env` 的值
- 修改 `_fill_root_meta` 方法，直接使用固化的 `fabik_name`
- 优先从环境配置中获取 `WORK_DIR`、`TPL_DIR`、`DEPLOY_DIR`

**实现要点**:
```python
class ConfigReplacer:
    # ... 其他属性 ...
    fabik_name: str  # 在初始化时固化
    fabik_conf_data: dict  # 重命名的属性
    fabik_env_data: dict   # 新增的环境数据属性
    
    def __init__(
        self,
        fabik_conf_data: dict[str, Any],
        fabik_env_data: dict[str, Any],  # 新增参数
        work_dir: Path,
        *,
        output_dir: Path | None = None,
        tpl_dir: Path | None = None,
        env_name: str | None = None,
        verbose: bool = False,
    ):
        """初始化"""
        self.fabik_conf_data = fabik_conf_data
        self.fabik_env_data = fabik_env_data  # 新增
        self.work_dir = work_dir
        
        # ... 其他初始化逻辑 ...
        
        # 固化 fabik_name：优先从环境配置获取，然后从 TOML 配置获取
        self.fabik_name = (
            fabik_env_data.get("NAME") or 
            fabik_conf_data.get("NAME") or 
            "fabik"
        )
        
        # 使用合并后的配置数据进行其他初始化
        merged_conf = merge_dict(fabik_conf_data, fabik_env_data)
        self.envs = merged_conf.get("ENV", None)
        
        # ... 其他初始化逻辑 ...

    def _fill_root_meta(self, replace_obj: dict = {}):
        """向被替换的值，填充 NAME/WORK_DIR/DEPLOY_DIR 变量。"""
        # 直接使用固化的 fabik_name
        replace_obj["NAME"] = self.fabik_name
        
        # 优先从环境配置获取 WORK_DIR，否则使用当前工作目录
        work_dir_from_env = self.fabik_env_data.get("WORK_DIR")
        if work_dir_from_env:
            replace_obj["WORK_DIR"] = Path(work_dir_from_env).resolve().as_posix()
        else:
            replace_obj["WORK_DIR"] = self.work_dir.resolve().as_posix()
        
        # 优先从环境配置获取 TPL_DIR
        tpl_dir_from_env = self.fabik_env_data.get("TPL_DIR")
        if tpl_dir_from_env:
            replace_obj["TPL_DIR"] = Path(tpl_dir_from_env).resolve().as_posix()
        
        # 处理 DEPLOY_DIR（优先从环境配置获取）
        deploy_dir = (
            self.fabik_env_data.get("DEPLOY_DIR") or
            self.fabik_conf_data.get("DEPLOY_DIR") or
            f"/srv/app/{self.fabik_name}"
        )
        if isinstance(deploy_dir, str):
            deploy_dir = Path(deploy_dir)
        if isinstance(deploy_dir, Path):
            replace_obj["DEPLOY_DIR"] = deploy_dir.as_posix()
        
        if self.env_name:
            replace_obj["ENV_NAME"] = self.env_name
        
        return replace_obj
```

### 7. 验证器函数调整

**影响文件**: `fabik/conf.py`

**修改内容**:
- 修改 `config_validator_name_workdir` 函数，验证环境配置文件中的路径
- 添加新的验证器函数检查两个配置文件是否同时存在

**实现要点**:
```python
def config_validator_both_files_exist(config: FabikConfig) -> bool:
    """检查两个配置文件是否都存在"""
    if not config.both_files_exist:
        missing_files = []
        if not config.file_exists:
            missing_files.append(FABIK_TOML_FILE)
        if not config.env_file_exists:
            missing_files.append(FABIK_ENV_FILE)
        echo_error(f"Required config files not found: {', '.join(missing_files)}")
        return False
    return True
```

### 8. GlobalState 和相关调用调整

**影响文件**: `fabik/cmd/__init__.py` 和其他使用 `ConfigReplacer` 的文件

**修改内容**:
- 注册新的验证器函数
- 确保配置加载逻辑能处理双配置文件
- 更新所有创建 `ConfigReplacer` 实例的地方，传递 `fabik_env_data` 参数

**实现要点**:
```python
# 在文件末尾注册新的验证器
global_state.register_config_validator(config_validator_both_files_exist)

# 更新 ConfigReplacer 的创建方式
def build_deploy_conn(self, deploy_class: type["Deploy"]) -> "Deploy":
    # ... 现有逻辑 ...
    
    # 获取环境数据
    env_data = self.fabik_config.env_data or {}
    
    replacer = ConfigReplacer(
        self.conf_data,      # fabik_conf_data
        env_data,            # fabik_env_data (新增)
        self.cwd, 
        env_name=self.env, 
        verbose=self.verbose
    )
    # ... 其他逻辑 ...
```

### 9. 主命令调整

**影响文件**: `fabik/cmd/main.py`

**修改内容**:
- 修改 `main_init` 函数，同时创建两个配置文件
- 使用 `FABIK_ENV_TPL` 模板创建 `.fabik.env` 文件
- 确保两个文件使用一致的变量值进行渲染

**实现要点**:
```python
def main_init(full_format: bool = False, force: bool = False):
    work_dir = global_state.cwd
    
    # 准备模板变量
    template_vars = {
        "create_time": f"{fabik.__now__!s}",
        "fabik_version": fabik.__version__,
        "WORK_DIR": work_dir.absolute().as_posix(),
        "NAME": work_dir.name,  # 使用目录名作为默认项目名
    }
    
    # 创建 fabik.toml
    toml_content = jinja2.Template(
        tpl.FABIK_TOML_TPL if full_format else tpl.FABIK_TOML_SIMPLE_TPL
    ).render(**template_vars)
    
    # 创建 .fabik.env  
    env_content = jinja2.Template(tpl.FABIK_ENV_TPL).render(**template_vars)
    
    toml_file = work_dir.joinpath(tpl.FABIK_TOML_FILE)
    env_file = work_dir.joinpath(tpl.FABIK_ENV_FILE)
    
    # 检查文件存在性和处理覆盖逻辑
    files_to_create = [(toml_file, toml_content), (env_file, env_content)]
    
    for file_path, content in files_to_create:
        if file_path.exists() and not force:
            echo_warning(f"{file_path!s} already exists. Use --force to overwrite it.")
            raise typer.Exit()
        elif file_path.exists() and force:
            echo_warning(f"Overwriting {file_path!s}.")
    
    # 写入文件
    for file_path, content in files_to_create:
        file_path.write_text(content)
        echo_info(f"{file_path} has been created.")
```

### 10. 相关调用更新

**影响文件**: 所有使用 `ConfigReplacer` 的文件

**修改内容**:
- 更新所有创建 `ConfigReplacer` 实例的地方
- 传递新的 `fabik_env_data` 参数
- 确保参数名称和顺序正确

**影响范围**:
- `fabik/cmd/__init__.py` - `build_deploy_conn` 方法
- `fabik/cmd/*.py` - 所有使用 `ConfigReplacer` 的命令
- `fabik/deploy/__init__.py` - `Deploy` 类初始化
- 其他可能使用 `ConfigReplacer` 的地方

**实现要点**:
```python
# 示例：更新 build_deploy_conn 方法
def build_deploy_conn(self, deploy_class: type["Deploy"]) -> "Deploy":
    # ... 现有逻辑 ...
    
    # 获取环境数据
    env_data = self.fabik_config.env_data or {}
    
    replacer = ConfigReplacer(
        self.conf_data,      # fabik_conf_data (重命名)
        env_data,            # fabik_env_data (新增参数)
        self.cwd, 
        env_name=self.env, 
        verbose=self.verbose
    )
    # ... 其他逻辑 ...
```

### 11. 测试用例更新

**影响文件**: `tests/test_*.py`

**修改内容**:
- 更新相关测试用例，确保兼容双配置文件架构
- 添加新的测试用例验证环境配置功能
- 模拟两个配置文件的存在性检查
- 更新 `ConfigReplacer` 的创建方式，传递新的参数

## 风险评估

### 兼容性风险
- **向后兼容性**: 现有只有 `fabik.toml` 的项目需要迁移
- **测试覆盖**: 需要全面测试双配置文件场景

### 缓解措施
- 在初期实现中保留单配置文件的兼容性，通过配置标志控制
- 提供迁移工具或清楚的迁移指南
- 完善的错误提示，指导用户正确配置

## 实施顺序

1. **第一阶段**: 文件路径生成和存在性检查（任务 1-2）
2. **第二阶段**: 环境配置加载逻辑（任务 3-4）
3. **第三阶段**: 配置合并和替换逻辑（任务 5-6）
4. **第四阶段**: 验证器和初始化命令（任务 7-9）
6. **第六阶段**: 相关调用更新和测试用例（任务 10-11）

## 验证标准

- [ ] 两个配置文件必须同时存在才能正常运行
- [ ] 环境配置文件中的变量能正确覆盖 TOML 配置中的同名变量
- [ ] 仅将 `.fabik.env` 中不以项目名称值开头的变量并入 `root_data`
- [ ] `fabik_name` 在 `ConfigReplacer` 初始化时固化，优先级正确
- [ ] `WORK_DIR`、`TPL_DIR`、`DEPLOY_DIR` 等变量能从环境配置文件中正确读取
- [ ] 初始化命令能同时创建两个配置文件
- [ ] 所有 `ConfigReplacer` 的创建处都已更新为新的参数结构
- [ ] 现有的测试用例在修改后仍能通过
- [ ] 错误提示清楚，能指导用户正确配置

---

*此计划基于当前代码结构制定，实施过程中可能需要根据具体情况进行微调。*