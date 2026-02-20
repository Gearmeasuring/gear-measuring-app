"""
检查MKA文件中的左右齿向数据
"""
import os
import sys
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
print(f'  模数: {module} mm')
print(f'  齿数: {teeth_count}')
print(f'  螺旋角: {helix_angle}°')

print('\n齿向数据:')
print(f'  左齿向齿数: {len(flank_data.get("left", {}))}')
print(f'  右齿向齿数: {len(flank_data.get("right", {}))}')

# 检查第一个齿的数据
if flank_data.get('left'):
    first_left = list(flank_data['left'].keys())[0]
    left_values = flank_data['left'][first_left]
    print(f'\n左齿向第一个齿({first_left}):')
    print(f'  数据点数: {len(left_values)}')
    print(f'  前5个值: {left_values[:5]}')
    print(f'  后5个值: {left_values[-5:]}')

if flank_data.get('right'):
    first_right = list(flank_data['right'].keys())[0]
    right_values = flank_data['right'][first_right]
    print(f'\n右齿向第一个齿({first_right}):')
    print(f'  数据点数: {len(right_values)}')
    print(f'  前5个值: {right_values[:5]}')
    print(f'  后5个值: {right_values[-5:]}')

# 检查评价范围
print('\n评价范围:')
print(f"  左齿向起评点: {gear_data.get('helix_eval_start', 'N/A')}")
print(f"  左齿向终评点: {gear_data.get('helix_eval_end', 'N/A')}")
