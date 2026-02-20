#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
频谱分析可视化
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import least_squares
import logging
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file

logging.basicConfig(level=logging.WARNING)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

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


def calculate_fft_spectrum(phi, dev, ZE, max_order=None):
    """计算FFT频谱"""
    if max_order is None:
        max_order = 8 * ZE
    
    # 均匀重采样
    phi_uniform = np.linspace(phi.min(), phi.max(), len(phi))
    dev_uniform = np.interp(phi_uniform, phi, dev)
    
    # FFT
    fft_result = np.fft.fft(dev_uniform)
    freqs = np.fft.fftfreq(len(dev_uniform), phi_uniform[1] - phi_uniform[0])
    
    # 只取正频率
    positive_freqs = freqs[freqs >= 0]
    positive_amps = np.abs(fft_result[freqs >= 0]) / len(dev_uniform) * 2
    
    # 转换为阶次
    orders = []
    amps = []
    for freq, amp in zip(positive_freqs, positive_amps):
        order = int(round(freq * ZE))
        if 1 <= order <= max_order:
            orders.append(order)
            amps.append(amp)
    
    return np.array(orders), np.array(amps)


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


def plot_spectrum_comparison(mka_file, sample_name, klingelnberg_ref, poly_order=3):
    """绘制频谱对比图"""
    
    # 解析MKA文件
    mka_data = parse_mka_file(mka_file)
    
    gear_data = mka_data.get('gear_data', {})
    ZE = int(gear_data.get('teeth', gear_data.get('ZE', 0)))
    m = float(gear_data.get('module', gear_data.get('m', 0)))
    alpha = float(gear_data.get('alpha', 20.0))
    beta = np.radians(float(gear_data.get('beta', 0.0)))
    
    print(f"\n{sample_name}")
    print(f"齿数 ZE = {ZE}")
    
    profile_data = mka_data.get('profile_data', {})
    flank_data = mka_data.get('flank_data', {})
    
    # 创建图形
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'{sample_name} - 频谱分析对比', fontsize=14, fontweight='bold')
    
    surfaces = [
        ('Right Profile', 'right_profile', 'profile', axes[0, 0]),
        ('Left Profile', 'left_profile', 'profile', axes[0, 1]),
        ('Right Helix', 'right_helix', 'helix', axes[1, 0]),
        ('Left Helix', 'left_helix', 'helix', axes[1, 1])
    ]
    
    for surface_name, surface_key, data_type, ax in surfaces:
        if data_type == 'profile':
            side = 'right' if 'right' in surface_key else 'left'
            raw_profiles = profile_data.get(side, {})
            if not raw_profiles:
                ax.set_title(f'{surface_name} - 无数据')
                continue
            profiles = prepare_profile_data(raw_profiles, alpha)
            tooth_positions = list(range(len(profiles)))
            phi, dev = merge_profile_curves(profiles, tooth_positions, ZE)
        else:
            side = 'right' if 'right' in surface_key else 'left'
            raw_flanks = flank_data.get(side, {})
            if not raw_flanks:
                ax.set_title(f'{surface_name} - 无数据')
                continue
            flank_lines = prepare_helix_data(raw_flanks)
            tooth_positions = list(range(len(flank_lines)))
            phi, dev = merge_helix_curves(flank_lines, tooth_positions, ZE, m, beta)
        
        # 预处理
        phi_proc, dev_proc = remove_trend_per_tooth(phi, dev, poly_order)
        
        # FFT频谱
        orders_fft, amps_fft = calculate_fft_spectrum(phi_proc, dev_proc, ZE)
        
        # 对目标阶次进行精确拟合
        ref = klingelnberg_ref.get(surface_key, {})
        target_orders = list(ref.keys())
        
        spectrum_fit = {}
        for order in target_orders:
            amp, _ = fit_sine_at_order(phi_proc, dev_proc, order, ZE)
            spectrum_fit[order] = amp
        
        # 绘制FFT频谱
        ax.bar(orders_fft, amps_fft, alpha=0.5, color='blue', label='FFT结果', width=3)
        
        # 绘制精确拟合结果
        fit_orders = list(spectrum_fit.keys())
        fit_amps = list(spectrum_fit.values())
        ax.bar([o + 1.5 for o in fit_orders], fit_amps, alpha=0.7, color='green', label='拟合正弦', width=3)
        
        # 绘制Klingelnberg参考值
        ref_orders = list(ref.keys())
        ref_amps = list(ref.values())
        ax.bar([o + 3 for o in ref_orders], ref_amps, alpha=0.7, color='red', label='Klingelnberg', width=3)
        
        ax.set_xlabel('阶次')
        ax.set_ylabel('振幅 (μm)')
        ax.set_title(surface_name)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        # 设置x轴范围
        max_order = max(max(orders_fft) if len(orders_fft) > 0 else 0, 
                       max(ref_orders) if len(ref_orders) > 0 else 0)
        ax.set_xlim(0, max_order + 10)
    
    plt.tight_layout()
    
    # 保存图像
    output_file = mka_file.replace('.mka', '_spectrum.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"频谱图已保存: {output_file}")
    
    plt.show()


def main():
    # 分析样本1
    plot_spectrum_comparison(
        "263751-018-WAV.mka",
        "样本1: 263751-018-WAV (87齿)",
        KLINGELNBERG_SAMPLE1,
        poly_order=3
    )
    
    # 分析样本2
    plot_spectrum_comparison(
        "004-xiaoxiao1.mka",
        "样本2: 004-xiaoxiao1 (26齿)",
        KLINGELNBERG_SAMPLE2,
        poly_order=3
    )


if __name__ == "__main__":
    main()
