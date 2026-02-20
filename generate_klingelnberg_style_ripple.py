"""
生成符合Klingelnberg标准的波纹度分析图

参考论文中的图表样式:
1. 频谱图(Spectrum) - 柱状图显示各阶次振幅
2. 合并曲线图(Combined Curves) - 显示所有齿的偏差曲线
3. 波纹度展开图(Ripple above rotation angle) - 显示波纹度随旋转角的变化
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import math
from matplotlib.patches import Rectangle

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file
from gear_ripple_algorithm import GearRippleAnalyzer


def plot_klingelnberg_style_spectrum(spectrum_data, high_order_data, teeth_count, 
                                      title, output_file, side='left'):
    """
    绘制Klingelnberg风格的频谱图
    
    参考论文中的Figure 5和Figure 9样式
    """
    fig = plt.figure(figsize=(12, 8))
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1.2], hspace=0.3, wspace=0.25)
    
    orders = spectrum_data['orders']
    amplitudes = spectrum_data['amplitudes']
    phases = spectrum_data['phases']
    
    # 图1: 前10阶次振幅柱状图 (类似Figure 5中的Spectrum)
    ax1 = fig.add_subplot(gs[0, :])
    
    colors = ['red' if o >= teeth_count else 'steelblue' for o in orders]
    bars = ax1.bar(range(len(orders)), amplitudes, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # 添加数值标签
    for i, (order, amp) in enumerate(zip(orders, amplitudes)):
        ax1.text(i, amp + 0.005, f'{order}', ha='center', va='bottom', fontsize=8)
    
    ax1.set_xlabel('Component Index', fontsize=10)
    ax1.set_ylabel('Amplitude (μm)', fontsize=10)
    ax1.set_title(f'{title} - Top 10 Waves per Revolution', fontsize=12, fontweight='bold')
    ax1.set_xticks(range(len(orders)))
    ax1.set_xticklabels([f'{i+1}' for i in range(len(orders))])
    ax1.grid(True, alpha=0.3, axis='y')
    
    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='steelblue', alpha=0.8, label=f'Low Order (<{teeth_count})'),
        Patch(facecolor='red', alpha=0.8, label=f'High Order (≥{teeth_count})')
    ]
    ax1.legend(handles=legend_elements, loc='upper right', fontsize=9)
    
    # 图2: 完整频谱 (1-5*ZE)
    ax2 = fig.add_subplot(gs[1, :])
    
    max_order = 5 * teeth_count
    all_orders = list(range(1, max_order + 1))
    all_amplitudes = []
    
    # 计算完整频谱
    angles_rad = np.radians(np.linspace(0, 360, 880))
    residual = np.array(spectrum_data['original'])
    
    for order in all_orders:
        cos_term = np.cos(order * angles_rad)
        sin_term = np.sin(order * angles_rad)
        A = np.column_stack([cos_term, sin_term])
        coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
        a, b = coeffs[0], coeffs[1]
        amp = np.sqrt(a**2 + b**2)
        all_amplitudes.append(amp)
    
    # 绘制频谱
    colors_full = ['red' if o >= teeth_count else 'steelblue' for o in all_orders]
    ax2.bar(all_orders, all_amplitudes, color=colors_full, alpha=0.6, width=0.8)
    
    # 标记fz及其倍数
    for i in range(1, 6):
        fz_order = i * teeth_count
        if fz_order <= max_order:
            ax2.axvline(x=fz_order, color='red', linestyle='--', alpha=0.5, linewidth=1)
            ax2.text(fz_order, max(all_amplitudes) * 0.9, f'{i}fz', 
                    ha='center', fontsize=8, color='red')
    
    ax2.set_xlabel('Order (waves/rev)', fontsize=10)
    ax2.set_ylabel('Amplitude (μm)', fontsize=10)
    ax2.set_title(f'Complete Spectrum (1-{max_order} orders)', fontsize=12, fontweight='bold')
    ax2.set_xlim(0, max_order)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 图3: 高阶波纹度合成 (类似Figure 5中的Ripple above rotation angle)
    ax3 = fig.add_subplot(gs[2, :])
    
    interp_angles = np.linspace(0, 360, 880)
    high_order_signal = high_order_data['high_order_reconstructed']
    
    ax3.plot(interp_angles, high_order_signal, 'b-', linewidth=1, alpha=0.8)
    ax3.fill_between(interp_angles, high_order_signal, alpha=0.3)
    
    # 添加统计信息
    w_value = high_order_data['total_high_order_amplitude']
    rms_value = high_order_data['high_order_rms']
    
    ax3.axhline(y=w_value, color='red', linestyle='--', linewidth=1, alpha=0.7, label=f'W = {w_value:.4f} μm')
    ax3.axhline(y=-w_value, color='red', linestyle='--', linewidth=1, alpha=0.7)
    ax3.axhline(y=rms_value, color='green', linestyle=':', linewidth=1, alpha=0.7, label=f'RMS = {rms_value:.4f} μm')
    ax3.axhline(y=-rms_value, color='green', linestyle=':', linewidth=1, alpha=0.7)
    
    ax3.set_xlabel('Rotation Angle (deg)', fontsize=10)
    ax3.set_ylabel('High Order Ripple (μm)', fontsize=10)
    ax3.set_title(f'High Order Undulation (≥{teeth_count} waves/rev)\nW = {w_value:.4f} μm, RMS = {rms_value:.4f} μm', 
                 fontsize=12, fontweight='bold')
    ax3.set_xlim(0, 360)
    ax3.legend(loc='upper right', fontsize=9)
    ax3.grid(True, alpha=0.3)
    
    # 添加整体标题
    fig.suptitle(f'{title}\nKlingelnberg Style Ripple Analysis', 
                fontsize=14, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


def plot_combined_curves(analyzer, data_dict, data_type, side, gear_data, 
                         title, output_file):
    """
    绘制合并曲线图 (类似Figure 2中的Combined Curves)
    """
    fig, axes = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle(f'{title}\nCombined Curves ({side.upper()} Side)', 
                fontsize=14, fontweight='bold')
    
    # 获取评价范围
    if data_type == 'profile':
        eval_start = gear_data.get('profile_eval_start', 0)
        eval_end = gear_data.get('profile_eval_end', 0)
        meas_start = gear_data.get('profile_meas_start', 0)
        meas_end = gear_data.get('profile_meas_end', 0)
        ylabel = 'Profile Deviation (μm)'
    else:
        eval_start = gear_data.get('helix_eval_start', 0)
        eval_end = gear_data.get('helix_eval_end', 0)
        meas_start = gear_data.get('helix_meas_start', 0)
        meas_end = gear_data.get('helix_meas_end', 0)
        ylabel = 'Helix Deviation (μm)'
    
    # 构建合并曲线
    curve_data = analyzer.build_merged_curve(
        data_dict, data_type, side,
        eval_start, eval_end, meas_start, meas_end
    )
    
    if curve_data is None:
        print(f"No data for {title}")
        return
    
    angles, values = curve_data
    
    # 图1: 完整合并曲线
    ax1 = axes[0]
    ax1.plot(angles, values, 'b-', linewidth=0.8, alpha=0.7)
    ax1.set_xlabel('Rotation Angle (deg)', fontsize=10)
    ax1.set_ylabel(ylabel, fontsize=10)
    ax1.set_title(f'Complete Stitched Curve ({len(angles)} points)', fontsize=11, fontweight='bold')
    ax1.set_xlim(0, 360)
    ax1.grid(True, alpha=0.3)
    
    # 添加节距角标记
    for i in range(analyzer.teeth_count + 1):
        tau = i * analyzer.pitch_angle
        if tau <= 360:
            ax1.axvline(x=tau, color='r', linestyle='--', alpha=0.2, linewidth=0.5)
    
    # 图2: 前5个齿的详细视图
    ax2 = axes[1]
    
    side_data = data_dict.get(side, {})
    sorted_teeth = sorted(side_data.keys())[:5]
    colors = plt.cm.tab10(np.linspace(0, 1, len(sorted_teeth)))
    
    for idx, tooth_id in enumerate(sorted_teeth):
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        if data_type == 'profile':
            angles_t, values_t = analyzer.process_profile_tooth(
                tooth_values, tooth_id, eval_start, eval_end, meas_start, meas_end, side
            )
        else:
            angles_t, values_t = analyzer.process_helix_tooth(
                tooth_values, tooth_id, eval_start, eval_end, meas_start, meas_end, side
            )
        
        if angles_t is not None:
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * analyzer.pitch_angle
            ax2.plot(angles_t, values_t, color=colors[idx], 
                    linewidth=1.5, label=f'Tooth {tooth_id} (τ={tau:.1f}°)')
    
    ax2.set_xlabel('Rotation Angle (deg)', fontsize=10)
    ax2.set_ylabel(ylabel, fontsize=10)
    ax2.set_title('First 5 Teeth Detail', fontsize=11, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


def main():
    # 读取MKA文件
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    if not os.path.exists(mka_file):
        mka_file = os.path.join(current_dir, '004-xiaoxiao1.mka')
    
    print("="*70)
    print("生成Klingelnberg风格的波纹度分析图")
    print("="*70)
    print(f"文件: {mka_file}")
    print()
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    # 提取齿轮参数
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 0.0)
    base_diameter = gear_data.get('base_diameter', 0.0)
    
    # 创建分析器
    analyzer = GearRippleAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    # 获取评价范围
    profile_eval_start = gear_data.get('profile_eval_start', 0)
    profile_eval_end = gear_data.get('profile_eval_end', 0)
    profile_meas_start = gear_data.get('profile_meas_start', 0)
    profile_meas_end = gear_data.get('profile_meas_end', 0)
    
    helix_eval_start = gear_data.get('helix_eval_start', 0)
    helix_eval_end = gear_data.get('helix_eval_end', 0)
    helix_meas_start = gear_data.get('helix_meas_start', 0)
    helix_meas_end = gear_data.get('helix_meas_end', 0)
    
    print(f"齿轮参数: ZE={teeth_count}, m={module}, β={helix_angle}°")
    print()
    
    # 分析并生成图表
    analyses = []
    
    # 左齿形
    if profile_data.get('left'):
        print("分析左齿形...")
        curve = analyzer.build_merged_curve(
            profile_data, 'profile', 'left',
            profile_eval_start, profile_eval_end,
            profile_meas_start, profile_meas_end
        )
        if curve:
            spectrum_result = analyzer.analyze_spectrum(curve)
            if spectrum_result:
                analyses.append({
                    'name': 'Left Profile',
                    'spectrum': spectrum_result['spectrum'],
                    'high_order': spectrum_result['high_order'],
                    'data_dict': profile_data,
                    'data_type': 'profile',
                    'side': 'left'
                })
    
    # 右齿形
    if profile_data.get('right'):
        print("分析右齿形...")
        curve = analyzer.build_merged_curve(
            profile_data, 'profile', 'right',
            profile_eval_start, profile_eval_end,
            profile_meas_start, profile_meas_end
        )
        if curve:
            spectrum_result = analyzer.analyze_spectrum(curve)
            if spectrum_result:
                analyses.append({
                    'name': 'Right Profile',
                    'spectrum': spectrum_result['spectrum'],
                    'high_order': spectrum_result['high_order'],
                    'data_dict': profile_data,
                    'data_type': 'profile',
                    'side': 'right'
                })
    
    # 左齿向
    if flank_data.get('left'):
        print("分析左齿向...")
        curve = analyzer.build_merged_curve(
            flank_data, 'helix', 'left',
            helix_eval_start, helix_eval_end,
            helix_meas_start, helix_meas_end
        )
        if curve:
            spectrum_result = analyzer.analyze_spectrum(curve)
            if spectrum_result:
                analyses.append({
                    'name': 'Left Helix',
                    'spectrum': spectrum_result['spectrum'],
                    'high_order': spectrum_result['high_order'],
                    'data_dict': flank_data,
                    'data_type': 'helix',
                    'side': 'left'
                })
    
    # 右齿向
    if flank_data.get('right'):
        print("分析右齿向...")
        curve = analyzer.build_merged_curve(
            flank_data, 'helix', 'right',
            helix_eval_start, helix_eval_end,
            helix_meas_start, helix_meas_end
        )
        if curve:
            spectrum_result = analyzer.analyze_spectrum(curve)
            if spectrum_result:
                analyses.append({
                    'name': 'Right Helix',
                    'spectrum': spectrum_result['spectrum'],
                    'high_order': spectrum_result['high_order'],
                    'data_dict': flank_data,
                    'data_type': 'helix',
                    'side': 'right'
                })
    
    # 生成Klingelnberg风格图表
    print()
    print("="*70)
    print("生成Klingelnberg风格频谱图...")
    print("="*70)
    
    for analysis in analyses:
        name = analysis['name']
        spectrum = analysis['spectrum']
        high_order = analysis['high_order']
        
        # 频谱图
        output_file = os.path.join(current_dir, f'klingelnberg_spectrum_{name.lower().replace(" ", "_")}.png')
        plot_klingelnberg_style_spectrum(
            spectrum, high_order, teeth_count,
            name, output_file, analysis['side']
        )
        
        # 合并曲线图
        output_file = os.path.join(current_dir, f'klingelnberg_combined_{name.lower().replace(" ", "_")}.png')
        plot_combined_curves(
            analyzer, analysis['data_dict'], analysis['data_type'], analysis['side'],
            gear_data, name, output_file
        )
    
    # 生成汇总报告
    print()
    print("="*70)
    print("波纹度分析结果汇总")
    print("="*70)
    print()
    
    for analysis in analyses:
        name = analysis['name']
        spectrum = analysis['spectrum']
        high_order = analysis['high_order']
        
        print(f"\n{name}:")
        print(f"  前3波数: {list(spectrum['orders'][:3])}")
        print(f"  前3振幅: {[f'{a:.4f}' for a in spectrum['amplitudes'][:3]]} μm")
        print(f"  高阶总振幅 W: {high_order['total_high_order_amplitude']:.4f} μm")
        print(f"  高阶RMS: {high_order['high_order_rms']:.4f} μm")
    
    print()
    print("="*70)
    print("生成的文件:")
    print("="*70)
    for analysis in analyses:
        name = analysis['name'].lower().replace(" ", "_")
        print(f"  klingelnberg_spectrum_{name}.png")
        print(f"  klingelnberg_combined_{name}.png")
    print("="*70)


if __name__ == '__main__':
    main()
