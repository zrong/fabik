使用说明
========

fabik 支持 python3.13 及以上版本。


.. _install:

安装
----

使用 pip 安装 fabik：

.. code-block:: bash

    pip install fabik

或者从源代码安装：

.. code-block:: bash

    git clone https://github.com/zrong/fabik.git
    cd fabik
    pip install -e .

快速开始
--------

1. 创建项目配置文件
~~~~~~~~~~~~~~~~~~~

fabik 使用 TOML 格式的配置文件。在项目根目录创建 ``fabik.toml`` 文件：


.. code-block:: bash
   
   fabik init

如果 fabik.toml 配置文件已经存在，可以使用：

.. code-block:: bash

    fabik init --force

2. 使用命令行工具
~~~~~~~~~~~~~~~~~

fabik 提供了丰富的命令行工具：

.. code-block:: bash

    # 查看命令行能力
    fabik --help
    

（文档待补充）