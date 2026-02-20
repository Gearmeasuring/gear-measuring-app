"""
================================================================================
前五个齿的合并曲线放大显示（版本2 - 使用实际算法）
================================================================================
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import RippleWavinessAnalyzer

print("="*80)
print("前五个齿的合并曲线放大显示（使用实际算法）")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

# 使用实际的build_rotation_curve方法
from ripple_waviness_analyzer import (
    InvoluteCalculator, ProfileAngleCalculator, DataPreprocessor
)

involute_calc = InvoluteCalculator(analyzer.gear_params)
profile_calc = ProfileAngleCalculator(analyzer.gear_params, involute_calc)

profile_eval = analyzer.reader.profile_eval_range

print()
print("[评价范围]")
print(f"  d1 (起评点) = {profile_eval.eval_start} mm")
print(f"  d2 (终评点) = {profile_eval.eval_end} mm")

# 右齿形
print()
print("="*80)
print("[右齿形前5个齿 - 使用build_rotation_curve]")
print("="*80)

profile_data_right = analyzer.reader.profile_data.get('right', {})
angles_right, values_right = profile_calc.build_rotation_curve(
    {k: v for k, v in list(profile_data_right.items())[:5]},  # 只取前5个齿
    profile_eval, 'right',
    meas_range=profile_eval
)

print(f"  总数据点数: {len(values_right)}")
print(f"  值范围: [{values_right.min():.4f}, {values_right.max():.4f}] um")

# 左齿形
print()
print("="*80)
print("[左齿形前5个齿 - 使用build_rotation_curve]")
print("="*80)

profile_data_left = analyzer.reader.profile_data.get('left', {})
angles_left, values_left = profile_calc.build_rotation_curve(
    {k: v for k, v in list(profile_data_left.items())[:5]},  # 只取前5个齿
    profile_eval, 'left',
    meas_range=profile_eval
)

print(f"  总数据点数: {len(values_left)}")
print(f"  值范围: [{values_left.min():.4f}, {values_left.max():.4f}] um")

# 绘制图表
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 图1: 右齿形所有数据
ax1 = axes[0, 0]
ax1.plot(angles_right, values_right, 'b-', linewidth=0.8)
ax1.set_xlabel('Rotation Angle (deg)')
ax1.set_ylabel('Deviation (um)')
ax1.set_title('Right Profile - First 5 Teeth (After Preprocessing)')
ax1.grid(True, alpha=0.3)

# 图2: 左齿形所有数据
ax2 = axes[0, 1]
ax2.plot(angles_left, values_left, 'r-', linewidth=0.8)
ax2.set_xlabel('Rotation Angle (deg)')
ax2.set_ylabel('Deviation (um)')
ax2.set_title('Left Profile - First 5 Teeth (After Preprocessing)')
ax2.grid(True, alpha=0.3)

# 图3: 右齿形齿1详细
ax3 = axes[1, 0]
# 筛选齿1的数据 (角度在-4.19到0之间)
tooth1_mask = (angles_right >= -4.5) & (angles_right <= 0.5)
if np.any(tooth1_mask):
    ax3.plot(angles_right[tooth1_mask], values_right[tooth1_mask], 'b-o', linewidth=1.0, markersize=2)
    ax3.set_xlabel('Rotation Angle (deg)')
    ax3.set_ylabel('Deviation (um)')
    ax3.set_title('Right Profile Tooth 1 - Detailed')
    ax3.grid(True, alpha=0.3)
    ax3.annotate(f'Range: [{values_right[tooth1_mask].min():.2f}, {values_right[tooth1_mask].max():.2f}] um', 
                 xy=(0.05, 0.95), xycoords='axes fraction', fontsize=10)

# 图4: 左齿形齿1详细
ax4 = axes[1, 1]
tooth1_mask_left = (angles_left >= -4.5) & (angles_left <= 0.5)
if np.any(tooth1_mask_left):
    ax4.plot(angles_left[tooth1_mask_left], values_left[tooth1_mask_left], 'r-o', linewidth=1.0, markersize=2)
    ax4.set_xlabel('Rotation Angle (deg)')
    ax4.set_ylabel('Deviation (um)')
    ax4.set_title('Left Profile Tooth 1 - Detailed')
    ax4.grid(True, alpha=0.3)
    ax4.annotate(f'Range: [{values_left[tooth1_mask_left].min():.2f}, {values_left[tooth1_mask_left].max():.2f}] um', 
                 xy=(0.05, 0.95), xycoords='axes fraction', fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(current_dir, 'first_5_teeth_v2.png'), dpi=150, bbox_inches='tight')
print()
print("图表已保存: first_5_teeth_v2.png")

print()
print("="*80)
print("完成")
print("="*80)
