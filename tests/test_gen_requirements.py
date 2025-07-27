"""gen_requirements 函数的单元测试"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

from fabik.cmd.gen import gen_requirements
from fabik.cmd import global_state


class TestGenRequirements:
    """gen_requirements 函数测试类"""

    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 创建临时目录
        self.temp_dir = Path(tempfile.mkdtemp())
        self.original_cwd = global_state.cwd if hasattr(global_state, 'cwd') else None
        
    def teardown_method(self):
        """每个测试方法执行后的清理"""
        # 清理临时目录
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        # 恢复原始状态
        if self.original_cwd:
            global_state.cwd = self.original_cwd

    @patch('fabik.cmd.gen.subprocess.run')
    @patch('fabik.cmd.gen.global_state')
    def test_gen_requirements_default_behavior(self, mock_global_state, mock_subprocess):
        """测试默认行为：使用工作目录和默认文件名"""
        # 设置 mock
        mock_global_state.check_work_dir_or_use_cwd.return_value = self.temp_dir
        mock_subprocess.return_value = MagicMock()
        
        # 执行函数
        gen_requirements()
        
        # 验证调用
        mock_global_state.check_work_dir_or_use_cwd.assert_called_once()
        expected_output = str((self.temp_dir / "requirements.txt").absolute())
        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        assert "--output-file" in args
        assert expected_output in args

    @patch('fabik.cmd.gen.subprocess.run')
    def test_gen_requirements_with_output_file(self, mock_subprocess):
        """测试使用指定输出文件"""
        # 创建输出文件路径
        output_file = self.temp_dir / "custom_requirements.txt"
        mock_subprocess.return_value = MagicMock()
        
        # 执行函数
        gen_requirements(output_file=output_file)
        
        # 验证调用
        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        assert "--output-file" in args
        assert str(output_file.absolute()) in args

    def test_gen_requirements_output_file_parent_not_exists(self):
        """测试输出文件的父目录不存在"""
        # 创建不存在的目录路径
        non_existent_dir = self.temp_dir / "non_existent" / "requirements.txt"
        
        # 执行函数并期望抛出异常
        with pytest.raises(SystemExit):
            gen_requirements(output_file=non_existent_dir)

    def test_gen_requirements_output_file_parent_not_writable(self):
        """测试输出文件的父目录不可写"""
        # 创建只读目录
        readonly_dir = self.temp_dir / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # 只读权限
        
        output_file = readonly_dir / "requirements.txt"
        
        try:
            # 执行函数并期望抛出异常
            with pytest.raises(SystemExit):
                gen_requirements(output_file=output_file)
        finally:
            # 恢复权限以便清理
            readonly_dir.chmod(0o755)

    @patch('fabik.cmd.gen.subprocess.run')
    @patch('fabik.cmd.gen.global_state')
    def test_gen_requirements_file_exists_no_force(self, mock_global_state, mock_subprocess):
        """测试文件已存在且不使用 force 参数"""
        # 创建已存在的文件
        existing_file = self.temp_dir / "requirements.txt"
        existing_file.touch()
        
        mock_global_state.check_work_dir_or_use_cwd.return_value = self.temp_dir
        
        # 执行函数并期望抛出异常
        with pytest.raises(SystemExit):
            gen_requirements()

    @patch('fabik.cmd.gen.subprocess.run')
    @patch('fabik.cmd.gen.global_state')
    def test_gen_requirements_file_exists_with_force(self, mock_global_state, mock_subprocess):
        """测试文件已存在且使用 force 参数"""
        # 创建已存在的文件
        existing_file = self.temp_dir / "requirements.txt"
        existing_file.touch()
        
        mock_global_state.check_work_dir_or_use_cwd.return_value = self.temp_dir
        mock_subprocess.return_value = MagicMock()
        
        # 执行函数
        gen_requirements(force=True)
        
        # 验证调用
        mock_subprocess.assert_called_once()

    @patch('fabik.cmd.gen.subprocess.run')
    def test_gen_requirements_output_file_exists_with_force(self, mock_subprocess):
        """测试指定输出文件已存在且使用 force 参数"""
        # 创建已存在的文件
        output_file = self.temp_dir / "custom_requirements.txt"
        output_file.touch()
        
        mock_subprocess.return_value = MagicMock()
        
        # 执行函数
        gen_requirements(force=True, output_file=output_file)
        
        # 验证调用
        mock_subprocess.assert_called_once()

    @patch('fabik.cmd.gen.subprocess.run')
    def test_gen_requirements_subprocess_error(self, mock_subprocess):
        """测试 subprocess 执行失败"""
        # 设置 subprocess 抛出异常
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, "uv", stderr="命令执行失败"
        )
        
        output_file = self.temp_dir / "requirements.txt"
        
        # 执行函数并期望抛出异常
        with pytest.raises(SystemExit):
            gen_requirements(output_file=output_file)

    @patch('fabik.cmd.gen.subprocess.run')
    def test_gen_requirements_uv_not_found(self, mock_subprocess):
        """测试 uv 命令未找到"""
        # 设置 subprocess 抛出 FileNotFoundError
        mock_subprocess.side_effect = FileNotFoundError("uv 命令未找到")
        
        output_file = self.temp_dir / "requirements.txt"
        
        # 执行函数并期望抛出异常
        with pytest.raises(SystemExit):
            gen_requirements(output_file=output_file)

    @patch('fabik.cmd.gen.subprocess.run')
    @patch('fabik.cmd.gen.global_state')
    def test_gen_requirements_custom_filename(self, mock_global_state, mock_subprocess):
        """测试使用自定义文件名"""
        mock_global_state.check_work_dir_or_use_cwd.return_value = self.temp_dir
        mock_subprocess.return_value = MagicMock()
        
        # 执行函数
        gen_requirements(requirements_file_name="custom_reqs.txt")
        
        # 验证调用
        expected_output = str((self.temp_dir / "custom_reqs.txt").absolute())
        mock_subprocess.assert_called_once()
        args = mock_subprocess.call_args[0][0]
        assert expected_output in args