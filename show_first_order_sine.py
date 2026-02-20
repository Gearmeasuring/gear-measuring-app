"""
================================================================================
所有齿的合并曲线和第一阶正弦曲线
All Teeth Merged Curves with First Order Sine
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
print("所有齿的合并曲线和第一阶正弦曲线")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

# 分析所有方向
analyzer.analyze_all()

# 获取结果
results = analyzer.results

# 计算第一阶正弦曲线
def calculate_first_order_sine(angles, values):
    """计算第一阶正弦曲线"""
    angles_rad = np.radians(angles)
    values_centered = values - np.mean(values)
    
    # 拟合第一阶正弦
    cos_term = np.cos(1 * angles_rad)
    sin_term = np.sin(1 * angles_rad)
    
    A = np.column_stack([cos_term, sin_term])
    coeffs, _, _, _ = np.linalg.lstsq(A, values_centered, rcond=None)
    
    a, b = coeffs[0], coeffs[1]
    amplitude = np.sqrt(a**2 + b**2)
    phase = np.arctan2(a, b)
    
    # 计算拟合曲线
    sine_fit = a * np.cos(angles_rad) + b * np.sin(angles_rad)
    
    return sine_fit, amplitude, phase

print()
print("[数据统计]")
print("-"*80)

for name, result in results.items():
    sine_fit, amp, phase = calculate_first_order_sine(result.angles, result.values)
    print(f"{name}:")
    print(f"  数据点数: {len(result.angles)}")
    print(f"  值范围: [{result.values.min():.4f}, {result.values.max():.4f}] um")
    print(f"  第一阶振幅: {amp:.4f} um, 相位: {np.degrees(phase):.1f} deg")
    print()

# 绘制图表
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

colors = {
    'profile_left': 'blue',
    'profile_right': 'red',
    'helix_left': 'green',
    'helix_right': 'orange'
}

for idx, (name, result) in enumerate(results.items()):
    row = idx // 2
    col = idx % 2
    ax = axes[row, col]
    
    # 绘制原始曲线
    ax.plot(result.angles, result.values, color=colors[name], linewidth=0.5, 
            alpha=0.7, label='Original Curve')
    
    # 计算第一阶正弦曲线
    sine_fit, amp, phase = calculate_first_order_sine(result.angles, result.values)
    
    # 绘制第一阶正弦曲线
    ax.plot(result.angles, sine_fit, 'k-', linewidth=2.0, 
            label=f'Order=1 Sine (Amp={amp:.3f}um)')
    
    ax.set_xlabel('Rotation Angle (deg)')
    ax.set_ylabel('Deviation (um)')
    ax.set_title(f'{name}\nFirst Order Amplitude={amp:.3f}um')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 360)

plt.tight_layout()
plt.savefig(os.path.join(current_dir, 'all_curves_with_first_order_sine.png'), dpi=150, bbox_inches='tight')
print("图表已保存: all_curves_with_first_order_sine.png")

print()
print("="*80)
print("完成")
print("="*80)
