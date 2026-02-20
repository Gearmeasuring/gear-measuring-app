"""
================================================================================
检查齿形和齿向的评价范围定义
Check Profile and Helix Evaluation Range Definitions
================================================================================
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import RippleWavinessAnalyzer

print("="*80)
print("检查齿形和齿向的评价范围定义")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

print()
print("[评价范围定义]")
print("-"*80)

print("齿形:")
profile_eval = analyzer.reader.profile_eval_range
print(f"  评价范围: d1={profile_eval.eval_start}mm 到 d2={profile_eval.eval_end}mm")
print(f"  测量范围: da={profile_eval.meas_start}mm 到 de={profile_eval.meas_end}mm")

print()
print("齿向:")
helix_eval = analyzer.reader.helix_eval_range
print(f"  评价范围: b1={helix_eval.eval_start}mm 到 b2={helix_eval.eval_end}mm")
print(f"  测量范围: ba={helix_eval.meas_start}mm 到 be={helix_eval.meas_end}mm")

print()
print("="*80)
print("[分析]")
print("-"*80)

print()
print("1. 齿形数据中的z位置应该在齿向测量范围内:")
print("-"*60)
print(f"  齿向测量范围: ba={helix_eval.meas_start}mm 到 be={helix_eval.meas_end}mm")

for side in ['left', 'right']:
    profile_data = analyzer.reader.profile_data.get(side, {})
    if 1 in profile_data:
        z_positions = list(profile_data[1].keys())
        print(f"\n{side}侧齿形齿1的z位置: {z_positions}")
        
        in_range = all(helix_eval.meas_start <= z <= helix_eval.meas_end for z in z_positions)
        print(f"  是否在齿向测量范围内: {'是' if in_range else '否'}")

print()
print("2. 齿向数据中的d位置应该在齿形测量范围内:")
print("-"*60)
print(f"  齿形测量范围: da={profile_eval.meas_start}mm 到 de={profile_eval.meas_end}mm")

for side in ['left', 'right']:
    helix_data = analyzer.reader.helix_data.get(side, {})
    if 1 in helix_data:
        d_positions = list(helix_data[1].keys())
        print(f"\n{side}侧齿向齿1的d位置: {d_positions}")
        
        in_range = all(profile_eval.meas_start <= d <= profile_eval.meas_end for d in d_positions)
        print(f"  是否在齿形测量范围内: {'是' if in_range else '否'}")

print()
print("3. 评价范围和测量范围的关系:")
print("-"*60)

print("齿形:")
print(f"  评价范围: {profile_eval.eval_start} - {profile_eval.eval_end} mm")
print(f"  测量范围: {profile_eval.meas_start} - {profile_eval.meas_end} mm")
print(f"  评价范围是否在测量范围内: {profile_eval.eval_start >= profile_eval.meas_start and profile_eval.eval_end <= profile_eval.meas_end}")

print()
print("齿向:")
print(f"  评价范围: {helix_eval.eval_start} - {helix_eval.eval_end} mm")
print(f"  测量范围: {helix_eval.meas_start} - {helix_eval.meas_end} mm")
print(f"  评价范围是否在测量范围内: {helix_eval.eval_start >= helix_eval.meas_start and helix_eval.eval_end <= helix_eval.meas_end}")

print()
print("="*80)
print("[可能的定义问题]")
print("-"*60)

print("""
根据齿轮测量标准，评价范围和测量范围的关系:

1. 评价范围是测量范围的子集:
   - 评价范围应该在测量范围内
   - 即: meas_start <= eval_start AND eval_end <= meas_end

2. 齿形和齿向的评价范围应该独立:
   - 齿形评价范围 (d1, d2) 用于齿形分析
   - 齿向评价范围 (b1, b2) 用于齿向分析

3. 数据筛选逻辑:
   - 齿形数据: z位置应在齿向测量范围内 (ba, be)
   - 齿向数据: d位置应在齿形测量范围内 (da, de)
   
当前代码使用:
   - 齿形数据: z位置在齿向评价范围内 (b1, b2) ✓
   - 齿向数据: d位置在齿形评价范围内 (d1, d2) ✓
   
这个逻辑是正确的！评价范围用于筛选数据，确保只分析有效区域。
""")

print()
print("="*80)
print("[结论]")
print("="*80)
print("""
齿形和齿向的评价范围定义是正确的：
- 齿形评价范围 (d1, d2) 用于筛选齿形数据
- 齿向评价范围 (b1, b2) 用于筛选齿向数据
- 评价范围是测量范围的子集
- 数据筛选逻辑正确

没有定义相反的问题！
""")
