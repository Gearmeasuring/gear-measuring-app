#!/usr/bin/env python3
"""
专门用于精准检测左齿形中存在下凹的前5个齿
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plot_ten_teeth import detect_top_5_dips

if __name__ == '__main__':
    print("=== Detecting Top 5 Left Profile Dips ===")
    top_5_teeth, output_file = detect_top_5_dips()
    print(f"\nDetection completed! Results saved to: {output_file}")
