"""检查MKA文件中的齿数据索引"""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file

mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"

parsed_data = parse_mka_file(mka_file)
gear_data = parsed_data.get('gear_data', {})
teeth_count = gear_data.get('teeth', 87)

print(f"齿轮齿数: {teeth_count}")
print()

profile_data = parsed_data.get('profile_data', {})
flank_data = parsed_data.get('flank_data', {})

for side, name in [('left', '左齿形'), ('right', '右齿形')]:
    data_dict = profile_data.get(side, {})
    tooth_ids = sorted(data_dict.keys())
    print(f"{name}齿索引: {tooth_ids}")
    print(f"  数量: {len(tooth_ids)}")
    
    missing = [i for i in range(teeth_count) if i not in tooth_ids]
    if missing:
        print(f"  缺失索引: {missing}")
    print()

for side, name in [('left', '左齿向'), ('right', '右齿向')]:
    data_dict = flank_data.get(side, {})
    tooth_ids = sorted(data_dict.keys())
    print(f"{name}齿索引: {tooth_ids}")
    print(f"  数量: {len(tooth_ids)}")
    
    missing = [i for i in range(teeth_count) if i not in tooth_ids]
    if missing:
        print(f"  缺失索引: {missing}")
    print()
