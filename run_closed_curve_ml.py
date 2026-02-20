#!/usr/bin/env python3
"""
运行使用机器学习处理过的数据生成闭合曲线
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plot_ten_teeth import generate_closed_curve_with_ml

if __name__ == '__main__':
    print("=== Generating Closed Curve with Machine Learning ===")
    output_file = generate_closed_curve_with_ml()
    if output_file:
        print(f"\nClosed curve generation completed! Results saved to: {output_file}")
    else:
        print("\nError: Failed to generate closed curve")
