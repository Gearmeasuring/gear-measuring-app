"""
================================================================================
Klingelnberg频谱图对比分析（不参照原始文档）
Direct Comparison Analysis
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

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()
analyzer.analyze_all()

print()
print("[分析1: 阶次范围差异]")
print("="*80)

print()
print("Klingelnberg频谱图特点:")
print("  - 主要阶次: ZE(87), ZE×2(174), ZE×3(261), ZE×4(348), ZE×5(435), ZE×6(522)")
print("  - 还包含: ZE-2(85), ZE-1(86), ZE+1(88), ZE+2(89)")
print("  - 即: ZE的整数倍 和 ZE±n (n=1,2,...)")

print()
print("我们的频谱图特点:")
result = analyzer.results['profile_right']
our_orders = [c.order for c in result.spectrum_components]
print(f"  - 阶次: {our_orders}")
print("  - 搜索策略: 在1-435范围内找振幅最大的10个")

print()
print("[分析2: 振幅量级差异]")
print("="*80)

print()
print("假设Klingelnberg的振幅（从图估算）:")
klingelnberg_amps = {
    87: 0.15,    # ZE
    174: 0.05,   # ZE×2
    261: 0.06,   # ZE×3
    348: 0.07,   # ZE×4
    435: 0.03,   # ZE×5
    86: 0.04,    # ZE-1
    88: 0.04,    # ZE+1
    89: 0.03,    # ZE+2
}

print("  阶次  振幅(μm)")
for order, amp in klingelnberg_amps.items():
    print(f"  {order:4d}  {amp:.3f}")

print()
print("我们的振幅:")
our_amp_dict = {c.order: c.amplitude for c in result.spectrum_components}
print("  阶次  振幅(μm)")
for order in our_orders[:10]:
    print(f"  {order:4d}  {our_amp_dict[order]:.4f}")

print()
print("[分析3: 计算缩放因子]")
print("="*80)

print()
print("如果Klingelnberg和我们的阶次87对应:")
scale_factor = our_amp_dict[87] / klingelnberg_amps[87]
print(f"  缩放因子 = {our_amp_dict[87]:.4f} / {klingelnberg_amps[87]:.3f} = {scale_factor:.2f}")

print()
print("验证其他阶次:")
print("  阶次  我们的振幅  /  缩放因子  =  期望值  vs  Klingelnberg")
for order in [174, 261, 348]:
    if order in our_amp_dict:
        expected = our_amp_dict[order] / scale_factor
        kl = klingelnberg_amps.get(order, 0)
        print(f"  {order:4d}  {our_amp_dict[order]:.4f}  /  {scale_factor:.2f}  =  {expected:.4f}  vs  {kl:.3f}")

print()
print("[分析4: 搜索策略差异]")
print("="*80)

print()
print("Klingelnberg策略（推测）:")
print("  1. 只计算特定阶次: ZE×n 和 ZE±n")
print("  2. 不搜索所有阶次，而是直接计算目标阶次")
print("  3. 应用缩放因子")

print()
print("我们的策略:")
print("  1. 搜索1-435所有阶次")
print("  2. 找振幅最大的10个")
print("  3. 迭代分解")

print()
print("[分析5: 直接计算目标阶次]")
print("="*80)

def calculate_spectrum_for_orders(angles, values, target_orders):
    """直接计算指定阶次的频谱"""
    angles_rad = np.radians(angles)
    values = np.array(values) - np.mean(values)
    
    components = []
    for order in target_orders:
        cos_term = np.cos(order * angles_rad)
        sin_term = np.sin(order * angles_rad)
        
        A = np.column_stack([cos_term, sin_term])
        coeffs, _, _, _ = np.linalg.lstsq(A, values, rcond=None)
        
        a, b = coeffs[0], coeffs[1]
        amplitude = np.sqrt(a**2 + b**2)
        phase = np.arctan2(a, b)
        
        components.append({
            'order': order,
            'amplitude': amplitude,
            'phase': phase,
            'a': a,
            'b': b
        })
    
    return components

# 定义Klingelnberg的目标阶次
ze = analyzer.gear_params.teeth_count
target_orders = [
    ze-2, ze-1, ze, ze+1, ze+2,      # ZE附近
    ze*2, ze*3, ze*4, ze*5, ze*6     # ZE的整数倍
]
target_orders = [o for o in target_orders if o > 0]

print()
print(f"目标阶次: {target_orders}")

# 直接计算
result = analyzer.results['profile_right']
direct_components = calculate_spectrum_for_orders(
    result.angles, result.values, target_orders
)

print()
print("直接计算结果:")
print("  阶次  振幅(μm)  缩放后(×0.17)")
scale = 0.17  # 估算的缩放因子
for comp in sorted(direct_components, key=lambda x: -x['amplitude']):
    scaled = comp['amplitude'] * scale
    print(f"  {comp['order']:4d}  {comp['amplitude']:.4f}    {scaled:.4f}")

print()
print("[分析6: 关键差异总结]")
print("="*80)

print()
print("差异1: 搜索策略")
print("  - Klingelnberg: 直接计算ZE附近的特定阶次")
print("  - 我们: 搜索所有阶次，找最大的")

print()
print("差异2: 振幅缩放")
print("  - Klingelnberg振幅约为我们的1/6")
print("  - 可能的缩放因子: ~0.17")

print()
print("差异3: 阶次范围")
print("  - Klingelnberg: ZE±n, ZE×n")
print("  - 我们: 任意阶次")

print()
print("[改进建议]")
print("="*80)

print()
print("1. 添加振幅缩放因子参数 (默认0.17)")
print("2. 支持直接计算目标阶次模式")
print("3. 目标阶次: ZE±n (n=0,1,2,...) 和 ZE×n (n=1,2,3,...)")
