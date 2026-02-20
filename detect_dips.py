#!/usr/bin/env python3
"""
专门用于检测左齿形中存在下凹的齿
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plot_ten_teeth import detect_left_profile_dips

if __name__ == '__main__':
    print("=== Detecting Left Profile Dips ===")
    result = detect_left_profile_dips()
    print("\nDetection completed!")
