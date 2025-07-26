# FABIK 文档

本目录包含 FABIK 项目的完整文档。

## 构建文档

### 安装依赖

```bash
# 安装文档构建依赖
pip install -e .[doc]
```

### 构建 HTML 文档

```bash
cd docs
make html
```

构建完成后，文档将生成在 `_build/html/` 目录中。

### 启动文档服务器

```bash
cd docs
make serve
```

这将在 http://localhost:8000 启动一个本地服务器来预览文档。

### 实时预览

如果安装了 `sphinx-autobuild`，可以使用实时预览功能：

```bash
pip install sphinx-autobuild
cd docs
make livehtml
```

## 文档结构

- `index.rst` - 主页和目录
- `usage.rst` - 使用说明
- `configuration.rst` - 配置管理
- `command.rst` - 命令行工具
- `development.rst` - 开发指南
- `reference.rst` - API 参考
- `conf.py` - Sphinx 配置文件

## ReadTheDocs 部署

项目配置了自动部署到 ReadTheDocs.org：

1. 推送代码到 GitHub
2. ReadTheDocs 会自动检测到更改
3. 自动构建和部署文档

配置文件：`.readthedocs.yaml`

## GitHub Actions

项目配置了 GitHub Actions 来自动测试文档构建：

- 每次推送到主分支时自动构建文档
- 检查文档链接的有效性
- 上传构建的文档作为 artifacts

配置文件：`.github/workflows/docs.yml`