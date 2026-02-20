#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于Klingelnberg文档的波纹度分析 - 优化版

关键发现：
1. 拟合正弦是优先选用的最精确的计算方法（标准）
2. 傅里叶变换作为备选方法
3. 评价类型<低阶>：消除鼓形（f < 0.5 ZE）
4. 评价类型<高阶>：消除鼓形和齿距（f ≥ ZE）
5. 共同评价：将所有齿关联产生一个共同的封闭曲线
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.optimize import least_squares
import logging
import os
import sys

# 添加gear_analysis_refactored到路径
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
    """计算渐开线展角"""
    # 避免除以零
    ratio = np.clip(rb / np.where(r > 0, r, 1e-10), -1, 1)
    alpha_r = np.arccos(ratio)
    return np.tan(alpha_r) - alpha_r


def prepare_profile_data(profile_dict, alpha_deg=20.0):
    """将解析的齿形数据转换为分析格式"""
    profiles = []
    for tooth_num in sorted(profile_dict.keys()):
        data = profile_dict[tooth_num]
        n = len(data) // 2
        r = np.array(data[:n])
        dev = np.array(data[n:])
        
        # 计算基圆半径
        rb = r * np.cos(np.radians(alpha_deg))
        
        profiles.append({
            'r': r,
            'dev': dev,
            'rb': rb[0] if len(rb) > 0 else r[0] * np.cos(np.radians(alpha_deg))
        })
    
    return profiles


def prepare_helix_data(flank_dict):
    """将解析的齿向数据转换为分析格式"""
    flank_lines = []
    for tooth_num in sorted(flank_dict.keys()):
        data = flank_dict[tooth_num]
        n = len(data) // 2
        z = np.array(data[:n])
        dev = np.array(data[n:])
        
        flank_lines.append({
            'z': z,
            'dev': dev
        })
    
    return flank_lines


def merge_profile_curves(profiles, tooth_positions, ZE):
    """合并齿形曲线（旋转角度法）- 共同评价"""
    all_phi = []
    all_dev = []
    
    rb = profiles[0]['rb']
    
    for i, (profile, pos) in enumerate(zip(profiles, tooth_positions)):
        r = profile['r']
        dev = profile['dev']
        
        # 计算渐开线展角
        xi = involute_angle(r, rb)
        
        # 齿位角
        tau = 2 * np.pi * pos / ZE
        
        # 合成角度 φ = -ξ + τ
        phi = -xi + tau
        
        all_phi.append(phi)
        all_dev.append(dev)
    
    # 按角度排序
    all_phi = np.concatenate(all_phi)
    all_dev = np.concatenate(all_dev)
    sort_idx = np.argsort(all_phi)
    
    return all_phi[sort_idx], all_dev[sort_idx]


def merge_helix_curves(flank_lines, tooth_positions, ZE, m, beta):
    """合并齿向曲线（旋转角度法）- 共同评价"""
    all_phi = []
    all_dev = []
    
    D0 = m * ZE / np.cos(beta) if np.cos(beta) != 0 else m * ZE * 1.1
    
    for i, (flank, pos) in enumerate(zip(flank_lines, tooth_positions)):
        z = flank['z']
        dev = flank['dev']
        
        # 轴向旋转角
        delta_phi = 2 * z * np.tan(beta) / D0
        
        # 齿位角
        tau = 2 * np.pi * pos / ZE
        
        # 合成角度 φ = -Δφ + τ
        phi = -delta_phi + tau
        
        all_phi.append(phi)
        all_dev.append(dev)
    
    # 按角度排序
    all_phi = np.concatenate(all_phi)
    all_dev = np.concatenate(all_dev)
    sort_idx = np.argsort(all_phi)
    
    return all_phi[sort_idx], all_dev[sort_idx]


def remove_crowning_and_slope(phi, dev, ZE, evaluation_type='all'):
    """
    根据评价类型消除鼓形和角偏差
    
    Args:
        evaluation_type: 'low' (低阶 f < 0.5 ZE), 'all' (所有阶 f < 1.5 ZE), 'high' (高阶 f >= ZE)
    """
    if evaluation_type == 'low':
        # 低阶：消除鼓形（使用2阶多项式）
        poly_order = 2
    elif evaluation_type == 'high':
        # 高阶：消除鼓形和齿距（使用3阶多项式）
        poly_order = 3
    else:
        # 所有阶：无修正或轻微修正
        poly_order = 1
    
    # 分段预处理（每齿单独处理）
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
    
    # 每段单独预处理
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
    
    # 合并
    phi_out = np.concatenate(processed_phi)
    dev_out = np.concatenate(processed_dev)
    
    # 重新排序
    sort_idx = np.argsort(phi_out)
    
    return phi_out[sort_idx], dev_out[sort_idx]


def fft_based_spectrum(phi, dev, ZE, max_order=None):
    """
    基于FFT的频谱分析 - 作为快速备选方法
    """
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
    spectrum = {}
    for freq, amp in zip(positive_freqs, positive_amps):
        order = int(round(freq * ZE))
        if 1 <= order <= max_order:
            if order in spectrum:
                spectrum[order] = max(spectrum[order], amp)
            else:
                spectrum[order] = amp
    
    return spectrum


def analyze_with_klingelnberg_method(mka_file, sample_name, klingelnberg_ref, evaluation_type='all'):
    """
    使用Klingelnberg方法分析样本
    
    Args:
        evaluation_type: 'low', 'all', 'high'
    """
    print(f"\n{'='*80}")
    print(f"Klingelnberg方法分析: {sample_name}")
    print(f"评价类型: {evaluation_type} ({'低阶' if evaluation_type=='low' else '所有阶' if evaluation_type=='all' else '高阶'})")
    print(f"{'='*80}\n")
    
    # 解析MKA文件
    try:
        mka_data = parse_mka_file(mka_file)
    except Exception as e:
        print(f"解析失败: {e}")
        return None
    
    # 获取齿轮参数
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
    
    # 获取测量数据
    profile_data = mka_data.get('profile_data', {})
    flank_data = mka_data.get('flank_data', {})
    
    # 分析四个面
    for surface_name, surface_key, data_type in [
        ('Right Profile', 'right_profile', 'profile'),
        ('Left Profile', 'left_profile', 'profile'),
        ('Right Helix', 'right_helix', 'helix'),
        ('Left Helix', 'left_helix', 'helix')
    ]:
        print(f"\n{surface_name} ({surface_key}):")
        
        # 获取数据
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
        
        # 根据评价类型消除鼓形和角偏差
        phi_proc, dev_proc = remove_crowning_and_slope(phi, dev, ZE, evaluation_type)
        
        # 使用FFT快速计算频谱
        spectrum = fft_based_spectrum(phi_proc, dev_proc, ZE)
        
        # 对比Klingelnberg
        ref = klingelnberg_ref.get(surface_key, {})
        
        print(f"  {'阶次':<8} {'我们的结果':<12} {'Klingelnberg':<12} {'误差':<10} {'状态'}")
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
    """主函数 - 测试三种评价类型"""
    
    for eval_type, eval_name in [('low', '低阶'), ('all', '所有阶'), ('high', '高阶')]:
        print(f"\n\n{'#'*80}")
        print(f"# 测试评价类型: {eval_name}")
        print(f"{'#'*80}")
        
        # 分析样本1
        error1 = analyze_with_klingelnberg_method(
            "263751-018-WAV.mka",
            "样本1: 263751-018-WAV (87齿)",
            KLINGELNBERG_SAMPLE1,
            evaluation_type=eval_type
        )
        
        # 分析样本2
        error2 = analyze_with_klingelnberg_method(
            "004-xiaoxiao1.mka",
            "样本2: 004-xiaoxiao1 (26齿)",
            KLINGELNBERG_SAMPLE2,
            evaluation_type=eval_type
        )
        
        # 对比
        print(f"\n{'='*80}")
        print(f"评价类型 '{eval_name}' 对比总结")
        print(f"{'='*80}")
        print(f"样本1 (87齿): 误差 = {error1:.1f}%" if error1 else "样本1: 分析失败")
        print(f"样本2 (26齿): 误差 = {error2:.1f}%" if error2 else "样本2: 分析失败")


if __name__ == "__main__":
    main()
