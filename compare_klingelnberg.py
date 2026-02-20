"""
================================================================================
Klingelnberg频谱图对比分析
Comparison with Klingelnberg Spectrum
================================================================================
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import RippleWavinessAnalyzer

print("="*80)
print("Klingelnberg频谱图对比分析")
print("="*80)

# Klingelnberg标准数据 (从PDF读取)
klingelnberg_data = {
    'profile_right': {
        'orders': [87, 348, 261, 174, 86, 88, 435, 522, 89],
        'amplitudes': [0.15, 0.07, 0.06, 0.05, 0.04, 0.04, 0.03, 0.03, 0.03]
    },
    'profile_left': {
        'orders': [261, 87, 174, 435, 86],
        'amplitudes': [0.14, 0.14, 0.05, 0.04, 0.03]
    },
    'helix_right': {
        'orders': [87, 174, 261, 88, 89, 86],
        'amplitudes': [0.09, 0.10, 0.05, 0.04, 0.04, 0.03]
    },
    'helix_left': {
        'orders': [87, 89, 86, 88, 174, 85, 348, 261],
        'amplitudes': [0.12, 0.07, 0.06, 0.05, 0.04, 0.04, 0.03, 0.02]
    }
}

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()
analyzer.analyze_all()

print()
print("[对比分析 - Profile Right (右齿形)]")
print("="*80)

result_name = 'profile_right'
our_result = analyzer.results[result_name]

print()
print("Klingelnberg标准:")
print("  阶次:  ", klingelnberg_data[result_name]['orders'])
print("  振幅:  ", [f"{a:.4f}" for a in klingelnberg_data[result_name]['amplitudes']])

print()
print("我们的计算:")
our_orders = [c.order for c in our_result.spectrum_components]
our_amps = [c.amplitude for c in our_result.spectrum_components]
print("  阶次:  ", our_orders)
print("  振幅:  ", [f"{a:.4f}" for a in our_amps])

print()
print("差异分析:")
print("-"*80)
print("1. 振幅量级差异:")
print(f"   Klingelnberg最大: {max(klingelnberg_data[result_name]['amplitudes']):.4f} μm")
print(f"   我们的最大:  {max(our_amps):.4f} μm")
print(f"   比例: {max(our_amps)/max(klingelnberg_data[result_name]['amplitudes']):.1f}x")

print()
print("2. 阶次范围差异:")
print("   Klingelnberg: ZE(87)附近的阶次")
print("   我们的:  搜索最大10个振幅的阶次(1-435)")

print()
print("3. 可能的原因:")
print("   a) 振幅缩放因子 (Klingelnberg可能有缩放)")
print("   b) 数据预处理方法不同")
print("   c) 搜索范围和策略不同")
print("   d) 角度合成方式不同")

print()
print("[Klingelnberg标准详细数据]")
print("="*80)
for name, data in klingelnberg_data.items():
    print(f"\n{name}:")
    print(f"  阶次:    {data['orders']}")
    print(f"  振幅(μm): {[f'{a:.3f}' for a in data['amplitudes']]}")
    print(f"  总计: {sum(data['amplitudes']):.3f} μm")

print()
print("[我们的计算 - 高阶筛选结果]")
print("="*80)
for name, result in analyzer.results.items():
    print(f"\n{name}:")
    print(f"  高阶波数:  {result.high_order_waves}")
    print(f"  高阶振幅:  {[f'{c.amplitude:.4f}' for c in result.spectrum_components if c.order >= analyzer.gear_params.teeth_count]}")
    print(f"  总振幅 W: {result.high_order_amplitude:.4f} μm")

print()
print("[搜索策略对比]")
print("="*80)
print()
print("Klingelnberg:")
print("  - 主要显示 ZE (87) 附近的阶次")
print("  - 85, 86, 87, 88, 89, 174, 261, 348, 435, 522")
print("  - 这些是 ZE×n, ZE±1, ZE±2")

print()
print("我们的:")
print("  - 搜索 1-435 所有阶次")
print("  - 找到振幅最大的10个")
print("  - 然后从中筛选阶次≥ZE的")

print()
print("="*80)
print("可能的改进方向:")
print("="*80)
print("1. 添加振幅缩放因子 (可能是 1/√ZE 或 0.1)")
print("2. 重点搜索 ZE 附近的阶次 (ZE±n, ZE×n)")
print("3. 检查数据预处理是否与Klingelnberg一致")
print("4. 检查极角计算方式")
print("="*80)
