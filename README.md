fabik /ˈfæbɪk/ = Fabric + Click

It is a foundation package for Python command-line projects, encapsulating common functionalities for command-line projects, as detailed below:

- Uses a TOML configuration file to solve configuration management issues.
- Multi-environment configuration, default value replacement, environment variable reading, and path management.
- Configuration template support.
- Multi-development environment support.
- Remote project deployment using Fabric.

fabik uses libraries including Fabric/Click/Jinja2/cryptography/python-dotenv/httpx/itdangerous, etc.

The idea for fabik comes from my previously created [pyape](https://pypi.org/project/pyape/#description) project. pyape is a Python web server development framework that includes numerous functionalities for deployment, configuration file processing, and command-line management. I've separated these features to create fabik, making it easier for more projects to directly reference them.

For more information about the fabik project, read the documentation: <https://pyape.rtfd.io/>.
