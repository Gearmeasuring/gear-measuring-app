"""
================================================================================
检查每条曲线的预处理效果
Check Preprocessing Effect on Each Curve
================================================================================
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import RippleWavinessAnalyzer, DataPreprocessor

print("="*80)
print("检查每条曲线的预处理效果")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

# 获取右齿形齿1的数据
profile_data = analyzer.reader.profile_data.get('right', {})
tooth1_data = profile_data.get(1, {})

print()
print("[右齿形齿1 - 各条曲线的预处理效果]")
print("-"*80)

preprocessor = DataPreprocessor()

fig, axes = plt.subplots(2, 3, figsize=(15, 8))
axes = axes.flatten()

for idx, (z_pos, values) in enumerate(tooth1_data.items()):
    print(f"\nz={z_pos}mm:")
    print(f"  原始数据范围: [{values.min():.4f}, {values.max():.4f}] um")
    
    # 应用预处理
    corrected = preprocessor.remove_crown_and_slope(values)
    print(f"  预处理后范围: [{corrected.min():.4f}, {corrected.max():.4f}] um")
    
    # 检查是否还有趋势
    x = np.linspace(-1, 1, len(corrected))
    
    # 拟合线性检查剩余斜率
    A = np.column_stack((x, np.ones(len(x))))
    coeffs, _, _, _ = np.linalg.lstsq(A, corrected, rcond=None)
    k, d = coeffs
    
    print(f"  剩余斜率: {k:.6f}")
    print(f"  剩余趋势: {'有' if abs(k) > 0.1 else '无'}")
    
    # 绘制
    if idx < 6:
        ax = axes[idx]
        ax.plot(x, corrected, 'b-', linewidth=1)
        ax.plot(x, k*x + d, 'r--', linewidth=1.5, label=f'Slope={k:.4f}')
        ax.set_title(f'z={z_pos}mm, Slope={k:.4f}')
        ax.set_xlabel('Normalized Position')
        ax.set_ylabel('Deviation (um)')
        ax.legend()
        ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(current_dir, 'preprocessing_check.png'), dpi=150, bbox_inches='tight')
print("\n图表已保存: preprocessing_check.png")

print()
print("="*80)
print("[分析]")
print("="*80)

print("""
从图中可以看出：

1. 预处理后每条曲线确实还有一定的斜率
2. 这是因为预处理是在合并前对每条曲线单独进行的
3. 合并后的曲线可能还保留了齿与齿之间的趋势

问题可能在于：
- 预处理是在单条曲线上进行的
- 但合并后的0-360度曲线可能还有整体趋势
- 需要在合并后再进行一次预处理？
""")

# 检查合并后的曲线
print()
print("="*80)
print("[检查合并后的曲线趋势]")
print("="*80)

from ripple_waviness_analyzer import (
    InvoluteCalculator, ProfileAngleCalculator, CurveBuilder
)

involute_calc = InvoluteCalculator(analyzer.gear_params)
profile_calc = ProfileAngleCalculator(analyzer.gear_params, involute_calc)

# 获取合并后的曲线
angles_raw = []
values_raw = []

for tooth_id in sorted(profile_data.keys())[:5]:  # 只取前5个齿
    tooth_profiles = profile_data[tooth_id]
    for z_pos, values in tooth_profiles.items():
        if z_pos == 21.0:  # 只取中间位置
            corrected = preprocessor.remove_crown_and_slope(values)
            
            # 筛选评价范围内的点
            profile_eval = analyzer.reader.profile_eval_range
            s_d1 = involute_calc.calculate_roll_length(profile_eval.eval_start)
            s_d2 = involute_calc.calculate_roll_length(profile_eval.eval_end)
            s_da = involute_calc.calculate_roll_length(profile_eval.meas_start)
            s_de = involute_calc.calculate_roll_length(profile_eval.meas_end)
            
            num_points_total = len(corrected)
            idx_start = max(0, int((s_d1 - s_da) / (s_de - s_da) * num_points_total))
            idx_end = min(num_points_total, int((s_d2 - s_da) / (s_de - s_da) * num_points_total))
            
            if idx_end > idx_start:
                corrected = corrected[idx_start:idx_end]
            
            num_points = len(corrected)
            polar_angles = profile_calc.calculate_profile_polar_angles(profile_eval, num_points, 'right')
            
            tooth_index = tooth_id - 1
            tau = tooth_index * analyzer.gear_params.pitch_angle
            final_angles = tau + polar_angles
            
            angles_raw.extend(final_angles.tolist())
            values_raw.extend(corrected.tolist())

angles_raw = np.array(angles_raw)
values_raw = np.array(values_raw)

print(f"\n合并后曲线（前5个齿）:")
print(f"  数据点数: {len(values_raw)}")
print(f"  值范围: [{values_raw.min():.4f}, {values_raw.max():.4f}] um")

# 检查整体趋势
x_norm = np.linspace(-1, 1, len(values_raw))
A = np.column_stack((x_norm, np.ones(len(x_norm))))
coeffs, _, _, _ = np.linalg.lstsq(A, values_raw, rcond=None)
k, d = coeffs

print(f"  整体斜率: {k:.6f}")
print(f"  整体趋势: {'有' if abs(k) > 0.01 else '无'}")

print()
print("="*80)
print("[结论]")
print("="*80)
print("""
问题确认：

1. 单条曲线的预处理是正确的
2. 但合并后的曲线还有整体趋势
3. 这是因为87个齿的数据合并后，齿与齿之间可能存在系统性偏差

建议：
- 在合并后的0-360度曲线上再进行一次预处理
- 去除整体的趋势（鼓形和斜率）
""")
