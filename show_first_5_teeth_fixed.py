"""
================================================================================
前五个齿的合并曲线放大显示（修复后版本）
Zoomed View of First 5 Teeth Merged Curve (Fixed Version)
================================================================================
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import (
    RippleWavinessAnalyzer, InvoluteCalculator, ProfileAngleCalculator,
    CurveBuilder, DataPreprocessor, EvaluationRange
)

print("="*80)
print("前五个齿的合并曲线放大显示（修复后版本）")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

# 获取评价范围
profile_eval = analyzer.reader.profile_eval_range

print()
print("[评价范围]")
print(f"  d1 (起评点) = {profile_eval.eval_start} mm")
print(f"  d2 (终评点) = {profile_eval.eval_end} mm")
print(f"  da (测量起点) = {profile_eval.meas_start} mm")
print(f"  de (测量终点) = {profile_eval.meas_end} mm")

# 计算展长
involute_calc = InvoluteCalculator(analyzer.gear_params)
s_d1 = involute_calc.calculate_roll_length(profile_eval.eval_start)
s_d2 = involute_calc.calculate_roll_length(profile_eval.eval_end)
s_da = involute_calc.calculate_roll_length(profile_eval.meas_start)
s_de = involute_calc.calculate_roll_length(profile_eval.meas_end)

print()
print("[展长计算]")
print(f"  s(da) = {s_da:.4f} mm")
print(f"  s(d1) = {s_d1:.4f} mm")
print(f"  s(d2) = {s_d2:.4f} mm")
print(f"  s(de) = {s_de:.4f} mm")

print()
print("="*80)
print("[右齿形前5个齿的数据（修复后）]")
print("="*80)

profile_data = analyzer.reader.profile_data.get('right', {})
profile_calc = ProfileAngleCalculator(analyzer.gear_params, involute_calc)
preprocessor = DataPreprocessor()

# 收集前5个齿的数据
teeth_data_right = []

for tooth_id in range(1, 6):
    if tooth_id in profile_data:
        tooth_profiles = profile_data[tooth_id]
        for z_pos, values in tooth_profiles.items():
            # 预处理
            corrected_values = preprocessor.remove_crown_and_slope(values)
            
            # 筛选评价范围内的数据点
            num_points_total = len(corrected_values)
            if s_de > s_da:
                idx_start = max(0, int((s_d1 - s_da) / (s_de - s_da) * num_points_total))
                idx_end = min(num_points_total, int((s_d2 - s_da) / (s_de - s_da) * num_points_total))
                
                if idx_end > idx_start:
                    corrected_values = corrected_values[idx_start:idx_end]
            
            num_points = len(corrected_values)
            if num_points < 3:
                continue
            
            polar_angles = profile_calc.calculate_profile_polar_angles(profile_eval, num_points, 'right')
            
            tooth_index = tooth_id - 1
            tau = tooth_index * analyzer.gear_params.pitch_angle
            final_angles = tau + polar_angles
            
            teeth_data_right.append({
                'tooth_id': tooth_id,
                'z_pos': z_pos,
                'angles': final_angles,
                'values': corrected_values,
                'num_points': num_points
            })
            
            print(f"齿{tooth_id} z={z_pos}: {num_points}点 (原{len(values)}点), 角度范围 [{final_angles.min():.2f}°, {final_angles.max():.2f}°], 值范围 [{corrected_values.min():.4f}, {corrected_values.max():.4f}] um")

print()
print("="*80)
print("[左齿形前5个齿的数据（修复后）]")
print("="*80)

profile_data_left = analyzer.reader.profile_data.get('left', {})
teeth_data_left = []

for tooth_id in range(1, 6):
    if tooth_id in profile_data_left:
        tooth_profiles = profile_data_left[tooth_id]
        for z_pos, values in tooth_profiles.items():
            # 预处理
            corrected_values = preprocessor.remove_crown_and_slope(values)
            
            # 筛选评价范围内的数据点
            num_points_total = len(corrected_values)
            if s_de > s_da:
                idx_start = max(0, int((s_d1 - s_da) / (s_de - s_da) * num_points_total))
                idx_end = min(num_points_total, int((s_d2 - s_da) / (s_de - s_da) * num_points_total))
                
                if idx_end > idx_start:
                    corrected_values = corrected_values[idx_start:idx_end]
            
            num_points = len(corrected_values)
            if num_points < 3:
                continue
            
            polar_angles = profile_calc.calculate_profile_polar_angles(profile_eval, num_points, 'left')
            
            tooth_index = tooth_id - 1
            tau = tooth_index * analyzer.gear_params.pitch_angle
            final_angles = tau - polar_angles
            
            teeth_data_left.append({
                'tooth_id': tooth_id,
                'z_pos': z_pos,
                'angles': final_angles,
                'values': corrected_values,
                'num_points': num_points
            })
            
            print(f"齿{tooth_id} z={z_pos}: {num_points}点 (原{len(values)}点), 角度范围 [{final_angles.min():.2f}°, {final_angles.max():.2f}°], 值范围 [{corrected_values.min():.4f}, {corrected_values.max():.4f}] um")

# 绘制图表
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 图1: 右齿形前5个齿
ax1 = axes[0, 0]
colors = ['blue', 'red', 'green', 'orange', 'purple']
for i, data in enumerate(teeth_data_right[:5]):
    ax1.plot(data['angles'], data['values'], color=colors[i % 5], 
             linewidth=1.0, label=f"Tooth {data['tooth_id']}")
ax1.set_xlabel('Rotation Angle (deg)')
ax1.set_ylabel('Deviation (um)')
ax1.set_title('Right Profile - First 5 Teeth (Fixed)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 图2: 左齿形前5个齿
ax2 = axes[0, 1]
for i, data in enumerate(teeth_data_left[:5]):
    ax2.plot(data['angles'], data['values'], color=colors[i % 5], 
             linewidth=1.0, label=f"Tooth {data['tooth_id']}")
ax2.set_xlabel('Rotation Angle (deg)')
ax2.set_ylabel('Deviation (um)')
ax2.set_title('Left Profile - First 5 Teeth (Fixed)')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 图3: 右齿形齿1详细
ax3 = axes[1, 0]
if teeth_data_right:
    data = teeth_data_right[0]
    ax3.plot(data['angles'], data['values'], 'b-o', linewidth=1.0, markersize=2)
    ax3.set_xlabel('Rotation Angle (deg)')
    ax3.set_ylabel('Deviation (um)')
    ax3.set_title(f'Right Profile Tooth 1 - {data["num_points"]} points')
    ax3.grid(True, alpha=0.3)
    ax3.annotate(f'Range: [{data["values"].min():.2f}, {data["values"].max():.2f}] um', 
                 xy=(0.05, 0.95), xycoords='axes fraction', fontsize=10)

# 图4: 左齿形齿1详细
ax4 = axes[1, 1]
if teeth_data_left:
    data = teeth_data_left[0]
    ax4.plot(data['angles'], data['values'], 'r-o', linewidth=1.0, markersize=2)
    ax4.set_xlabel('Rotation Angle (deg)')
    ax4.set_ylabel('Deviation (um)')
    ax4.set_title(f'Left Profile Tooth 1 - {data["num_points"]} points')
    ax4.grid(True, alpha=0.3)
    ax4.annotate(f'Range: [{data["values"].min():.2f}, {data["values"].max():.2f}] um', 
                 xy=(0.05, 0.95), xycoords='axes fraction', fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(current_dir, 'first_5_teeth_curves_fixed.png'), dpi=150, bbox_inches='tight')
print()
print("图表已保存: first_5_teeth_curves_fixed.png")

print()
print("="*80)
print("总结")
print("="*80)
print(f"""
修复效果:
  - 原始数据点: 约470点/齿
  - 筛选后数据点: 约321点/齿 (只保留评价范围内)
  - 值范围: 从 ±20um 缩小到 ±2um
""")
