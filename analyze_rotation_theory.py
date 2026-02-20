"""
================================================================================
齿形旋转角理论分析
Profile Rotation Angle Theory Analysis
================================================================================

原文:
"In a straight gearing with an unmodified tooth trace, no-load intermating tooth 
flanks contact each other on a straight line parallel to the tooth root. For every 
rotational angle of the component, a different contact line is produced. If we now 
add the pitch measurement, we can assign a rotational angle of the toothed gear 
for all teeth at each point on the profile measurement. And if we arrange all 
profile measurements along the rotational angle and pitch measurement, we obtain 
the curve shown in Figure 9"

================================================================================
"""

print("="*80)
print("齿形旋转角理论分析")
print("="*80)

print()
print("[原文翻译]")
print("-"*80)
print("""
在具有未修正齿迹的直齿轮中，无载啮合齿面在平行于齿根的直线上相互接触。
对于齿轮的每个旋转角度，都会产生不同的接触线。
如果我们现在加上节距测量，我们可以为每个齿在齿形测量上的每个点分配齿轮的旋转角度。
如果我们沿着旋转角度和节距测量排列所有齿形测量，我们得到图9所示的曲线。
""")

print()
print("[理论要点解析]")
print("-"*80)
print("""
1. 直齿轮啮合特性:
   - 齿面接触线平行于齿根
   - 每个旋转角度对应不同的接触线

2. 旋转角度分配:
   - 通过节距测量(pitch measurement)确定每个齿的位置
   - 为每个齿的每个测量点分配旋转角度

3. 曲线构建:
   - 将所有齿形测量沿旋转角度排列
   - 结合节距测量得到完整曲线
""")

print()
print("[对0-360度合并的帮助]")
print("-"*80)
print("""
这段理论对我们的算法有以下帮助:

1. 确认了旋转角度分配的核心思想:
   - 每个齿的旋转角度 = 节距角 × (齿序号 - 1)
   - 节距角 = 360° / 齿数

2. 齿形测量点的角度计算:
   - 测量点的相对角度由渐开线特性决定
   - 最终角度 = 齿序角 + 测量点相对角度

3. 曲线合并方法:
   - 所有齿的测量数据按旋转角度排列
   - 形成0-360度的闭合曲线

4. 关键理解:
   - "pitch measurement" 即节距测量，确定了齿与齿之间的角度关系
   - 这就是为什么我们需要用节距角来偏移每个齿的角度
""")

print()
print("[理论验证]")
print("-"*80)

import sys
import os
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import RippleWavinessAnalyzer

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

ze = analyzer.gear_params.teeth_count
pitch_angle = analyzer.gear_params.pitch_angle

print(f"""
齿轮参数:
  齿数 ZE = {ze}
  节距角 = 360° / {ze} = {pitch_angle:.4f}°

旋转角度分配:
  齿1: 0 × {pitch_angle:.4f}° = 0°
  齿2: 1 × {pitch_angle:.4f}° = {pitch_angle:.4f}°
  齿3: 2 × {pitch_angle:.4f}° = {2*pitch_angle:.4f}°
  ...
  齿{ze}: {ze-1} × {pitch_angle:.4f}° = {(ze-1)*pitch_angle:.4f}°

验证: 最后一齿的角度 = {(ze-1)*pitch_angle:.4f}° ≈ 360° - {pitch_angle:.4f}°
""")

print()
print("[结论]")
print("-"*80)
print("""
这段理论完全支持我们的0-360度合并算法:

1. ✓ 每个齿按节距角偏移
2. ✓ 测量点角度由渐开线决定
3. ✓ 所有齿排列形成闭合曲线

这正是我们实现的算法核心思想!
""")
