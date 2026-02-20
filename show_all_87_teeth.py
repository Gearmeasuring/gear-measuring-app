"""
================================================================================
87个齿的左右齿形、齿向合并曲线图形
Merged Curves for All 87 Teeth - Profile and Helix
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
print("87个齿的左右齿形、齿向合并曲线图形")
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
    print(f"{name}:")
    print(f"  数据点数: {len(result.angles)}")
    print(f"  角度范围: [0, 360] deg")
    print(f"  值范围: [{result.values.min():.4f}, {result.values.max():.4f}] um")
    print(f"  高阶总振幅 W: {result.high_order_amplitude:.4f} um")
    print(f"  高阶 RMS: {result.high_order_rms:.4f} um")
    print()

# 绘制图表
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# 颜色设置
colors = {
    'profile_left': 'blue',
    'profile_right': 'red',
    'helix_left': 'green',
    'helix_right': 'orange'
}

# 图1: 左齿形
ax1 = axes[0, 0]
if 'profile_left' in results:
    result = results['profile_left']
    ax1.plot(result.angles, result.values, color=colors['profile_left'], linewidth=0.5)
    ax1.plot(result.angles, result.reconstructed_signal, color='black', linewidth=1.5, 
             label=f'High-Order Reconstructed')
    ax1.set_xlabel('Rotation Angle (deg)')
    ax1.set_ylabel('Deviation (um)')
    ax1.set_title(f'Left Profile (87 teeth)\nW={result.high_order_amplitude:.2f}um, RMS={result.high_order_rms:.2f}um')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, 360)

# 图2: 右齿形
ax2 = axes[0, 1]
if 'profile_right' in results:
    result = results['profile_right']
    ax2.plot(result.angles, result.values, color=colors['profile_right'], linewidth=0.5)
    ax2.plot(result.angles, result.reconstructed_signal, color='black', linewidth=1.5,
             label=f'High-Order Reconstructed')
    ax2.set_xlabel('Rotation Angle (deg)')
    ax2.set_ylabel('Deviation (um)')
    ax2.set_title(f'Right Profile (87 teeth)\nW={result.high_order_amplitude:.2f}um, RMS={result.high_order_rms:.2f}um')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(0, 360)

# 图3: 左齿向
ax3 = axes[1, 0]
if 'helix_left' in results:
    result = results['helix_left']
    ax3.plot(result.angles, result.values, color=colors['helix_left'], linewidth=0.5)
    ax3.plot(result.angles, result.reconstructed_signal, color='black', linewidth=1.5,
             label=f'High-Order Reconstructed')
    ax3.set_xlabel('Rotation Angle (deg)')
    ax3.set_ylabel('Deviation (um)')
    ax3.set_title(f'Left Helix (87 teeth)\nW={result.high_order_amplitude:.2f}um, RMS={result.high_order_rms:.2f}um')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(0, 360)

# 图4: 右齿向
ax4 = axes[1, 1]
if 'helix_right' in results:
    result = results['helix_right']
    ax4.plot(result.angles, result.values, color=colors['helix_right'], linewidth=0.5)
    ax4.plot(result.angles, result.reconstructed_signal, color='black', linewidth=1.5,
             label=f'High-Order Reconstructed')
    ax4.set_xlabel('Rotation Angle (deg)')
    ax4.set_ylabel('Deviation (um)')
    ax4.set_title(f'Right Helix (87 teeth)\nW={result.high_order_amplitude:.2f}um, RMS={result.high_order_rms:.2f}um')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(0, 360)

plt.tight_layout()
plt.savefig(os.path.join(current_dir, 'all_87_teeth_curves.png'), dpi=150, bbox_inches='tight')
print("图表已保存: all_87_teeth_curves.png")

# 绘制频谱图
fig2, axes2 = plt.subplots(2, 2, figsize=(16, 10))

ze = analyzer.gear_params.teeth_count

for idx, (name, result) in enumerate(results.items()):
    row = idx // 2
    col = idx % 2
    ax = axes2[row, col]
    
    orders = [c.order for c in result.spectrum_components]
    amplitudes = [c.amplitude for c in result.spectrum_components]
    
    colors_bar = ['red' if o >= ze else 'blue' for o in orders]
    ax.bar(range(len(orders)), amplitudes, color=colors_bar, alpha=0.7)
    ax.axvline(x=ze - 0.5, color='green', linestyle='--', label=f'ZE={ze}')
    ax.set_xlabel('Order Rank')
    ax.set_ylabel('Amplitude (um)')
    ax.set_title(f'{name} - Spectrum')
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(current_dir, 'all_87_teeth_spectrum.png'), dpi=150, bbox_inches='tight')
print("频谱图已保存: all_87_teeth_spectrum.png")

print()
print("="*80)
print("完成")
print("="*80)
