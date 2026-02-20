#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试阶次计算问题

关键发现：
- 提取的阶次1的振幅0.1692 ≈ 参考值0.19 (26阶次)
- 这说明频率到阶次的转换关系需要修正
"""

import numpy as np
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


def involute_angle(r, rb):
    """计算渐开线展角"""
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
            'r': r,
            'dev': dev,
            'rb': rb[0] if len(rb) > 0 else r[0] * np.cos(np.radians(alpha_deg))
        })
    return profiles


def main():
    print("="*80)
    print("调试阶次计算问题")
    print("="*80)
    
    # 解析样本2 (26齿)
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
    
    # 分析phi的范围
    print(f"\nphi范围分析:")
    print(f"  phi_min = {phi.min():.4f} rad = {np.degrees(phi.min()):.1f}°")
    print(f"  phi_max = {phi.max():.4f} rad = {np.degrees(phi.max()):.1f}°")
    print(f"  phi_range = {phi.max() - phi.min():.4f} rad = {np.degrees(phi.max() - phi.min()):.1f}°")
    print(f"  2π = {2*np.pi:.4f} rad = {np.degrees(2*np.pi):.1f}°")
    print(f"  2π * ZE = {2*np.pi*ZE:.4f} rad = {np.degrees(2*np.pi*ZE):.1f}°")
    
    # 计算等效圆周数
    num_circles = (phi.max() - phi.min()) / (2 * np.pi)
    print(f"\n  等效圆周数 = phi_range / 2π = {num_circles:.2f}")
    
    # FFT分析
    print(f"\nFFT分析:")
    phi_uniform = np.linspace(phi.min(), phi.max(), len(phi))
    dev_uniform = np.interp(phi_uniform, phi, dev)
    
    fft_result = np.fft.fft(dev_uniform)
    freqs = np.fft.fftfreq(len(dev_uniform), phi_uniform[1] - phi_uniform[0])
    
    positive_freqs = freqs[freqs >= 0]
    positive_amps = np.abs(fft_result[freqs >= 0]) / len(dev_uniform) * 2
    
    # 找出主要峰值
    peak_indices = np.argsort(positive_amps)[::-1][:10]
    
    print(f"\n  主要频率成分:")
    print(f"  {'频率':<12} {'振幅':<12} {'阶次(旧)':<12} {'阶次(新)':<12}")
    print(f"  {'-'*50}")
    
    for idx in peak_indices:
        freq = positive_freqs[idx]
        amp = positive_amps[idx]
        
        if amp < 0.01:
            continue
        
        # 旧方法：阶次 = 频率 * ZE
        order_old = int(round(freq * ZE))
        
        # 新方法：阶次 = 频率 * (phi_range / 2π) = 频率 * num_circles
        order_new = int(round(freq * num_circles * 2 * np.pi / (2 * np.pi)))
        # 或者更简单：阶次 = 频率 * phi_range
        order_new2 = int(round(freq * (phi.max() - phi.min())))
        
        print(f"  {freq:<12.4f} {amp:<12.4f} {order_old:<12} {order_new2:<12}")
    
    # 关键洞察
    print(f"\n关键洞察:")
    print(f"  如果phi范围是2π（一个圆周），那么频率1对应阶次1")
    print(f"  如果phi范围是2π*ZE（ZE个圆周），那么频率1对应阶次ZE")
    print(f"  实际phi范围 = {phi.max() - phi.min():.4f} rad")
    print(f"  这相当于 {num_circles:.2f} 个圆周")
    print(f"\n  所以正确的阶次计算应该是：")
    print(f"  阶次 = 频率 * phi_range / (2π) = 频率 * {num_circles:.2f}")
    
    # 验证
    print(f"\n验证:")
    print(f"  如果频率 = 1/{num_circles:.2f} = {1/num_circles:.4f}")
    print(f"  那么阶次 = {1/num_circles:.4f} * {num_circles:.2f} = 1")
    print(f"  但实际我们想要的是：频率 = 1 时，阶次 = ZE = {ZE}")
    print(f"\n  正确的关系应该是：")
    print(f"  阶次 = 频率 * ZE / num_circles")
    print(f"  或者：阶次 = 频率 * 2π * ZE / phi_range")


if __name__ == "__main__":
    main()
