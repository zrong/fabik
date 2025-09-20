"""
.. _fabik_conf:

fabik.conf
-------------------

提供配置文件支持
"""

import os
import jinja2
from pathlib import Path
from typing import Any, Union
import shutil

import tomllib
import tomli_w
import json
import typer
from dotenv import dotenv_values

import fabik
from fabik.error import (
    EnvError,
    echo_error,
    echo_info,
    echo_warning,
    FabikError,
    ConfigError,
    PathError,
    TplError,
)
from fabik.tpl import FABIK_TOML_FILE, FABIK_ENV_FILE


