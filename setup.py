#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPA桌面软件安装脚本
"""

from setuptools import setup, find_packages
import pathlib

# 项目根目录
HERE = pathlib.Path(__file__).parent

# README文件作为长描述
README = (HERE / "README.md").read_text(encoding="utf-8")

# 项目版本
VERSION = "1.0.0"

setup(
    name="rpa-desktop",
    version=VERSION,
    description="RPA桌面自动化软件 - 影刀复刻版",
    long_description=README,
    long_description_content_type="text/markdown",
    author="RPA开发团队",
    author_email="dev@rpa-team.com",
    url="https://github.com/your-repo/rpa-desktop",
    license="MIT",
    # 项目分类
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Operating System :: Microsoft :: Windows :: Windows 11",
        "Topic :: Office/Business :: Office Suites",
        "Topic :: Software Development :: Testing",
        "Topic :: System :: System Shells",
    ],
    # 关键词
    keywords="rpa automation desktop gui selenium pyautogui workflow",
    # 包发现
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    # Python版本要求
    python_requires=">=3.10",
    # 核心依赖
    install_requires=[
        # GUI框架
        "PyQt6>=6.6.0",
        # 网页自动化
        "selenium>=4.15.2",
        "undetected-chromedriver>=3.5.4",
        "beautifulsoup4>=4.12.2",
        "requests>=2.31.0",
        # 桌面自动化
        "pyautogui>=0.9.54",
        "pygetwindow>=0.0.9",
        "pynput>=1.7.6",
        "pywin32>=306; sys_platform == 'win32'",
        # 图像处理
        "opencv-python>=4.8.1.78",
        "pytesseract>=0.3.10",
        "Pillow>=10.1.0",
        "numpy>=1.24.3",
        # 数据库
        "SQLAlchemy>=2.0.23",
        "alembic>=1.12.1",
        # 异步处理
        "aiofiles>=23.2.1",
        # 配置管理
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
        # 日志
        "structlog>=23.2.0",
        "colorama>=0.4.6",
        # 工具
        "click>=8.1.7",
        "tqdm>=4.66.1",
        "psutil>=5.9.6",
        "watchdog>=3.0.0",
    ],
    # 可选依赖
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-qt>=4.2.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "build": [
            "pyinstaller>=6.0.0",
            "cx_Freeze>=6.15.0",
        ],
    },
    # 入口点
    entry_points={
        "console_scripts": [
            "rpa-desktop=main:main",
        ],
    },
    # 包含数据文件
    include_package_data=True,
    # 数据文件
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml", "*.json"],
    },
    # 项目URL
    project_urls={
        "Bug Reports": "https://github.com/your-repo/rpa-desktop/issues",
        "Source": "https://github.com/your-repo/rpa-desktop",
        "Documentation": "https://docs.rpa-platform.com",
    },
)
