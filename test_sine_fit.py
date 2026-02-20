"""
测试最大正弦拟合曲线
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

print(f"最大阶次: {max_comp.order}")
print(f"振幅: {max_comp.amplitude:.4f} um")
print(f"系数a: {max_comp.coefficient_a:.4f}")
print(f"系数b: {max_comp.coefficient_b:.4f}")

# 计算正弦拟合曲线
angles_rad = np.radians(result.angles)
order = max_comp.order
a = max_comp.coefficient_a
b = max_comp.coefficient_b

sine_fit = a * np.cos(order * angles_rad) + b * np.sin(order * angles_rad)

print(f"\n正弦拟合曲线范围: [{sine_fit.min():.4f}, {sine_fit.max():.4f}] um")

# 绘制
fig, ax = plt.subplots(figsize=(12, 6))

# 原始曲线
ax.plot(result.angles, result.values, 'b-', linewidth=0.5, alpha=0.7, label='Original')

# 正弦拟合曲线
ax.plot(result.angles, sine_fit, 'r-', linewidth=2.0, label=f'Sine Fit (Order={order})')

ax.set_xlabel('Rotation Angle (deg)')
ax.set_ylabel('Deviation (um)')
ax.set_title(f'Profile Left - Max Sine Fit (Order={order}, Amp={max_comp.amplitude:.3f}um)')
ax.legend()
ax.grid(True, alpha=0.3)
ax.set_xlim(0, 360)

plt.tight_layout()
plt.savefig(os.path.join(current_dir, 'test_sine_fit.png'), dpi=150, bbox_inches='tight')
print("\n图表已保存: test_sine_fit.png")
