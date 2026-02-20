#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试不同预处理策略对频谱的影响
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

logging.basicConfig(level=logging.WARNING)

# Klingelnberg参考数据
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


def test_preprocessing_strategies(phi, dev, ZE, ref_orders):
    """测试不同预处理策略"""
    
    print(f"\n测试不同预处理策略:")
    print(f"参考阶次: {sorted(ref_orders.keys())}")
    
    # 策略1: 无预处理
    print(f"\n策略1: 无预处理")
    analyze_spectrum(phi, dev, ZE, ref_orders, "无预处理")
    
    # 策略2: 全局去均值
    print(f"\n策略2: 全局去均值")
    dev_mean = dev - np.mean(dev)
    analyze_spectrum(phi, dev_mean, ZE, ref_orders, "全局去均值")
    
    # 策略3: 每齿去均值
    print(f"\n策略3: 每齿去均值")
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
        processed_phi.append(seg_phi)
        processed_dev.append(seg_dev - np.mean(seg_dev))
    
    phi_out = np.concatenate(processed_phi)
    dev_out = np.concatenate(processed_dev)
    sort_idx = np.argsort(phi_out)
    analyze_spectrum(phi_out[sort_idx], dev_out[sort_idx], ZE, ref_orders, "每齿去均值")
    
    # 策略4: 每齿去线性趋势
    print(f"\n策略4: 每齿去线性趋势")
    processed_dev = []
    for seg_phi, seg_dev in zip(segments_phi, segments_dev):
        if len(seg_phi) > 2:
            coeffs = np.polyfit(seg_phi, seg_dev, 1)
            trend = np.polyval(coeffs, seg_phi)
            processed_dev.append(seg_dev - trend)
        else:
            processed_dev.append(seg_dev - np.mean(seg_dev))
    
    dev_out = np.concatenate(processed_dev)
    analyze_spectrum(phi_out[sort_idx], dev_out[sort_idx], ZE, ref_orders, "每齿去线性趋势")
    
    # 策略5: 每齿去2阶趋势
    print(f"\n策略5: 每齿去2阶趋势(鼓形)")
    processed_dev = []
    for seg_phi, seg_dev in zip(segments_phi, segments_dev):
        if len(seg_phi) > 3:
            coeffs = np.polyfit(seg_phi, seg_dev, 2)
            trend = np.polyval(coeffs, seg_phi)
            processed_dev.append(seg_dev - trend)
        else:
            processed_dev.append(seg_dev - np.mean(seg_dev))
    
    dev_out = np.concatenate(processed_dev)
    analyze_spectrum(phi_out[sort_idx], dev_out[sort_idx], ZE, ref_orders, "每齿去2阶趋势")


def analyze_spectrum(phi, dev, ZE, ref_orders, strategy_name):
    """分析频谱并对比参考值"""
    
    # FFT分析
    phi_uniform = np.linspace(phi.min(), phi.max(), len(phi))
    dev_uniform = np.interp(phi_uniform, phi, dev)
    
    fft_result = np.fft.fft(dev_uniform)
    freqs = np.fft.fftfreq(len(dev_uniform), phi_uniform[1] - phi_uniform[0])
    
    positive_freqs = freqs[freqs >= 0]
    positive_amps = np.abs(fft_result[freqs >= 0]) / len(dev_uniform) * 2
    
    # 计算目标阶次的振幅
    print(f"  {'阶次':<8} {'我们的结果':<12} {'参考值':<12} {'误差':<10} {'状态'}")
    print(f"  {'-'*55}")
    
    errors = []
    for order in sorted(ref_orders.keys()):
        ref_val = ref_orders[order]
        
        # 计算对应频率
        target_freq = order / ZE
        
        # 在FFT结果中找最接近的频率
        freq_idx = np.argmin(np.abs(positive_freqs - target_freq))
        our_val = positive_amps[freq_idx]
        
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
        print(f"\n  平均误差: {np.mean(errors):.1f}%")


def main():
    print("="*80)
    print("测试不同预处理策略对频谱的影响")
    print("="*80)
    
    # 解析样本2
    mka_data = parse_mka_file("004-xiaoxiao1.mka")
    gear_data = mka_data.get('gear_data', {})
    ZE = int(gear_data.get('teeth', gear_data.get('ZE', 0)))
    alpha = float(gear_data.get('alpha', 20.0))
    
    print(f"\n齿数 ZE = {ZE}")
    
    # 获取右齿形数据
    profile_data = mka_data.get('profile_data', {})
    raw_profiles = profile_data.get('right', {})
    profiles = prepare_profile_data(raw_profiles, alpha)
    
    # 合并曲线
    all_phi = []
    all_dev = []
    rb = profiles[0]['rb']
    
    for i, profile in enumerate(profiles):
        r = profile['r']
        dev = profile['dev']
        xi = involute_angle(r, rb)
        tau = 2 * np.pi * i / ZE
        phi = -xi + tau
        all_phi.append(phi)
        all_dev.append(dev)
    
    all_phi = np.concatenate(all_phi)
    all_dev = np.concatenate(all_dev)
    sort_idx = np.argsort(all_phi)
    phi = all_phi[sort_idx]
    dev = all_dev[sort_idx]
    
    # 测试不同预处理策略
    ref_orders = KLINGELNBERG_SAMPLE2['right_profile']
    test_preprocessing_strategies(phi, dev, ZE, ref_orders)


if __name__ == "__main__":
    main()
