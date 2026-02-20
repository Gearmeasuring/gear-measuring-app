"""
================================================================================
修正后的相对极角计算方法
Corrected Relative Polar Angle Calculation
================================================================================

修正说明:
- 右齿形: 从齿顶开始，齿顶极角为0°
- 左齿形: 从齿根开始，齿根极角为0°
"""

import sys
import os
import numpy as np
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import RippleWavinessAnalyzer

print("="*80)
print("修正后的相对极角计算方法")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

ze = analyzer.gear_params.teeth_count
module = analyzer.gear_params.module
pressure_angle = analyzer.gear_params.pressure_angle
helix_angle = analyzer.gear_params.helix_angle

alpha_n = math.radians(pressure_angle)
beta = math.radians(helix_angle)

if abs(beta) > 0.001:
    alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta))
else:
    alpha_t = alpha_n

pitch_diameter = module * ze
base_diameter = pitch_diameter * math.cos(alpha_t)

eval_range = analyzer.reader.profile_eval_range
d1 = eval_range.eval_start  # 起评点 (齿根方向)
d2 = eval_range.eval_end    # 终评点 (齿顶方向)

def calculate_roll_angle(diameter, base_diameter):
    """计算展长角度"""
    radius = diameter / 2
    base_radius = base_diameter / 2
    
    if radius <= base_radius:
        return 0.0
    
    roll_length = math.sqrt(radius**2 - base_radius**2)
    base_circumference = math.pi * base_diameter
    
    roll_angle = (roll_length / base_circumference) * 360.0
    return roll_angle

xi1 = calculate_roll_angle(d1, base_diameter)  # 齿根展长角
xi2 = calculate_roll_angle(d2, base_diameter)  # 齿顶展长角

print(f"""
齿轮参数:
  齿数 ZE = {ze}
  基圆直径 db = {base_diameter:.3f} mm

评价范围:
  d1 (齿根) = {d1} mm
  d2 (齿顶) = {d2} mm

展长角度:
  ξ(d1) = {xi1:.4f}° (齿根)
  ξ(d2) = {xi2:.4f}° (齿顶)
  差值 = {xi2 - xi1:.4f}°
""")

print()
print("="*80)
print("修正后的相对极角计算")
print("="*80)

print()
print("[右齿形] 从齿顶开始，齿顶极角为0°")
print("-"*80)
print("""
公式:
  φ_right(d) = ξ(d) - ξ(d_tip)
  
其中 d_tip = 齿顶直径 (d2)

结果:
  齿顶 (d2): φ = ξ(d2) - ξ(d2) = 0°
  齿根 (d1): φ = ξ(d1) - ξ(d2) = {0:.4f}° - {1:.4f}° = {2:.4f}°
""".format(xi1, xi2, xi1 - xi2))

phi_right_tip = 0.0
phi_right_root = xi1 - xi2

print(f"验证:")
print(f"  齿顶: φ = 0°")
print(f"  齿根: φ = {phi_right_root:.4f}°")

print()
print("[左齿形] 从齿根开始，齿根极角为0°")
print("-"*80)
print("""
公式:
  φ_left(d) = ξ(d) - ξ(d_root)
  
其中 d_root = 齿根直径 (d1)

结果:
  齿根 (d1): φ = ξ(d1) - ξ(d1) = 0°
  齿顶 (d2): φ = ξ(d2) - ξ(d1) = {0:.4f}° - {1:.4f}° = {2:.4f}°
""".format(xi2, xi1, xi2 - xi1))

phi_left_root = 0.0
phi_left_tip = xi2 - xi1

print(f"验证:")
print(f"  齿根: φ = 0°")
print(f"  齿顶: φ = {phi_left_tip:.4f}°")

print()
print("="*80)
print("最终旋转角度计算")
print("="*80)

pitch_angle = 360.0 / ze

print()
print("[右齿形]")
print("-"*80)
print(f"""
最终旋转角度:
  θ_right = τ + φ_right
          = (齿序号-1) × {pitch_angle:.4f}° + φ_right

其中 φ_right 从齿顶开始为0°，向齿根方向增加
""")

print()
print("[左齿形]")
print("-"*80)
print(f"""
最终旋转角度:
  θ_left = τ - φ_left
         = (齿序号-1) × {pitch_angle:.4f}° - φ_left

其中 φ_left 从齿根开始为0°，向齿顶方向增加
""")

print()
print("="*80)
print("具体例子对比")
print("="*80)

num_points = 5
diameters = np.linspace(d1, d2, num_points)

print()
print("齿1的角度计算:")
print()
print("右齿形 (从齿顶开始):")
print(f"  {'点号':>4} {'直径(mm)':>10} {'展长角ξ':>10} {'相对极角φ':>12} {'最终角度θ':>10}")
print(f"  {'-'*50}")

for i, d in enumerate(diameters):
    xi = calculate_roll_angle(d, base_diameter)
    phi = xi - xi2  # 右齿形: 从齿顶开始
    tau = 0  # 齿1
    theta = tau + phi
    print(f"  {i+1:>4} {d:>10.3f} {xi:>10.4f}° {phi:>12.4f}° {theta:>10.4f}°")

print()
print("左齿形 (从齿根开始):")
print(f"  {'点号':>4} {'直径(mm)':>10} {'展长角ξ':>10} {'相对极角φ':>12} {'最终角度θ':>10}")
print(f"  {'-'*50}")

for i, d in enumerate(diameters):
    xi = calculate_roll_angle(d, base_diameter)
    phi = xi - xi1  # 左齿形: 从齿根开始
    tau = 0  # 齿1
    theta = tau - phi  # 左齿形: 减
    print(f"  {i+1:>4} {d:>10.3f} {xi:>10.4f}° {phi:>12.4f}° {theta:>10.4f}°")

print()
print("="*80)
print("总结")
print("="*80)
print("""
修正后的相对极角计算:

右齿形 (从齿顶开始):
  φ_right(d) = ξ(d) - ξ(d_tip)
  齿顶: φ = 0°
  齿根: φ = ξ(d1) - ξ(d2) < 0 (负值)
  
左齿形 (从齿根开始):
  φ_left(d) = ξ(d) - ξ(d_root)
  齿根: φ = 0°
  齿顶: φ = ξ(d2) - ξ(d1) > 0 (正值)

最终角度:
  右齿形: θ = τ + φ_right
  左齿形: θ = τ - φ_left
""")
