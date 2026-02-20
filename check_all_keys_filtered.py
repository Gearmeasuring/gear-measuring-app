"""
查看MKA文件中所有可用的参数（过滤）
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

keywords = ['齿形', '齿向', '起评', '终评', '展长', '起测', '终测', 'd1', 'd2', 'b1', 'b2']

print('\n\n匹配的参数键:')
for key in sorted(gear_data.keys()):
    if any(kw in key for kw in keywords):
        value = gear_data[key]
        print(f"  {key}: {value}")

print('\n\n所有字典类型的键:')
for key in sorted(gear_data.keys()):
    if isinstance(gear_data[key], dict):
        print(f"  {key}: {gear_data[key]}")
