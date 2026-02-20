#!/usr/bin/env python3
"""
调试脚本：对比单个齿和平均曲线的频谱分析
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

from gear_analysis_refactored.utils.file_parser import parse_mka_file
from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings, SineFitParams

# 设置输出编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 查找MKA文件
mka_files = [
    "263751-018-WAV.mka",
    "004-xiaoxiao1.mka"
]

mka_file = None
for file in mka_files:
    if os.path.exists(file):
        mka_file = file
        break

if mka_file is None:
    print("错误：未找到MKA文件")
    sys.exit(1)

print(f"使用MKA文件: {mka_file}")

# 解析MKA文件
try:
    mka_data = parse_mka_file(mka_file)
    print(f"MKA文件解析成功")
except Exception as e:
    print(f"解析MKA文件失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 提取数据
gear_data = mka_data['gear_data']
profile_data = mka_data['profile_data']
flank_data = mka_data['flank_data']

# 创建报告生成器
settings = RippleSpectrumSettings()
report = KlingelnbergRippleSpectrumReport(settings)

# 分析Profile Right数据
print("\n=== 分析 Profile Right：单个齿 vs 平均曲线 ===")
profile_right_data = profile_data.get('right', {})

if profile_right_data:
    # 获取前5个齿
    tooth_ids = sorted(profile_right_data.keys())[:5]
    print(f"分析前5个齿: {tooth_ids}")

    # 对每个齿单独进行频谱分析
    single_tooth_results = []
    for tooth_id in tooth_ids:
        tooth_data = profile_right_data[tooth_id]
        vals = report._values_to_um(np.array(tooth_data, dtype=float))
        
        # 去趋势
        detrended = vals - float(np.mean(vals))
        detrended = report._end_match(detrended)
        
        # 进行频谱分析
        ze = gear_data.get('teeth', 87)
        n = len(detrended)
        x = np.linspace(0.0, 2.0 * np.pi, n, dtype=float)
        
        # 测试ZE倍数阶次
        ze_multiples = [87, 174, 261, 348, 435]
        tooth_amplitudes = {}
        
        for order in ze_multiples:
            try:
                sin_x = np.sin(float(order) * x)
                cos_x = np.cos(float(order) * x)
                A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
                
                coeffs, _, _, _ = np.linalg.lstsq(A, detrended, rcond=None)
                a, b, c = coeffs
                amplitude = float(np.sqrt(a * a + b * b))
                
                tooth_amplitudes[order] = amplitude
            except Exception as e:
                pass
        
        single_tooth_results.append((tooth_id, tooth_amplitudes))
        print(f"\n齿 {tooth_id}:")
        for order in ze_multiples:
            if order in tooth_amplitudes:
                print(f"  阶次 {order}（{order/ze:.1f}ZE）: 幅值 = {tooth_amplitudes[order]:.6f} μm")

    # 计算所有齿的平均曲线
    print(f"\n=== 计算平均曲线 ===")
    all_tooth_data = []
    for tooth_id in tooth_ids:
        tooth_data = profile_right_data[tooth_id]
        vals = report._values_to_um(np.array(tooth_data, dtype=float))
        detrended = vals - float(np.mean(vals))
        detrended = report._end_match(detrended)
        all_tooth_data.append(detrended)
    
    # 对齐到最小长度
    min_len = min(len(d) for d in all_tooth_data)
    aligned_data = [d[:min_len] for d in all_tooth_data]
    avg_data = np.mean(aligned_data, axis=0)
    
    print(f"平均曲线长度: {len(avg_data)}")
    print(f"平均曲线范围: [{np.min(avg_data):.3f}, {np.max(avg_data):.3f}] μm")
    
    # 对平均曲线进行频谱分析
    print(f"\n=== 平均曲线频谱分析 ===")
    n = len(avg_data)
    x = np.linspace(0.0, 2.0 * np.pi, n, dtype=float)
    
    avg_amplitudes = {}
    for order in ze_multiples:
        try:
            sin_x = np.sin(float(order) * x)
            cos_x = np.cos(float(order) * x)
            A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
            
            coeffs, _, _, _ = np.linalg.lstsq(A, avg_data, rcond=None)
            a, b, c = coeffs
            amplitude = float(np.sqrt(a * a + b * b))
            
            avg_amplitudes[order] = amplitude
        except Exception as e:
            pass
    
    print(f"平均曲线:")
    for order in ze_multiples:
        if order in avg_amplitudes:
            print(f"  阶次 {order}（{order/ze:.1f}ZE）: 幅值 = {avg_amplitudes[order]:.6f} μm")
    
    # 对比结果
    print(f"\n=== 对比结果 ===")
    print(f"{'阶次':<10} {'平均曲线':<15} {'单个齿范围':<30} {'差异'}")
    print("-" * 70)
    for order in ze_multiples:
        if order in avg_amplitudes:
            avg_amp = avg_amplitudes[order]
            single_amps = [tooth_amplitudes.get(order, 0) for _, tooth_amplitudes in single_tooth_results]
            min_amp = min(single_amps)
            max_amp = max(single_amps)
            mean_amp = np.mean(single_amps)
            
            print(f"{order:<10} {avg_amp:<15.6f} [{min_amp:.6f}, {max_amp:.6f}] (平均: {mean_amp:.6f}) {'不同' if abs(avg_amp - mean_amp) > 0.001 else '相似'}")

print("\n=== 调试完成 ===")
