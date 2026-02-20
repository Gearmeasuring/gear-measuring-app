"""
================================================================================
前五个齿的合并曲线放大显示
Zoomed View of First 5 Teeth Merged Curve
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
    CurveBuilder, DataPreprocessor
)

print("="*80)
print("前五个齿的合并曲线放大显示")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

# 获取右齿形数据
profile_data = analyzer.reader.profile_data.get('right', {})
eval_range = analyzer.reader.profile_eval_range

print()
print("[右齿形前5个齿的数据]")
print("-"*80)

involute_calc = InvoluteCalculator(analyzer.gear_params)
profile_calc = ProfileAngleCalculator(analyzer.gear_params, involute_calc)
preprocessor = DataPreprocessor()

# 收集前5个齿的数据
teeth_data = []
for tooth_id in range(1, 6):
    if tooth_id in profile_data:
        tooth_profiles = profile_data[tooth_id]
        for z_pos, values in tooth_profiles.items():
            corrected_values = preprocessor.remove_crown_and_slope(values)
            num_points = len(corrected_values)
            polar_angles = profile_calc.calculate_profile_polar_angles(eval_range, num_points, 'right')
            
            tooth_index = tooth_id - 1
            tau = tooth_index * analyzer.gear_params.pitch_angle
            final_angles = tau + polar_angles
            
            teeth_data.append({
                'tooth_id': tooth_id,
                'z_pos': z_pos,
                'angles': final_angles,
                'values': corrected_values
            })
            
            print(f"齿{tooth_id} z={z_pos}: {len(values)}点, 角度范围 [{final_angles.min():.2f}°, {final_angles.max():.2f}°]")

# 绘制前5个齿的曲线
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 图1: 前5个齿的原始曲线（按齿分开）
ax1 = axes[0, 0]
colors = ['blue', 'red', 'green', 'orange', 'purple']
for i, data in enumerate(teeth_data[:5]):
    ax1.plot(data['angles'], data['values'], color=colors[i], 
             linewidth=1.0, label=f"Tooth {data['tooth_id']}")
ax1.set_xlabel('Rotation Angle (deg)')
ax1.set_ylabel('Deviation (um)')
ax1.set_title('First 5 Teeth - Individual Curves (Right Profile)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 图2: 合并后的曲线（前5个齿）
ax2 = axes[0, 1]
all_angles = []
all_values = []
for data in teeth_data:
    all_angles.extend(data['angles'].tolist())
    all_values.extend(data['values'].tolist())

all_angles = np.array(all_angles)
all_values = np.array(all_values)

# 归一化到0-360
all_angles_norm = all_angles % 360.0
all_angles_norm[all_angles_norm < 0] += 360.0

# 排序
sort_idx = np.argsort(all_angles_norm)
sorted_angles = all_angles_norm[sort_idx]
sorted_values = all_values[sort_idx]

ax2.plot(sorted_angles, sorted_values, 'b-', linewidth=0.8)
ax2.set_xlabel('Rotation Angle (deg)')
ax2.set_ylabel('Deviation (um)')
ax2.set_title('First 5 Teeth - Merged Curve')
ax2.grid(True, alpha=0.3)
ax2.set_xlim(0, 25)

# 图3: 放大显示齿1和齿2的过渡区域
ax3 = axes[1, 0]
pitch_angle = analyzer.gear_params.pitch_angle

# 齿1数据
tooth1 = teeth_data[0]
ax3.plot(tooth1['angles'], tooth1['values'], 'b-', linewidth=1.5, label='Tooth 1')

# 齿2数据
tooth2 = teeth_data[1]
ax3.plot(tooth2['angles'], tooth2['values'], 'r-', linewidth=1.5, label='Tooth 2')

ax3.axvline(x=pitch_angle, color='green', linestyle='--', label=f'Pitch Angle = {pitch_angle:.2f} deg')
ax3.set_xlabel('Rotation Angle (deg)')
ax3.set_ylabel('Deviation (um)')
ax3.set_title('Tooth 1 and Tooth 2 Transition')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 图4: 齿1的详细曲线
ax4 = axes[1, 1]
tooth1 = teeth_data[0]
ax4.plot(tooth1['angles'], tooth1['values'], 'b-o', linewidth=1.0, markersize=2)
ax4.set_xlabel('Rotation Angle (deg)')
ax4.set_ylabel('Deviation (um)')
ax4.set_title('Tooth 1 - Detailed Curve')
ax4.grid(True, alpha=0.3)

# 标注角度范围
ax4.annotate(f'Start: {tooth1["angles"].min():.2f} deg', 
             xy=(tooth1['angles'].min(), tooth1['values'].max()),
             fontsize=9)
ax4.annotate(f'End: {tooth1["angles"].max():.2f} deg', 
             xy=(tooth1['angles'].max(), tooth1['values'].min()),
             fontsize=9)

plt.tight_layout()
plt.savefig(os.path.join(current_dir, 'first_5_teeth_curves.png'), dpi=150, bbox_inches='tight')
print()
print("图表已保存: first_5_teeth_curves.png")

# 打印详细数据
print()
print("="*80)
print("前5个齿的详细数据")
print("="*80)

for data in teeth_data[:5]:
    print(f"\n齿{data['tooth_id']} (z={data['z_pos']}):")
    print(f"  点数: {len(data['values'])}")
    print(f"  角度范围: [{data['angles'].min():.4f}°, {data['angles'].max():.4f}°]")
    print(f"  角度跨度: {data['angles'].max() - data['angles'].min():.4f}°")
    print(f"  值范围: [{data['values'].min():.4f}, {data['values'].max():.4f}] um")
    print(f"  前5个角度: {data['angles'][:5]}")
    print(f"  后5个角度: {data['angles'][-5:]}")

print()
print("="*80)
print(f"节距角 = 360° / {analyzer.gear_params.teeth_count} = {pitch_angle:.4f}°")
print("="*80)
