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
        global_state.cwd = None
        global_state.env = None
        global_state.fabik_file = None
        global_state.fabik_config = None

    def test_init_new_config_file(self, temp_dir, mocker, mock_echo_functions):
        """测试创建新的配置文件"""
        # 准备测试环境
        mock_jinja_template = mocker.patch('jinja2.Template')
        mock_template_instance = MagicMock()
        mock_jinja_template.return_value = mock_template_instance
        mock_template_instance.render.return_value = "mock_config_content"
        
        # 模拟 Path.exists 返回 False，表示文件不存在
        mocker.patch('pathlib.Path.exists', return_value=False)
        
        # 模拟 Path.write_text 方法
        mock_write_text = mocker.patch('pathlib.Path.write_text')
        
        # 设置 global_state
        global_state.cwd = temp_dir
        
        # 模拟 FabikConfig 的行为
        mock_fabik_config_class = mocker.patch('fabik.cmd.FabikConfig')
        mock_fabik_config_class.gen_fabik_toml.return_value = temp_dir / FABIK_TOML_FILE
        
        # 创建一个模拟实例，但让 load_config 抛出异常
        mock_instance = MagicMock()
        mock_instance.load_config.side_effect = PathError(
            err_type=FileNotFoundError(), err_msg="File not found"
        )
        mock_fabik_config_class.return_value = mock_instance
        
        # 执行测试函数
        main_init(full_format=False, force=False)
        
        # 验证结果
        mock_template_instance.render.assert_called_once()
        mock_echo_functions['echo_info'].assert_called_once()
        
        # 验证 render 方法被调用时包含了所有必要的参数
        render_kwargs = mock_template_instance.render.call_args.kwargs
        assert 'create_time' in render_kwargs
        assert 'fabik_version' in render_kwargs
        assert 'WORK_DIR' in render_kwargs
        # 注意：实际上还有一个 NAME 参数，这是我们之前没有预期到的
        
        # 验证写入文件的调用
        mock_write_text.assert_called_once_with("mock_config_content")
        assert mock_jinja_template.call_args[0][0] == FABIK_TOML_TPL

    def test_init_with_full_format(self, temp_dir, mocker, mock_echo_functions):
        """测试使用完整格式创建配置文件"""
        # 准备测试环境
        mock_jinja_template = mocker.patch('jinja2.Template')
        mock_template_instance = MagicMock()
        mock_jinja_template.return_value = mock_template_instance
        mock_template_instance.render.return_value = "mock_full_config_content"
        
        # 模拟 Path.exists 返回 False，表示文件不存在
        mocker.patch('pathlib.Path.exists', return_value=False)
        
        # 模拟 Path.write_text 方法
        mock_write_text = mocker.patch('pathlib.Path.write_text')
        
        # 设置 global_state
        global_state.cwd = temp_dir
        
        # 模拟 FabikConfig 的行为
        mock_fabik_config_class = mocker.patch('fabik.cmd.FabikConfig')
        mock_fabik_config_class.gen_fabik_toml.return_value = temp_dir / FABIK_TOML_FILE
        
        # 创建一个模拟实例，但让 load_config 抛出异常
        mock_instance = MagicMock()
        mock_instance.load_config.side_effect = PathError(
            err_type=FileNotFoundError(), err_msg="File not found"
        )
        mock_fabik_config_class.return_value = mock_instance
        
        # 执行测试函数
        main_init(full_format=True, force=False)
        
        # 验证结果
        mock_template_instance.render.assert_called_once()
        mock_echo_functions['echo_info'].assert_called_once()
        
        # 验证 render 方法被调用时包含了所有必要的参数
        render_kwargs = mock_template_instance.render.call_args.kwargs
        assert 'create_time' in render_kwargs
        assert 'fabik_version' in render_kwargs
        assert 'WORK_DIR' in render_kwargs
        # 注意：实际上还有一个 NAME 参数，这是我们之前没有预期到的
        
        # 验证写入文件的调用
        mock_write_text.assert_called_once_with("mock_full_config_content")
        assert mock_jinja_template.call_args[0][0] == FABIK_TOML_TPL

    def test_init_existing_config_without_force(self, temp_dir, mocker, mock_echo_functions):
        """测试在配置文件已存在且不使用 force 参数的情况"""
        # 准备测试环境 - 创建一个真实的配置文件
        config_file = temp_dir / FABIK_TOML_FILE
        config_file.write_text("existing_config")
        
        # 模拟 Path.exists 返回 True
        mocker.patch('pathlib.Path.exists', return_value=True)
        
        # 设置 global_state
        global_state.cwd = temp_dir
        
        # 模拟 FabikConfig 的行为
        mock_fabik_config_class = mocker.patch('fabik.cmd.FabikConfig')
        mock_instance = MagicMock()
        mock_instance.load_config.side_effect = PathError(
            err_type=FileNotFoundError(), err_msg="File not found"
        )
        mock_fabik_config_class.return_value = mock_instance
        
        # 执行测试函数，应该抛出 typer.Exit 异常
        with pytest.raises(typer.Exit):
            main_init(full_format=False, force=False)
        
        # 验证警告信息被调用
        mock_echo_functions['echo_warning'].assert_called_once()
        mock_echo_functions['echo_info'].assert_not_called()

    def test_init_existing_config_with_force(self, temp_dir, mocker, mock_echo_functions):
        """测试在配置文件已存在且使用 force 参数的情况"""
        # 准备测试环境
        config_file = temp_dir / FABIK_TOML_FILE
        config_file.write_text("existing_config")
        
        # 模拟 jinja2.Template
        mock_jinja_template = mocker.patch('jinja2.Template')
        mock_template_instance = MagicMock()
        mock_jinja_template.return_value = mock_template_instance
        mock_template_instance.render.return_value = "new_config_content"
        
        # 模拟 Path.exists 返回 True
        mocker.patch('pathlib.Path.exists', return_value=True)
        
        # 模拟 Path.write_text 方法
        mock_write_text = mocker.patch('pathlib.Path.write_text')
        
        # 设置 global_state
        global_state.cwd = temp_dir
        
        # 模拟 FabikConfig 的行为
        mock_fabik_config_class = mocker.patch('fabik.cmd.FabikConfig')
        mock_instance = MagicMock()
        mock_instance.load_config.side_effect = PathError(
            err_type=FileNotFoundError(), err_msg="File not found"
        )
        mock_fabik_config_class.return_value = mock_instance
        
        # 执行测试函数
        main_init(full_format=False, force=True)
        
        # 验证结果
        mock_echo_functions['echo_warning'].assert_called_once()
        mock_echo_functions['echo_info'].assert_called_once()
        mock_write_text.assert_called_once_with("new_config_content")

    def test_init_with_valid_work_dir(self, temp_dir, mocker, mock_echo_functions):
        """测试当 work_dir 有效时的情况"""
        # 准备测试环境
        custom_work_dir = temp_dir / "custom_work_dir"
        custom_work_dir.mkdir(exist_ok=True)
        
        # 模拟 jinja2.Template
        mock_jinja_template = mocker.patch('jinja2.Template')
        mock_template_instance = MagicMock()
        mock_jinja_template.return_value = mock_template_instance
        mock_template_instance.render.return_value = "config_with_work_dir"
        
        # 模拟 Path.exists 返回 False
        mocker.patch('pathlib.Path.exists', return_value=False)
        
        # 模拟 Path.write_text 方法
        mock_write_text = mocker.patch('pathlib.Path.write_text')
        
        # 设置 global_state
        global_state.cwd = temp_dir
        
        # 创建一个模拟的 FabikConfig 实例
        mock_fabik_config_class = mocker.patch('fabik.cmd.FabikConfig')
        mock_config_instance = MagicMock()
        mock_fabik_config_class.return_value = mock_config_instance
        
        # 设置 getcfg 返回值
        mock_config_instance.getcfg.return_value = str(custom_work_dir)
        
        # 执行测试函数
        main_init(full_format=False, force=False)
        
        # 验证结果
        mock_echo_functions['echo_info'].assert_called_once()
        
        # 验证模板渲染调用包含了正确的工作目录
        render_kwargs = mock_template_instance.render.call_args.kwargs
        assert 'WORK_DIR' in render_kwargs
        assert str(custom_work_dir.absolute()) in render_kwargs['WORK_DIR']
        
        # 验证写入了正确的文件
        mock_write_text.assert_called_once_with("config_with_work_dir")

    def test_template_syntax(self):
        """测试模板语法是否正确，使用真实的模板数据"""
        # 测试完整模板
        try:
            template = jinja2.Template(FABIK_TOML_TPL)
            result = template.render(
                create_time="2023-01-01",
                fabik_version="0.1.0",
                NAME="test_project",
                WORK_DIR="/path/to/project",
                ADMIN_NAME="admin"
            )
            assert "test_project" in result
            assert "/path/to/project" in result
            assert "python3" in result  # PYE 默认值
            assert "/srv/app/test_project" in result  # DEPLOY_DIR
        except jinja2.exceptions.TemplateSyntaxError as e:
            pytest.fail(f"Full template has syntax error: {e}")

    def test_real_template_rendering(self, temp_dir):
        """使用真实的模板和渲染引擎测试"""
        # 准备测试数据
        test_data = {
            'create_time': '2023-01-01',
            'fabik_version': '0.1.0',
            'NAME': 'test_project',
            'WORK_DIR': str(temp_dir)
        }
        
        # 测试完整模板
        full_template = jinja2.Template(FABIK_TOML_TPL)
        full_result = full_template.render(**test_data)
        
        # 验证完整模板的渲染结果
        assert 'test_project' in full_result
        assert str(temp_dir) in full_result
        assert 'python3' in full_result
        assert '/srv/app/test_project' in full_result
        
        # 将渲染结果写入临时文件，验证是否可以正确写入
        simple_file = temp_dir / 'simple_config.toml'
        full_file = temp_dir / 'full_config.toml'
        
        full_file.write_text(full_result)
        
        assert simple_file.exists()
        assert full_file.exists()
        
        # 读取文件内容，验证是否与渲染结果一致
        assert full_file.read_text() == full_result