"""
显示左齿向前三个齿的合并曲线（使用评价范围内数据）
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


def process_first_three_teeth_helix(flank_data, gear_data):
    """处理前三个齿的齿向数据（使用评价范围内数据）"""
    if 'left' not in flank_data or not flank_data['left']:
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
    
    print(f'\nEvaluation Range:')
    print(f'  helix_eval_start: {start_eval} mm')
    print(f'  helix_eval_end: {end_eval} mm')
    print(f'  helix_meas_start: {start_meas} mm')
    print(f'  helix_meas_end: {end_meas} mm')
    
    side_data = flank_data['left']
    sorted_teeth = sorted(side_data.keys())[:3]
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Left Helix - First 3 Teeth Merge Curve (z={teeth_count})', fontsize=14, fontweight='bold')
    
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
        
        # 计算相对轴向距离（从起评点开始的距离）
        # 根据公式: Δφ = 2 × Δz × tan(β) / D₀
        # 其中 Δz 是相对于起评点的轴向距离
        delta_L = end_eval - start_eval  # 评价范围内的轴向距离
        relative_positions = np.linspace(0, delta_L, eval_points)  # 从0开始的相对距离
        
        # 计算轴向位置产生的旋转 Δφ = 2 * Δz * tan(β) / D₀
        if abs(helix_angle) > 0.01:
            delta_phi_angles = 2 * relative_positions * np.tan(np.radians(helix_angle)) / pitch_diameter
            delta_phi_angles = np.degrees(delta_phi_angles)
        else:
            delta_phi_angles = np.linspace(0, 1, eval_points)
        
        tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else idx
        
        # 节距角 τ
        tau_angle = tooth_index * pitch_angle_deg
        
        # 旋转角度 φ = -Δφ + τ
        # 不进行归一化，保持原始角度值（可能为负或超过360）
        final_angles = tau_angle - delta_phi_angles
        
        # 按原始角度排序（不归一化）
        sort_idx = np.argsort(final_angles)
        final_angles = final_angles[sort_idx]
        corrected_values = corrected_values[sort_idx]
        
        color = colors[idx % len(colors)]
        
        print(f'\nTooth {tooth_id}:')
        print(f'  Total points: {actual_points}')
        print(f'  Eval range: {start_idx} ~ {end_idx} ({eval_points} points)')
        print(f'  Relative axial distance: 0 ~ {delta_L} mm')
        print(f'  Delta phi: {min(delta_phi_angles):.3f} ~ {max(delta_phi_angles):.3f} deg')
        print(f'  Tau angle: {tau_angle:.2f} deg')
        print(f'  Final angles (raw): {min(final_angles):.2f} ~ {max(final_angles):.2f} deg')
        
        # 子图1: 数据点分布（使用原始角度）
        axes[0, 0].scatter(final_angles, corrected_values, c=color, s=1, alpha=0.5, label=f'Tooth {tooth_id}')
        
        # 子图2: 曲线
        axes[0, 1].plot(final_angles, corrected_values, color=color, alpha=0.7, linewidth=0.8, label=f'Tooth {tooth_id}')
        
        # 子图3: 节距角位置
        axes[1, 0].axvline(x=tau_angle, color=color, linestyle='--', alpha=0.7, label=f'Tooth {tooth_id} tau={tau_angle:.1f} deg')
        
        # 子图4: Δφ变化
        axes[1, 1].plot(relative_positions, delta_phi_angles, color=color, alpha=0.7, label=f'Tooth {tooth_id}')
    
    axes[0, 0].set_xlabel('Rotation Angle (deg) - Raw')
    axes[0, 0].set_ylabel('Deviation (um)')
    axes[0, 0].set_title('First 3 Teeth Data Points (Eval Range)')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    axes[0, 1].set_xlabel('Rotation Angle (deg) - Raw')
    axes[0, 1].set_ylabel('Deviation (um)')
    axes[0, 1].set_title('First 3 Teeth Curves (Eval Range)')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    axes[1, 0].set_xlabel('Angle (deg)')
    axes[1, 0].set_title('Pitch Angle Position of Each Tooth')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    axes[1, 1].set_xlabel('Relative Axial Distance (mm)')
    axes[1, 1].set_ylabel('Delta Phi (deg)')
    axes[1, 1].set_title('Axial Rotation (Delta Phi) vs Relative Distance')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_file = os.path.join(current_dir, 'first_three_teeth_left_helix.png')
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
    
    print(f'\nLeft Helix Data: {len(flank_data.get("left", {}))} teeth')
    
    first_three = process_first_three_teeth_helix(flank_data, gear_data)
    
    if first_three:
        print(f'\nFirst 3 teeth: {first_three}')


if __name__ == '__main__':
    main()
