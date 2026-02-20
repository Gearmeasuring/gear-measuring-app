#!/usr/bin/env python3
"""
测试 Klingelnberg 波纹度频谱报告生成器
使用真实的MKA文件数据测试左齿形、右齿形、左齿向、右齿向的频谱分析
"""

import sys
import os
import numpy as np
from dataclasses import dataclass

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings
from gear_analysis_refactored.utils.file_parser import parse_mka_file

@dataclass
class BasicInfo:
    """基本信息类"""
    teeth: int = 87
    module: float = 1.0
    pressure_angle: float = 20.0
    helix_angle: float = 0.0
    drawing_no: str = "Test Drawing"
    customer: str = "Test Customer"
    order_no: str = "Test Order"
    type: str = "gear"
    program: str = "Test Program"
    date: str = "2026-01-31"
    profile_eval_start: float = 10.0
    profile_eval_end: float = 20.0
    profile_range_right: tuple = (5.0, 25.0)
    profile_range_left: tuple = (5.0, 25.0)
    lead_eval_start: float = 5.0
    lead_eval_end: float = 15.0
    lead_range_right: tuple = (0.0, 20.0)
    lead_range_left: tuple = (0.0, 20.0)

@dataclass
class MeasurementData:
    """测量数据类"""
    basic_info: BasicInfo
    profile_data: dict
    flank_data: dict
    tolerance: object = None

@dataclass
class Tolerance:
    """公差类"""
    ripple_tolerance_enabled: bool = True
    ripple_tolerance_R: float = 2.0
    ripple_tolerance_N0: float = 1.0
    ripple_tolerance_K: float = 0.0

def test_ripple_spectrum_with_mka():
    """使用MKA文件测试波纹度频谱报告生成器"""
    print("=== 测试 Klingelnberg 波纹度频谱报告生成器（使用真实MKA数据）===")

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
        return

    print(f"使用MKA文件: {mka_file}")

    # 解析MKA文件
    try:
        mka_data = parse_mka_file(mka_file)
        print(f"MKA文件解析成功")
        print(f"齿轮数据: {mka_data['gear_data']}")
    except Exception as e:
        print(f"解析MKA文件失败: {e}")
        return

    # 提取数据
    gear_data = mka_data['gear_data']
    profile_data = mka_data['profile_data']
    flank_data = mka_data['flank_data']
    pitch_data = mka_data.get('pitch_data', {})

    # 创建基本信息
    basic_info = BasicInfo(
        teeth=gear_data.get('teeth', 87),
        module=gear_data.get('module', 1.0),
        pressure_angle=gear_data.get('pressure_angle', 20.0),
        helix_angle=gear_data.get('helix_angle', 0.0),
        drawing_no=gear_data.get('drawing_no', 'Test Drawing'),
        customer=gear_data.get('customer', 'Test Customer'),
        order_no=gear_data.get('order_no', 'Test Order'),
        type=gear_data.get('type', 'gear'),
        program=gear_data.get('program', 'Test Program'),
        date=gear_data.get('date', '2026-01-31')
    )

    # 创建测量数据
    tolerance = Tolerance()
    measurement_data = MeasurementData(
        basic_info=basic_info,
        profile_data=profile_data,
        flank_data=flank_data,
        tolerance=tolerance
    )

    # 创建报告生成器
    settings = RippleSpectrumSettings()
    report = KlingelnbergRippleSpectrumReport(settings)

    # 测试数据获取
    print("\n1. 测试数据获取")
    print(f"Profile data: left={len(profile_data.get('left', {}))} teeth, right={len(profile_data.get('right', {}))} teeth")
    print(f"Flank data: left={len(flank_data.get('left', {}))} teeth, right={len(flank_data.get('right', {}))} teeth")

    # 测试频谱计算
    print("\n2. 测试频谱计算")

    # 导入必要的类
    from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import SpectrumParams

    # 测试Profile Right数据
    print("\n=== Profile Right ===")
    profile_right_data = profile_data.get('right', {})
    if profile_right_data:
        # 检查数据格式
        first_tooth_id = list(profile_right_data.keys())[0]
        first_tooth_data = profile_right_data[first_tooth_id]
        print(f"第一个齿号: {first_tooth_id}")
        print(f"第一个齿数据类型: {type(first_tooth_data)}")
        if isinstance(first_tooth_data, (list, np.ndarray)):
            print(f"第一个齿数据长度: {len(first_tooth_data)}")
            print(f"第一个齿数据前10个点: {first_tooth_data[:10]}")
        elif isinstance(first_tooth_data, dict):
            print(f"第一个齿数据键: {first_tooth_data.keys()}")

        params = SpectrumParams(
            data_dict=profile_right_data,
            teeth_count=basic_info.teeth,
            max_order=500,
            max_components=10,
            side="right",
            data_type="profile",
            info=basic_info,
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

    # 测试Profile Left数据
    print("\n=== Profile Left ===")
    profile_left_data = profile_data.get('left', {})
    if profile_left_data:
        # 检查数据格式
        first_tooth_id = list(profile_left_data.keys())[0]
        first_tooth_data = profile_left_data[first_tooth_id]
        print(f"第一个齿号: {first_tooth_id}")
        print(f"第一个齿数据类型: {type(first_tooth_data)}")
        if isinstance(first_tooth_data, (list, np.ndarray)):
            print(f"第一个齿数据长度: {len(first_tooth_data)}")
            print(f"第一个齿数据前10个点: {first_tooth_data[:10]}")
        elif isinstance(first_tooth_data, dict):
            print(f"第一个齿数据键: {first_tooth_data.keys()}")

        params = SpectrumParams(
            data_dict=profile_left_data,
            teeth_count=basic_info.teeth,
            max_order=500,
            max_components=10,
            side="left",
            data_type="profile",
            info=basic_info,
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

    # 测试Flank Right数据
    print("\n=== Flank Right ===")
    flank_right_data = flank_data.get('right', {})
    if flank_right_data:
        # 检查数据格式
        first_tooth_id = list(flank_right_data.keys())[0]
        first_tooth_data = flank_right_data[first_tooth_id]
        print(f"第一个齿号: {first_tooth_id}")
        print(f"第一个齿数据类型: {type(first_tooth_data)}")
        if isinstance(first_tooth_data, (list, np.ndarray)):
            print(f"第一个齿数据长度: {len(first_tooth_data)}")
            print(f"第一个齿数据前10个点: {first_tooth_data[:10]}")
        elif isinstance(first_tooth_data, dict):
            print(f"第一个齿数据键: {first_tooth_data.keys()}")

        params = SpectrumParams(
            data_dict=flank_right_data,
            teeth_count=basic_info.teeth,
            max_order=500,
            max_components=10,
            side="right",
            data_type="flank",
            info=basic_info,
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

    # 测试Flank Left数据
    print("\n=== Flank Left ===")
    flank_left_data = flank_data.get('left', {})
    if flank_left_data:
        # 检查数据格式
        first_tooth_id = list(flank_left_data.keys())[0]
        first_tooth_data = flank_left_data[first_tooth_id]
        print(f"第一个齿号: {first_tooth_id}")
        print(f"第一个齿数据类型: {type(first_tooth_data)}")
        if isinstance(first_tooth_data, (list, np.ndarray)):
            print(f"第一个齿数据长度: {len(first_tooth_data)}")
            print(f"第一个齿数据前10个点: {first_tooth_data[:10]}")
        elif isinstance(first_tooth_data, dict):
            print(f"第一个齿数据键: {first_tooth_data.keys()}")

        params = SpectrumParams(
            data_dict=flank_left_data,
            teeth_count=basic_info.teeth,
            max_order=500,
            max_components=10,
            side="left",
            data_type="flank",
            info=basic_info,
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

    # 测试PDF生成
    print("\n3. 测试PDF生成")
    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages

        with PdfPages('test_ripple_spectrum_mka.pdf') as pdf:
            report.create_page(pdf, measurement_data)
        print("Successfully generated PDF report: test_ripple_spectrum_mka.pdf")
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_ripple_spectrum_with_mka()
