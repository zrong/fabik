"""
Tests for fabik.cmd module's gen_* commands
"""

import pytest
from unittest.mock import MagicMock, patch
import string
import uuid

from fabik.cmd.gen import gen_token, gen_password, gen_fernet_key, gen_uuid, gen_requirements, UUIDType
from fabik.util import gen as util_gen


class TestGenCommands:
    """测试生成命令函数"""

    def test_gen_password(self, mocker):
        """测试 gen_password 命令"""
        # Mock echo_info 函数
        mock_echo_info = mocker.patch('fabik.cmd.gen.echo_info')
        # Mock util.gen.gen_password 函数
        mock_gen_password = mocker.patch('fabik.cmd.gen.util.gen.gen_password', return_value="hashed_password")
        
        # 执行测试函数
        gen_password("test_password", "test_salt")
        
        # 验证 util.gen.gen_password 被调用
        mock_gen_password.assert_called_once_with("test_password", "test_salt")
        
        # 验证 echo_info 被调用
        mock_echo_info.assert_called_once_with("hashed_password")

    def test_gen_fernet_key(self, mocker):
        """测试 gen_fernet_key 命令"""
        # Mock echo_info 函数
        mock_echo_info = mocker.patch('fabik.cmd.echo_info')
        # Mock util.gen.gen_fernet_key 函数
        mock_gen_fernet_key = mocker.patch('fabik.cmd.util.gen.gen_fernet_key', return_value="fernet_key")
        
        # 执行测试函数
        gen_fernet_key()
        
        # 验证 util.gen.gen_fernet_key 被调用
        mock_gen_fernet_key.assert_called_once()
        
        # 验证 echo_info 被调用
        mock_echo_info.assert_called_once_with("fernet_key")

    def test_gen_token(self, mocker):
        """测试 gen_token 命令"""
        # Mock echo_info 函数
        mock_echo_info = mocker.patch('fabik.cmd.echo_info')
        # Mock util.gen.gen_token 函数
        mock_gen_token = mocker.patch('fabik.cmd.util.gen.gen_token', return_value="test_token")
        
        # 执行测试函数（默认长度为8）
        gen_token()
        
        # 验证 util.gen.gen_token 被调用
        mock_gen_token.assert_called_once_with(k=8)
        
        # 验证 echo_info 被调用
        mock_echo_info.assert_called_once_with("test_token")
        
        # 重置 mock
        mock_echo_info.reset_mock()
        mock_gen_token.reset_mock()
        
        # 测试自定义长度
        gen_token(16)
        
        # 验证 util.gen.gen_token 被调用
        mock_gen_token.assert_called_once_with(k=16)
        
        # 验证 echo_info 被调用
        mock_echo_info.assert_called_once_with("test_token")

    def test_gen_uuid(self, mocker):
        """测试 gen_uuid 命令"""
        # Mock echo_info 函数
        mock_echo_info = mocker.patch('fabik.cmd.echo_info')
        # Mock util.gen.gen_uuid 函数
        mock_gen_uuid = mocker.patch('fabik.cmd.util.gen.gen_uuid', return_value="test_uuid")
        
        # 执行测试函数（默认为uuid4）
        gen_uuid()
        
        # 验证 util.gen.gen_uuid 被调用
        mock_gen_uuid.assert_called_once_with('uuid4')
        
        # 验证 echo_info 被调用
        mock_echo_info.assert_called_once_with("test_uuid")
        
        # 重置 mock
        mock_echo_info.reset_mock()
        mock_gen_uuid.reset_mock()
        
        # 测试 uuid1
        gen_uuid(UUIDType.UUID1)
        
        # 验证 util.gen.gen_uuid 被调用
        mock_gen_uuid.assert_called_once_with('uuid1')
        
        # 验证 echo_info 被调用
        mock_echo_info.assert_called_once_with("test_uuid")

    def test_gen_requirements_success(self, mocker):
        """测试 gen_requirements 命令成功生成 requirements.txt"""
        # Mock echo_info 函数
        mock_echo_info = mocker.patch('fabik.cmd.echo_info')
        # Mock subprocess.run 函数
        mock_subprocess = mocker.patch('fabik.cmd.subprocess.run')
        
        # 执行测试函数
        gen_requirements()
        
        # 验证 subprocess.run 被正确调用
        mock_subprocess.assert_called_once_with(
            ["uv", "export", "--format", "requirements-txt", "--output-file", "requirements.txt"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # 验证 echo_info 被调用
        mock_echo_info.assert_called_once_with("requirements.txt 文件已成功生成！")

    def test_gen_requirements_subprocess_error(self, mocker):
        """测试 gen_requirements 命令处理 subprocess 错误"""
        from subprocess import CalledProcessError
        
        # Mock echo_error 函数
        mock_echo_error = mocker.patch('fabik.cmd.echo_error')
        # Mock subprocess.run 抛出 CalledProcessError
        mock_subprocess = mocker.patch('fabik.cmd.subprocess.run')
        mock_subprocess.side_effect = CalledProcessError(1, "uv", stderr="Command failed")
        
        # Mock typer.Abort
        mock_abort = mocker.patch('fabik.cmd.typer.Abort', side_effect=SystemExit)
        
        # 执行测试函数并验证异常
        with pytest.raises(SystemExit):
            gen_requirements()
        
        # 验证 echo_error 被调用
        mock_echo_error.assert_called_once_with("生成 requirements.txt 失败: Command failed")

    def test_gen_requirements_uv_not_found(self, mocker):
        """测试 gen_requirements 命令处理 uv 命令未找到错误"""
        # Mock echo_error 函数
        mock_echo_error = mocker.patch('fabik.cmd.echo_error')
        # Mock subprocess.run 抛出 FileNotFoundError
        mock_subprocess = mocker.patch('fabik.cmd.subprocess.run')
        mock_subprocess.side_effect = FileNotFoundError()
        
        # Mock typer.Abort
        mock_abort = mocker.patch('fabik.cmd.typer.Abort', side_effect=SystemExit)
        
        # 执行测试函数并验证异常
        with pytest.raises(SystemExit):
            gen_requirements()
        
        # 验证 echo_error 被调用
        mock_echo_error.assert_called_once_with("未找到 uv 命令，请确保已安装 uv 工具")