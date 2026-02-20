#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接拟合目标阶次的波纹度分析

策略：
1. 不使用迭代分解
2. 直接对每个目标阶次进行最小二乘拟合
3. 测试不同的预处理参数
"""

import numpy as np
from scipy.optimize import least_squares
import logging
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file

logging.basicConfig(level=logging.WARNING)

# Klingelnberg参考数据
KLINGELNBERG_SAMPLE1 = {
    'right_profile': {87: 0.47, 174: 0.17, 261: 0.09, 348: 0.06, 435: 0.05, 522: 0.06, 609: 0.04, 696: 0.04},
    'left_profile': {87: 0.66, 174: 0.24, 261: 0.09, 348: 0.06, 435: 0.05, 522: 0.06, 609: 0.04, 696: 0.04},
    'right_helix': {87: 0.28, 174: 0.12, 261: 0.08, 348: 0.05, 435: 0.04, 522: 0.04, 609: 0.03, 696: 0.03},
    'left_helix': {87: 0.32, 174: 0.14, 261: 0.09, 348: 0.06, 435: 0.04, 522: 0.04, 609: 0.03, 696: 0.03}
}

KLINGELNBERG_SAMPLE2 = {
    'right_profile': {26: 0.19, 52: 0.07, 78: 0.10, 104: 0.05, 130: 0.05, 156: 0.06, 182: 0.08},
    'left_profile': {22: 0.03, 26: 0.24, 44: 0.04, 52: 0.19, 78: 0.09, 104: 0.16, 130: 0.09, 156: 0.06, 182: 0.08},
    'right_helix': {26: 0.03, 52: 0.06, 78: 0.03, 141: 0.03, 156: 0.02},
    'left_helix': {26: 0.07, 48: 0.03, 52: 0.08, 78: 0.04, 104: 0.03, 130: 0.02, 141: 0.04, 182: 0.02}
}


def involute_angle(r, rb):
    ratio = np.clip(rb / np.where(r > 0, r, 1e-10), -1, 1)
    alpha_r = np.arccos(ratio)
    return np.tan(alpha_r) - alpha_r


def prepare_profile_data(profile_dict, alpha_deg=20.0):
    profiles = []
    for tooth_num in sorted(profile_dict.keys()):
        data = profile_dict[tooth_num]
        n = len(data) // 2
        r = np.array(data[:n])
        dev = np.array(data[n:])
        rb = r * np.cos(np.radians(alpha_deg))
        profiles.append({
            'r': r, 'dev': dev,
            'rb': rb[0] if len(rb) > 0 else r[0] * np.cos(np.radians(alpha_deg))
        })
    return profiles


def prepare_helix_data(flank_dict):
    flank_lines = []
    for tooth_num in sorted(flank_dict.keys()):
        data = flank_dict[tooth_num]
        n = len(data) // 2
        z = np.array(data[:n])
        dev = np.array(data[n:])
        flank_lines.append({'z': z, 'dev': dev})
    return flank_lines


def merge_profile_curves(profiles, tooth_positions, ZE):
    all_phi = []
    all_dev = []
    rb = profiles[0]['rb']
    
    for i, (profile, pos) in enumerate(zip(profiles, tooth_positions)):
        r = profile['r']
        dev = profile['dev']
        xi = involute_angle(r, rb)
        tau = 2 * np.pi * pos / ZE
        phi = -xi + tau
        all_phi.append(phi)
        all_dev.append(dev)
    
    all_phi = np.concatenate(all_phi)
    all_dev = np.concatenate(all_dev)
    sort_idx = np.argsort(all_phi)
    return all_phi[sort_idx], all_dev[sort_idx]


def merge_helix_curves(flank_lines, tooth_positions, ZE, m, beta):
    all_phi = []
    all_dev = []
    D0 = m * ZE / np.cos(beta) if np.cos(beta) != 0 else m * ZE * 1.1
    
    for i, (flank, pos) in enumerate(zip(flank_lines, tooth_positions)):
        z = flank['z']
        dev = flank['dev']
        delta_phi = 2 * z * np.tan(beta) / D0
        tau = 2 * np.pi * pos / ZE
        phi = -delta_phi + tau
        all_phi.append(phi)
        all_dev.append(dev)
    
    all_phi = np.concatenate(all_phi)
    all_dev = np.concatenate(all_dev)
    sort_idx = np.argsort(all_phi)
    return all_phi[sort_idx], all_dev[sort_idx]


def remove_trend_per_tooth(phi, dev, poly_order=3):
    dphi = np.diff(phi)
    breaks = np.where(dphi < -np.pi)[0] + 1
    
    segments_phi = []
    segments_dev = []
    start = 0
    for break_idx in breaks:
        segments_phi.append(phi[start:break_idx])
        segments_dev.append(dev[start:break_idx])
        start = break_idx
    segments_phi.append(phi[start:])
    segments_dev.append(dev[start:])
    
    processed_phi = []
    processed_dev = []
    
    for seg_phi, seg_dev in zip(segments_phi, segments_dev):
        if len(seg_phi) > poly_order + 1:
            coeffs = np.polyfit(seg_phi, seg_dev, poly_order)
            trend = np.polyval(coeffs, seg_phi)
            residual = seg_dev - trend
            processed_phi.append(seg_phi)
            processed_dev.append(residual)
        else:
            processed_phi.append(seg_phi)
            processed_dev.append(seg_dev - np.mean(seg_dev))
    
    phi_out = np.concatenate(processed_phi)
    dev_out = np.concatenate(processed_dev)
    sort_idx = np.argsort(phi_out)
    
    return phi_out[sort_idx], dev_out[sort_idx]


def fit_sine_at_order(phi, dev, order, ZE):
    """对特定阶次进行精确拟合"""
    freq = order / ZE
    
    def sine_func(params):
        amp, phase = params
        return dev - amp * np.sin(freq * phi + phase)
    
    guess_amp = np.std(dev) * np.sqrt(2)
    
    result = least_squares(
        sine_func,
        [guess_amp, 0.0],
        bounds=([0, -np.pi], [np.inf, np.pi]),
        method='trf'
    )
    
    return result.x[0], result.x[1]


def fit_all_orders_simultaneously(phi, dev, ZE, target_orders):
    """
    同时拟合所有目标阶次
    
    使用多变量最小二乘拟合
    """
    n_orders = len(target_orders)
    
    def multi_sine_func(params):
        # params = [amp1, phase1, amp2, phase2, ...]
        residual = dev.copy()
        for i, order in enumerate(target_orders):
            freq = order / ZE
            amp = params[2*i]
            phase = params[2*i + 1]
            residual = residual - amp * np.sin(freq * phi + phase)
        return residual
    
    # 初始猜测
    x0 = []
    for order in target_orders:
        amp, phase = fit_sine_at_order(phi, dev, order, ZE)
        x0.extend([amp, phase])
    
    # 边界
    lb = [0, -np.pi] * n_orders
    ub = [np.inf, np.pi] * n_orders
    
    result = least_squares(
        multi_sine_func,
        x0,
        bounds=(lb, ub),
        method='trf',
        ftol=1e-10,
        xtol=1e-10,
        max_nfev=1000
    )
    
    # 提取结果
    spectrum = {}
    for i, order in enumerate(target_orders):
        spectrum[order] = result.x[2*i]
    
    return spectrum


def analyze_with_direct_fitting(mka_file, sample_name, klingelnberg_ref, poly_order=3):
    print(f"\n{'='*80}")
    print(f"直接拟合目标阶次分析: {sample_name}")
    print(f"预处理多项式阶数: {poly_order}")
    print(f"{'='*80}\n")
    
    try:
        mka_data = parse_mka_file(mka_file)
    except Exception as e:
        print(f"解析失败: {e}")
        return None
    
    gear_data = mka_data.get('gear_data', {})
    ZE = int(gear_data.get('teeth', gear_data.get('ZE', 0)))
    m = float(gear_data.get('module', gear_data.get('m', 0)))
    alpha = float(gear_data.get('alpha', 20.0))
    beta = np.radians(float(gear_data.get('beta', 0.0)))
    
    print(f"\n齿轮参数:")
    print(f"  齿数 ZE = {ZE}")
    print(f"  模数 m = {m}")
    print(f"  压力角 α = {alpha}°")
    print(f"  螺旋角 β = {np.degrees(beta):.1f}°")
    
    if ZE == 0:
        print("错误: 无法获取齿数")
        return None
    
    total_error = []
    profile_data = mka_data.get('profile_data', {})
    flank_data = mka_data.get('flank_data', {})
    
    for surface_name, surface_key, data_type in [
        ('Right Profile', 'right_profile', 'profile'),
        ('Left Profile', 'left_profile', 'profile'),
        ('Right Helix', 'right_helix', 'helix'),
        ('Left Helix', 'left_helix', 'helix')
    ]:
        print(f"\n{surface_name} ({surface_key}):")
        
        if data_type == 'profile':
            side = 'right' if 'right' in surface_key else 'left'
            raw_profiles = profile_data.get(side, {})
            if not raw_profiles:
                print(f"  无数据")
                continue
            profiles = prepare_profile_data(raw_profiles, alpha)
            tooth_positions = list(range(len(profiles)))
            phi, dev = merge_profile_curves(profiles, tooth_positions, ZE)
        else:
            side = 'right' if 'right' in surface_key else 'left'
            raw_flanks = flank_data.get(side, {})
            if not raw_flanks:
                print(f"  无数据")
                continue
            flank_lines = prepare_helix_data(raw_flanks)
            tooth_positions = list(range(len(flank_lines)))
            phi, dev = merge_helix_curves(flank_lines, tooth_positions, ZE, m, beta)
        
        # 预处理
        phi_proc, dev_proc = remove_trend_per_tooth(phi, dev, poly_order)
        
        # 获取参考值和目标阶次
        ref = klingelnberg_ref.get(surface_key, {})
        target_orders = list(ref.keys())
        
        # 同时拟合所有目标阶次
        spectrum = fit_all_orders_simultaneously(phi_proc, dev_proc, ZE, target_orders)
        
        print(f"\n  {'阶次':<8} {'我们的结果':<12} {'Klingelnberg':<12} {'误差':<10} {'状态'}")
        print(f"  {'-'*60}")
        
        errors = []
        for order in sorted(ref.keys()):
            our_val = spectrum.get(order, 0)
            ref_val = ref[order]
            
            if ref_val > 0:
                error_pct = abs(our_val - ref_val) / ref_val * 100
                errors.append(error_pct)
                
                if error_pct < 15:
                    status = "✅"
                elif error_pct < 30:
                    status = "✓"
                elif error_pct < 50:
                    status = "⚠"
                else:
                    status = "✗"
                
                print(f"  {order:<8} {our_val:<12.4f} {ref_val:<12.2f} {error_pct:<10.1f} % {status}")
        
        if errors:
            avg_error = np.mean(errors)
            total_error.append(avg_error)
            print(f"\n  平均误差: {avg_error:.1f}%")
    
    if total_error:
        overall_error = np.mean(total_error)
        print(f"\n{'='*80}")
        print(f"样本平均误差: {overall_error:.1f}%")
        print(f"{'='*80}")
        return overall_error
    
    return None


def main():
    print("="*80)
    print("直接拟合目标阶次的波纹度分析")
    print("="*80)
    print("\n策略：")
    print("1. 不使用迭代分解")
    print("2. 同时拟合所有目标阶次")
    print("3. 测试不同的预处理参数")
    
    # 测试不同预处理阶数
    for poly_order in [2, 3]:
        print(f"\n\n{'#'*80}")
        print(f"# 预处理多项式阶数: {poly_order}")
        print(f"{'#'*80}")
        
        # 分析样本1
        error1 = analyze_with_direct_fitting(
            "263751-018-WAV.mka",
            "样本1: 263751-018-WAV (87齿)",
            KLINGELNBERG_SAMPLE1,
            poly_order=poly_order
        )
        
        # 分析样本2
        error2 = analyze_with_direct_fitting(
            "004-xiaoxiao1.mka",
            "样本2: 004-xiaoxiao1 (26齿)",
            KLINGELNBERG_SAMPLE2,
            poly_order=poly_order
        )
        
        print(f"\n{'='*80}")
        print(f"预处理阶数 {poly_order} 对比总结")
        print(f"{'='*80}")
        print(f"样本1 (87齿): 误差 = {error1:.1f}%" if error1 else "样本1: 分析失败")
        print(f"样本2 (26齿): 误差 = {error2:.1f}%" if error2 else "样本2: 分析失败")


if __name__ == "__main__":
    main()
