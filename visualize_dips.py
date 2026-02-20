#!/usr/bin/env python3
"""
专门用于可视化左齿形中存在下凹的齿的图形
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plot_ten_teeth import visualize_left_profile_dips

if __name__ == '__main__':
    print("=== Visualizing Left Profile Dips ===")
    output_file = visualize_left_profile_dips()
    print(f"\nVisualization completed! Results saved to: {output_file}")
