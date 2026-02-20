#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正版迭代正弦分解算法

关键修正：
- 频率范围：1.0 ~ 8.0 对应 ZE ~ 8*ZE 阶次
- 阶次 = 频率 * ZE
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
    """每齿单独去除趋势"""
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


def iterative_sine_decomposition_corrected(phi, dev, ZE, max_components=30, min_amplitude=0.001):
    """
    迭代正弦分解 - 修正版
    
    关键修正：
    - 频率范围：1.0 ~ 8.0 对应 ZE ~ 8*ZE 阶次
    - 阶次 = 频率 * ZE
    """
    residual = dev.copy()
    components = []
    
    # 修正：频率范围
    # 频率1.0 = 齿轮旋转一周 = ZE阶次
    # 频率2.0 = 齿轮旋转两周 = 2*ZE阶次
    min_freq = 1.0  # 对应ZE阶次
    max_freq = 8.0  # 对应8*ZE阶次
    
    for iteration in range(max_components):
        if np.std(residual) < min_amplitude:
            break
        
        # FFT找主要频率
        phi_uniform = np.linspace(phi.min(), phi.max(), len(phi))
        dev_uniform = np.interp(phi_uniform, phi, residual)
        
        fft_result = np.fft.fft(dev_uniform)
        freqs = np.fft.fftfreq(len(dev_uniform), phi_uniform[1] - phi_uniform[0])
        
        positive_freqs = freqs[freqs >= 0]
        positive_amps = np.abs(fft_result[freqs >= 0]) / len(dev_uniform) * 2
        
        # 在目标频率范围内找最大峰值
        valid_idx = (positive_freqs >= min_freq) & (positive_freqs <= max_freq)
        if not np.any(valid_idx):
            break
        
        valid_freqs = positive_freqs[valid_idx]
        valid_amps = positive_amps[valid_idx]
        
        # 找最大峰值
        peak_idx = np.argmax(valid_amps)
        peak_freq = valid_freqs[peak_idx]
        peak_amp = valid_amps[peak_idx]
        
        if peak_amp < min_amplitude:
            break
        
        # 精确拟合
        def sine_func(params):
            freq, amp, phase = params
            return residual - amp * np.sin(freq * phi + phase)
        
        try:
            result = least_squares(
                sine_func,
                [peak_freq, peak_amp, 0.0],
                bounds=([min_freq, 0, -np.pi], [max_freq, np.inf, np.pi]),
                method='trf',
                ftol=1e-10,
                xtol=1e-10
            )
            
            freq, amp, phase = result.x
            
            if amp < min_amplitude:
                break
            
            # 修正：阶次 = 频率 * ZE
            order = int(round(freq * ZE))
            
            # 从残差中减去
            sine_wave = amp * np.sin(freq * phi + phase)
            residual = residual - sine_wave
            
            components.append({
                'frequency': freq,
                'amplitude': amp,
                'phase': phase,
                'order': order
            })
            
        except:
            break
    
    return components


def calculate_spectrum_from_components(components, ZE, max_order=None):
    """从分量列表计算频谱"""
    if max_order is None:
        max_order = 8 * ZE
    
    spectrum = {}
    for comp in components:
        order = comp['order']
        if 1 <= order <= max_order:
            if order in spectrum:
                if comp['amplitude'] > spectrum[order]:
                    spectrum[order] = comp['amplitude']
            else:
                spectrum[order] = comp['amplitude']
    
    return spectrum


def analyze_with_corrected_decomposition(mka_file, sample_name, klingelnberg_ref, poly_order=3):
    print(f"\n{'='*80}")
    print(f"修正版迭代正弦分解: {sample_name}")
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
        
        # 迭代分解
        components = iterative_sine_decomposition_corrected(phi_proc, dev_proc, ZE)
        
        # 计算频谱
        spectrum = calculate_spectrum_from_components(components, ZE)
        
        # 获取参考值
        ref = klingelnberg_ref.get(surface_key, {})
        
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
        
        # 显示提取的主要分量
        if components:
            print(f"\n  提取的主要分量 (前10个):")
            sorted_comps = sorted(components, key=lambda x: x['amplitude'], reverse=True)[:10]
            for comp in sorted_comps:
                print(f"    阶次 {comp['order']}: 振幅={comp['amplitude']:.4f}")
        
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
    # 测试不同预处理阶数
    for poly_order in [2, 3]:
        print(f"\n\n{'#'*80}")
        print(f"# 预处理多项式阶数: {poly_order}")
        print(f"{'#'*80}")
        
        # 分析样本1
        error1 = analyze_with_corrected_decomposition(
            "263751-018-WAV.mka",
            "样本1: 263751-018-WAV (87齿)",
            KLINGELNBERG_SAMPLE1,
            poly_order=poly_order
        )
        
        # 分析样本2
        error2 = analyze_with_corrected_decomposition(
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
