"""
================================================================================
显示左右齿形前5个齿的合并曲线
Show First 5 Teeth Merged Curves for Both Left and Right Profiles
================================================================================
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import (
    RippleWavinessAnalyzer, InvoluteCalculator, ProfileAngleCalculator,
    CurveBuilder, DataPreprocessor
)

print("="*80)
print("左右齿形前5个齿的合并曲线")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

# 创建图表
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

for side_idx, side in enumerate(['right', 'left']):
    print(f"\n{'='*80}")
    print(f"[{side.upper()} PROFILE]")
    print(f"{'='*80}")
    
    profile_data = analyzer.reader.profile_data.get(side, {})
    eval_range = analyzer.reader.profile_eval_range
    
    involute_calc = InvoluteCalculator(analyzer.gear_params)
    profile_calc = ProfileAngleCalculator(analyzer.gear_params, involute_calc)
    preprocessor