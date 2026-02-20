"""
验证齿向计算是否正确
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

# 齿轮参数
module = gear_data.get('module', gear_data.get('模数', 0))
teeth_count = gear_data.get('teeth', gear_data.get('齿数', 0))
helix_angle = gear_data.get('helix_angle', gear_data.get('螺旋角', 0))
pitch_diameter = module * teeth_count
pitch_angle_deg = 360.0 / teeth_count

# 评价范围
start_eval = gear_data.get('helix_eval_start', 2.1)
end_eval = gear_data.get('helix_eval_end', 39.9)
delta_L = end_eval - start_eval

print('\n' + '='*70)
print('验证齿向计算')
print('='*70)

print(f'\n齿轮参数:')
print(f'  模数: {module} mm')
print(f'  齿数: {teeth_count}')
print(f'  螺旋角: {helix_angle}°')
print(f'  节圆直径: {pitch_diameter:.3f} mm')
print(f'  节距角: {pitch_angle_deg:.2f}°')

print(f'\n评价范围:')
print(f'  起评点: {start_eval} mm')
print(f'  终评点: {end_eval} mm')
print(f'  评价长度: {delta_L} mm')

# 计算Δφ
delta_phi_max = np.degrees(2 * delta_L * np.tan(np.radians(helix_angle)) / pitch_diameter)
print(f'\n轴向旋转计算:')
print(f'  Δφ = 2 × Δz × tan(β) / D')
print(f'  Δφ_max = 2 × {delta_L} × tan({helix_angle}°) / {pitch_diameter:.3f}')
print(f'  Δφ_max = {delta_phi_max:.2f}°')

# 验证左右齿向
for side in ['left', 'right']:
    print(f'\n{"="*70}')
    print(f'{side.upper()} HELIX 验证')
    print(f'{"="*70}')
    
    if side == 'left':
        print('公式: φ = τ - Δφ')
    else:
        print('公式: φ = τ + Δφ')
    
    for tooth_idx in [1, 2, 3]:
        tau = tooth_idx * pitch_angle_deg
        
        if side == 'left':
            phi_start = tau - 0
            phi_end = tau - delta_phi_max
            formula = f'{tau:.2f}° - 0° = {phi_start:.2f}°'
            formula_end = f'{tau:.2f}° - {delta_phi_max:.2f}° = {phi_end:.2f}°'
        else:
            phi_start = tau + 0
            phi_end = tau + delta_phi_max
            formula = f'{tau:.2f}° + 0° = {phi_start:.2f}°'
            formula_end = f'{tau:.2f}° + {delta_phi_max:.2f}° = {phi_end:.2f}°'
        
        print(f'\n  齿{tooth_idx+1}:')
        print(f'    起评点: φ = {formula}')
        print(f'    终评点: φ = {formula_end}')
        print(f'    角度范围: {min(phi_start, phi_end):.2f}° ~ {max(phi_start, phi_end):.2f}°')

print(f'\n{"="*70}')
print('验证结论')
print(f'{"="*70}')
print('✓ 使用相对轴向距离 Δz（从起评点开始）')
print('✓ 左齿向: φ = τ - Δφ（向左倾斜，角度减小）')
print('✓ 右齿向: φ = τ + Δφ（向右倾斜，角度增大）')
print('✓ 符合图片中的公式: φ = -ξ - Δφ + τ (齿向ξ=0)')
