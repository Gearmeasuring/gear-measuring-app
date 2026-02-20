"""
详细分析图片中的公式

图片中的关键信息:
1. Δφ = 2 * Δz * tan(β₀) / D₀
2. φ = -ξ₁ - Δφ = -ξ₂ - Δφ + τ

对于齿向:
- ξ = 0 (没有滚动角)
- 所以 φ = -Δφ + τ

问题:
1. Δz 的定义是什么？是从齿的哪一端开始？
2. Δφ 的符号如何确定？
3. 左右齿向的区别是什么？

从图片右侧的示意图:
- tooth 1 和 tooth 2 之间有一个角度 τ (节距角)
- φ 是从 tooth 1 到测量位置的角度
- ξ₁ 是 tooth 1 的滚动角
- 对于齿向，ξ₁ = 0

所以: φ = -Δφ + τ

这意味着:
- 当 Δφ = 0 时, φ = τ (在节距角位置)
- 当 Δφ 增大时, φ 减小
- 这对应于左齿向（向左倾斜）

对于右齿向:
- 螺旋方向相反
- 所以 φ = +Δφ + τ
"""

import numpy as np

# 齿轮参数
module = 1.859
teeth_count = 87
helix_angle = 25.3
pitch_diameter = module * teeth_count
pitch_angle = 360.0 / teeth_count

# 评价范围
start_eval = 2.1
end_eval = 39.9
delta_L = end_eval - start_eval

print("=" * 70)
print("根据图片公式重新分析齿向计算")
print("=" * 70)

print(f"\n齿轮参数:")
print(f"  节距角 τ = 360° / {teeth_count} = {pitch_angle:.2f}°")

# 计算Δφ
delta_phi_max = np.degrees(2 * delta_L * np.tan(np.radians(helix_angle)) / pitch_diameter)
print(f"\n轴向旋转:")
print(f"  Δφ_max = 2 × {delta_L} × tan({helix_angle}°) / {pitch_diameter:.3f}")
print(f"  Δφ_max = {delta_phi_max:.2f}°")

print(f"\n" + "=" * 70)
print("左齿向计算 (螺旋向左倾斜)")
print("=" * 70)
print("公式: φ = τ - Δφ")
print("说明: 随着轴向移动，旋转角度减小")

for i, tooth_idx in enumerate([1, 2, 3]):
    tau = tooth_idx * pitch_angle
    # 起评点: Δz = 0, Δφ = 0
    phi_start = tau - 0
    # 终评点: Δz = delta_L, Δφ = delta_phi_max
    phi_end = tau - delta_phi_max
    
    print(f"\n  齿{tooth_idx+1} (τ = {tau:.2f}°):")
    print(f"    起评点 (Δz=0, Δφ=0°): φ = {tau:.2f}° - 0° = {phi_start:.2f}°")
    print(f"    终评点 (Δz={delta_L}mm, Δφ={delta_phi_max:.2f}°): φ = {tau:.2f}° - {delta_phi_max:.2f}° = {phi_end:.2f}°")
    print(f"    角度范围: {phi_end:.2f}° → {phi_start:.2f}°")

print(f"\n" + "=" * 70)
print("右齿向计算 (螺旋向右倾斜)")
print("=" * 70)
print("公式: φ = τ + Δφ")
print("说明: 随着轴向移动，旋转角度增大")

for i, tooth_idx in enumerate([1, 2, 3]):
    tau = tooth_idx * pitch_angle
    # 起评点: Δz = 0, Δφ = 0
    phi_start = tau + 0
    # 终评点: Δz = delta_L, Δφ = delta_phi_max
    phi_end = tau + delta_phi_max
    
    print(f"\n  齿{tooth_idx+1} (τ = {tau:.2f}°):")
    print(f"    起评点 (Δz=0, Δφ=0°): φ = {tau:.2f}° + 0° = {phi_start:.2f}°")
    print(f"    终评点 (Δz={delta_L}mm, Δφ={delta_phi_max:.2f}°): φ = {tau:.2f}° + {delta_phi_max:.2f}° = {phi_end:.2f}°")
    print(f"    角度范围: {phi_start:.2f}° → {phi_end:.2f}°")

print(f"\n" + "=" * 70)
print("关键结论")
print("=" * 70)
print("1. 公式 φ = -Δφ + τ 适用于左齿向（向左倾斜）")
print("2. 公式 φ = +Δφ + τ 适用于右齿向（向右倾斜）")
print("3. Δz 是从起评点开始计算的相对距离")
print("4. 左右齿向的螺旋方向相反，所以Δφ的符号相反")
