"""
检查齿向数据
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

print('\n齿向数据:')
print(f"  左齿向齿数: {len(flank_data.get('left', {}))}")
print(f"  右齿向齿数: {len(flank_data.get('right', {}))}")

if flank_data.get('left'):
    first_tooth = list(flank_data['left'].keys())[0]
    print(f"  第一个齿({first_tooth})数据点数: {len(flank_data['left'][first_tooth])}")

print('\n齿向评价范围参数:')
print(f"  齿向起评点 (left): {gear_data.get('齿向起评点', {}).get('left', 'N/A')}")
print(f"  齿向终评点 (left): {gear_data.get('齿向终评点', {}).get('left', 'N/A')}")
print(f"  齿向起测点 (left): {gear_data.get('齿向起测点', {}).get('left', 'N/A')}")
print(f"  齿向终测点 (left): {gear_data.get('齿向终测点', {}).get('left', 'N/A')}")

# 测试计算
start_eval = gear_data.get('齿向起评点', {}).get('left', None)
end_eval = gear_data.get('齿向终评点', {}).get('left', None)
start_meas = gear_data.get('齿向起测点', {}).get('left', 0.0)
end_meas = gear_data.get('齿向终测点', {}).get('left', 42.0)

print('\n计算测试:')
print(f"  start_eval: {start_eval}")
print(f"  end_eval: {end_eval}")
print(f"  start_meas: {start_meas}")
print(f"  end_meas: {end_meas}")

if start_eval is not None and end_eval is not None and end_meas > start_meas:
    eval_start_ratio = (start_eval - start_meas) / (end_meas - start_meas)
    eval_end_ratio = (end_eval - start_meas) / (end_meas - start_meas)
    print(f"  eval_start_ratio: {eval_start_ratio}")
    print(f"  eval_end_ratio: {eval_end_ratio}")
    
    actual_points = 480  # 假设480个点
    start_idx = int(actual_points * max(0.0, min(1.0, eval_start_ratio)))
    end_idx = int(actual_points * max(0.0, min(1.0, eval_end_ratio)))
    print(f"  start_idx: {start_idx}")
    print(f"  end_idx: {end_idx}")
    print(f"  评价范围内点数: {end_idx - start_idx}")
