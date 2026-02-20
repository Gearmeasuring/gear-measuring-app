"""
================================================================================
检查鼓形去除效果
Check Crown Removal Effect
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
print("检查鼓形去除效果")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

# 获取一条测试数据
profile_data = analyzer.reader.profile_data.get('right', {})
tooth1_data = profile_data.get(1, {})
values = list(tooth1_data.values())[0]

print(f"\n原始数据点数: {len(values)}")
print(f"原始值范围: [{values.min():.4f}, {values.max():.4f}] um")

# 应用当前的预处理方法
preprocessor = DataPreprocessor()
corrected = preprocessor.remove_crown_and_slope(values)

print(f"\n预处理后值范围: [{corrected.min():.4f}, {corrected.max():.4f}] um")

# 检查是否还有鼓形（二次趋势）
x = np.linspace(-1, 1, len(corrected))

# 拟合二次多项式检查剩余鼓形
A_quad = np.column_stack((x**2, x, np.ones(len(x))))
coeffs_quad, _, _, _ = np.linalg.lstsq(A_quad, corrected, rcond=None)
a, b, c = coeffs_quad

print(f"\n剩余二次拟合: y = {a:.6f}x² + {b:.6f}x + {c:.6f}")
print(f"二次系数 a = {a:.6f} (越小越好)")

# 绘制对比图
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# 原始数据
ax1 = axes[0]
ax1.plot(x, values, 'b-', linewidth=1)
ax1.set_title('Original Data')
ax1.set_xlabel('Normalized Position')
ax1.set_ylabel('Deviation (um)')
ax1.grid(True, alpha=0.3)

# 预处理后
ax2 = axes[1]
ax2.plot(x, corrected, 'g-', linewidth=1)
# 绘制拟合的二次曲线
quad_fit = a * x**2 + b * x + c
ax2.plot(x, quad_fit, 'r--', linewidth=1.5, label=f'Quad fit: a={a:.4f}')
ax2.set_title('After Preprocessing')
ax2.set_xlabel('Normalized Position')
ax2.set_ylabel('Deviation (um)')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 去除二次趋势后再检查
if abs(a) > 0.01:
    print("\n检测到明显的剩余鼓形，进行二次去除...")
    corrected2 = corrected - (a * x**2 + b * x + c - np.mean(corrected))
    print(f"二次去除后值范围: [{corrected2.min():.4f}, {corrected2.max():.4f}] um")
    
    # 再次检查
    coeffs_quad2, _, _, _ = np.linalg.lstsq(A_quad, corrected2, rcond=None)
    a2, b2, c2 = coeffs_quad2
    print(f"二次去除后拟合: y = {a2:.6f}x² + {b2:.6f}x + {c2:.6f}")
    
    ax3 = axes[2]
    ax3.plot(x, corrected2, 'm-', linewidth=1)
    ax3.set_title('After Second Crown Removal')
    ax3.set_xlabel('Normalized Position')
    ax3.set_ylabel('Deviation (um)')
    ax3.grid(True, alpha=0.3)
else:
    ax3 = axes[2]
    ax3.text(0.5, 0.5, 'No significant crown\nremaining', 
             ha='center', va='center', transform=ax3.transAxes, fontsize=14)
    ax3.set_title('Crown Check')

plt.tight_layout()
plt.savefig(os.path.join(current_dir, 'crown_removal_check.png'), dpi=150, bbox_inches='tight')
print("\n图表已保存: crown_removal_check.png")

print()
print("="*80)
print("结论")
print("="*80)
if abs(a) > 0.01:
    print(f"检测到明显的剩余鼓形 (a={a:.4f})，建议加强鼓形去除")
else:
    print(f"鼓形去除效果良好 (a={a:.4f})")
