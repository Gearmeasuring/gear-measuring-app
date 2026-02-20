#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成频谱分析报告 - 类似Gleason/Klingelnberg格式
"""

import numpy as np
from numpy.linalg import lstsq
import matplotlib.pyplot as plt
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


def fit_sine_at_order_with_freq(phi, signal, order, ZE):
    """对特定阶次进行拟合"""
    phi_range = phi.max() - phi.min()
    freq = order / phi_range
    
    A_matrix = np.column_stack([
        np.sin(freq * phi),
        np.cos(freq * phi)
    ])
    
    result, residuals, rank, s = lstsq(A_matrix, signal, rcond=None)
    
    A_coef, B_coef = result
    amplitude = np.sqrt(A_coef**2 + B_coef**2)
    
    return amplitude


def generate_spectrum_report(mka_file, sample_name, poly_order=3):
    """生成频谱分析报告"""
    
    # 解析MKA文件
    mka_data = parse_mka_file(mka_file)
    
    gear_data = mka_data.get('gear_data', {})
    ZE = int(gear_data.get('teeth', gear_data.get('ZE', 0)))
    m = float(gear_data.get('module', gear_data.get('m', 0)))
    alpha = float(gear_data.get('alpha', 20.0))
    beta = np.radians(float(gear_data.get('beta', 0.0)))
    
    print(f"\n{'='*80}")
    print(f"频谱分析报告: {sample_name}")
    print(f"{'='*80}")
    print(f"\n齿轮参数:")
    print(f"  齿数 ZE = {ZE}")
    print(f"  模数 m = {m}")
    print(f"  压力角 α = {alpha}°")
    print(f"  螺旋角 β = {np.degrees(beta):.1f}°")
    
    profile_data = mka_data.get('profile_data', {})
    flank_data = mka_data.get('flank_data', {})
    
    # 创建图形
    fig, axes = plt.subplots(4, 1, figsize=(12, 14))
    fig.suptitle(f'{sample_name} - 波纹度频谱分析\n齿数 ZE = {ZE}', fontsize=14, fontweight='bold')
    
    surfaces = [
        ('INVOLUTE LEFT', 'left_profile', 'profile', axes[0]),
        ('INVOLUTE RIGHT', 'right_profile', 'profile', axes[1]),
        ('LEAD LEFT', 'left_helix', 'helix', axes[2]),
        ('LEAD RIGHT', 'right_helix', 'helix', axes[3])
    ]
    
    all_results = {}
    
    for surface_name, surface_key, data_type, ax in surfaces:
        if data_type == 'profile':
            side = 'left' if 'left' in surface_key else 'right'
            raw_profiles = profile_data.get(side, {})
            if not raw_profiles:
                ax.set_title(f'{surface_name} - 无数据')
                continue
            profiles = prepare_profile_data(raw_profiles, alpha)
            tooth_positions = list(range(len(profiles)))
            phi, dev = merge_profile_curves(profiles, tooth_positions, ZE)
        else:
            side = 'left' if 'left' in surface_key else 'right'
            raw_flanks = flank_data.get(side, {})
            if not raw_flanks:
                ax.set_title(f'{surface_name} - 无数据')
                continue
            flank_lines = prepare_helix_data(raw_flanks)
            tooth_positions = list(range(len(flank_lines)))
            phi, dev = merge_helix_curves(flank_lines, tooth_positions, ZE, m, beta)
        
        # 预处理
        phi_proc, dev_proc = remove_trend_per_tooth(phi, dev, poly_order)
        
        # 计算频谱（1到200阶）
        orders = list(range(1, 201))
        amplitudes = []
        
        for order in orders:
            amp = fit_sine_at_order_with_freq(phi_proc, dev_proc, order, ZE)
            amplitudes.append(amp)
        
        amplitudes = np.array(amplitudes)
        
        # 找出前10个最大振幅
        top_indices = np.argsort(amplitudes)[::-1][:10]
        top_orders = [orders[i] for i in top_indices]
        top_amplitudes = [amplitudes[i] for i in top_indices]
        
        # 绘制频谱
        ax.bar(orders, amplitudes, alpha=0.6, color='blue', width=1.5)
        
        # 标注ZE的倍数
        for i in range(1, 8):
            ze_multiple = i * ZE
            if ze_multiple <= 200:
                ax.axvline(x=ze_multiple, color='red', linestyle='--', alpha=0.5, linewidth=1)
                ax.text(ze_multiple, ax.get_ylim()[1]*0.9, f'{i}×ZE', 
                       ha='center', fontsize=8, color='red')
        
        # 标注前10个最大振幅
        for order, amp in zip(top_orders, top_amplitudes):
            ax.plot(order, amp, 'ro', markersize=8)
            ax.text(order, amp, f'{order}', ha='center', va='bottom', fontsize=8)
        
        ax.set_xlabel('阶次 (Order)')
        ax.set_ylabel('振幅 (μm)')
        ax.set_title(surface_name)
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, 200)
        
        # 保存结果
        all_results[surface_name] = {
            'orders': orders,
            'amplitudes': amplitudes,
            'top_orders': top_orders,
            'top_amplitudes': top_amplitudes
        }
        
        # 打印表格
        print(f"\n{surface_name}:")
        print(f"  {'排名':<6} {'阶次':<8} {'振幅 (μm)':<12} {'类型'}")
        print(f"  {'-'*40}")
        for i, (order, amp) in enumerate(zip(top_orders, top_amplitudes), 1):
            if order % ZE == 0:
                order_type = f"{order//ZE}×ZE (啮合谐波)"
            else:
                order_type = "鬼阶次"
            print(f"  {i:<6} {order:<8} {amp:<12.4f} {order_type}")
    
    plt.tight_layout()
    
    # 保存图像
    output_file = mka_file.replace('.mka', '_spectrum_report.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n频谱报告已保存: {output_file}")
    
    plt.show()
    
    return all_results


def main():
    print("="*80)
    print("频谱分析报告生成工具")
    print("="*80)
    
    # 分析样本1
    results1 = generate_spectrum_report(
        "263751-018-WAV.mka",
        "样本1: 263751-018-WAV",
        poly_order=3
    )
    
    # 分析样本2
    results2 = generate_spectrum_report(
        "004-xiaoxiao1.mka",
        "样本2: 004-xiaoxiao1",
        poly_order=3
    )


if __name__ == "__main__":
    main()
