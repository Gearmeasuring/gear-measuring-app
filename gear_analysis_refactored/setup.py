#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
齿轮分析软件 - 重构版
打包配置文件
"""

from setuptools import setup, find_packages
import os

# 读取README文件作为长描述
def read_readme():
    """读取README文件内容"""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "齿轮分析软件 - 重构版"

# 读取requirements.txt文件
def read_requirements():
    """读取依赖包列表"""
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
    return []

setup(
    name="gear-analysis-refactored",
    version="2.0.0",
    author="齿轮分析团队",
    author_email="support@gearanalysis.com",
    description="专业的齿轮测量数据分析软件，支持MKA文件解析、多种图表展示和专业PDF报告生成",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/gear-analysis-refactored",
    packages=find_packages(exclude=["tests*", "test_*"]),
    include_package_data=True,
    package_data={
        '': ['*.md', '*.txt', '*.bat', '*.sh'],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "gear-analysis=gear_analysis_refactored.main:main",
        ],
        "gui_scripts": [
            "gear-analysis-gui=gear_analysis_refactored.main:main",
        ]
    },
    keywords="gear analysis mka parser pdf report",
    project_urls={
        "Bug Reports": "https://github.com/your-username/gear-analysis-refactored/issues",
        "Documentation": "https://github.com/your-username/gear-analysis-refactored/blob/main/README.md",
        "Source": "https://github.com/your-username/gear-analysis-refactored",
    },
)