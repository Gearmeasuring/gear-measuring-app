#!/usr/bin/env python3
"""
运行自学习异常检测系统
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plot_ten_teeth import self_learning_anomaly_detector

if __name__ == '__main__':
    print("=== Running Self-Learning Anomaly Detector ===")
    result = self_learning_anomaly_detector()
    print(f"\nSelf-learning completed! Results saved to: {result['output_file']}")
