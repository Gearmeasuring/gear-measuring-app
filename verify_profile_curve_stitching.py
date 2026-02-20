"""
验证齿形曲线拼接是否符合标准公式

根据标准公式:
φ = -ξ - Δφ + τ

对于齿形(渐开线):
- Δφ = 0 (无轴向旋转)
- ξ = 渐开线极角 = inv(α) = tan(α) - α
- τ = 节距角 = 齿序号 × 360° / 齿数

因此齿形公式为:
φ = -ξ + τ

对于左齿面: φ = τ - ξ
对于右齿面: φ = τ + ξ
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file
from gear_ripple_algorithm import GearRippleAnalyzer


def verify_involute_formula():
    """验证渐开线极角计算公式"""
    print("="*70)
    print("验证渐开线极角计算公式")
    print("="*70)
    print()
    print("公式: inv(α) = tan(α) - α")
    print("其中: α = arccos(rb/r)")
    print("      rb = 基圆半径")
    print("      r = 测量点半径")
    print()
    
    # 测试数据
    rb = 76.642  # 基圆半径 (153.285/2)
    test_radii = [77.0, 78.0, 79.0, 80.0, 81.0]  # 测试半径
    
    print("测试计算:")
    print(f"基圆半径 rb = {rb:.3f} mm")
    print()
    print(f"{'半径r(mm)':<12} {'α(deg)':<12} {'inv(α)(rad)':<15} {'ξ(deg)':<12}")
    print("-"*55)
    
    for r in test_radii:
        cos_alpha = rb / r
        alpha = math.acos(cos_alpha)
        inv_alpha = math.tan(alpha) - alpha
        xi_deg = math.degrees(inv_alpha)
        
        print(f"{r:<12.3f} {math.degrees(alpha):<12.4f} {inv_alpha:<15.6f} {xi_deg:<12.4f}")
    
    print()


def verify_angle_synthesis(analyzer, tooth_id, side='left'):
    """验证角度合成公式"""
    print("="*70)
    print(f"验证齿{tooth_id} {side}齿面的角度合成公式")
    print("="*70)
    print()
    
    # 齿序号
    tooth_index = tooth_id - 1
    # 节距角
    tau = tooth_index * analyzer.pitch_angle
    
    print(f"齿序号: {tooth_index}")
    print(f"节距角 τ = {tooth_index} × {analyzer.pitch_angle:.4f}° = {tau:.4f}°")
    print()
    
    # 测试渐开线极角
    rb = analyzer.base_radius
    test_radii = np.linspace(rb * 1.01, rb * 1.15, 5)
    
    print(f"{'半径r(mm)':<12} {'ξ(deg)':<12} {'τ(deg)':<12} {'φ=τ-ξ(deg)':<15} {'φ=τ+ξ(deg)':<15}")
    print("-"*70)
    
    for r in test_radii:
        cos_alpha = rb / r
        alpha = math.acos(cos_alpha)
        xi = math.degrees(math.tan(alpha) - alpha)
        
        phi_left = tau - xi   # 左齿面: φ = τ - ξ
        phi_right = tau + xi  # 右齿面: φ = τ + ξ
        
        print(f"{r:<12.3f} {xi:<12.4f} {tau:<12.4f} {phi_left:<15.4f} {phi_right:<15.4f}")
    
    print()
    print("说明:")
    print("  左齿面: φ = τ - ξ (负号)")
    print("  右齿面: φ = τ + ξ (正号)")
    print()


def plot_profile_curve_stitching(analyzer, profile_data, gear_data, side='left'):
    """绘制齿形曲线拼接图"""
    print("="*70)
    print(f"生成{side}齿面齿形曲线拼接图")
    print("="*70)
    print()
    
    profile_eval_start = gear_data.get('profile_eval_start', 0)
    profile_eval_end = gear_data.get('profile_eval_end', 0)
    profile_meas_start = gear_data.get('profile_meas_start', 0)
    profile_meas_end = gear_data.get('profile_meas_end', 0)
    
    # 构建合并曲线
    curve_data = analyzer.build_merged_curve(
        profile_data, 'profile', side,
        profile_eval_start, profile_eval_end,
        profile_meas_start, profile_meas_end
    )
    
    if curve_data is None:
        print("无数据")
        return
    
    angles, values = curve_data
    
    # 创建图形
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'{side.upper()} Profile Curve Stitching Verification\n' + 
                 f'Formula: φ = {"τ - ξ" if side == "left" else "τ + ξ"} (ZE={analyzer.teeth_count}, m={analyzer.module})',
                 fontsize=14, fontweight='bold')
    
    # 图1: 完整拼接曲线
    ax1 = axes[0, 0]
    ax1.plot(angles, values, 'b-', alpha=0.6, linewidth=0.8)
    ax1.set_xlabel('Rotation Angle φ (deg)')
    ax1.set_ylabel('Deviation (um)')
    ax1.set_title('Complete Stitched Curve (0-360°)')
    ax1.set_xlim(0, 360)
    ax1.grid(True, alpha=0.3)
    
    # 添加节距角标记线
    for i in range(analyzer.teeth_count + 1):
        tau = i * analyzer.pitch_angle
        if tau <= 360:
            ax1.axvline(x=tau, color='r', linestyle='--', alpha=0.3, linewidth=0.5)
    
    # 图2: 前3个齿的详细视图
    ax2 = axes[0, 1]
    
    # 获取前3个齿的数据
    side_data = profile_data.get(side, {})
    sorted_teeth = sorted(side_data.keys())[:3]
    colors = ['blue', 'green', 'red']
    
    for idx, tooth_id in enumerate(sorted_teeth):
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        angles_t, values_t = analyzer.process_profile_tooth(
            tooth_values, tooth_id,
            profile_eval_start, profile_eval_end,
            profile_meas_start, profile_meas_end, side
        )
        
        if angles_t is not None:
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * analyzer.pitch_angle
            
            ax2.plot(angles_t, values_t, color=colors[idx], alpha=0.7, 
                    linewidth=1.5, label=f'Tooth {tooth_id} (τ={tau:.2f}°)')
    
    ax2.set_xlabel('Rotation Angle φ (deg)')
    ax2.set_ylabel('Deviation (um)')
    ax2.set_title('First 3 Teeth Detail')
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    # 图3: 角度分布直方图
    ax3 = axes[1, 0]
    ax3.hist(angles, bins=100, alpha=0.7, color='steelblue', edgecolor='black')
    ax3.set_xlabel('Rotation Angle φ (deg)')
    ax3.set_ylabel('Count')
    ax3.set_title('Angle Distribution')
    ax3.set_xlim(0, 360)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 添加节距角标记
    for i in range(analyzer.teeth_count + 1):
        tau = i * analyzer.pitch_angle
        if tau <= 360:
            ax3.axvline(x=tau, color='r', linestyle='--', alpha=0.5, linewidth=1)
    
    # 图4: 角度 vs 齿序号关系
    ax4 = axes[1, 1]
    
    # 计算每个齿的角度范围
    tooth_angles = {}
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        angles_t, _ = analyzer.process_profile_tooth(
            tooth_values, tooth_id,
            profile_eval_start, profile_eval_end,
            profile_meas_start, profile_meas_end, side
        )
        
        if angles_t is not None:
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * analyzer.pitch_angle
            tooth_angles[tooth_id] = {
                'min': np.min(angles_t),
                'max': np.max(angles_t),
                'tau': tau,
                'xi_min': tau - np.min(angles_t) if side == 'left' else np.min(angles_t) - tau,
                'xi_max': tau - np.max(angles_t) if side == 'left' else np.max(angles_t) - tau
            }
    
    # 绘制角度范围
    for tooth_id, data in tooth_angles.items():
        tooth_index = int(tooth_id) - 1
        ax4.barh(tooth_index, data['max'] - data['min'], left=data['min'], 
                alpha=0.6, color='steelblue', edgecolor='black')
        ax4.plot(data['tau'], tooth_index, 'ro', markersize=8, label='τ (Pitch Angle)' if tooth_index == 0 else '')
    
    ax4.set_xlabel('Rotation Angle φ (deg)')
    ax4.set_ylabel('Tooth Index')
    ax4.set_title('Angle Range per Tooth')
    ax4.set_xlim(0, 360)
    ax4.legend(loc='upper right')
    ax4.grid(True, alpha=0.3, axis='x')
    
    # 添加公式说明
    formula_text = f"""Angle Synthesis Formula:
φ = -ξ + τ

Where:
  ξ = inv(α) = tan(α) - α  (Involute polar angle)
  τ = tooth_index × 360°/ZE  (Pitch angle)
  α = arccos(rb/r)  (Pressure angle)

For {side} side:
  φ = {'τ - ξ' if side == 'left' else 'τ + ξ'}

Parameters:
  ZE = {analyzer.teeth_count}
  m = {analyzer.module} mm
  rb = {analyzer.base_radius:.3f} mm
  τ = {analyzer.pitch_angle:.4f}°
"""
    
    fig.text(0.02, 0.02, formula_text, fontsize=9, verticalalignment='bottom',
            fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    output_file = os.path.join(current_dir, f'profile_curve_stitching_{side}.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()
    
    # 打印统计信息
    print(f"数据统计:")
    print(f"  总数据点数: {len(angles)}")
    print(f"  角度范围: [{np.min(angles):.2f}°, {np.max(angles):.2f}°]")
    print(f"  角度跨度: {np.max(angles) - np.min(angles):.2f}°")
    print()
    
    # 检查每个齿的角度范围
    print("各齿角度范围:")
    for tooth_id in sorted_teeth[:5]:  # 只显示前5个齿
        if tooth_id in tooth_angles:
            data = tooth_angles[tooth_id]
            print(f"  齿{tooth_id}: φ=[{data['min']:.2f}°, {data['max']:.2f}°], "
                  f"τ={data['tau']:.2f}°, ξ=[{data['xi_min']:.2f}°, {data['xi_max']:.2f}°]")
    print()


def main():
    # 读取MKA文件
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    if not os.path.exists(mka_file):
        mka_file = os.path.join(current_dir, '004-xiaoxiao1.mka')
    
    print("="*70)
    print("齿形曲线拼接验证")
    print("="*70)
    print(f"文件: {mka_file}")
    print()
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    
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
    
    # 验证渐开线公式
    verify_involute_formula()
    
    # 验证角度合成公式
    verify_angle_synthesis(analyzer, tooth_id=2, side='left')
    verify_angle_synthesis(analyzer, tooth_id=2, side='right')
    
    # 生成可视化
    if profile_data.get('left'):
        plot_profile_curve_stitching(analyzer, profile_data, gear_data, side='left')
    
    if profile_data.get('right'):
        plot_profile_curve_stitching(analyzer, profile_data, gear_data, side='right')
    
    print("="*70)
    print("验证完成!")
    print("="*70)


if __name__ == '__main__':
    main()
