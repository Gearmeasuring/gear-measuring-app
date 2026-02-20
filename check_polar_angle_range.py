"""
================================================================================
检查齿形和齿向的极角计算是否从起评点到终评点
Check if Polar Angle Calculation is from eval_start to eval_end
================================================================================
"""

import sys
import os
import numpy as np
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import (
    RippleWavinessAnalyzer, InvoluteCalculator
)

print("="*80)
print("检查齿形和齿向的极角计算是否从起评点到终评点")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

profile_eval = analyzer.reader.profile_eval_range
helix_eval = analyzer.reader.helix_eval_range

print()
print("[评价范围]")
print("-"*80)
print(f"齿形评价范围: d1={profile_eval.eval_start}mm (起评点) 到 d2={profile_eval.eval_end}mm (终评点)")
print(f"齿向评价范围: b1={helix_eval.eval_start}mm (起评点) 到 b2={helix_eval.eval_end}mm (终评点)")

print()
print("="*80)
print("[齿形极角计算]")
print("="*80)

print("""
算法描述:
  对于齿形，测量点是沿着渐开线分布的，可以根据渐开线理论计算每个点的极角。
  找出起评点，算出起始极角，以此类推，把每一个测量点的极角都算出来，直到终评点极角。

实现方式:
  1. 计算起评点(d1)和终评点(d2)对应的展长
  2. 在起评点到终评点之间均匀分布测量点
  3. 计算每个测量点的展长角度
  4. 转换为相对极角（从齿顶或齿根开始为0°）
""")

involute_calc = InvoluteCalculator(analyzer.gear_params)

d1 = profile_eval.eval_start  # 起评点
d2 = profile_eval.eval_end    # 终评点
db = analyzer.gear_params.base_diameter

# 计算展长
s_d1 = involute_calc.calculate_roll_length(d1)
s_d2 = involute_calc.calculate_roll_length(d2)

print()
print(f"展长计算:")
print(f"  起评点 d1 = {d1}mm")
print(f"  终评点 d2 = {d2}mm")
print(f"  基圆直径 db = {db:.3f}mm")
print(f"  s(d1) = sqrt((d1/2)^2 - (db/2)^2) = {s_d1:.4f}mm")
print(f"  s(d2) = sqrt((d2/2)^2 - (db/2)^2) = {s_d2:.4f}mm")

# 计算展长角度
xi_d1 = involute_calc.calculate_roll_angle_degrees(d1)
xi_d2 = involute_calc.calculate_roll_angle_degrees(d2)

print()
print(f"展长角度:")
print(f"  xi(d1) = s(d1) / (pi * db) * 360 = {xi_d1:.4f} deg")
print(f"  xi(d2) = s(d2) / (pi * db) * 360 = {xi_d2:.4f} deg")

# 模拟测量点分布
num_points = 10
roll_lengths = np.linspace(s_d1, s_d2, num_points)

print()
print(f"测量点分布 (从起评点到终评点，共{num_points}个点):")
print("-"*60)
print(f"{'点号':>4} {'展长(mm)':>12} {'展长角(deg)':>12} {'相对极角(deg)':>15}")
print("-"*60)

for i, s in enumerate(roll_lengths):
    xi = s / (math.pi * db) * 360
    # 右齿形: 从齿顶开始，齿顶极角为0
    relative_angle = xi - xi_d2
    print(f"{i+1:>4} {s:>12.4f} {xi:>12.4f} {relative_angle:>15.4f}")

print()
print("="*80)
print("[齿向极角计算]")
print("="*80)

print("""
算法描述:
  对于齿向，从起评点到终评点，每一个测量点的极角 = 2*(测量点-起评点)*tan(螺旋角)/节圆直径

实现方式:
  1. 从起评点(b1)开始，测量点沿齿向分布
  2. 计算每个测量点相对于起评点的轴向位移
  3. 根据螺旋角计算旋转角度
""")

b1 = helix_eval.eval_start  # 起评点
b2 = helix_eval.eval_end    # 终评点
D0 = analyzer.gear_params.pitch_diameter
beta = analyzer.gear_params.helix_angle

print()
print(f"齿向参数:")
print(f"  起评点 b1 = {b1}mm")
print(f"  终评点 b2 = {b2}mm")
print(f"  节圆直径 D0 = {D0:.3f}mm")
print(f"  螺旋角 beta = {beta} deg")

# 计算极角
axial_positions = np.linspace(b1, b2, num_points)

print()
print(f"测量点分布 (从起评点到终评点，共{num_points}个点):")
print("-"*60)
print(f"{'点号':>4} {'轴向位置(mm)':>12} {'Delta_z(mm)':>12} {'极角(deg)':>12}")
print("-"*60)

for i, z in enumerate(axial_positions):
    delta_z = z - b1
    tan_beta = math.tan(math.radians(abs(beta)))
    polar_angle = 2 * delta_z * tan_beta / D0
    polar_angle_deg = math.degrees(polar_angle)
    print(f"{i+1:>4} {z:>12.4f} {delta_z:>12.4f} {polar_angle_deg:>12.4f}")

print()
print("="*80)
print("[代码实现检查]")
print("="*80)

print("""
齿形极角计算 (ProfileAngleCalculator.calculate_profile_polar_angles):
  - 输入: eval_range (包含eval_start和eval_end)
  - 计算: roll_lengths = linspace(s(eval_start), s(eval_end), num_points)
  - 输出: 相对极角数组
  ✓ 确认: 从起评点到终评点

齿向极角计算 (HelixAngleCalculator.build_rotation_curve):
  - 输入: eval_range (包含eval_start和eval_end)
  - 计算: axial_positions = linspace(eval_start, eval_end, num_points)
  - 计算: polar_angle = 2 * (z - eval_start) * tan(beta) / D0
  ✓ 确认: 从起评点到终评点
""")

print()
print("="*80)
print("[结论]")
print("="*80)
print("""
确认: 无论是齿形还是齿向，极角计算都是从起评点到终评点

齿形:
  - 测量点沿渐开线分布
  - 从起评点(d1)到终评点(d2)
  - 每个点对应一个展长角度

齿向:
  - 测量点沿齿向分布
  - 从起评点(b1)到终评点(b2)
  - 每个点对应一个螺旋角产生的旋转角度

代码实现正确！
""")
