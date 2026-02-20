"""
================================================================================
齿轮波纹度算法详细验证
Algorithm Verification
================================================================================

根据用户要求的算法：

1. 从0度到360度合并的曲线中移除已提取的最大阶次正弦波
2. 对剩余信号重复上述过程，直到提取出第十个较大的阶次
3. 最终第十较大阶次的正弦波被分解并计算，得出频谱图像
4. 评价方式的高阶大于等于ZE=波数，ZE为总齿数
5. 0到360度之间有多少个波，0到360为一周，一周中有多少个波
6. 如有87个波，阶次，频率为87

================================================================================
"""

import sys
import os
import numpy as np
import math
import matplotlib.pyplot as plt

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import RippleWavinessAnalyzer

print("="*80)
print("齿轮波纹度算法详细验证")
print("="*80)

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

print()
print("[齿轮参数]")
print(f"  齿数 ZE = {analyzer.gear_params.teeth_count}")
print(f"  模数 m = {analyzer.gear_params.module} mm")
print(f"  压力角 α = {analyzer.gear_params.pressure_angle}°")
print(f"  螺旋角 β = {analyzer.gear_params.helix_angle}°")
print(f"  节圆直径 D₀ = {analyzer.gear_params.pitch_diameter:.3f} mm")
print(f"  基圆直径 db = {analyzer.gear_params.base_diameter:.3f} mm")
print(f"  节距角 = {analyzer.gear_params.pitch_angle:.4f}°")

print()
print("="*80)
print("步骤1: 分析右齿形 (profile_right)")
print("="*80)

result = analyzer.analyze_profile('right', verbose=True)

print()
print("="*80)
print("算法验证要点")
print("="*80)

print()
print("1. 0到360度闭合曲线:")
print(f"   ✓ 数据点数: {len(result.angles)}")
print(f"   ✓ 角度范围: [{result.angles.min():.2f}°, {result.angles.max():.2f}°]")
print(f"   ✓ 偏差范围: [{result.values.min():.4f}, {result.values.max():.4f}] μm")

print()
print("2. 迭代正弦波分解 (10个周期):")
print("   " + "-"*60)
col1, col2, col3, col4, col5 = "周期", "阶次", "振幅(um)", "相位(deg)", "类型"
print(f"   {col1:>4} {col2:>6} {col3:>12} {col4:>10} {col5:>12}")
print("   " + "-"*60)

for i, comp in enumerate(result.spectrum_components):
    high_order = "★高阶(≥ZE)" if comp.order >= analyzer.gear_params.teeth_count else "低阶(<ZE)"
    print(f"   {i+1:>4} {comp.order:>6} {comp.amplitude:>12.4f} {np.degrees(comp.phase):>10.1f} {high_order:>14}")

print()
print("3. 高阶波纹度评价 (阶次 ≥ ZE):")
print(f"   ✓ ZE = 总齿数 = {analyzer.gear_params.teeth_count}")
print(f"   ✓ 高阶波数列表: {result.high_order_waves}")
print(f"   ✓ 总振幅 W = {result.high_order_amplitude:.4f} μm")
print(f"   ✓ RMS = {result.high_order_rms:.4f} μm")

print()
print("="*80)
print("算法说明详解")
print("="*80)

print()
print("【阶次和频率的关系】")
print("-"*80)
print("阶次 = 0-360度一周中的波数")
print()
print("例如:")
print("  - 阶次 = 87  → 一周87个波 → 频率 = 87")
print("  - 阶次 = 174 → 一周174个波 → 频率 = 174")
print("  - 阶次 = 261 → 一周261个波 → 频率 = 261")
print()
print("数学关系:")
print("  f = k / T")
print("  其中 T = 360° = 1周")
print("  所以 f = k (周^-1)")
print()
print("正弦波模型:")
print("  y = C × sin(k×θ + φ)")
print("  或")
print("  y = A×cos(k×θ) + B×sin(k×θ)")
print()
print("其中:")
print("  k = 阶次（波数）")
print("  C = 振幅 = √(A² + B²)")
print("  φ = 相位 = arctan2(A, B)")
print("  θ = 角度 (弧度)")

print()
print("【迭代分解算法步骤】")
print("-"*80)
print("输入: 0-360度闭合曲线 (angles, values)")
print("输出: 10个最大振幅的频谱分量")
print()
print("算法流程:")
print()
print("  初始化:")
print("    residual = values - mean(values)  (去除直流分量)")
print("    components = []")
print("    extracted_orders = set()")
print()
print("  周期 1:")
print("    1. 在1-435范围内搜索所有未提取的阶次")
print("    2. 对每个阶次用最小二乘法拟合正弦波")
print("    3. 找到振幅最大的阶次 (87, 振幅=0.8759)")
print("    4. 记录该分量到 components")
print("    5. 从 residual 中减去该正弦波")
print("    6. 标记 87 为已提取")
print()
print("  周期 2:")
print("    1. 搜索剩余未提取的阶次（排除87）")
print("    2. 找到振幅最大的阶次 (261, 振幅=0.6485)")
print("    3. 记录并从 residual 中减去")
print()
print("  ... 重复直到 ...")
print()
print("  周期 10:")
print("    提取第10个最大阶次 (64, 振幅=0.3747)")
print()
print("完成:")
print("  components 包含10个频谱分量")
print("  振幅按从大到小排序")

print()
print("【高阶波纹度评价】")
print("-"*80)
print("定义:")
print("  高阶分量 = 阶次 ≥ ZE 的分量")
print(f"  ZE = {analyzer.gear_params.teeth_count} (总齿数)")
print()
print("计算:")
print("  1. 筛选: 从10个分量中选出阶次≥87的")
print(f"  2. 高阶波数列表: {result.high_order_waves}")
print("  3. 总振幅 W = Σ(高阶分量振幅)")
print(f"  4. W = {result.high_order_amplitude:.4f} μm")
print("  5. 重构高阶信号")
print("  6. RMS = √(mean(重构信号²))")
print(f"  7. RMS = {result.high_order_rms:.4f} μm")

print()
print("="*80)
print("完整的算法实现请参考:")
print("  ripple_waviness_analyzer.py")
print()
print("算法文档:")
print("  波纹度算法完整说明.md")
print("="*80)
