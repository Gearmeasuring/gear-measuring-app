"""
================================================================================
检查齿1的三条曲线
Check Tooth 1 Three Curves
================================================================================
"""

import sys
import os
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import RippleWavinessAnalyzer

print("="*80)
print("检查齿1的三条曲线")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

# 获取齿向评价范围
helix_eval = analyzer.reader.helix_eval_range
print(f"\n齿向评价范围: b1={helix_eval.eval_start}mm, b2={helix_eval.eval_end}mm")

# 右齿形
print()
print("="*80)
print("[右齿形齿1]")
print("="*80)

profile_data_right = analyzer.reader.profile_data.get('right', {})
if 1 in profile_data_right:
    tooth1_data = profile_data_right[1]
    print(f"\n齿1的所有z位置: {list(tooth1_data.keys())}")
    
    for z_pos, values in tooth1_data.items():
        in_eval = helix_eval.eval_start <= z_pos <= helix_eval.eval_end
        marker = "✓ 在评价范围内" if in_eval else "✗ 不在评价范围内"
        print(f"  z={z_pos}mm: {len(values)}点, {marker}")

# 左齿形
print()
print("="*80)
print("[左齿形齿1]")
print("="*80)

profile_data_left = analyzer.reader.profile_data.get('left', {})
if 1 in profile_data_left:
    tooth1_data = profile_data_left[1]
    print(f"\n齿1的所有z位置: {list(tooth1_data.keys())}")
    
    for z_pos, values in tooth1_data.items():
        in_eval = helix_eval.eval_start <= z_pos <= helix_eval.eval_end
        marker = "✓ 在评价范围内" if in_eval else "✗ 不在评价范围内"
        print(f"  z={z_pos}mm: {len(values)}点, {marker}")

print()
print("="*80)
print("[问题分析]")
print("="*80)

print(f"""
齿1有三条曲线：
  - z=2.1mm (齿宽底部)
  - z=21.0mm (齿宽中间) ← 应该是正确的
  - z=39.9mm (齿宽顶部)

齿向评价范围: [{helix_eval.eval_start}, {helix_eval.eval_end}] mm

所有三条曲线都在评价范围内，所以都被使用了。

但用户说"只有位置中间一条是正确的"，这意味着：
  - 应该只使用 z=21.0mm (中间位置)
  - 或者只使用最接近齿向评价范围中间位置的曲线

齿向评价范围中间: {(helix_eval.eval_start + helix_eval.eval_end) / 2} mm
""")

# 计算哪个z位置最接近中间
mid_point = (helix_eval.eval_start + helix_eval.eval_end) / 2
print(f"\n齿向评价范围中间点: {mid_point} mm")

if 1 in profile_data_right:
    z_positions = list(profile_data_right[1].keys())
    closest_z = min(z_positions, key=lambda z: abs(z - mid_point))
    print(f"最接近中间点的z位置: {closest_z} mm")
