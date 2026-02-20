"""
查看MKA文件中的起评点和终评点
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

print('\n齿形评价范围:')
print(f"  齿形起评点展长 (left): {gear_data.get('齿形起评点展长', {}).get('left', 'N/A')}")
print(f"  齿形终评点展长 (left): {gear_data.get('齿形终评点展长', {}).get('left', 'N/A')}")
print(f"  齿形起评点直径 (left): {gear_data.get('齿形起评点直径', {}).get('left', 'N/A')}")
print(f"  齿形终评点直径 (left): {gear_data.get('齿形终评点直径', {}).get('left', 'N/A')}")

print('\n齿向评价范围:')
print(f"  齿向起评点 (left): {gear_data.get('齿向起评点', {}).get('left', 'N/A')}")
print(f"  齿向终评点 (left): {gear_data.get('齿向终评点', {}).get('left', 'N/A')}")

print('\n其他相关参数:')
print(f"  齿形起测点展长 (left): {gear_data.get('齿形起测点展长', {}).get('left', 'N/A')}")
print(f"  齿形终测点展长 (left): {gear_data.get('齿形终测点展长', {}).get('left', 'N/A')}")
print(f"  齿向起测点 (left): {gear_data.get('齿向起测点', {}).get('left', 'N/A')}")
print(f"  齿向终测点 (left): {gear_data.get('齿向终测点', {}).get('left', 'N/A')}")
