"""
放大显示最大正弦拟合曲线
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import RippleWavinessAnalyzer

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()
analyzer.analyze_all()

# 获取左齿形结果
result = analyzer.results['profile_left']
max_comp = result.spectrum_components[0]

# 计算正弦拟合曲线
angles_rad = np.radians(result.angles)
order = max_comp.order
a = max_comp.coefficient_a
b = max_comp.coefficient_b

sine_fit = a * np.cos(order * angles_rad) + b * np.sin(order * angles_rad)

# 绘制 - 放大显示前20度
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# 图1: 全图
ax1 = axes[0]
ax1.plot(result.angles, result.values, 'b-', linewidth=0.5, alpha=0.7, label='Original')
ax1.plot(result.angles, sine_fit, 'r-', linewidth=1.5, label=f'Sine Fit (Order={order})')
ax1.set_xlabel('Rotation Angle (deg)')
ax1.set_ylabel('Deviation (um)')
ax1.set_title(f'Profile Left - Full View (Order={order}, Amp={max_comp.amplitude:.3f}um)')
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.set_xlim(0, 360)

# 图2: 放大显示前10度
ax2 = axes[1]
mask = result.angles <= 10
ax2.plot(result.angles[mask], result.values[mask], 'b-', linewidth=1.0, alpha=0.7, label='Original')
ax2.plot(result.angles[mask], sine_fit[mask], 'r-', linewidth=2.0, label=f'Sine Fit (Order={order})')
ax2.set_xlabel('Rotation Angle (deg)')
ax2.set_ylabel('Deviation (um)')
ax2.set_title(f'Profile Left - Zoomed View (0-10 deg, ~{order*10//360} cycles)')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(current_dir, 'sine_fit_zoomed.png'), dpi=150, bbox_inches='tight')
print("图表已保存: sine_fit_zoomed.png")

# 计算10度内有多少个周期
cycles_in_10deg = order * 10 / 360
print(f"\n在10度范围内约有 {cycles_in_10deg:.1f} 个周期")
print(f"每个周期约 {360/order:.2f} 度")
