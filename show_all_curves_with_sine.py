"""
================================================================================
所有齿的合并曲线和最大正弦拟合曲线
All Teeth Merged Curves with Maximum Sine Fit
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
print("所有齿的合并曲线和最大正弦拟合曲线")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

# 分析所有方向
analyzer.analyze_all()

# 获取结果
results = analyzer.results

print()
print("[数据统计]")
print("-"*80)

for name, result in results.items():
    max_comp = result.spectrum_components[0]
    print(f"{name}:")
    print(f"  数据点数: {len(result.angles)}")
    print(f"  值范围: [{result.values.min():.4f}, {result.values.max():.4f}] um")
    print(f"  最大阶次: {max_comp.order}, 振幅: {max_comp.amplitude:.4f} um")
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
    
    # 获取最大正弦分量
    max_comp = result.spectrum_components[0]
    order = max_comp.order
    amplitude = max_comp.amplitude
    phase = max_comp.phase
    a = max_comp.coefficient_a
    b = max_comp.coefficient_b
    
    # 计算最大正弦拟合曲线
    angles_rad = np.radians(result.angles)
    sine_fit = a * np.cos(order * angles_rad) + b * np.sin(order * angles_rad)
    
    # 绘制最大正弦拟合曲线
    ax.plot(result.angles, sine_fit, 'k-', linewidth=2.0, 
            label=f'Sine Fit (Order={order}, Amp={amplitude:.3f}um)')
    
    ax.set_xlabel('Rotation Angle (deg)')
    ax.set_ylabel('Deviation (um)')
    ax.set_title(f'{name}\nMax Order={order}, Amplitude={amplitude:.3f}um')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 360)

plt.tight_layout()
plt.savefig(os.path.join(current_dir, 'all_curves_with_sine_fit.png'), dpi=150, bbox_inches='tight')
print("图表已保存: all_curves_with_sine_fit.png")

# 绘制第二张图：高阶重构信号
fig2, axes2 = plt.subplots(2, 2, figsize=(16, 12))

for idx, (name, result) in enumerate(results.items()):
    row = idx // 2
    col = idx % 2
    ax = axes2[row, col]
    
    # 绘制原始曲线
    ax.plot(result.angles, result.values, color=colors[name], linewidth=0.5, 
            alpha=0.5, label='Original Curve')
    
    # 绘制高阶重构信号
    ax.plot(result.angles, result.reconstructed_signal, 'k-', linewidth=1.5, 
            label=f'High-Order Reconstructed (W={result.high_order_amplitude:.3f}um)')
    
    ax.set_xlabel('Rotation Angle (deg)')
    ax.set_ylabel('Deviation (um)')
    ax.set_title(f'{name}\nHigh-Order W={result.high_order_amplitude:.3f}um, RMS={result.high_order_rms:.3f}um')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 360)

plt.tight_layout()
plt.savefig(os.path.join(current_dir, 'all_curves_with_reconstructed.png'), dpi=150, bbox_inches='tight')
print("图表已保存: all_curves_with_reconstructed.png")

print()
print("="*80)
print("完成")
print("="*80)
