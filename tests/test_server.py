"""
Tests for fabik.cmd module's server_* commands
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from fabik.cmd import server_deploy, server_start, server_stop, server_reload, server_dar
from fabik.error import FabikError


class TestServerCommands:
    """测试服务器命令函数"""

    def test_server_deploy_success(self, mocker):
        """测试 server_deploy 命令成功执行"""
        # Mock global_state.deploy_conn
        mock_deploy_conn = MagicMock()
        mock_deploy_conn.rsync = MagicMock()
        mock_deploy_conn.put_config = MagicMock()
        
        # Mock global_state.pyape_conf
        mock_pyape_conf = {"RSYNC_EXCLUDE": [".git", "__pycache__", ".venv"]}
        
        # Mock global_state
        with patch('fabik.cmd.global_state') as mock_global:
            mock_global.deploy_conn = mock_deploy_conn
            mock_global.pyape_conf = mock_pyape_conf
            
            # 执行测试函数
            server_deploy()
            
            # 验证方法被正确调用
            mock_deploy_conn.rsync.assert_called_once_with(exclude=mock_pyape_conf["RSYNC_EXCLUDE"])
            mock_deploy_conn.put_config.assert_called_once_with(force=True)

    def test_server_start_success(self, mocker):
        """测试 server_start 命令成功执行"""
        # Mock global_state.deploy_conn
        mock_deploy_conn = MagicMock()
        mock_deploy_conn.start = MagicMock()
        
        # Mock global_state
        with patch('fabik.cmd.global_state') as mock_global:
            mock_global.deploy_conn = mock_deploy_conn
            
            # 执行测试函数
            server_start()
            
            # 验证方法被正确调用
            mock_deploy_conn.start.assert_called_once()

    def test_server_stop_success(self, mocker):
        """测试 server_stop 命令成功执行"""
        # Mock global_state.deploy_conn
        mock_deploy_conn = MagicMock()
        mock_deploy_conn.stop = MagicMock()
        
        # Mock global_state
        with patch('fabik.cmd.global_state') as mock_global:
            mock_global.deploy_conn = mock_deploy_conn
            
            # 执行测试函数
            server_stop()
            
            # 验证方法被正确调用
            mock_deploy_conn.stop.assert_called_once()

    def test_server_reload_success(self, mocker):
        """测试 server_reload 命令成功执行"""
        # Mock global_state.deploy_conn
        mock_deploy_conn = MagicMock()
        mock_deploy_conn.reload = MagicMock()
        
        # Mock global_state
        with patch('fabik.cmd.global_state') as mock_global:
            mock_global.deploy_conn = mock_deploy_conn
            
            # 执行测试函数
            server_reload()
            
            # 验证方法被正确调用
            mock_deploy_conn.reload.assert_called_once()

    def test_server_dar_success(self, mocker):
        """测试 server_dar 命令成功执行"""
        # Mock global_state.deploy_conn
        mock_deploy_conn = MagicMock()
        mock_deploy_conn.rsync = MagicMock()
        mock_deploy_conn.put_config = MagicMock()
        mock_deploy_conn.reload = MagicMock()
        
        # Mock global_state.pyape_conf
        mock_pyape_conf = {"RSYNC_EXCLUDE": [".git", "__pycache__", ".venv"]}
        
        # Mock global_state
        with patch('fabik.cmd.global_state') as mock_global:
            mock_global.deploy_conn = mock_deploy_conn
            mock_global.pyape_conf = mock_pyape_conf
            
            # 执行测试函数
            server_dar()
            
            # 验证方法被正确调用
            mock_deploy_conn.rsync.assert_called_once_with(exclude=mock_pyape_conf["RSYNC_EXCLUDE"])
            mock_deploy_conn.put_config.assert_called_once_with(force=True)
            mock_deploy_conn.reload.assert_called_once()

    def test_server_dar_with_fabik_error(self, mocker):
        """测试 server_dar 命令处理 FabikError"""
        # Mock global_state.deploy_conn
        mock_deploy_conn = MagicMock()
        mock_deploy_conn.rsync = MagicMock(side_effect=FabikError(err_type="TestType", err_msg="Test error"))
        
        # Mock global_state.pyape_conf
        mock_pyape_conf = {"RSYNC_EXCLUDE": [".git", "__pycache__", ".venv"]}
        
        # Mock global_state
        with patch('fabik.cmd.global_state') as mock_global:
            mock_global.deploy_conn = mock_deploy_conn
            mock_global.pyape_conf = mock_pyape_conf
            
            # Mock echo_error 和 typer.Abort
            mock_echo_error = mocker.patch('fabik.cmd.echo_error')
            mock_abort = mocker.patch('fabik.cmd.typer.Abort', side_effect=SystemExit)
            
            # 执行测试函数并验证异常
            with pytest.raises(SystemExit):
                server_dar()
            
            # 验证 echo_error 被调用
            mock_echo_error.assert_called_once_with("Test error")

    def test_server_dar_with_generic_exception(self, mocker):
        """测试 server_dar 命令处理通用异常"""
        # Mock global_state.deploy_conn
        mock_deploy_conn = MagicMock()
        mock_deploy_conn.rsync = MagicMock(side_effect=Exception("Generic error"))
        
        # Mock global_state.pyape_conf
        mock_pyape_conf = {"RSYNC_EXCLUDE": [".git", "__pycache__", ".venv"]}
        
        # Mock global_state
        with patch('fabik.cmd.global_state') as mock_global:
            mock_global.deploy_conn = mock_deploy_conn
            mock_global.pyape_conf = mock_pyape_conf
            
            # Mock echo_error 和 typer.Abort
            mock_echo_error = mocker.patch('fabik.cmd.echo_error')
            mock_abort = mocker.patch('fabik.cmd.typer.Abort', side_effect=SystemExit)
            
            # 执行测试函数并验证异常
            with pytest.raises(SystemExit):
                server_dar()
            
            # 验证 echo_error 被调用
            mock_echo_error.assert_called_once_with("Generic error")