"""
分析齿向计算公式

根据图片:
- 通用公式: φ = -ξ - Δφ + τ
- 齿向: ξ = 0, 所以 φ = -Δφ + τ

其中:
- φ: 旋转角度
- Δφ: 轴向旋转 = 2 * Δz * tan(β) / D
- τ: 节距角
- Δz: 轴向距离（从齿的一端开始）

问题分析:
1. 左齿向和右齿向的区别
2. 角度方向（顺时针/逆时针）
3. 轴向距离的起始点
"""

import numpy as np

# 齿轮参数
module = 1.859
teeth_count = 87
helix_angle = 25.3  # 度
pitch_diameter = module * teeth_count  # 161.733 mm
pitch_angle = 360.0 / teeth_count  # 4.14度

# 评价范围
start_eval = 2.1  # mm
end_eval = 39.9   # mm
delta_L = end_eval - start_eval  # 37.8 mm

print("=" * 60)
print("齿向计算公式分析")
print("=" * 60)

print(f"\n齿轮参数:")
print(f"  模数: {module} mm")
print(f"  齿数: {teeth_count}")
print(f"  螺旋角: {helix_angle}°")
print(f"  节圆直径: {pitch_diameter:.3f} mm")
print(f"  节距角: {pitch_angle:.2f}°")

print(f"\n评价范围:")
print(f"  起评点: {start_eval} mm")
print(f"  终评点: {end_eval} mm")
print(f"  评价长度: {delta_L} mm")

# 计算Δφ
# Δφ = 2 * Δz * tan(β) / D
delta_phi_max = 2 * delta_L * np.tan(np.radians(helix_angle)) / pitch_diameter
delta_phi_max_deg = np.degrees(delta_phi_max)

print(f"\n轴向旋转计算:")
print(f"  Δφ_max = 2 * {delta_L} * tan({helix_angle}°) / {pitch_diameter:.3f}")
print(f"  Δφ_max = {delta_phi_max:.6f} rad = {delta_phi_max_deg:.2f}°")

# 分析左齿向
print(f"\n左齿向分析:")
print(f"  公式: φ = -Δφ + τ")
print(f"  对于左齿向，随着轴向移动，旋转角度减小")

for tooth_idx in [1, 2, 3]:  # 齿2, 3, 4
    tau = tooth_idx * pitch_angle
    phi_start = tau - 0  # Δφ = 0 at start
    phi_end = tau - delta_phi_max_deg
    
    print(f"\n  齿{tooth_idx+1} (τ={tau:.2f}°):")
    print(f"    起评点 (Δφ=0°): φ = {tau:.2f} - 0 = {phi_start:.2f}°")
    print(f"    终评点 (Δφ={delta_phi_max_deg:.2f}°): φ = {tau:.2f} - {delta_phi_max_deg:.2f} = {phi_end:.2f}°")
    print(f"    角度范围: {phi_end:.2f}° ~ {phi_start:.2f}°")

# 检查是否合理
print(f"\n合理性检查:")
print(f"  齿2角度范围: {1 * pitch_angle - delta_phi_max_deg:.2f}° ~ {1 * pitch_angle:.2f}°")
print(f"  齿3角度范围: {2 * pitch_angle - delta_phi_max_deg:.2f}° ~ {2 * pitch_angle:.2f}°")
print(f"  齿4角度范围: {3 * pitch_angle - delta_phi_max_deg:.2f}° ~ {3 * pitch_angle:.2f}°")

# 检查是否有重叠
print(f"\n重叠检查:")
print(f"  齿2最大值: {1 * pitch_angle:.2f}°")
print(f"  齿3最小值: {2 * pitch_angle - delta_phi_max_deg:.2f}°")
print(f"  间隙: {(2 * pitch_angle - delta_phi_max_deg) - (1 * pitch_angle):.2f}°")

if (2 * pitch_angle - delta_phi_max_deg) > (1 * pitch_angle):
    print("  结果: 齿2和齿3之间有间隙 ✓")
else:
    print("  结果: 齿2和齿3之间有重叠 ✗")
