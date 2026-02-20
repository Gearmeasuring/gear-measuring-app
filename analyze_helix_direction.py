"""
重新分析齿向方向

根据图片中的示意图:
- tooth 1 和 tooth 2 显示在节距角 τ 的两侧
- ξ₁ 和 ξ₂ 是滚动角
- 对于齿向，ξ = 0

关键问题:
1. 左齿向和右齿向的区别是什么？
2. 角度方向应该如何定义？

对于左齿向:
- 从齿的啮合端看，螺旋线向左倾斜
- 当沿着轴向移动时，旋转方向是顺时针还是逆时针？

对于右齿向:
- 从齿的啮合端看，螺旋线向右倾斜
- 当沿着轴向移动时，旋转方向相反
"""

import numpy as np

# 齿轮参数
module = 1.859
teeth_count = 87
helix_angle = 25.3
pitch_diameter = module * teeth_count
pitch_angle = 360.0 / teeth_count

# 评价范围
delta_L = 37.8  # mm

# 计算Δφ
delta_phi_max_deg = np.degrees(2 * delta_L * np.tan(np.radians(helix_angle)) / pitch_diameter)

print("=" * 60)
print("齿向方向分析")
print("=" * 60)

print(f"\n基本参数:")
print(f"  节距角: {pitch_angle:.2f}°")
print(f"  最大轴向旋转: {delta_phi_max_deg:.2f}°")
print(f"  比值: {delta_phi_max_deg / pitch_angle:.2f} (轴向旋转/节距角)")

print(f"\n问题分析:")
print(f"  由于轴向旋转({delta_phi_max_deg:.2f}°) > 节距角({pitch_angle:.2f}°)")
print(f"  这会导致相邻齿的角度范围重叠")

print(f"\n可能的解决方案:")
print(f"  1. 使用绝对角度（不归一化），保持负值")
print(f"  2. 对于左齿向，可能需要反转Δφ的符号")
print(f"  3. 或者左右齿向的定义不同")

print(f"\n左齿向 vs 右齿向:")
print(f"  左齿向: 螺旋线向左倾斜")
print(f"  右齿向: 螺旋线向右倾斜")
print(f"  两者的Δφ符号应该相反")

print(f"\n当前计算（左齿向）:")
for tooth_idx in [1, 2, 3]:
    tau = tooth_idx * pitch_angle
    phi_start = tau  # Δφ = 0
    phi_end = tau - delta_phi_max_deg  # Δφ = max
    print(f"  齿{tooth_idx+1}: {phi_end:.2f}° ~ {phi_start:.2f}° (跨度 {phi_start - phi_end:.2f}°)")

print(f"\n如果反转Δφ符号（可能用于右齿向）:")
for tooth_idx in [1, 2, 3]:
    tau = tooth_idx * pitch_angle
    phi_start = tau  # Δφ = 0
    phi_end = tau + delta_phi_max_deg  # Δφ = max (正号)
    print(f"  齿{tooth_idx+1}: {phi_start:.2f}° ~ {phi_end:.2f}° (跨度 {phi_end - phi_start:.2f}°)")

print(f"\n结论:")
print(f"  当前计算是正确的，重叠是由于物理原因（螺旋角大+评价范围长）")
print(f"  这不是计算错误，而是实际数据的特征")
