"""
测试主程序中的齿向数据处理
"""
import os
import sys
sys.path.insert(0, os.path.join(os.getcwd(), 'gear_analysis_refactored'))
from utils.file_parser import parse_mka_file
from 齿轮波纹度软件2_修改版_simplified import GearDataViewer

mka_file = '263751-018-WAV.mka'
if not os.path.exists(mka_file):
    mka_file = '004-xiaoxiao1.mka'

print(f'读取文件: {mka_file}')
parsed_data = parse_mka_file(mka_file)

# 创建GearDataViewer实例
viewer = GearDataViewer()
viewer.gear_data = parsed_data.get('gear_data', {})
viewer.flank_data = parsed_data.get('flank_data', {})

print('\n齿轮参数:')
print(f"  模数: {viewer.gear_data.get('module', viewer.gear_data.get('模数', 0))}")
print(f"  齿数: {viewer.gear_data.get('teeth', viewer.gear_data.get('齿数', 0))}")
print(f"  螺旋角: {viewer.gear_data.get('helix_angle', viewer.gear_data.get('螺旋角', 0))}")

print('\n评价范围参数:')
print(f"  helix_eval_start: {viewer.gear_data.get('helix_eval_start', None)}")
print(f"  helix_eval_end: {viewer.gear_data.get('helix_eval_end', None)}")
print(f"  helix_meas_start: {viewer.gear_data.get('helix_meas_start', 0.0)}")
print(f"  helix_meas_end: {viewer.gear_data.get('helix_meas_end', 42.0)}")

print('\n处理左齿向数据...')
result = viewer.process_helix_data('left')

if result:
    print(f"  成功！")
    print(f"  数据点数: {len(result['angles'])}")
    print(f"  角度范围: {min(result['angles']):.2f}° ~ {max(result['angles']):.2f}°")
    print(f"  数值范围: {min(result['values']):.2f} ~ {max(result['values']):.2f}")
else:
    print("  失败！返回None")
