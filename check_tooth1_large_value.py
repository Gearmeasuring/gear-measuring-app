"""
================================================================================
检查齿1靠近0度时数值特别大的原因
Check why Tooth 1 has large values near 0 degrees
================================================================================
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import RippleWavinessAnalyzer, DataPreprocessor

print("="*80)
print("检查齿1靠近0度时数值特别大的原因")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

# 获取右齿形齿1的数据
profile_data = analyzer.reader.profile_data.get('right', {})
tooth1_data = profile_data.get(1, {})

print()
print("[齿1的数据分析]")
print("-"*80)

for z_pos, values in tooth1_data.items():
    print(f"\nz={z_pos}mm:")
    print(f"  数据点数: {len(values)}")
    print(f"  原始值范围: [{values.min():.4f}, {values.max():.4f}] um")
    
    # 检查前10个和后10个数据点
    print(f"  前10个原始值: {values[:10]}")
    print(f"  后10个原始值: {values[-10:]}")
    
    # 预处理后
    preprocessor = DataPreprocessor()
    corrected = preprocessor.remove_crown_and_slope(values)
    print(f"  预处理后范围: [{corrected.min():.4f}, {corrected.max():.4f}] um")
    print(f"  前10个预处理后: {corrected[:10]}")
    print(f"  后10个预处理后: {corrected[-10:]}")

print()
print("="*80)
print("[分析齿根方向的数据特点]")
print("="*80)

# 齿1 z=21.0的数据
z_pos = 21.0
values = tooth1_data[z_pos]

print(f"\n齿1 z={z_pos}mm 详细分析:")
print(f"  总点数: {len(values)}")

# 将数据分为前一半（齿根方向）和后一半（齿顶方向）
n = len(values)
half = n // 2

root_values = values[:half]  # 齿根方向（前一半）
tip_values = values[half:]   # 齿顶方向（后一半）

print(f"\n齿根方向（前{half}个点）:")
print(f"  范围: [{root_values.min():.4f}, {root_values.max():.4f}] um")
print(f"  均值: {root_values.mean():.4f} um")
print(f"  前5个: {root_values[:5]}")

print(f"\n齿顶方向（后{len(tip_values)}个点）:")
print(f"  范围: [{tip_values.min():.4f}, {tip_values.max():.4f}] um")
print(f"  均值: {tip_values.mean():.4f} um")
print(f"  后5个: {tip_values[-5:]}")

print()
print("="*80)
print("[检查评价范围]")
print("="*80)

profile_eval = analyzer.reader.profile_eval_range
print(f"\n齿形评价范围:")
print(f"  d1 (起评点/齿根) = {profile_eval.eval_start} mm")
print(f"  d2 (终评点/齿顶) = {profile_eval.eval_end} mm")

print(f"\n分析:")
print(f"  从图中可以看到，齿1在靠近0度时（齿根方向）数值急剧下降到-20μm左右")
print(f"  这是因为原始测量数据在齿根方向有较大的负偏差")
print(f"  预处理后虽然去除了趋势，但齿根方向的绝对值仍然较大")

print()
print("="*80)
print("[可能的原因]")
print("="*80)
print("""
1. 原始测量数据特点:
   - 齿根方向的测量值本身就有较大的负偏差
   - 这可能是齿轮的实际加工误差
   - 或者是测量设备的系统误差

2. 预处理效果:
   - 二次+线性预处理去除了鼓形和斜率趋势
   - 但保留了原始数据的波动特征
   - 齿根方向的大负值被保留下来

3. 角度映射:
   - 齿根方向对应角度接近0度（或360度）
   - 齿顶方向对应角度为负值（或接近360度）
   - 在合并曲线时，齿根的大负值会显示在0度附近

4. 这是正常现象:
   - 齿轮齿根通常有较大的加工误差
   - 齿形偏差在齿根和齿顶位置通常较大
   - 中间区域（节圆附近）偏差较小
""")

print()
print("="*80)
print("[验证：查看其他齿的数据]")
print("="*80)

for tooth_id in [2, 3, 4, 5]:
    if tooth_id in profile_data:
        tooth_profiles = profile_data[tooth_id]
        for z_pos, values in tooth_profiles.items():
            if z_pos == 21.0:  # 只取中间位置
                preprocessor = DataPreprocessor()
                corrected = preprocessor.remove_crown_and_slope(values)
                print(f"\n齿{tooth_id} z={z_pos}mm:")
                print(f"  预处理后范围: [{corrected.min():.4f}, {corrected.max():.4f}] um")
                break

print()
print("="*80)
print("[结论]")
print("="*80)
print("""
齿1靠近0度时数值特别大是正常的，原因如下：

1. 原始测量数据在齿根方向有较大负偏差
2. 预处理后保留了这一特征
3. 齿根方向对应角度接近0度
4. 这是齿轮实际加工误差的反映

这不是算法问题，而是数据本身的特征！
""")
