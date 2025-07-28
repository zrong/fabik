"""
.. _fabik_tpl:

fabik.tpl
-------------------

Provide template support.
"""


FABIK_TOML_FILE: str = 'fabik.toml'
""" Main config file name. """


FABIK_TOML_SIMPLE_TPL: str = """
###########################################
# fabik main config file
#
# @author:  zrong(https://zengrong.net)
# @source:  https://github.com/zrong/fabik.git
# @create:  {{ create_time }}
# @version: {{ fabik_version }}
# 
###########################################
# use NAME to define your project name.
NAME = '{{ NAME }}'

# Define project source code folder, default is the absolute path of fabik command run folder.
WORK_DIR = "{{ WORK_DIR }}"

# Define template folder, default is the absolute path of fabik command run folder + '/tpls'.
TPL_DIR = "{{ WORK_DIR }}/tpls"
"""
""" This is a template for fabik main config file. """

FABIK_TOML_TPL: str = """
###########################################
# fabik main config file
#
# @author:  zrong(https://zengrong.net)
# @source:  https://github.com/zrong/fabik.git
# @create:  {{ create_time }}
# @version: {{ fabik_version }}
# 
#
# Use { { } } to include variable names, which will be replaced with specific values, two curly braces should be continuous, no content should be included, such as no spaces.
#
# NAME: project name, defined in config file
# WORK_DIR: absolute path of project source code folder
# DEPLOY_DIR: absolute path of deploy folder on server
###########################################

# use NAME to define your project name.
NAME = '{{ NAME }}'

# Define project source code folder, default is the absolute path of fabik command run folder.
WORK_DIR = "{{ WORK_DIR }}"

# Define template folder, default is the absolute path of fabik command run folder + '/tpls'.
TPL_DIR = "{{ WORK_DIR }}/tpls"

# DEPLOY_DIR is the absolute path of deploy folder on server
DEPLOY_DIR = '/srv/app/{{ NAME }}'

# Python executable name, default is 'python3', you can use a absolute path to specify a specific python executable.
PYE = 'python3'

# Allow to replace environment variables.
# The following { { } } variables will be replaced with environment variables. Two curly braces should be continuous, no content should be included, such as no spaces.
# If the value contains the following keys, it will be replaced with the value of the environment variable.
#
# For example:
# 1. The project name is 'fabik' (default value), when it is replaced with environment variable, it will be converted to uppercase.
# 2. The environment variable contains FABIK_LOCAL_ADMIN_NAME
# 3. When using --env local to generate the config file, it will replace the value of {{ ADMIN_NAME }} with the value of the environment variable FABIK_LOCAL_ADMIN_NAME
#
# ADMIN_NAME
# ADMIN_PASSWORD
# SECRET_KEY
#
# You can add environment variables yourself, as long as the variable name in the config file is the same.
REPLACE_ENVIRON = [
    'ADMIN_NAME',
    'ADMIN_PASSWORD',
]

#==============================================
# The following configuration overrides the above configuration.
# The override is performed in the form of "supplement", the same name key will be overwritten, and the different name key will be retained.
#
# ENV represents the environment, when you want to deploy to different environments, you can use these different environments
# to generate configuration files for different environments, the key name after ENV is the environment name.
#
# For example, [ENV.local.path] is used to replace the path.work_dir or path.tpl_dir to specific value in the local environment.
#==============================================
[ENV.local.PATH]
work_dir = "/Users/zrong/tool/my_new_tool"
tpl_dir = "/Users/zrong/tool/my_new_tool/tpls"

"""
""" This is a template for fabik main config file. """

SYSTEMD_USER_UNIT_SERVICE_TPL = """
[Unit]
Description={{ NAME }}
Wants=network.target network-online.target
After=network.target network-online.target

[Service]
ExecStart={{ exec }}
WorkingDirectory={{ work_dir }}
LimitNOFILE=500000
LimitNPROC=500000
Restart=always

[Install]
WantedBy=multi-user.target
"""