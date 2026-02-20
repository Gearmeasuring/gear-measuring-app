"""
查看MKA文件中所有可用的参数
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

print('\n所有可用的参数键:')
for key in sorted(gear_data.keys()):
    value = gear_data[key]
    if isinstance(value, dict):
        print(f"  {key}: {value}")
    else:
        print(f"  {key}: {value}")
