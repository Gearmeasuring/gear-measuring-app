"""
================================================================================
检查评价范围与数据点的对应关系
Check Evaluation Range vs Data Points Mapping
================================================================================
"""

import sys
import os
import numpy as np
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import RippleWavinessAnalyzer, InvoluteCalculator

print("="*80)
print("检查评价范围与数据点的对应关系")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

profile_eval = analyzer.reader.profile_eval_range

print()
print("[齿形评价范围]")
print("-"*80)
print(f"d1 (起评点) = {profile_eval.eval_start} mm")
print(f"d2 (终评点) = {profile_eval.eval_end} mm")
print(f"da (测量起点) = {profile_eval.meas_start} mm")
print(f"de (测量终点) = {profile_eval.meas_end} mm")

print()
print("="*80)
print("[分析：数据点如何映射到评价范围]")
print("="*80)

# 获取齿形数据
profile_data = analyzer.reader.profile_data.get('right', {})
tooth1_data = profile_data.get(1, {})

# 取z=21.0的数据
z_pos = 21.0
values = tooth1_data[z_pos]
num_points = len(values)

print(f"\n齿1 z={z_pos}mm:")
print(f"  数据点数: {num_points}")

# 计算展长
involute_calc = InvoluteCalculator(analyzer.gear_params)

d1 = profile_eval.eval_start
d2 = profile_eval.eval_end
da = profile_eval.meas_start
de = profile_eval.meas_end

s_d1 = involute_calc.calculate_roll_length(d1)
s_d2 = involute_calc.calculate_roll_length(d2)
s_da = involute_calc.calculate_roll_length(da)
s_de = involute_calc.calculate_roll_length(de)

print(f"\n展长计算:")
print(f"  s(da={da}mm) = {s_da:.4f} mm (测量起点)")
print(f"  s(d1={d1}mm) = {s_d1:.4f} mm (起评点)")
print(f"  s(d2={d2}mm) = {s_d2:.4f} mm (终评点)")
print(f"  s(de={de}mm) = {s_de:.4f} mm (测量终点)")

# 计算展长角度
xi_d1 = involute_calc.calculate_roll_angle_degrees(d1)
xi_d2 = involute_calc.calculate_roll_angle_degrees(d2)

print(f"\n展长角度:")
print(f"  xi(d1) = {xi_d1:.4f} deg")
print(f"  xi(d2) = {xi_d2:.4f} deg")
print(f"  角度跨度 = {xi_d2 - xi_d1:.4f} deg")

# 关键点：数据点是如何分布的？
print()
print("="*80)
print("[关键问题：数据点分布]")
print("="*80)

print(f"""
当前算法逻辑:
  1. 数据点从测量文件读取，包含整个测量范围
  2. 算法假设数据点从起评点到终评点均匀分布
  3. 计算: roll_lengths = linspace(s(d1), s(d2), num_points)

但实际情况:
  - 测量数据可能包含测量起点到测量终点的所有点
  - 评价范围只是测量范围的子集
  - 如果数据点包含测量范围外的点，就会有问题
""")

# 检查实际的数据范围
print()
print("[检查实际数据范围]")
print("-"*80)

# 假设数据点从测量起点到测量终点均匀分布
s_meas_start = s_da
s_meas_end = s_de
s_eval_start = s_d1
s_eval_end = s_d2

print(f"测量范围展长: [{s_meas_start:.4f}, {s_meas_end:.4f}] mm")
print(f"评价范围展长: [{s_eval_start:.4f}, {s_eval_end:.4f}] mm")

# 计算评价范围在数据点中的索引
if s_meas_end > s_meas_start:
    idx_start = int((s_eval_start - s_meas_start) / (s_meas_end - s_meas_start) * num_points)
    idx_end = int((s_eval_end - s_meas_start) / (s_meas_end - s_meas_start) * num_points)
else:
    idx_start = 0
    idx_end = num_points

print(f"\n评价范围对应的索引:")
print(f"  起始索引: {idx_start}")
print(f"  结束索引: {idx_end}")
print(f"  评价范围内的点数: {idx_end - idx_start}")
print(f"  总点数: {num_points}")

# 检查这些数据点
print(f"\n评价范围内的数据点 (索引{idx_start}到{idx_end}):")
print(f"  值范围: [{values[idx_start]:.4f}, {values[idx_end-1]:.4f}] um")

print(f"\n测量范围外的数据点:")
if idx_start > 0:
    print(f"  索引0到{idx_start-1}: {values[:idx_start]}")
if idx_end < num_points:
    print(f"  索引{idx_end}到{num_points-1}: {values[idx_end:]}")

print()
print("="*80)
print("[问题发现]")
print("="*80)

print(f"""
问题:
  当前代码直接使用所有数据点，假设它们都在评价范围内。
  但实际上，测量数据可能包含评价范围外的点。

解决方案:
  需要根据展长角度筛选数据点，只使用评价范围内的点。

具体步骤:
  1. 计算每个数据点对应的展长
  2. 筛选展长在[s(d1), s(d2)]范围内的点
  3. 只使用这些点进行极角计算
""")

print()
print("="*80)
print("[验证：查看原始MKA文件中的数据]")
print("="*80)

# 读取原始文件查看数据点数量
with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
    content = f.read()

import re
pattern = re.compile(r'Profil:\s*Zahn-Nr\.:\s*1b\s*rechts.*?/\s*(\d+)\s*Werte', re.IGNORECASE)
match = pattern.search(content)
if match:
    num_werte = int(match.group(1))
    print(f"MKA文件中标注的数据点数: {num_werte}")
    print(f"实际读取的数据点数: {num_points}")
    print(f"是否一致: {'是' if num_werte == num_points else '否'}")

print()
print("="*80)
print("[结论]")
print("="*80)
print("""
需要修改代码，确保只使用评价范围内的数据点:

当前问题:
  - 代码假设所有数据点都在评价范围内
  - 实际上数据点可能包含测量范围外的点
  - 导致齿顶/齿根的大负值被包含进来

修复方案:
  - 根据展长角度筛选数据点
  - 只使用评价范围内的点进行计算
""")
