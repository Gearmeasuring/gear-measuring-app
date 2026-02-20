"""
放大显示前三个齿的合并曲线
"""

import os
import sys
import math
import numpy as np
import matplotlib.pyplot as plt

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from analysis.ripple_analyzer import (
    RippleAnalyzer, GearParameters, EvaluationRange,
    DataType, Side, DataPreprocessor, AngleSynthesizer, CurveMerger
)
from utils.file_parser import parse_mka_file

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def plot_single_tooth(tooth_values, tooth_id, data_type, side, gear_params, 
                      eval_range, ax, color, title_suffix=""):
    """绘制单个齿的曲线"""
    
    preprocessor = DataPreprocessor()
    synthesizer = AngleSynthesizer(gear_params)
    merger = CurveMerger(gear_params, preprocessor, synthesizer)
    
    if tooth_values is None or len(tooth_values) < 3:
        ax.text(0.5, 0.5, '数据不足', ha='center', va='center', fontsize=12)
        return None, None
    
    corrected_values, positions = merger.process_tooth_data(tooth_values, eval_range, data_type)
    
    if len(corrected_values) < 3:
        ax.text(0.5, 0.5, '数据不足', ha='center', va='center', fontsize=12)
        return None, None
    
    tooth_index = int(tooth_id) if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
    
    if data_type == DataType.PROFILE:
        roll_lengths = positions
        angles = synthesizer.synthesize_profile_angles_from_roll(roll_lengths, tooth_index, side)
        x_label = '旋转角度 (°)'
        position_info = f"展长范围: {roll_lengths[0]:.2f} ~ {roll_lengths[-1]:.2f} mm"
    else:
        axial_positions = positions
        angles = synthesizer.synthesize_helix_angles(axial_positions, tooth_index, eval_range, side)
        x_label = '旋转角度 (°)'
        position_info = f"轴向范围: {axial_positions[0]:.2f} ~ {axial_positions[-1]:.2f} mm"
    
    angles = np.array(angles)
    angles = angles % 360.0
    angles[angles < 0] += 360.0
    
    ax.scatter(angles, corrected_values, c=color, s=50, alpha=0.8, 
              label=f'数据点 ({len(angles)}个)', zorder=5)
    ax.plot(angles, corrected_values, c=color, alpha=0.5, linewidth=2)
    
    ax.set_xlabel(x_label, fontsize=10)
    ax.set_ylabel('偏差值 (μm)', fontsize=10)
    ax.set_title(f'齿 {tooth_id}{title_suffix}', fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right', fontsize=8)
    
    angle_range = max(angles) - min(angles)
    angle_center = (max(angles) + min(angles)) / 2
    ax.set_xlim(angle_center - angle_range * 0.6, angle_center + angle_range * 0.6)
    
    if len(corrected_values) > 0:
        y_range = max(corrected_values) - min(corrected_values)
        y_center = (max(corrected_values) + min(corrected_values)) / 2
        ax.set_ylim(y_center - y_range * 0.7, y_center + y_range * 0.7)
    
    info_text = f"角度范围: {min(angles):.2f}° ~ {max(angles):.2f}°\n{position_info}"
    ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=8,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    return angles, corrected_values


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
    print(f"  节距角: {params.pitch_angle:.4f}°")
    
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
    
    directions = [
        ('left', 'profile', '左齿形', profile_data, profile_eval_range),
        ('right', 'profile', '右齿形', profile_data, profile_eval_range),
        ('left', 'helix', '左齿向', flank_data, helix_eval_range),
        ('right', 'helix', '右齿向', flank_data, helix_eval_range),
    ]
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    for side_key, data_type_str, name, data_source, eval_range in directions:
        side = Side.LEFT if side_key == 'left' else Side.RIGHT
        data_type = DataType.PROFILE if data_type_str == 'profile' else DataType.HELIX
        
        tooth_data_dict = data_source.get(side_key, {})
        
        if not tooth_data_dict:
            print(f"\n{name}: 无数据")
            continue
        
        sorted_teeth = sorted(tooth_data_dict.keys())
        first_three_teeth = sorted_teeth[:3]
        
        print(f"\n{name}: 共 {len(sorted_teeth)} 个齿")
        print(f"  前3个齿: {first_three_teeth}")
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        fig.suptitle(f'{name} - 前三个齿放大显示\n' + 
                     f'(齿数={teeth_count}, 模数={module}mm, 螺旋角={helix_angle}°)', 
                     fontsize=12, fontweight='bold')
        
        for i, tooth_id in enumerate(first_three_teeth):
            tooth_values = tooth_data_dict[tooth_id]
            plot_single_tooth(
                tooth_values, tooth_id, data_type, side, params, 
                eval_range, axes[i], colors[i]
            )
        
        plt.tight_layout()
        
        output_file = os.path.join(current_dir, f'merged_curve_{side_key}_{data_type_str}_zoom.png')
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"  图表已保存: {output_file}")
        plt.close()
    
    print("\n所有图表生成完成!")


if __name__ == '__main__':
    main()
