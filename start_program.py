#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Python 3.11启动齿轮波纹度软件
"""

import os
import subprocess
import sys

# 设置Python 3.11的路径
PYTHON311_PATH = r"C:\Users\Administrator\AppData\Local\Programs\Python\Python311\python.exe"
PROGRAM_NAME = "齿轮波纹度软件2_修改版_simplified.py"

def main():
    print("=" * 60)
    print("使用 Python 3.11 启动齿轮波纹度软件")
    print("=" * 60)
    print()
    
    # 检查Python 3.11是否存在
    if not os.path.exists(PYTHON311_PATH):
        print(f"错误：未找到Python 3.11！")
        print(f"查找路径: {PYTHON311_PATH}")
        input("\n按Enter键退出...")
        return
    
    print(f"✓ 找到Python 3.11: {PYTHON311_PATH}")
    print(f"✓ 程序文件: {PROGRAM_NAME}")
    print()
    
    # 运行程序
    print("正在启动程序...")
    try:
        subprocess.run([PYTHON311_PATH, PROGRAM_NAME], check=True)
    except subprocess.CalledProcessError as e:
        print(f"程序运行出错: {e}")
    except KeyboardInterrupt:
        print("程序已被中断")
    except Exception as e:
        print(f"发生错误: {e}")
    
    print()
    print("程序已退出")
    input("按Enter键继续...")

if __name__ == "__main__":
    main()
