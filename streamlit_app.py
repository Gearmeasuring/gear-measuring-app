"""
齿轮测量报告 Web 应用 - 入口文件
用于 Streamlit Cloud 部署
"""

import sys
import os

# 添加 web_app 目录到路径
web_app_dir = os.path.join(os.path.dirname(__file__), 'web_app')
if web_app_dir not in sys.path:
    sys.path.insert(0, web_app_dir)

# 导入主应用
from app_professional import *
