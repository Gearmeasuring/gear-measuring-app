"""
================================================================================
每个测量点的旋转角度确定方法
How to Determine Rotation Angle for Each Measurement Point
================================================================================
"""

import sys
import os
import numpy as np
import math
import matplotlib.pyplot as plt

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import RippleWavinessAnalyzer, InvoluteCalculator

print("="*80)
print("每个测量点的旋转角度确定方法")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

print()
print("[基本概念]")
print("-"*80)
print("""
每个测量点的旋转角度由两部分组成:

1. 齿序角 (τ): 表示这是第几个齿
   τ = (齿序号 - 1) × 节距角
   节距角 = 360° / 齿数

2. 测量点相对角度 (ξ): 表示测量点在齿上的位置
   由渐开线理论计算得出
""")

print()
print("[齿形测量点相对角度计算]")
print("-"*80)

ze = analyzer.gear_params.teeth_count
module = analyzer.gear_params.module
pressure_angle = analyzer.gear_params.pressure_angle
helix_angle = analyzer.gear_params.helix_angle

print(f"""
齿轮参数:
  齿数 ZE = {ze}
  模数 m = {module} mm
  压力角 α = {pressure_angle}°
  螺旋角 β = {helix_angle}°
""")

# 计算关键直径
alpha_n = math.radians(pressure_angle)
beta = math.radians(helix_angle)

# 端面压力角
if abs(beta) > 0.001:
    alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta))
else:
    alpha_t = alpha_n

pitch_diameter = module * ze
base_diameter = pitch_diameter * math.cos(alpha_t)

print(f"计算结果:")
print(f"  节圆直径 D₀ = m × ZE = {module} × {ze} = {pitch_diameter:.3f} mm")
print(f"  端面压力角 αt = {math.degrees(alpha_t):.4f}°")
print(f"  基圆直径 db = D₀ × cos(αt) = {base_diameter:.3f} mm")

print()
print("[渐开线极角计算原理]")
print("-"*80)
print("""
渐开线方程:
  极角 θ = inv(α) = tan(α) - α
  
其中压力角 α 由以下关系确定:
  cos(α) = rb / r = 基圆半径 / 测量点半径
  
测量点直径 d → 测量点半径 r = d/2
  cos(α) = db / d
  α = arccos(db / d)
""")

print()
print("[展长角度计算]")
print("-"*80)
print("""
另一种计算方式 - 展长角度:

展长 s(d): 从基圆到测量点的渐开线弧长
  s(d) = √((d/2)² - (db/2)²)
  
展长对应的旋转角 ξ:
  ξ = s / (π × db) × 360°

这个角度表示: 从基圆展开到测量点所需的旋转角度
""")

# 获取评价范围
eval_range = analyzer.reader.profile_eval_range
d1 = eval_range.eval_start  # 起评点 (齿根方向)
d2 = eval_range.eval_end    # 终评点 (齿顶方向)

print(f"""
评价范围:
  d1 (起评点) = {d1} mm
  d2 (终评点) = {d2} mm
""")

# 计算展长角度
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

xi1 = calculate_roll_angle(d1, base_diameter)
xi2 = calculate_roll_angle(d2, base_diameter)

print(f"展长角度计算:")
print(f"  s(d1) = √(({d1}/2)² - ({base_diameter:.3f}/2)²) = {math.sqrt((d1/2)**2 - (base_diameter/2)**2):.4f} mm")
print(f"  s(d2) = √(({d2}/2)² - ({base_diameter:.3f}/2)²) = {math.sqrt((d2/2)**2 - (base_diameter/2)**2):.4f} mm")
print(f"  ξ(d1) = {xi1:.4f}°")
print(f"  ξ(d2) = {xi2:.4f}°")
print(f"  差值 = {xi2 - xi1:.4f}°")

print()
print("[相对极角计算]")
print("-"*80)
print("""
从齿顶开始排列，齿顶极角为0°:

  相对极角 = 展长角度 - 齿顶展长角度
  φ(d) = ξ(d) - ξ(d_tip)

其中 d_tip = 终评点直径 (齿顶方向)

所以:
  齿顶 (d2): φ = ξ(d2) - ξ(d2) = 0°
  齿根 (d1): φ = ξ(d1) - ξ(d2) = {0:.4f}° - {1:.4f}° = {2:.4f}°
""".format(xi1, xi2, xi1 - xi2))

# 计算相对极角
relative_angle_d1 = xi1 - xi2
relative_angle_d2 = 0.0  # 齿顶为0

print(f"验证:")
print(f"  齿顶 (d2={d2}mm): φ = 0°")
print(f"  齿根 (d1={d1}mm): φ = {relative_angle_d1:.4f}°")

print()
print("[最终旋转角度计算]")
print("-"*80)

pitch_angle = 360.0 / ze

print(f"""
最终旋转角度 = 齿序角 + 相对极角

对于右齿形:
  θ = τ + φ = (齿序号-1) × {pitch_angle:.4f}° + φ

对于左齿形:
  θ = τ - φ = (齿序号-1) × {pitch_angle:.4f}° - φ

其中:
  τ = 齿序角 = (齿序号-1) × 节距角
  φ = 相对极角 = ξ(d) - ξ(d_tip)
""")

print()
print("[具体例子]")
print("-"*80)

# 生成几个示例点
num_points = 10
diameters = np.linspace(d1, d2, num_points)

print(f"\n齿1右齿形的测量点角度:")
print(f"  {'点号':>4} {'直径(mm)':>10} {'展长角ξ':>10} {'相对极角φ':>12} {'最终角度θ':>10}")
print(f"  {'-'*50}")

for i, d in enumerate(diameters):
    xi = calculate_roll_angle(d, base_diameter)
    phi = xi - xi2  # 相对极角
    tau = 0  # 齿1的齿序角为0
    theta = tau + phi  # 右齿形
    print(f"  {i+1:>4} {d:>10.3f} {xi:>10.4f}° {phi:>12.4f}° {theta:>10.4f}°")

print(f"\n齿2右齿形的测量点角度:")
print(f"  {'点号':>4} {'直径(mm)':>10} {'展长角ξ':>10} {'相对极角φ':>12} {'最终角度θ':>10}")
print(f"  {'-'*50}")

for i, d in enumerate(diameters):
    xi = calculate_roll_angle(d, base_diameter)
    phi = xi - xi2
    tau = pitch_angle  # 齿2的齿序角
    theta = tau + phi  # 右齿形
    print(f"  {i+1:>4} {d:>10.3f} {xi:>10.4f}° {phi:>12.4f}° {theta:>10.4f}°")

print()
print("[总结]")
print("-"*80)
print("""
每个测量点的旋转角度确定步骤:

步骤1: 计算基圆直径
  db = m × ZE × cos(αt)

步骤2: 计算展长角度
  ξ(d) = √((d/2)² - (db/2)²) / (π × db) × 360°

步骤3: 计算相对极角 (从齿顶开始)
  φ(d) = ξ(d) - ξ(d_tip)
  其中 d_tip = 终评点直径

步骤4: 计算齿序角
  τ = (齿序号 - 1) × 360° / ZE

步骤5: 计算最终旋转角度
  右齿形: θ = τ + φ
  左齿形: θ = τ - φ

步骤6: 归一化到0-360°
  θ = θ mod 360°
""")
