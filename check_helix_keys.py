"""
检查齿向参数的实际键名
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

print('\n所有键名:')
for key in sorted(gear_data.keys()):
    print(f"  {key}")

print('\n\n可能的齿向评价范围键:')
for key in sorted(gear_data.keys()):
    if 'helix' in key.lower() or 'flank' in key.lower() or 'b1' in key.lower() or 'b2' in key.lower():
        print(f"  {key}: {gear_data[key]}")
