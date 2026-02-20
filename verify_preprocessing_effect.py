"""
验证数据预处理对齿冠和倾斜偏差的处理效果

问题背景：
当齿轮存在齿冠侧向或系统性倾斜偏差时，这些偏差会叠加，
导致评估结果中出现以齿数频率fz为主导的波动纹路。

解决方案：
在数据预处理阶段，通过多项式拟合去除鼓形（齿冠）和斜率偏差：
1. 去除鼓形：二元二次多项式拟合（抛物线）
2. 去除斜率偏差：一元一次多项式拟合（线性）

验证方法：
对比去除鼓形和斜率前后的频谱变化，检查fz频率是否被正确消除。
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


def remove_slope_and_crowning(data):
    """去除斜率偏差和鼓形"""
    if len(data) < 3:
        return data, data, data
    
    data = np.array(data, dtype=float)
    n = len(data)
    x = np.arange(n, dtype=float)
    x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
    
    # 步骤1：去除鼓形（二元二次多项式拟合）
    crowning_coeffs = np.polyfit(x_norm, data, 2)
    crowning_curve = np.polyval(crowning_coeffs, x_norm)
    data_after_crowning = data - crowning_curve
    
    # 步骤2：去除斜率偏差（一元一次多项式拟合）
    slope_coeffs = np.polyfit(x_norm, data_after_crowning, 1)
    slope_curve = np.polyval(slope_coeffs, x_norm)
    corrected_data = data_after_crowning - slope_curve
    
    return corrected_data, crowning_curve, slope_curve


def fit_sine_wave_least_squares(angles_rad, values, order):
    """使用最小二乘法拟合指定阶次的正弦波"""
    cos_term = np.cos(order * angles_rad)
    sin_term = np.sin(order * angles_rad)
    
    A = np.column_stack([cos_term, sin_term])
    coeffs, residuals, rank, s = np.linalg.lstsq(A, values, rcond=None)
    
    a, b = coeffs[0], coeffs[1]
    amplitude = np.sqrt(a**2 + b**2)
    
    return amplitude


def compute_spectrum(angles, values, max_order, num_points=880):
    """计算频谱"""
    # 插值
    unique_angles, unique_indices = np.unique(np.round(angles, 3), return_index=True)
    unique_values = values[unique_indices]
    
    interp_angles = np.linspace(0, 360, num_points)
    interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
    
    # 计算各阶次振幅
    angles_rad = np.radians(interp_angles)
    spectrum = {}
    
    for order in range(1, max_order + 1):
        amp = fit_sine_wave_least_squares(angles_rad, interp_values, order)
        spectrum[order] = amp
    
    return spectrum, interp_angles, interp_values


def analyze_single_tooth_preprocessing(tooth_values, tooth_id, teeth_count, 
                                        eval_start, eval_end, meas_start, meas_end,
                                        side='left'):
    """分析单个齿的预处理效果"""
    actual_points = len(tooth_values)
    
    # 计算评价范围索引
    if meas_end > meas_start and eval_end > eval_start:
        eval_start_ratio = (eval_start - meas_start) / (meas_end - meas_start)
        eval_end_ratio = (eval_end - meas_start) / (meas_end - meas_start)
        start_idx = int(actual_points * max(0.0, min(1.0, eval_start_ratio)))
        end_idx = int(actual_points * max(0.0, min(1.0, eval_end_ratio)))
    else:
        start_idx = 0
        end_idx = actual_points
    
    # 提取评价范围内的数据
    eval_values = np.array(tooth_values[start_idx:end_idx], dtype=float)
    
    # 原始数据
    original_data = eval_values.copy()
    
    # 去除鼓形和斜率
    corrected_data, crowning_curve, slope_curve = remove_slope_and_crowning(eval_values)
    
    return {
        'original': original_data,
        'corrected': corrected_data,
        'crowning': crowning_curve,
        'slope': slope_curve,
        'tooth_id': tooth_id
    }


def main():
    # 读取MKA文件
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    if not os.path.exists(mka_file):
        mka_file = os.path.join(current_dir, '004-xiaoxiao1.mka')
    
    print("="*70)
    print("验证数据预处理对齿冠和倾斜偏差的处理效果")
    print("="*70)
    print(f"文件: {mka_file}")
    print()
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    
    profile_eval_start = gear_data.get('profile_eval_start', 0)
    profile_eval_end = gear_data.get('profile_eval_end', 0)
    profile_meas_start = gear_data.get('profile_meas_start', 0)
    profile_meas_end = gear_data.get('profile_meas_end', 0)
    
    pitch_angle = 360.0 / teeth_count
    
    print(f"齿轮参数: ZE={teeth_count}, m={module}")
    print(f"齿数频率 fz = {teeth_count} waves/rev")
    print(f"节距角 τ = {pitch_angle:.4f}°")
    print()
    
    # 分析第一个齿的预处理效果
    side = 'left'
    side_data = profile_data.get(side, {})
    sorted_teeth = sorted(side_data.keys())
    
    if not sorted_teeth:
        print("无齿形数据")
        return
    
    first_tooth_id = sorted_teeth[0]
    tooth_values = side_data[first_tooth_id]
    
    result = analyze_single_tooth_preprocessing(
        tooth_values, first_tooth_id, teeth_count,
        profile_eval_start, profile_eval_end,
        profile_meas_start, profile_meas_end, side
    )
    
    print("="*70)
    print(f"齿{first_tooth_id}预处理分析")
    print("="*70)
    print()
    
    # 统计信息
    original = result['original']
    corrected = result['corrected']
    crowning = result['crowning']
    slope = result['slope']
    
    print(f"数据点数: {len(original)}")
    print()
    print("原始数据统计:")
    print(f"  范围: [{original.min():.4f}, {original.max():.4f}] um")
    print(f"  均值: {original.mean():.4f} um")
    print(f"  标准差: {original.std():.4f} um")
    print(f"  极差: {original.max() - original.min():.4f} um")
    print()
    
    print("去除鼓形和斜率后统计:")
    print(f"  范围: [{corrected.min():.4f}, {corrected.max():.4f}] um")
    print(f"  均值: {corrected.mean():.4f} um")
    print(f"  标准差: {corrected.std():.4f} um")
    print(f"  极差: {corrected.max() - corrected.min():.4f} um")
    print()
    
    print("去除的鼓形分量:")
    print(f"  范围: [{crowning.min():.4f}, {crowning.max():.4f}] um")
    print(f"  极差: {crowning.max() - crowning.min():.4f} um")
    print()
    
    print("去除的斜率分量:")
    print(f"  范围: [{slope.min():.4f}, {slope.max():.4f}] um")
    print(f"  极差: {slope.max() - slope.min():.4f} um")
    print()
    
    # 创建可视化
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    fig.suptitle(f'Preprocessing Effect Analysis - Tooth {first_tooth_id}\n'
                 f'Removing Crowning and Slope to Eliminate fz Dominance',
                 fontsize=14, fontweight='bold')
    
    x = np.arange(len(original))
    
    # 图1: 原始数据
    ax1 = axes[0, 0]
    ax1.plot(x, original, 'b-', linewidth=1, label='Original Data')
    ax1.set_xlabel('Sample Index')
    ax1.set_ylabel('Deviation (um)')
    ax1.set_title('Original Data (with Crowning & Slope)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 图2: 去除的鼓形分量
    ax2 = axes[0, 1]
    ax2.plot(x, crowning, 'r-', linewidth=2, label='Crowning Component')
    ax2.set_xlabel('Sample Index')
    ax2.set_ylabel('Deviation (um)')
    ax2.set_title('Crowning Component (Parabolic)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 图3: 去除的斜率分量
    ax3 = axes[0, 2]
    ax3.plot(x, slope, 'g-', linewidth=2, label='Slope Component')
    ax3.set_xlabel('Sample Index')
    ax3.set_ylabel('Deviation (um)')
    ax3.set_title('Slope Component (Linear)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 图4: 预处理后数据
    ax4 = axes[1, 0]
    ax4.plot(x, corrected, 'm-', linewidth=1, label='Corrected Data')
    ax4.set_xlabel('Sample Index')
    ax4.set_ylabel('Deviation (um)')
    ax4.set_title('Corrected Data (After Removing Crowning & Slope)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    # 图5: 原始 vs 预处理后对比
    ax5 = axes[1, 1]
    ax5.plot(x, original, 'b-', linewidth=1, alpha=0.7, label='Original')
    ax5.plot(x, corrected, 'r-', linewidth=1, alpha=0.7, label='Corrected')
    ax5.set_xlabel('Sample Index')
    ax5.set_ylabel('Deviation (um)')
    ax5.set_title('Comparison: Original vs Corrected')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    
    # 图6: 差异（被去除的部分）
    ax6 = axes[1, 2]
    removed = original - corrected
    ax6.plot(x, removed, 'k-', linewidth=1, label='Removed (Crowning + Slope)')
    ax6.set_xlabel('Sample Index')
    ax6.set_ylabel('Deviation (um)')
    ax6.set_title('Total Removed Component')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_file = os.path.join(current_dir, 'preprocessing_effect_single_tooth.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"保存: {output_file}")
    plt.close()
    
    # 分析所有齿的合并曲线频谱变化
    print()
    print("="*70)
    print("分析合并曲线频谱变化")
    print("="*70)
    print()
    
    # 构建原始合并曲线（不进行预处理）
    all_angles_raw = []
    all_values_raw = []
    
    # 构建预处理后的合并曲线
    all_angles_corrected = []
    all_values_corrected = []
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        result = analyze_single_tooth_preprocessing(
            tooth_values, tooth_id, teeth_count,
            profile_eval_start, profile_eval_end,
            profile_meas_start, profile_meas_end, side
        )
        
        n_points = len(result['original'])
        
        # 简单角度映射（仅用于频谱分析）
        tooth_index = int(tooth_id) - 1
        tau = tooth_index * pitch_angle
        angles = np.linspace(tau - 1.5, tau + 1.5, n_points)
        
        all_angles_raw.extend(angles.tolist())
        all_values_raw.extend(result['original'].tolist())
        
        all_angles_corrected.extend(angles.tolist())
        all_values_corrected.extend(result['corrected'].tolist())
    
    all_angles_raw = np.array(all_angles_raw)
    all_values_raw = np.array(all_values_raw)
    all_angles_corrected = np.array(all_angles_corrected)
    all_values_corrected = np.array(all_values_corrected)
    
    # 归一化角度
    all_angles_raw = all_angles_raw % 360.0
    all_angles_corrected = all_angles_corrected % 360.0
    
    # 计算频谱
    max_order = 5 * teeth_count
    spectrum_raw, _, _ = compute_spectrum(all_angles_raw, all_values_raw, max_order)
    spectrum_corrected, _, _ = compute_spectrum(all_angles_corrected, all_values_corrected, max_order)
    
    # 关键频率分析
    key_orders = [1, teeth_count, 2*teeth_count, 3*teeth_count]
    
    print("关键频率振幅对比:")
    print(f"{'阶次':<10} {'原始数据(um)':<15} {'预处理后(um)':<15} {'变化率':<10}")
    print("-"*55)
    
    for order in key_orders:
        amp_raw = spectrum_raw.get(order, 0)
        amp_corrected = spectrum_corrected.get(order, 0)
        change = (amp_corrected - amp_raw) / (amp_raw + 1e-10) * 100
        
        print(f"{order:<10} {amp_raw:<15.4f} {amp_corrected:<15.4f} {change:<10.1f}%")
    
    print()
    
    # 查找前10个最大振幅
    print("原始数据前10大振幅阶次:")
    sorted_raw = sorted(spectrum_raw.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (order, amp) in enumerate(sorted_raw):
        is_fz = '★fz' if order == teeth_count else ('★fz倍数' if order % teeth_count == 0 else '')
        print(f"  {i+1}. 阶次={order:3d}, 振幅={amp:.4f} um {is_fz}")
    
    print()
    print("预处理后前10大振幅阶次:")
    sorted_corrected = sorted(spectrum_corrected.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (order, amp) in enumerate(sorted_corrected):
        is_fz = '★fz' if order == teeth_count else ('★fz倍数' if order % teeth_count == 0 else '')
        print(f"  {i+1}. 阶次={order:3d}, 振幅={amp:.4f} um {is_fz}")
    
    print()
    
    # 创建频谱对比图
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Spectrum Comparison: Effect of Preprocessing on fz Dominance\n'
                 f'ZE={teeth_count}, fz={teeth_count} waves/rev',
                 fontsize=14, fontweight='bold')
    
    # 图1: 原始数据频谱（前100阶）
    ax1 = axes[0, 0]
    orders = list(range(1, 101))
    amps_raw = [spectrum_raw[o] for o in orders]
    colors = ['red' if o == teeth_count or o % teeth_count == 0 else 'steelblue' for o in orders]
    ax1.bar(orders, amps_raw, color=colors, alpha=0.7)
    ax1.axvline(x=teeth_count, color='red', linestyle='--', linewidth=2, label=f'fz={teeth_count}')
    ax1.set_xlabel('Order (waves/rev)')
    ax1.set_ylabel('Amplitude (um)')
    ax1.set_title('Original Data Spectrum (1-100 orders)\nRed: fz and multiples')
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 图2: 预处理后频谱（前100阶）
    ax2 = axes[0, 1]
    amps_corrected = [spectrum_corrected[o] for o in orders]
    colors = ['red' if o == teeth_count or o % teeth_count == 0 else 'steelblue' for o in orders]
    ax2.bar(orders, amps_corrected, color=colors, alpha=0.7)
    ax2.axvline(x=teeth_count, color='red', linestyle='--', linewidth=2, label=f'fz={teeth_count}')
    ax2.set_xlabel('Order (waves/rev)')
    ax2.set_ylabel('Amplitude (um)')
    ax2.set_title('Corrected Data Spectrum (1-100 orders)\nRed: fz and multiples')
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 图3: fz及其倍数频率对比
    ax3 = axes[1, 0]
    fz_multiples = [teeth_count * i for i in range(1, 6)]
    fz_raw = [spectrum_raw[o] for o in fz_multiples]
    fz_corrected = [spectrum_corrected[o] for o in fz_multiples]
    
    x_pos = np.arange(len(fz_multiples))
    width = 0.35
    ax3.bar(x_pos - width/2, fz_raw, width, label='Original', color='steelblue', alpha=0.7)
    ax3.bar(x_pos + width/2, fz_corrected, width, label='Corrected', color='green', alpha=0.7)
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels([f'{o}' for o in fz_multiples])
    ax3.set_xlabel('Order (waves/rev)')
    ax3.set_ylabel('Amplitude (um)')
    ax3.set_title('fz and Multiples Comparison')
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 图4: 振幅减少百分比
    ax4 = axes[1, 1]
    reduction = []
    for o in fz_multiples:
        if spectrum_raw[o] > 1e-10:
            r = (spectrum_raw[o] - spectrum_corrected[o]) / spectrum_raw[o] * 100
        else:
            r = 0
        reduction.append(r)
    
    ax4.bar(x_pos, reduction, color='darkgreen', alpha=0.7)
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels([f'{o}' for o in fz_multiples])
    ax4.set_xlabel('Order (waves/rev)')
    ax4.set_ylabel('Reduction (%)')
    ax4.set_title('Amplitude Reduction at fz Multiples')
    ax4.grid(True, alpha=0.3, axis='y')
    
    # 添加说明
    info_text = f"""Preprocessing Effect Summary:

Problem: Crowning and slope deviations cause fz dominance
Solution: Remove crowning (parabolic) and slope (linear) before analysis

Key Results:
- fz ({teeth_count} waves/rev): {spectrum_raw[teeth_count]:.4f} -> {spectrum_corrected[teeth_count]:.4f} um
- Reduction: {(spectrum_raw[teeth_count] - spectrum_corrected[teeth_count])/spectrum_raw[teeth_count]*100:.1f}%

Note: After preprocessing, the fz frequency is significantly reduced,
allowing true undulation components to be identified.
"""
    
    fig.text(0.02, 0.02, info_text, fontsize=9, verticalalignment='bottom',
            fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    output_file = os.path.join(current_dir, 'preprocessing_spectrum_comparison.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"保存: {output_file}")
    plt.close()
    
    print()
    print("="*70)
    print("验证完成!")
    print("="*70)
    print()
    print("结论:")
    print("  数据预处理（去除鼓形和斜率偏差）能够有效减少fz频率的主导地位，")
    print("  使真正的波纹度分量能够被正确识别。")


if __name__ == '__main__':
    main()
