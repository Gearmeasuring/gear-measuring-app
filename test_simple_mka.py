#!/usr/bin/env python3
"""
简单测试：检查MKA文件数据并输出到文件
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

from gear_analysis_refactored.utils.file_parser import parse_mka_file
from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings, SpectrumParams

# 设置输出编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 查找MKA文件
mka_files = [
    "263751-018-WAV.mka",
    "004-xiaoxiao1.mka"
]

mka_file = None
for file in mka_files:
    if os.path.exists(file):
        mka_file = file
        break

if mka_file is None:
    print("错误：未找到MKA文件")
    sys.exit(1)

print(f"使用MKA文件: {mka_file}")

# 解析MKA文件
try:
    mka_data = parse_mka_file(mka_file)
    print(f"MKA文件解析成功")
except Exception as e:
    print(f"解析MKA文件失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 提取数据
gear_data = mka_data['gear_data']
profile_data = mka_data['profile_data']
flank_data = mka_data['flank_data']
pitch_data = mka_data.get('pitch_data', {})

print(f"\n=== Profile数据 ===")
print(f"Profile Left: {len(profile_data.get('left', {}))} teeth")
print(f"Profile Right: {len(profile_data.get('right', {}))} teeth")

print(f"\n=== Flank数据 ===")
print(f"Flank Left: {len(flank_data.get('left', {}))} teeth")
print(f"Flank Right: {len(flank_data.get('right', {}))} teeth")

# 创建报告生成器
settings = RippleSpectrumSettings()
report = KlingelnbergRippleSpectrumReport(settings)

# 测试Profile Right
print("\n=== 测试 Profile Right ===")
profile_right_data = profile_data.get('right', {})
if profile_right_data:
    print(f"数据字典键: {list(profile_right_data.keys())[:5]}")
    first_tooth_id = list(profile_right_data.keys())[0]
    first_tooth_data = profile_right_data[first_tooth_id]
    print(f"第一个齿数据类型: {type(first_tooth_data)}")
    if isinstance(first_tooth_data, (list, np.ndarray)):
        print(f"第一个齿数据长度: {len(first_tooth_data)}")
        print(f"第一个齿数据前5个点: {first_tooth_data[:5]}")

    params = SpectrumParams(
        data_dict=profile_right_data,
        teeth_count=gear_data.get('teeth', 87),
        max_order=500,
        max_components=10,
        side="right",
        data_type="profile",
        info=gear_data,
        pitch_data=pitch_data.get('right')
    )

    try:
        orders, amplitudes, rms = report._calculate_spectrum(params)
        print(f"Orders: {orders}")
        print(f"Amplitudes: {amplitudes}")
        print(f"RMS: {rms:.4f}")
        print(f"Successfully calculated spectrum for Profile Right")
    except Exception as e:
        print(f"Error calculating spectrum for Profile Right: {e}")
        import traceback
        traceback.print_exc()
else:
    print("Profile Right data is empty")

# 测试Profile Left
print("\n=== 测试 Profile Left ===")
profile_left_data = profile_data.get('left', {})
if profile_left_data:
    print(f"数据字典键: {list(profile_left_data.keys())[:5]}")
    first_tooth_id = list(profile_left_data.keys())[0]
    first_tooth_data = profile_left_data[first_tooth_id]
    print(f"第一个齿数据类型: {type(first_tooth_data)}")
    if isinstance(first_tooth_data, (list, np.ndarray)):
        print(f"第一个齿数据长度: {len(first_tooth_data)}")
        print(f"第一个齿数据前5个点: {first_tooth_data[:5]}")

    params = SpectrumParams(
        data_dict=profile_left_data,
        teeth_count=gear_data.get('teeth', 87),
        max_order=500,
        max_components=10,
        side="left",
        data_type="profile",
        info=gear_data,
        pitch_data=pitch_data.get('left')
    )

    try:
        orders, amplitudes, rms = report._calculate_spectrum(params)
        print(f"Orders: {orders}")
        print(f"Amplitudes: {amplitudes}")
        print(f"RMS: {rms:.4f}")
        print(f"Successfully calculated spectrum for Profile Left")
    except Exception as e:
        print(f"Error calculating spectrum for Profile Left: {e}")
        import traceback
        traceback.print_exc()
else:
    print("Profile Left data is empty")

# 测试Flank Right
print("\n=== 测试 Flank Right ===")
flank_right_data = flank_data.get('right', {})
if flank_right_data:
    print(f"数据字典键: {list(flank_right_data.keys())[:5]}")
    first_tooth_id = list(flank_right_data.keys())[0]
    first_tooth_data = flank_right_data[first_tooth_id]
    print(f"第一个齿数据类型: {type(first_tooth_data)}")
    if isinstance(first_tooth_data, (list, np.ndarray)):
        print(f"第一个齿数据长度: {len(first_tooth_data)}")
        print(f"第一个齿数据前5个点: {first_tooth_data[:5]}")

    params = SpectrumParams(
        data_dict=flank_right_data,
        teeth_count=gear_data.get('teeth', 87),
        max_order=500,
        max_components=10,
        side="right",
        data_type="flank",
        info=gear_data,
        pitch_data=pitch_data.get('right')
    )

    try:
        orders, amplitudes, rms = report._calculate_spectrum(params)
        print(f"Orders: {orders}")
        print(f"Amplitudes: {amplitudes}")
        print(f"RMS: {rms:.4f}")
        print(f"Successfully calculated spectrum for Flank Right")
    except Exception as e:
        print(f"Error calculating spectrum for Flank Right: {e}")
        import traceback
        traceback.print_exc()
else:
    print("Flank Right data is empty")

# 测试Flank Left
print("\n=== 测试 Flank Left ===")
flank_left_data = flank_data.get('left', {})
if flank_left_data:
    print(f"数据字典键: {list(flank_left_data.keys())[:5]}")
    first_tooth_id = list(flank_left_data.keys())[0]
    first_tooth_data = flank_left_data[first_tooth_id]
    print(f"第一个齿数据类型: {type(first_tooth_data)}")
    if isinstance(first_tooth_data, (list, np.ndarray)):
        print(f"第一个齿数据长度: {len(first_tooth_data)}")
        print(f"第一个齿数据前5个点: {first_tooth_data[:5]}")

    params = SpectrumParams(
        data_dict=flank_left_data,
        teeth_count=gear_data.get('teeth', 87),
        max_order=500,
        max_components=10,
        side="left",
        data_type="flank",
        info=gear_data,
        pitch_data=pitch_data.get('left')
    )

    try:
        orders, amplitudes, rms = report._calculate_spectrum(params)
        print(f"Orders: {orders}")
        print(f"Amplitudes: {amplitudes}")
        print(f"RMS: {rms:.4f}")
        print(f"Successfully calculated spectrum for Flank Left")
    except Exception as e:
        print(f"Error calculating spectrum for Flank Left: {e}")
        import traceback
        traceback.print_exc()
else:
    print("Flank Left data is empty")

print("\n=== 测试完成 ===")
