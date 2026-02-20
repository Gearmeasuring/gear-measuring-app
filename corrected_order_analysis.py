#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正后的波纹度分析 - 正确的阶次计算

关键发现：
- phi范围只有约1个圆周，不是ZE个圆周
- 正确的阶次计算：阶次 = 频率 * 2π * ZE / phi_range
"""

import numpy as np
from scipy import signal
from scipy.optimize import least_squares
import logging
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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


def remove_crowning_and_slope(phi, dev, poly_order=3):
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
            try:
                coeffs = np.polyfit(seg_phi, seg_dev, poly_order)
                trend = np.polyval(coeffs, seg_phi)
                residual = seg_dev - trend
                processed_phi.append(seg_phi)
                processed_dev.append(residual)
            except:
                processed_phi.append(seg_phi)
                processed_dev.append(seg_dev)
    
    phi_out = np.concatenate(processed_phi)
    dev_out = np.concatenate(processed_dev)
    sort_idx = np.argsort(phi_out)
    return phi_out[sort_idx], dev_out[sort_idx]


def iterative_sine_fitting_corrected(phi, dev, ZE, max_components=15, min_amplitude=0.002):
    """
    迭代拟合正弦分析 - 修正版
    
    关键修正：阶次 = 频率 * 2π * ZE / phi_range
    """
    residual = dev.copy()
    components = []
    
    # 计算phi范围和阶次转换因子
    phi_range = phi.max() - phi.min()
    order_factor = 2 * np.pi * ZE / phi_range  # 修正的转换因子
    
    max_order = 8 * ZE
    min_freq = 1.0 / order_factor  # 对应阶次1的频率
    max_freq = max_order / order_factor  # 对应max_order阶次的频率
    
    print(f"    phi_range = {phi_range:.4f} rad = {np.degrees(phi_range):.1f}°")
    print(f"    阶次转换因子 = {order_factor:.2f}")
    print(f"    频率范围: {min_freq:.4f} ~ {max_freq:.4f}")
    
    for iteration in range(max_components):
        if len(residual) < 10 or np.std(residual) < min_amplitude:
            break
        
        # FFT找出主要频率
        phi_uniform = np.linspace(phi.min(), phi.max(), len(phi))
        dev_uniform = np.interp(phi_uniform, phi, residual)
        
        fft_result = np.fft.fft(dev_uniform)
        freqs = np.fft.fftfreq(len(dev_uniform), phi_uniform[1] - phi_uniform[0])
        
        positive_freqs = freqs[freqs >= 0]
        positive_amps = np.abs(fft_result[freqs >= 0]) / len(dev_uniform) * 2
        
        # 在目标频率范围内找峰值
        valid_idx = (positive_freqs >= min_freq) & (positive_freqs <= max_freq)
        if not np.any(valid_idx):
            break
        
        valid_freqs = positive_freqs[valid_idx]
        valid_amps = positive_amps[valid_idx]
        
        if len(valid_amps) == 0:
            break
        
        peak_idx = np.argmax(valid_amps)
        peak_freq = valid_freqs[peak_idx]
        peak_amp = valid_amps[peak_idx]
        
        if peak_amp < min_amplitude:
            break
        
        # 精确拟合正弦波参数
        def sine_func(params):
            freq, amp, phase = params
            return residual - amp * np.sin(freq * phi + phase)
        
        try:
            result = least_squares(
                sine_func,
                [peak_freq, peak_amp, 0.0],
                bounds=([min_freq, 0, -np.pi], [max_freq, np.inf, np.pi]),
                method='trf',
                ftol=1e-9,
                xtol=1e-9,
                max_nfev=200
            )
            
            if not result.success:
                break
            
            freq, amp, phase = result.x
            
            if amp < min_amplitude:
                break
            
            # 修正的阶次计算
            order = int(round(freq * order_factor))
            
            sine_wave = amp * np.sin(freq * phi + phase)
            residual = residual - sine_wave
            
            components.append({
                'frequency': freq,
                'amplitude': amp,
                'phase': phase,
                'order': order
            })
            
        except Exception as e:
            break
    
    return components


def calculate_spectrum(components, ZE, max_order=None):
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


def analyze_with_corrected_method(mka_file, sample_name, klingelnberg_ref, poly_order=3):
    print(f"\n{'='*80}")
    print(f"修正后的波纹度分析: {sample_name}")
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
        
        phi_proc, dev_proc = remove_crowning_and_slope(phi, dev, poly_order)
        components = iterative_sine_fitting_corrected(phi_proc, dev_proc, ZE)
        spectrum = calculate_spectrum(components, ZE)
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
        
        if components:
            print(f"\n  提取的主要分量 (前5个):")
            sorted_comps = sorted(components, key=lambda x: x['amplitude'], reverse=True)[:5]
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
    for poly_order, name in [(2, '消除鼓形 (2阶)'), (3, '消除鼓形和齿距 (3阶)')]:
        print(f"\n\n{'#'*80}")
        print(f"# 预处理方法: {name}")
        print(f"{'#'*80}")
        
        error1 = analyze_with_corrected_method(
            "263751-018-WAV.mka",
            "样本1: 263751-018-WAV (87齿)",
            KLINGELNBERG_SAMPLE1,
            poly_order=poly_order
        )
        
        error2 = analyze_with_corrected_method(
            "004-xiaoxiao1.mka",
            "样本2: 004-xiaoxiao1 (26齿)",
            KLINGELNBERG_SAMPLE2,
            poly_order=poly_order
        )
        
        print(f"\n{'='*80}")
        print(f"预处理方法 '{name}' 对比总结")
        print(f"{'='*80}")
        print(f"样本1 (87齿): 误差 = {error1:.1f}%" if error1 else "样本1: 分析失败")
        print(f"样本2 (26齿): 误差 = {error2:.1f}%" if error2 else "样本2: 分析失败")


if __name__ == "__main__":
    main()
