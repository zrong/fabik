"""
Pytest configuration file for fabik tests
"""

import os
import sys
import pytest
from pathlib import Path
from typing import Any, Dict

# 确保 fabik 包可以被导入
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import fabik
from fabik.cmd import GlobalState, FabikConfig


@pytest.fixture
def temp_dir(tmp_path) -> Path:
    """提供一个临时目录用于测试"""
    return tmp_path


@pytest.fixture
def mock_fabik_config(mocker) -> Any:
    """Mock FabikConfig 类"""
    return mocker.patch('fabik.cmd.FabikConfig')


@pytest.fixture
def global_state() -> GlobalState:
    """创建一个干净的 GlobalState 实例用于测试"""
    return GlobalState()


@pytest.fixture
def mock_echo_functions(mocker) -> Dict[str, Any]:
    """Mock echo 函数"""
    mocks = {
        'echo_info': mocker.patch('fabik.error.echo_info'),
        'echo_warning': mocker.patch('fabik.error.echo_warning'),
        'echo_error': mocker.patch('fabik.error.echo_error')
    }
    return mocks 