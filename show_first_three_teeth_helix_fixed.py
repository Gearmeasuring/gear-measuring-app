"""
显示左齿向前三个齿的合并曲线（修复版本）

关键修复:
1. 对于左齿向，使用 φ = τ - Δφ
2. 对于右齿向，使用 φ = τ + Δφ
3. 左右齿向的螺旋方向相反
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

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
    
    crowning_coeffs = np.polyfit(x_norm, data, 2)
    crowning_curve = np.polyval(crowning_coeffs, x_norm)
    data_after_crowning = data - crowning_curve
    
    slope_coeffs = np.polyfit(x_norm, data_after_crowning, 1)
    slope_curve = np.polyval(slope_coeffs, x_norm)
    corrected_data = data_after_crowning - slope_curve
    
    return corrected_data


def process_first_three_teeth_helix(flank_data, gear_data, side='left'):
    """处理前三个齿的齿向数据"""
    if side not in flank_data or not flank_data[side]:
        return None
    
    module = gear_data.get('module', gear_data.get('模数', 0))
    teeth_count = gear_data.get('teeth', gear_data.get('齿数', 0))
    helix_angle = gear_data.get('helix_angle', gear_data.get('螺旋角', 0))
    pitch_diameter = module * teeth_count
    pitch_angle_deg = 360.0 / teeth_count
    
    # 获取评价范围参数
    start_eval = gear_data.get('helix_eval_start', None)
    end_eval = gear_data.get('helix_eval_end', None)
    start_meas = gear_data.get('helix_meas_start', 0.0)
    end_meas = gear_data.get('helix_meas_end', 42.0)
    
    print(f'\n{side.capitalize()} Helix Evaluation Range:')
    print(f'  helix_eval_start: {start_eval} mm')
    print(f'  helix_eval_end: {end_eval} mm')
    
    side_data = flank_data[side]
    sorted_teeth = sorted(side_data.keys())[:3]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'{side.capitalize()} Helix - First 3 Teeth Merge Curve (z={teeth_count})', fontsize=14, fontweight='bold')
    
    colors = ['blue', 'green', 'red']
    
    for idx, tooth_id in enumerate(sorted_teeth):
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        actual_points = len(tooth_values)
        
        # 计算评价范围索引
        if start_eval is not None and end_eval is not None and end_meas > start_meas:
            eval_start_ratio = (start_eval - start_meas) / (end_meas - start_meas)
            eval_end_ratio = (end_eval - start_meas) / (end_meas - start_meas)
            start_idx = int(actual_points * max(0.0, min(1.0, eval_start_ratio)))
            end_idx = int(actual_points * max(0.0, min(1.0, eval_end_ratio)))
        else:
            start_idx = 0
            end_idx = actual_points
        
        # 只使用评价范围内的数据
        eval_values = np.array(tooth_values[start_idx:end_idx], dtype=float)
        eval_points = len(eval_values)
        
        if eval_points < 3:
            continue
        
        corrected_values = remove_slope_and_crowning(eval_values)
        
        # 计算相对轴向距离
        delta_L = end_eval - start_eval
        relative_positions = np.linspace(0, delta_L, eval_points)
        
        # 计算轴向旋转 Δφ = 2 * Δz * tan(β) / D
        if abs(helix_angle) > 0.01:
            delta_phi_angles = 2 * relative_positions * np.tan(np.radians(helix_angle)) / pitch_diameter
            delta_phi_angles = np.degrees(delta_phi_angles)
        else:
            delta_phi_angles = np.linspace(0, 1, eval_points)
        
        tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else idx
        
        # 节距角 τ
        tau_angle = tooth_index * pitch_angle_deg
        
        # 根据左右齿向确定符号
        # 左齿向: φ = τ - Δφ (向左倾斜)
        # 右齿向: φ = τ + Δφ (向右倾斜)
        if side == 'left':
            final_angles = tau_angle - delta_phi_angles
        else:
            final_angles = tau_angle + delta_phi_angles
        
        color = colors[idx % len(colors)]
        
        print(f'\nTooth {tooth_id} ({side}):')
        print(f'  Tau angle: {tau_angle:.2f}°')
        print(f'  Delta phi: {min(delta_phi_angles):.3f} ~ {max(delta_phi_angles):.3f}°')
        print(f'  Final angles: {min(final_angles):.2f} ~ {max(final_angles):.2f}°')
        
        # 子图1: 数据点分布
        axes[0, 0].scatter(final_angles, corrected_values, c=color, s=1, alpha=0.5, label=f'Tooth {tooth_id}')
        
        # 子图2: 曲线
        axes[0, 1].plot(final_angles, corrected_values, color=color, alpha=0.7, linewidth=0.8, label=f'Tooth {tooth_id}')
        
        # 子图3: 节距角位置
        axes[1, 0].axvline(x=tau_angle, color=color, linestyle='--', alpha=0.7, label=f'Tooth {tooth_id} tau={tau_angle:.1f}°')
        
        # 子图4: Δφ变化
        axes[1, 1].plot(relative_positions, delta_phi_angles, color=color, alpha=0.7, label=f'Tooth {tooth_id}')
    
    axes[0, 0].set_xlabel('Rotation Angle (deg)')
    axes[0, 0].set_ylabel('Deviation (um)')
    axes[0, 0].set_title(f'First 3 Teeth Data Points ({side})')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    axes[0, 1].set_xlabel('Rotation Angle (deg)')
    axes[0, 1].set_ylabel('Deviation (um)')
    axes[0, 1].set_title(f'First 3 Teeth Curves ({side})')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    axes[1, 0].set_xlabel('Angle (deg)')
    axes[1, 0].set_title('Pitch Angle Position')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    axes[1, 1].set_xlabel('Relative Axial Distance (mm)')
    axes[1, 1].set_ylabel('Delta Phi (deg)')
    axes[1, 1].set_title('Axial Rotation vs Distance')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_file = os.path.join(current_dir, f'first_three_teeth_{side}_helix.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f'\nSaved: {output_file}')
    plt.close()
    
    return sorted_teeth


def main():
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    if not os.path.exists(mka_file):
        mka_file = os.path.join(current_dir, '004-xiaoxiao1.mka')
    
    print(f'Reading file: {mka_file}')
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', gear_data.get('齿数', 0))
    module = gear_data.get('module', gear_data.get('模数', 0))
    helix_angle = gear_data.get('helix_angle', gear_data.get('螺旋角', 0))
    
    print(f'\nGear Parameters:')
    print(f'  Teeth: {teeth_count}')
    print(f'  Module: {module} mm')
    print(f'  Helix Angle: {helix_angle} deg')
    print(f'  Pitch Diameter: {module * teeth_count} mm')
    print(f'  Pitch Angle: {360.0/teeth_count:.2f} deg')
    
    # 处理左齿向
    print(f'\n{"="*60}')
    print('Processing LEFT helix...')
    print(f'{"="*60}')
    process_first_three_teeth_helix(flank_data, gear_data, 'left')
    
    # 处理右齿向
    print(f'\n{"="*60}')
    print('Processing RIGHT helix...')
    print(f'{"="*60}')
    process_first_three_teeth_helix(flank_data, gear_data, 'right')


if __name__ == '__main__':
    main()
