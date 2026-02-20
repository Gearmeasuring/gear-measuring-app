"""
检查齿向计算方法
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

module = gear_data.get('module', gear_data.get('模数', 0))
teeth_count = gear_data.get('teeth', gear_data.get('齿数', 0))
helix_angle = gear_data.get('helix_angle', gear_data.get('螺旋角', 0))
pitch_diameter = module * teeth_count

print(f'\n齿轮参数:')
print(f'  模数: {module} mm')
print(f'  齿数: {teeth_count}')
print(f'  螺旋角: {helix_angle}°')
print(f'  节圆直径: {pitch_diameter} mm')

start_eval = gear_data.get('helix_eval_start', None)
end_eval = gear_data.get('helix_eval_end', None)
start_meas = gear_data.get('helix_meas_start', 0.0)
end_meas = gear_data.get('helix_meas_end', 42.0)

print(f'\n评价范围:')
print(f'  起评点: {start_eval} mm')
print(f'  终评点: {end_eval} mm')
print(f'  起测点: {start_meas} mm')
print(f'  终测点: {end_meas} mm')

print(f'\n当前计算方法（错误）:')
print(f'  使用绝对轴向位置 L = {start_eval} ~ {end_eval} mm')
delta_phi_wrong = 2 * np.array([start_eval, end_eval]) * np.tan(np.radians(helix_angle)) / pitch_diameter
delta_phi_wrong_deg = np.degrees(delta_phi_wrong)
print(f'  Δφ = {delta_phi_wrong_deg[0]:.3f} ~ {delta_phi_wrong_deg[1]:.3f}°')

print(f'\n正确计算方法:')
print(f'  使用相对轴向距离 ΔL = 0 ~ (终评点 - 起评点) = 0 ~ {end_eval - start_eval} mm')
delta_L = end_eval - start_eval
delta_phi_correct = 2 * np.array([0, delta_L]) * np.tan(np.radians(helix_angle)) / pitch_diameter
delta_phi_correct_deg = np.degrees(delta_phi_correct)
print(f'  Δφ = {delta_phi_correct_deg[0]:.3f} ~ {delta_phi_correct_deg[1]:.3f}°')

print(f'\n角度计算对比（以齿2为例，τ = 4.14°）:')
tau = 4.14
print(f'  错误方法: φ = τ - Δφ = {tau} - ({delta_phi_wrong_deg[0]:.3f} ~ {delta_phi_wrong_deg[1]:.3f})')
print(f'           = {tau - delta_phi_wrong_deg[1]:.2f} ~ {tau - delta_phi_wrong_deg[0]:.2f}°')
print(f'  正确方法: φ = τ - Δφ = {tau} - ({delta_phi_correct_deg[0]:.3f} ~ {delta_phi_correct_deg[1]:.3f})')
print(f'           = {tau - delta_phi_correct_deg[1]:.2f} ~ {tau - delta_phi_correct_deg[0]:.2f}°')
