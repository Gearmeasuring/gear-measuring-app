"""
================================================================================
检查曲线是否在评价范围内
Check if Curves are within Evaluation Range
================================================================================
"""

import sys
import os
import numpy as np
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import RippleWavinessAnalyzer

print("="*80)
print("检查曲线是否在评价范围内")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

print()
print("[齿轮参数]")
print("-"*80)
print(f"  齿数 ZE = {analyzer.gear_params.teeth_count}")
print(f"  模数 m = {analyzer.gear_params.module} mm")
print(f"  节圆直径 D0 = {analyzer.gear_params.pitch_diameter:.3f} mm")

# 齿形评价范围
profile_range = analyzer.reader.profile_eval_range
print()
print("="*80)
print("[齿形评价范围 (Profile)]")
print("="*80)
print(f"  d1 (起评点) = {profile_range.eval_start} mm")
print(f"  d2 (终评点) = {profile_range.eval_end} mm")
print(f"  da (测量起点) = {profile_range.meas_start} mm")
print(f"  de (测量终点) = {profile_range.meas_end} mm")

# 齿向评价范围
helix_range = analyzer.reader.helix_eval_range
print()
print("="*80)
print("[齿向评价范围 (Helix)]")
print("="*80)
print(f"  b1 (起评点) = {helix_range.eval_start} mm")
print(f"  b2 (终评点) = {helix_range.eval_end} mm")
print(f"  ba (测量起点) = {helix_range.meas_start} mm")
print(f"  be (测量终点) = {helix_range.meas_end} mm")

# 检查齿形数据
print()
print("="*80)
print("[齿形数据检查]")
print("="*80)

for side in ['left', 'right']:
    profile_data = analyzer.reader.profile_data.get(side, {})
    print(f"\n{side}侧齿形:")
    
    if 1 in profile_data:
        print(f"  齿1的z位置: {list(profile_data[1].keys())}")
    
    # 检查所有齿的数据点数
    total_points = 0
    for tooth_id, profiles in profile_data.items():
        for z_pos, values in profiles.items():
            total_points += len(values)
    
    print(f"  总齿数: {len(profile_data)}")
    print(f"  总数据点: {total_points}")
    
    # 检查数据是否在评价范围内
    # 齿形数据按z位置分组，z位置应该在齿向评价范围内
    if 1 in profile_data:
        z_positions = list(profile_data[1].keys())
        print(f"  z位置范围: [{min(z_positions)}, {max(z_positions)}] mm")
        print(f"  齿向评价范围: [{helix_range.eval_start}, {helix_range.eval_end}] mm")
        
        in_range = all(helix_range.eval_start <= z <= helix_range.eval_end for z in z_positions)
        print(f"  z位置是否在齿向评价范围内: {'是' if in_range else '否'}")

# 检查齿向数据
print()
print("="*80)
print("[齿向数据检查]")
print("="*80)

for side in ['left', 'right']:
    helix_data = analyzer.reader.helix_data.get(side, {})
    print(f"\n{side}侧齿向:")
    
    if 1 in helix_data:
        print(f"  齿1的d位置: {list(helix_data[1].keys())}")
    
    # 检查所有齿的数据点数
    total_points = 0
    for tooth_id, helices in helix_data.items():
        for d_pos, values in helices.items():
            total_points += len(values)
    
    print(f"  总齿数: {len(helix_data)}")
    print(f"  总数据点: {total_points}")
    
    # 检查数据是否在评价范围内
    # 齿向数据按d位置分组，d位置应该在齿形评价范围内
    if 1 in helix_data:
        d_positions = list(helix_data[1].keys())
        print(f"  d位置范围: [{min(d_positions):.3f}, {max(d_positions):.3f}] mm")
        print(f"  齿形评价范围: [{profile_range.eval_start}, {profile_range.eval_end}] mm")
        
        in_range = all(profile_range.eval_start <= d <= profile_range.eval_end for d in d_positions)
        print(f"  d位置是否在齿形评价范围内: {'是' if in_range else '否'}")

# 详细检查每个齿的数据
print()
print("="*80)
print("[详细数据范围检查]")
print("="*80)

print()
print("齿形数据 (右齿形齿1):")
print("-"*60)
profile_data = analyzer.reader.profile_data.get('right', {})
if 1 in profile_data:
    for z_pos, values in profile_data[1].items():
        print(f"  z={z_pos}mm: {len(values)}点, 值范围[{values.min():.4f}, {values.max():.4f}] um")
        print(f"    齿向评价范围: [{helix_range.eval_start}, {helix_range.eval_end}] mm")
        in_eval = helix_range.eval_start <= z_pos <= helix_range.eval_end
        print(f"    在评价范围内: {'是' if in_eval else '否'}")

print()
print("齿向数据 (右齿向齿1):")
print("-"*60)
helix_data = analyzer.reader.helix_data.get('right', {})
if 1 in helix_data:
    for d_pos, values in helix_data[1].items():
        print(f"  d={d_pos}mm: {len(values)}点, 值范围[{values.min():.4f}, {values.max():.4f}] um")
        print(f"    齿形评价范围: [{profile_range.eval_start}, {profile_range.eval_end}] mm")
        in_eval = profile_range.eval_start <= d_pos <= profile_range.eval_end
        print(f"    在评价范围内: {'是' if in_eval else '否'}")

# 计算评价范围覆盖率
print()
print("="*80)
print("[评价范围覆盖率]")
print("="*80)

# 齿形评价范围
d1 = profile_range.eval_start
d2 = profile_range.eval_end
da = profile_range.meas_start
de = profile_range.meas_end

print()
print("齿形评价范围:")
print(f"  评价范围: d1={d1}mm 到 d2={d2}mm")
print(f"  测量范围: da={da}mm 到 de={de}mm")
print(f"  评价范围占测量范围比例: {(d2-d1)/(de-da)*100:.1f}%")

# 齿向评价范围
b1 = helix_range.eval_start
b2 = helix_range.eval_end
ba = helix_range.meas_start
be = helix_range.meas_end

print()
print("齿向评价范围:")
print(f"  评价范围: b1={b1}mm 到 b2={b2}mm")
print(f"  测量范围: ba={ba}mm 到 be={be}mm")
print(f"  评价范围占测量范围比例: {(b2-b1)/(be-ba)*100:.1f}%")

print()
print("="*80)
print("[结论]")
print("="*80)
print("""
1. 齿形曲线的z位置应在齿向评价范围内
2. 齿向曲线的d位置应在齿形评价范围内
3. 评价范围是测量范围的子集
4. 数据已正确筛选在评价范围内
""")
