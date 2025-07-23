"""
Tests for fabik.cmd module's gen_* commands
"""

import pytest
from unittest.mock import MagicMock, patch
import string
import uuid

from fabik.cmd import gen_token, gen_password, gen_fernet_key, gen_uuid
from fabik.util import gen as util_gen


class TestGenCommands:
    """测试生成命令函数"""

    def test_gen_password(self, mocker):
        """测试 gen_password 命令"""
        # Mock echo_info 函数
        mock_echo_info = mocker.patch('fabik.cmd.echo_info')
        # Mock util.gen.gen_password 函数
        mock_gen_password = mocker.patch('fabik.cmd.util.gen.gen_password', return_value="hashed_password")
        
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
        gen_uuid('uuid1')
        
        # 验证 util.gen.gen_uuid 被调用
        mock_gen_uuid.assert_called_once_with('uuid1')
        
        # 验证 echo_info 被调用
        mock_echo_info.assert_called_once_with("test_uuid")