"""
显示合并曲线的前三个齿图形
"""

import os
import sys
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from analysis.ripple_analyzer import (
    RippleAnalyzer, GearParameters, EvaluationRange,
    DataType, Side, DataPreprocessor, AngleSynthesizer, CurveMerger
)
from utils.file_parser import parse_mka_file

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def plot_first_three_teeth(tooth_data_dict, data_type, side, gear_params, 
                           eval_range, ax, title):
    """绘制前三个齿的合并曲线"""
    
    preprocessor = DataPreprocessor()
    synthesizer = AngleSynthesizer(gear_params)
    merger = CurveMerger(gear_params, preprocessor, synthesizer)
    
    sorted_teeth = sorted(tooth_data_dict.keys())
    first_three_teeth = sorted_teeth[:3]
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    markers = ['o', 's', '^']
    
    all_angles = []
    all_values = []
    
    for i, tooth_id in enumerate(first_three_teeth):
        tooth_values = tooth_data_dict[tooth_id]
        if tooth_values is None or len(tooth_values) < 3:
            continue
        
        corrected_values, positions = merger.process_tooth_data(tooth_values, eval_range)
        
        if len(corrected_values) < 3:
            continue
        
        tooth_index = int(tooth_id) if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
        
        if data_type == DataType.PROFILE:
            diameters = positions
            angles = synthesizer.synthesize_profile_angles(diameters, tooth_index, side)
        else:
            axial_positions = positions
            angles = synthesizer.synthesize_helix_angles(axial_positions, tooth_index, eval_range, side)
        
        angles = np.array(angles)
        angles = angles % 360.0
        angles[angles < 0] += 360.0
        
        ax.scatter(angles, corrected_values, c=colors[i], marker=markers[i], 
                  s=30, alpha=0.7, label=f'齿 {tooth_id}')
        
        ax.plot(angles, corrected_values, c=colors[i], alpha=0.3, linewidth=1)
        
        all_angles.extend(angles.tolist())
        all_values.extend(corrected_values.tolist())
    
    if all_angles:
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        
        ax.plot(all_angles, all_values, 'k-', alpha=0.5, linewidth=1.5, label='合并曲线')
    
    ax.set_xlabel('旋转角度 (°)', fontsize=10)
    ax.set_ylabel('偏差值 (μm)', fontsize=10)
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.set_xlim(0, 360)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right', fontsize=8)
    
    if all_values is not None and len(all_values) > 0:
        y_range = max(all_values) - min(all_values)
        y_center = (max(all_values) + min(all_values)) / 2
        ax.set_ylim(y_center - y_range * 0.7, y_center + y_range * 0.7)


def main():
    """主函数"""
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    
    if not os.path.exists(mka_file):
        print(f"文件不存在: {mka_file}")
        return
    
    print(f"读取文件: {mka_file}")
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 18.6)
    helix_angle = gear_data.get('helix_angle', 25.3)
    
    params = GearParameters(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle
    )
    
    print(f"\n齿轮参数:")
    print(f"  齿数: {params.teeth_count}")
    print(f"  模数: {params.module} mm")
    print(f"  压力角: {params.pressure_angle}°")
    print(f"  螺旋角: {params.helix_angle}°")
    print(f"  基圆直径: {params.base_diameter:.3f} mm")
    print(f"  节圆直径: {params.pitch_diameter:.3f} mm")
    
    profile_eval_range = EvaluationRange(
        eval_start=gear_data.get('profile_eval_start', 174.822),
        eval_end=gear_data.get('profile_eval_end', 180.603),
        meas_start=gear_data.get('profile_meas_start', 174.822),
        meas_end=gear_data.get('profile_meas_end', 180.603)
    )
    
    helix_eval_range = EvaluationRange(
        eval_start=gear_data.get('helix_eval_start', 2.1),
        eval_end=gear_data.get('helix_eval_end', 39.9),
        meas_start=gear_data.get('helix_meas_start', 2.1),
        meas_end=gear_data.get('helix_meas_end', 39.9)
    )
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'合并曲线前三个齿显示 (齿数={teeth_count}, 模数={module}mm)\n' + 
                 f'压力角={pressure_angle}°, 螺旋角={helix_angle}°', 
                 fontsize=12, fontweight='bold')
    
    directions = [
        ('left', 'profile', '左齿形', profile_data, profile_eval_range, axes[0, 0]),
        ('right', 'profile', '右齿形', profile_data, profile_eval_range, axes[0, 1]),
        ('left', 'helix', '左齿向', flank_data, helix_eval_range, axes[1, 0]),
        ('right', 'helix', '右齿向', flank_data, helix_eval_range, axes[1, 1]),
    ]
    
    for side_key, data_type_str, name, data_source, eval_range, ax in directions:
        side = Side.LEFT if side_key == 'left' else Side.RIGHT
        data_type = DataType.PROFILE if data_type_str == 'profile' else DataType.HELIX
        
        tooth_data_dict = data_source.get(side_key, {})
        
        if tooth_data_dict:
            sorted_teeth = sorted(tooth_data_dict.keys())
            print(f"\n{name}: 共 {len(sorted_teeth)} 个齿")
            print(f"  前3个齿: {sorted_teeth[:3]}")
            
            plot_first_three_teeth(
                tooth_data_dict, data_type, side, params, eval_range, ax, name
            )
        else:
            ax.text(0.5, 0.5, '无数据', ha='center', va='center', fontsize=14)
            ax.set_title(name, fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    
    output_file = os.path.join(current_dir, 'merged_curve_first_three_teeth.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n图表已保存: {output_file}")
    
    plt.show()


if __name__ == '__main__':
    main()
