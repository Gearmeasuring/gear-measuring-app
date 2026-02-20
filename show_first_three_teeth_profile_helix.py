"""
显示前三个齿的齿形和齿向合并曲线
使用更新后的标准公式：
- 齿形: φ = -ξ + τ
- 齿向: φ = -Δφ + τ, 其中 Δφ = 2 × Δz × tan(β₀) / D₀
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
    """去除斜率和鼓形"""
    if len(data) < 3:
        return data
    data = np.array(data, dtype=float)
    x = np.arange(len(data), dtype=float)
    x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
    
    # 去除鼓形
    crowning_coeffs = np.polyfit(x_norm, data, 2)
    crowning_curve = np.polyval(crowning_coeffs, x_norm)
    data_after_crowning = data - crowning_curve
    
    # 去除斜率
    slope_coeffs = np.polyfit(x_norm, data_after_crowning, 1)
    slope_curve = np.polyval(slope_coeffs, x_norm)
    corrected_data = data_after_crowning - slope_curve
    
    return corrected_data


def calculate_involute_polar_angle(radius, base_radius):
    """计算渐开线极角 inv(α) = tan(α) - α"""
    if radius <= base_radius or base_radius <= 0:
        return 0.0
    cos_alpha = base_radius / radius
    if cos_alpha >= 1.0:
        return 0.0
    alpha = np.arccos(cos_alpha)
    return np.tan(alpha) - alpha


def process_profile_tooth(tooth_values, tooth_id, gear_data, side='left'):
    """处理单个齿的齿形数据"""
    module = gear_data.get('module', 0)
    teeth_count = gear_data.get('teeth', 0)
    pressure_angle = gear_data.get('pressure_angle', 20)
    
    pitch_radius = module * teeth_count / 2.0
    base_radius = pitch_radius * np.cos(np.radians(pressure_angle))
    pitch_angle_deg = 360.0 / teeth_count
    
    # 获取评价范围
    eval_start = gear_data.get('profile_eval_start', 0)
    eval_end = gear_data.get('profile_eval_end', 0)
    meas_start = gear_data.get('profile_meas_start', 0)
    meas_end = gear_data.get('profile_meas_end', 0)
    
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
    
    # 只使用评价范围内的数据
    eval_values = np.array(tooth_values[start_idx:end_idx], dtype=float)
    eval_points = len(eval_values)
    
    if eval_points < 3:
        return None, None
    
    corrected_values = remove_slope_and_crowning(eval_values)
    
    # 计算渐开线极角
    if eval_start > 0 and eval_end > 0:
        radii = np.linspace(eval_start/2, eval_end/2, eval_points)
    else:
        radii = np.linspace(pitch_radius * 0.95, pitch_radius * 1.05, eval_points)
    
    polar_angles = []
    for r in radii:
        xi = calculate_involute_polar_angle(r, base_radius)
        polar_angles.append(np.degrees(xi))
    polar_angles = np.array(polar_angles)
    
    # 计算齿序号
    tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
    
    # 节距角 τ
    tau_angle = tooth_index * pitch_angle_deg
    
    # 旋转角度 φ = -ξ + τ (齿形公式)
    if side == 'left':
        final_angles = tau_angle - polar_angles
    else:
        final_angles = tau_angle + polar_angles
    
    return final_angles, corrected_values


def process_helix_tooth(tooth_values, tooth_id, gear_data, side='left'):
    """处理单个齿的齿向数据 - 使用标准公式 Δφ = 2 × Δz × tan(β₀) / D₀"""
    module = gear_data.get('module', 0)
    teeth_count = gear_data.get('teeth', 0)
    helix_angle = gear_data.get('helix_angle', 0)
    pitch_diameter = module * teeth_count
    pitch_angle_deg = 360.0 / teeth_count
    
    # 获取评价范围
    eval_start = gear_data.get('helix_eval_start', 0)
    eval_end = gear_data.get('helix_eval_end', 0)
    meas_start = gear_data.get('helix_meas_start', 0)
    meas_end = gear_data.get('helix_meas_end', 0)
    
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
    
    # 只使用评价范围内的数据
    eval_values = np.array(tooth_values[start_idx:end_idx], dtype=float)
    eval_points = len(eval_values)
    
    if eval_points < 3:
        return None, None
    
    corrected_values = remove_slope_and_crowning(eval_values)
    
    # 计算轴向位置（相对于评价范围中心）
    # 使用标准公式: Δφ = 2 × Δz × tan(β₀) / D₀
    if abs(helix_angle) > 0.01 and pitch_diameter > 0:
        # 生成轴向位置数组
        axial_positions = np.linspace(eval_start, eval_end, eval_points)
        # 计算评价范围中心
        eval_center = (eval_start + eval_end) / 2.0
        # 计算相对于中心的轴向距离 Δz
        delta_z = axial_positions - eval_center
        # 使用标准公式计算轴向旋转角度 Δφ
        tan_beta0 = math.tan(math.radians(helix_angle))
        delta_phi_rad = 2 * delta_z * tan_beta0 / pitch_diameter
        delta_phi_deg = np.degrees(delta_phi_rad)
    else:
        delta_phi_deg = np.linspace(0, 1, eval_points)
    
    # 计算齿序号
    tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
    
    # 节距角 τ
    tau_angle = tooth_index * pitch_angle_deg
    
    # 旋转角度 φ = -Δφ + τ (齿向公式)
    if side == 'left':
        final_angles = tau_angle - delta_phi_deg
    else:
        final_angles = tau_angle + delta_phi_deg
    
    return final_angles, corrected_values


def plot_first_three_teeth(profile_data, flank_data, gear_data, side='left'):
    """绘制前三个齿的齿形和齿向合并曲线"""
    teeth_count = gear_data.get('teeth', 0)
    module = gear_data.get('module', 0)
    helix_angle = gear_data.get('helix_angle', 0)
    pitch_diameter = module * teeth_count
    
    # 获取前三个齿
    profile_side_data = profile_data.get(side, {})
    flank_side_data = flank_data.get(side, {})
    
    profile_teeth = sorted(profile_side_data.keys())[:3]
    flank_teeth = sorted(flank_side_data.keys())[:3]
    
    colors = ['blue', 'green', 'red']
    
    # 创建图形: 2行2列
    # 左上: 齿形合并曲线, 右上: 齿向合并曲线
    # 左下: 齿形数据点分布, 右下: 齿向数据点分布
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.25)
    
    ax_profile_curve = fig.add_subplot(gs[0, 0])
    ax_helix_curve = fig.add_subplot(gs[0, 1])
    ax_profile_scatter = fig.add_subplot(gs[1, 0])
    ax_helix_scatter = fig.add_subplot(gs[1, 1])
    
    side_name = '左' if side == 'left' else '右'
    fig.suptitle(f'{side_name}齿面 - 前三个齿的合并曲线 (z={teeth_count}, β={helix_angle}°)', 
                 fontsize=16, fontweight='bold')
    
    # 处理齿形数据
    print(f'\n=== {side_name}齿形 ===')
    for idx, tooth_id in enumerate(profile_teeth):
        tooth_values = profile_side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        angles, values = process_profile_tooth(tooth_values, tooth_id, gear_data, side)
        if angles is None:
            continue
        
        # 按角度排序
        sort_idx = np.argsort(angles)
        angles = angles[sort_idx]
        values = values[sort_idx]
        
        color = colors[idx % len(colors)]
        
        # 绘制齿形曲线
        ax_profile_curve.plot(angles, values, color=color, alpha=0.7, linewidth=1, 
                             label=f'齿{tooth_id}')
        ax_profile_scatter.scatter(angles, values, c=color, s=2, alpha=0.5, 
                                  label=f'齿{tooth_id}')
        
        print(f'齿{tooth_id}: 角度范围 [{angles.min():.2f}°, {angles.max():.2f}°], '
              f'{len(angles)}个点')
    
    # 处理齿向数据
    print(f'\n=== {side_name}齿向 ===')
    for idx, tooth_id in enumerate(flank_teeth):
        tooth_values = flank_side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        angles, values = process_helix_tooth(tooth_values, tooth_id, gear_data, side)
        if angles is None:
            continue
        
        # 按角度排序
        sort_idx = np.argsort(angles)
        angles = angles[sort_idx]
        values = values[sort_idx]
        
        color = colors[idx % len(colors)]
        
        # 绘制齿向曲线
        ax_helix_curve.plot(angles, values, color=color, alpha=0.7, linewidth=1, 
                           label=f'齿{tooth_id}')
        ax_helix_scatter.scatter(angles, values, c=color, s=2, alpha=0.5, 
                                label=f'齿{tooth_id}')
        
        print(f'齿{tooth_id}: 角度范围 [{angles.min():.2f}°, {angles.max():.2f}°], '
              f'{len(angles)}个点')
    
    # 设置齿形图表
    ax_profile_curve.set_xlabel('旋转角度 φ (°)', fontsize=11)
    ax_profile_curve.set_ylabel('偏差 (μm)', fontsize=11)
    ax_profile_curve.set_title(f'{side_name}齿形 - 合并曲线', fontsize=12, fontweight='bold')
    ax_profile_curve.legend(loc='upper right')
    ax_profile_curve.grid(True, alpha=0.3)
    ax_profile_curve.set_xlim(0, 360)
    
    ax_profile_scatter.set_xlabel('旋转角度 φ (°)', fontsize=11)
    ax_profile_scatter.set_ylabel('偏差 (μm)', fontsize=11)
    ax_profile_scatter.set_title(f'{side_name}齿形 - 数据点分布', fontsize=12, fontweight='bold')
    ax_profile_scatter.legend(loc='upper right')
    ax_profile_scatter.grid(True, alpha=0.3)
    ax_profile_scatter.set_xlim(0, 360)
    
    # 设置齿向图表
    ax_helix_curve.set_xlabel('旋转角度 φ (°)', fontsize=11)
    ax_helix_curve.set_ylabel('偏差 (μm)', fontsize=11)
    ax_helix_curve.set_title(f'{side_name}齿向 - 合并曲线\n(使用公式: Δφ = 2×Δz×tan(β₀)/D₀)', 
                            fontsize=12, fontweight='bold')
    ax_helix_curve.legend(loc='upper right')
    ax_helix_curve.grid(True, alpha=0.3)
    ax_helix_curve.set_xlim(0, 360)
    
    ax_helix_scatter.set_xlabel('旋转角度 φ (°)', fontsize=11)
    ax_helix_scatter.set_ylabel('偏差 (μm)', fontsize=11)
    ax_helix_scatter.set_title(f'{side_name}齿向 - 数据点分布', fontsize=12, fontweight='bold')
    ax_helix_scatter.legend(loc='upper right')
    ax_helix_scatter.grid(True, alpha=0.3)
    ax_helix_scatter.set_xlim(0, 360)
    
    # 添加公式说明
    formula_text = f'齿形公式: φ = -ξ + τ\n齿向公式: φ = -Δφ + τ\n其中 Δφ = 2×Δz×tan(β₀)/D₀\n'
    formula_text += f'β₀ = {helix_angle}°, D₀ = {pitch_diameter:.3f} mm'
    fig.text(0.5, 0.02, formula_text, ha='center', fontsize=10, 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    output_file = os.path.join(current_dir, f'first_three_teeth_{side}_profile_helix.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f'\n已保存: {output_file}')
    plt.close()
    
    return profile_teeth, flank_teeth


def main():
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    if not os.path.exists(mka_file):
        mka_file = os.path.join(current_dir, '004-xiaoxiao1.mka')
    
    print(f'读取文件: {mka_file}')
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 0)
    module = gear_data.get('module', 0)
    helix_angle = gear_data.get('helix_angle', 0)
    pressure_angle = gear_data.get('pressure_angle', 20)
    
    print(f'\n齿轮参数:')
    print(f'  齿数 ZE = {teeth_count}')
    print(f'  模数 m = {module} mm')
    print(f'  螺旋角 β₀ = {helix_angle}°')
    print(f'  压力角 α = {pressure_angle}°')
    print(f'  节圆直径 D₀ = {module * teeth_count:.3f} mm')
    print(f'  节距角 τ = 360°/{teeth_count} = {360.0/teeth_count:.4f}°')
    
    print(f'\n数据概况:')
    print(f'  左齿形: {len(profile_data.get("left", {}))} 齿')
    print(f'  右齿形: {len(profile_data.get("right", {}))} 齿')
    print(f'  左齿向: {len(flank_data.get("left", {}))} 齿')
    print(f'  右齿向: {len(flank_data.get("right", {}))} 齿')
    
    # 生成左齿面图形
    if profile_data.get('left') or flank_data.get('left'):
        print('\n' + '='*60)
        print('生成左齿面合并曲线...')
        plot_first_three_teeth(profile_data, flank_data, gear_data, side='left')
    
    # 生成右齿面图形
    if profile_data.get('right') or flank_data.get('right'):
        print('\n' + '='*60)
        print('生成右齿面合并曲线...')
        plot_first_three_teeth(profile_data, flank_data, gear_data, side='right')
    
    print('\n' + '='*60)
    print('完成!')


if __name__ == '__main__':
    main()
