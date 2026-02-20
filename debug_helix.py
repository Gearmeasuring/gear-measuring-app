"""
调试齿向数据处理
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
print(f'  模数: {module}')
print(f'  齿数: {teeth_count}')
print(f'  螺旋角: {helix_angle}')

print('\n齿向评价范围参数:')
start_eval = gear_data.get('helix_eval_start', None)
end_eval = gear_data.get('helix_eval_end', None)
start_meas = gear_data.get('helix_meas_start', 0.0)
end_meas = gear_data.get('helix_meas_end', 42.0)
print(f'  helix_eval_start: {start_eval}')
print(f'  helix_eval_end: {end_eval}')
print(f'  helix_meas_start: {start_meas}')
print(f'  helix_meas_end: {end_meas}')

print('\n左齿向数据:')
if 'left' in flank_data:
    sorted_teeth = sorted(flank_data['left'].keys())[:3]
    print(f'  前三个齿: {sorted_teeth}')
    
    for tooth_id in sorted_teeth:
        tooth_values = flank_data['left'][tooth_id]
        actual_points = len(tooth_values)
        print(f'\n  齿{tooth_id}:')
        print(f'    总数据点数: {actual_points}')
        
        # 计算评价范围索引
        if start_eval is not None and end_eval is not None and end_meas > start_meas:
            eval_start_ratio = (start_eval - start_meas) / (end_meas - start_meas)
            eval_end_ratio = (end_eval - start_meas) / (end_meas - start_meas)
            start_idx = int(actual_points * max(0.0, min(1.0, eval_start_ratio)))
            end_idx = int(actual_points * max(0.0, min(1.0, eval_end_ratio)))
            print(f'    eval_start_ratio: {eval_start_ratio:.4f}')
            print(f'    eval_end_ratio: {eval_end_ratio:.4f}')
            print(f'    start_idx: {start_idx}')
            print(f'    end_idx: {end_idx}')
            print(f'    评价范围内点数: {end_idx - start_idx}')
        else:
            print(f'    使用默认范围: 0 到 {actual_points}')
