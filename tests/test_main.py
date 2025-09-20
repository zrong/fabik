"""
Tests for fabik.cmd module's main_init function
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

import typer
import jinja2
from fabik.cmd.main import main_init
from fabik.cmd import global_state
from fabik.tpl import FABIK_TOML_FILE, FABIK_TOML_TPL, FABIK_ENV_FILE
from fabik.error import PathError, ConfigError


class TestMainInit:
    """测试 main_init 函数"""

    def setup_method(self):
        """每个测试方法前重置 global_state"""
        # 重置GlobalState的属性，现在很多是只读属性
        global_state.fabik_config = None
        global_state.force = False
        global_state.rename = False
        global_state.env_postfix = False
        global_state.verbose = False
        global_state.env_name = ""
        global_state.output_dir = None
        global_state.output_file = None
        global_state._config_validators = []

    def test_template_syntax(self):
        """测试模板语法是否正确，使用真实的模板数据"""
        # 测试 TOML 模板
        try:
            template = jinja2.Template(FABIK_TOML_TPL)
            result = template.render(
                create_time="2023-01-01",
                fabik_version="0.1.0",
                NAME="test_project",
                ADMIN_NAME="admin"
            )
            assert "test_project" in result
            assert "python3" in result  # PYE 默认值
            assert "/srv/app/test_project" in result  # DEPLOY_DIR
        except jinja2.exceptions.TemplateSyntaxError as e:
            pytest.fail(f"TOML template has syntax error: {e}")

    def test_real_template_rendering(self, temp_dir):
        """使用真实的模板和渲染引擎测试"""
        # 准备测试数据
        test_data = {
            'create_time': '2023-01-01',
            'fabik_version': '0.1.0',
            'NAME': 'test_project'
        }
        
        # 测试 TOML 模板
        toml_template = jinja2.Template(FABIK_TOML_TPL)
        toml_result = toml_template.render(**test_data)
        
        # 验证 TOML 模板的渲染结果
        assert 'test_project' in toml_result
        assert 'python3' in toml_result
        assert '/srv/app/test_project' in toml_result
        
        # 将渲染结果写入临时文件，验证是否可以正确写入
        toml_file = temp_dir / 'test_config.toml'
        toml_file.write_text(toml_result)
        
        assert toml_file.exists()
        
        # 读取文件内容，验证是否与渲染结果一致
        assert toml_file.read_text() == toml_result

    def test_env_template_rendering(self, temp_dir):
        """测试环境文件模板渲染"""
        from fabik.tpl import FABIK_ENV_TPL
        
        # 准备测试数据
        test_data = {
            'create_time': '2023-01-01',
            'fabik_version': '0.1.0',
            'NAME': 'test_project',
            'WORK_DIR': str(temp_dir)
        }
        
        # 测试 ENV 模板
        env_template = jinja2.Template(FABIK_ENV_TPL)
        env_result = env_template.render(**test_data)
        
        # 验证 ENV 模板的渲染结果
        assert str(temp_dir) in env_result
        
        # 将渲染结果写入临时文件
        env_file = temp_dir / '.test.env'
        env_file.write_text(env_result)
        
        assert env_file.exists()
        assert env_file.read_text() == env_result