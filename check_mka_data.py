"""
检查MKA文件中的数据结构
"""
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file

mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"

print("解析MKA文件...")
parsed_data = parse_mka_file(mka_file)

print("\n" + "="*70)
print("数据结构检查")
print("="*70)

print("\n【顶层键】:")
for key in parsed_data.keys():
    print(f"  - {key}")

print("\n【gear_data】:")
gear_data = parsed_data.get('gear_data', {})
for key, value in gear_data.items():
    print(f"  {key}: {value}")

print("\n【measurements】:")
measurements = parsed_data.get('measurements', {})
print(f"  类型: {type(measurements)}")

if isinstance(measurements, dict):
    for key in measurements.keys():
        print(f"  - {key}")
        sub_data = measurements[key]
        if isinstance(sub_data, dict):
            for sub_key in sub_data.keys():
                print(f"      - {sub_key}")
                if isinstance(sub_data[sub_key], dict):
                    tooth_ids = list(sub_data[sub_key].keys())[:3]
                    print(f"          齿ID示例: {tooth_ids}")
                    if tooth_ids:
                        sample_data = sub_data[sub_key][tooth_ids[0]]
                        print(f"          数据类型: {type(sample_data)}")
                        if isinstance(sample_data, dict):
                            print(f"          数据键: {list(sample_data.keys())}")
                        elif hasattr(sample_data, '__len__'):
                            print(f"          数据长度: {len(sample_data)}")

print("\n【topography_data】:")
topo_data = parsed_data.get('topography_data', {})
print(f"  类型: {type(topo_data)}")
if isinstance(topo_data, dict):
    for key in topo_data.keys():
        print(f"  - {key}")

print("\n【其他数据】:")
for key in ['header', 'evaluation', 'tolerances']:
    if key in parsed_data:
        print(f"  - {key}: {type(parsed_data[key])}")
