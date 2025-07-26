#!/usr/bin/env python3
"""
验证 fabik 文档构建脚本
"""

import os
import sys
from pathlib import Path

def check_docs_structure():
    """检查文档结构是否完整"""
    docs_dir = Path("docs")
    build_dir = docs_dir / "_build" / "html"
    
    # 检查源文件
    required_files = [
        "index.rst",
        "usage.rst", 
        "configuration.rst",
        "command.rst",
        "development.rst",
        "reference.rst",
        "conf.py",
        "Makefile",
        "make.bat"
    ]
    
    print("检查文档源文件...")
    missing_files = []
    for file in required_files:
        file_path = docs_dir / file
        if file_path.exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n缺少文件: {missing_files}")
        return False
    
    # 检查构建结果
    if build_dir.exists():
        html_files = list(build_dir.glob("*.html"))
        print(f"\n构建的 HTML 文件数量: {len(html_files)}")
        for html_file in html_files:
            print(f"  - {html_file.name}")
        
        # 检查关键文件
        key_html_files = ["index.html", "usage.html", "configuration.html"]
        for html_file in key_html_files:
            if (build_dir / html_file).exists():
                print(f"✓ {html_file}")
            else:
                print(f"✗ {html_file}")
    else:
        print("\n⚠️  HTML 构建目录不存在，请运行: cd docs && make html")
        return False
    
    return True

def check_config_files():
    """检查配置文件"""
    config_files = [
        ".readthedocs.yaml",
        ".github/workflows/docs.yml",
        "pyproject.toml"
    ]
    
    print("\n检查配置文件...")
    for file in config_files:
        if Path(file).exists():
            print(f"✓ {file}")
        else:
            print(f"✗ {file}")

def main():
    print("FABIK 文档验证")
    print("=" * 50)
    
    # 检查当前目录
    if not Path("pyproject.toml").exists():
        print("错误: 请在项目根目录运行此脚本")
        sys.exit(1)
    
    success = check_docs_structure()
    check_config_files()
    
    print("\n" + "=" * 50)
    if success:
        print("✓ 文档结构验证通过!")
        print("\n下一步:")
        print("1. 运行 'cd docs && make html' 构建文档")
        print("2. 运行 'cd docs && make serve' 预览文档")
        print("3. 推送到 GitHub 自动部署到 ReadTheDocs")
    else:
        print("✗ 文档结构验证失败，请检查缺少的文件")
        sys.exit(1)

if __name__ == "__main__":
    main()