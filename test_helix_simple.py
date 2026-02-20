"""
简单测试齿向数据处理
"""
import os
import sys
import numpy as np
sys.path.insert(0, os.path.join(os.getcwd(), 'gear_analysis_refactored'))
from utils.file_parser import parse_mka_file

mka_file = '263751-018-WAV.mka'
if not os.path.exists(mka_file):
    mka_file = '004-xiaoxiao1.mka'

print(f'读取文件: {mka_file}')
parsed_data = parse_mka_file(mka_file)
gear_data = parsed_data.get('gear_data', {})
flank_data = parsed_data.get('flank_data', {})

print('\n齿轮参数:')
module = gear_data.get('module', gear_data.get('模数', 0))
teeth_count = gear_data.get('teeth', gear_data.get('齿数', 0))
helix_angle = gear_data.get('helix_angle', gear_data.get('螺旋角', 0))
pitch_diameter = module * teeth_count
print(f'  模数: {module}')
print(f'  齿数: {teeth_count}')
print(f'  螺旋角: {helix_angle}')
print(f'  节圆直径: {pitch_diameter}')

print('\n评价范围参数:')
start_eval = gear_data.get('helix_eval_start', None)
end_eval = gear_data.get('helix_eval_end', None)
start_meas = gear_data.get('helix_meas_start', 0.0)
end_meas = gear_data.get('helix_meas_end', 42.0)
print(f'  helix_eval_start: {start_eval}')
print(f'  helix_eval_end: {end_eval}')
print(f'  helix_meas_start: {start_meas}')
print(f'  helix_meas_end: {end_meas}')

print('\n处理左齿向数据...')
if 'left' in flank_data:
    sorted_teeth = sorted(flank_data['left'].keys())
    print(f'  总齿数: {len(sorted_teeth)}')
    
    all_angles = []
    all_values = []
    
    for tooth_id in sorted_teeth[:3]:  # 只处理前3个齿
        tooth_values = flank_data['left'][tooth_id]
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
        
        eval_values = tooth_values[start_idx:end_idx]
        eval_points = len(eval_values)
        
        if eval_points < 3:
            print(f'  齿{tooth_id}: 评价范围内点数不足({eval_points})，跳过')
            continue
        
        # 计算角度
        pitch_angle_deg = 360.0 / teeth_count
        tooth_index = int(tooth_id) - 1
        tau_angle = tooth_index * pitch_angle_deg
        
        # 计算轴向旋转
        if abs(helix_angle) > 0.01:
            point_positions = np.linspace(0, 10, eval_points)
            delta_phi_angles = 2 * point_positions * np.tan(np.radians(helix_angle)) / pitch_diameter
            delta_phi_angles = np.degrees(delta_phi_angles)
        else:
            delta_phi_angles = np.linspace(0, 1, eval_points)
        
        final_angles = tau_angle - delta_phi_angles
        final_angles = final_angles % 360.0
        
        all_angles.extend(final_angles.tolist() if hasattr(final_angles, 'tolist') else final_angles)
        all_values.extend(eval_values)
        
        print(f'  齿{tooth_id}: 评价范围{start_idx}~{end_idx} ({eval_points}点), 角度范围{min(final_angles):.2f}~{max(final_angles):.2f}°')
    
    print(f'\n总计: {len(all_angles)}个数据点')
    if all_angles:
        print(f'  角度范围: {min(all_angles):.2f}° ~ {max(all_angles):.2f}°')
        print(f'  数值范围: {min(all_values):.2f} ~ {max(all_values):.2f}')
else:
    print('  没有左齿向数据')
