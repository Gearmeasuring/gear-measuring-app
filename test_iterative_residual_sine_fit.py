#!/usr/bin/env python3
"""
测试迭代残差正弦拟合算法
验证修改后的算法是否能够正确生成均匀分布的频率值，并对评价区域中的平均曲线进行分析
"""

import sys
import os
import numpy as np
from dataclasses import dataclass

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum特斯特 import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings
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

# 生成测试数据
def generate_test_data(teeth_count=87, num_teeth=5, num_points=100):
    """生成测试数据"""
    profile_data = {}
    flank_data = {}
    
    # 为每个齿生成数据
    for tooth_id in range(num_teeth):
        # 生成含有多个阶次的测试数据
        x = np.linspace(0, 2 * np.pi, num_points)
        
        # 生成含有ZE及其倍数阶次的信号
        signal = np.zeros_like(x)
        
        # 添加ZE阶次（87）
        signal += 0.2 * np.sin(teeth_count * x + 0.1 * tooth_id)
        
        # 添加2ZE阶次（174）
        signal += 0.1 * np.sin(2 * teeth_count * x + 0.2 * tooth_id)
        
        # 添加3ZE阶次（261）
        signal += 0.06 * np.sin(3 * teeth_count * x + 0.3 * tooth_id)
        
        # 添加4ZE阶次（348）
        signal += 0.04 * np.sin(4 * teeth_count * x + 0.4 * tooth_id)
        
        # 添加噪声
        signal += 0.02 * np.random.randn(len(x))
        
        # 添加线性趋势
        signal += 0.0001 * x
        
        profile_data[tooth_id] = signal.tolist()
        flank_data[tooth_id] = signal.tolist()
    
    return profile_data, flank_data

def test_iterative_residual_sine_fit():
    """测试迭代残差正弦拟合算法"""
    print("=== 测试迭代残差正弦拟合算法 ===")
    
    # 创建基本信息
    basic_info = BasicInfo()
    
    # 生成测试数据
    profile_data, flank_data = generate_test_data()
    
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
    print("1. 测试数据获取")
    print(f"Profile data: {len(profile_data)} teeth")
    print(f"Flank data: {len(flank_data)} teeth")
    
    # 计算四个方向的最大阶的幅值和频率
    print("\n2. 计算四个方向的最大阶的幅值和频率")
    
    # 右齿形
    print("\n=== 右齿形 (Profile Right) ===")
    orders_pr, amplitudes_pr = report._calculate_spectrum(profile_data, basic_info.teeth)
    if len(orders_pr) > 0:
        max_idx_pr = np.argmax(amplitudes_pr)
        max_order_pr = orders_pr[max_idx_pr]
        max_amp_pr = amplitudes_pr[max_idx_pr]
        print(f"最大阶: 频率 = {max_order_pr}, 幅值 = {max_amp_pr:.4f} μm")
    else:
        print("没有找到频谱分量")
    
    # 左齿形
    print("\n=== 左齿形 (Profile Left) ===")
    orders_pl, amplitudes_pl = report._calculate_spectrum(profile_data, basic_info.teeth)
    if len(orders_pl) > 0:
        max_idx_pl = np.argmax(amplitudes_pl)
        max_order_pl = orders_pl[max_idx_pl]
        max_amp_pl = amplitudes_pl[max_idx_pl]
        print(f"最大阶: 频率 = {max_order_pl}, 幅值 = {max_amp_pl:.4f} μm")
    else:
        print("没有找到频谱分量")
    
    # 右齿向
    print("\n=== 右齿向 (Helix Right) ===")
    orders_hr, amplitudes_hr = report._calculate_spectrum(flank_data, basic_info.teeth)
    if len(orders_hr) > 0:
        max_idx_hr = np.argmax(amplitudes_hr)
        max_order_hr = orders_hr[max_idx_hr]
        max_amp_hr = amplitudes_hr[max_idx_hr]
        print(f"最大阶: 频率 = {max_order_hr}, 幅值 = {max_amp_hr:.4f} μm")
    else:
        print("没有找到频谱分量")
    
    # 左齿向
    print("\n=== 左齿向 (Helix Left) ===")
    orders_hl, amplitudes_hl = report._calculate_spectrum(flank_data, basic_info.teeth)
    if len(orders_hl) > 0:
        max_idx_hl = np.argmax(amplitudes_hl)
        max_order_hl = orders_hl[max_idx_hl]
        max_amp_hl = amplitudes_hl[max_idx_hl]
        print(f"最大阶: 频率 = {max_order_hl}, 幅值 = {max_amp_hl:.4f} μm")
    else:
        print("没有找到频谱分量")
    
    # 测试PDF生成
    print("\n3. 测试PDF生成")
    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
        
        with PdfPages('test_iterative_residual_sine_fit.pdf') as pdf:
            report.create_page(pdf, measurement_data)
        print("Successfully generated PDF report")
    except Exception as e:
        print(f"Error generating PDF: {e}")
    
    print("\n=== 测试完成 ===")

def test_mka_file_analysis():
    """从MKA文件读取数据并分析四个方向的最大阶幅值和频率"""
    print("=== 从MKA文件读取数据并分析 ===")
    
    # MKA文件路径
    mka_file_path = "263751-018-WAV.mka"
    
    # 创建报告生成器
    settings = RippleSpectrumSettings()
    report = KlingelnbergRippleSpectrumReport(settings)
    
    try:
        # 从MKA文件读取数据
        print(f"1. 读取MKA文件: {mka_file_path}")
        parsed_data = parse_mka_file(mka_file_path)
        
        if parsed_data:
            # 提取齿轮基本数据
            gear_data = parsed_data.get('gear_data', {})
            teeth_count = gear_data.get('teeth', 87)
            
            # 提取测量数据
            profile_data = parsed_data.get('profile_data', {})
            flank_data = parsed_data.get('flank_data', {})
            
            # 获取各个方向的数据
            profile_left = profile_data.get('left', {})
            profile_right = profile_data.get('right', {})
            helix_left = flank_data.get('left', {})
            helix_right = flank_data.get('right', {})
            
            print(f"成功读取MKA文件，包含以下数据:")
            print(f"齿数: {teeth_count}")
            print(f"左齿形数据: {len(profile_left)} 个齿")
            print(f"右齿形数据: {len(profile_right)} 个齿")
            print(f"左齿向数据: {len(helix_left)} 个齿")
            print(f"右齿向数据: {len(helix_right)} 个齿")
            
            # 计算四个方向的最大阶、次大阶和一阶的幅值和频率
            print("\n2. 计算四个方向的最大阶、次大阶和一阶的幅值和频率")
            
            # 右齿形
            print("\n=== 右齿形 (Profile Right) ===")
            if profile_right:
                orders_pr, amplitudes_pr = report._calculate_spectrum(profile_right, teeth_count)
                if len(orders_pr) > 0:
                    # 计算最大阶
                    max_idx_pr = np.argmax(amplitudes_pr)
                    max_order_pr = orders_pr[max_idx_pr]
                    max_amp_pr = amplitudes_pr[max_idx_pr]
                    print(f"最大阶: 频率 = {max_order_pr}, 幅值 = {max_amp_pr:.4f} μm")
                    
                    # 计算次大阶
                    if len(orders_pr) > 1:
                        # 创建幅值的副本并将最大值设为-无穷，然后找新的最大值
                        amplitudes_pr_copy = amplitudes_pr.copy()
                        amplitudes_pr_copy[max_idx_pr] = -np.inf
                        second_max_idx_pr = np.argmax(amplitudes_pr_copy)
                        second_max_order_pr = orders_pr[second_max_idx_pr]
                        second_max_amp_pr = amplitudes_pr[second_max_idx_pr]
                        print(f"次大阶: 频率 = {second_max_order_pr}, 幅值 = {second_max_amp_pr:.4f} μm")
                    
                    # 计算一阶
                    if 1 in orders_pr:
                        first_order_idx_pr = np.where(orders_pr == 1)[0][0]
                        first_order_amp_pr = amplitudes_pr[first_order_idx_pr]
                        print(f"一阶: 频率 = 1, 幅值 = {first_order_amp_pr:.4f} μm")
                    else:
                        print("未找到一阶分量")
                else:
                    print("没有找到频谱分量")
            else:
                print("没有右齿形数据")
            
            # 左齿形
            print("\n=== 左齿形 (Profile Left) ===")
            if profile_left:
                orders_pl, amplitudes_pl = report._calculate_spectrum(profile_left, teeth_count)
                if len(orders_pl) > 0:
                    # 计算最大阶
                    max_idx_pl = np.argmax(amplitudes_pl)
                    max_order_pl = orders_pl[max_idx_pl]
                    max_amp_pl = amplitudes_pl[max_idx_pl]
                    print(f"最大阶: 频率 = {max_order_pl}, 幅值 = {max_amp_pl:.4f} μm")
                    
                    # 计算次大阶
                    if len(orders_pl) > 1:
                        amplitudes_pl_copy = amplitudes_pl.copy()
                        amplitudes_pl_copy[max_idx_pl] = -np.inf
                        second_max_idx_pl = np.argmax(amplitudes_pl_copy)
                        second_max_order_pl = orders_pl[second_max_idx_pl]
                        second_max_amp_pl = amplitudes_pl[second_max_idx_pl]
                        print(f"次大阶: 频率 = {second_max_order_pl}, 幅值 = {second_max_amp_pl:.4f} μm")
                    
                    # 计算一阶
                    if 1 in orders_pl:
                        first_order_idx_pl = np.where(orders_pl == 1)[0][0]
                        first_order_amp_pl = amplitudes_pl[first_order_idx_pl]
                        print(f"一阶: 频率 = 1, 幅值 = {first_order_amp_pl:.4f} μm")
                    else:
                        print("未找到一阶分量")
                else:
                    print("没有找到频谱分量")
            else:
                print("没有左齿形数据")
            
            # 右齿向
            print("\n=== 右齿向 (Helix Right) ===")
            if helix_right:
                orders_hr, amplitudes_hr = report._calculate_spectrum(helix_right, teeth_count)
                if len(orders_hr) > 0:
                    # 计算最大阶
                    max_idx_hr = np.argmax(amplitudes_hr)
                    max_order_hr = orders_hr[max_idx_hr]
                    max_amp_hr = amplitudes_hr[max_idx_hr]
                    print(f"最大阶: 频率 = {max_order_hr}, 幅值 = {max_amp_hr:.4f} μm")
                    
                    # 计算次大阶
                    if len(orders_hr) > 1:
                        amplitudes_hr_copy = amplitudes_hr.copy()
                        amplitudes_hr_copy[max_idx_hr] = -np.inf
                        second_max_idx_hr = np.argmax(amplitudes_hr_copy)
                        second_max_order_hr = orders_hr[second_max_idx_hr]
                        second_max_amp_hr = amplitudes_hr[second_max_idx_hr]
                        print(f"次大阶: 频率 = {second_max_order_hr}, 幅值 = {second_max_amp_hr:.4f} μm")
                    
                    # 计算一阶
                    if 1 in orders_hr:
                        first_order_idx_hr = np.where(orders_hr == 1)[0][0]
                        first_order_amp_hr = amplitudes_hr[first_order_idx_hr]
                        print(f"一阶: 频率 = 1, 幅值 = {first_order_amp_hr:.4f} μm")
                    else:
                        print("未找到一阶分量")
                else:
                    print("没有找到频谱分量")
            else:
                print("没有右齿向数据")
            
            # 左齿向
            print("\n=== 左齿向 (Helix Left) ===")
            if helix_left:
                orders_hl, amplitudes_hl = report._calculate_spectrum(helix_left, teeth_count)
                if len(orders_hl) > 0:
                    # 计算最大阶
                    max_idx_hl = np.argmax(amplitudes_hl)
                    max_order_hl = orders_hl[max_idx_hl]
                    max_amp_hl = amplitudes_hl[max_idx_hl]
                    print(f"最大阶: 频率 = {max_order_hl}, 幅值 = {max_amp_hl:.4f} μm")
                    
                    # 计算次大阶
                    if len(orders_hl) > 1:
                        amplitudes_hl_copy = amplitudes_hl.copy()
                        amplitudes_hl_copy[max_idx_hl] = -np.inf
                        second_max_idx_hl = np.argmax(amplitudes_hl_copy)
                        second_max_order_hl = orders_hl[second_max_idx_hl]
                        second_max_amp_hl = amplitudes_hl[second_max_idx_hl]
                        print(f"次大阶: 频率 = {second_max_order_hl}, 幅值 = {second_max_amp_hl:.4f} μm")
                    
                    # 计算一阶
                    if 1 in orders_hl:
                        first_order_idx_hl = np.where(orders_hl == 1)[0][0]
                        first_order_amp_hl = amplitudes_hl[first_order_idx_hl]
                        print(f"一阶: 频率 = 1, 幅值 = {first_order_amp_hl:.4f} μm")
                    else:
                        print("未找到一阶分量")
                else:
                    print("没有找到频谱分量")
            else:
                print("没有左齿向数据")
            
            # 创建简化的MeasurementData对象用于PDF生成
            class MockBasicInfo:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)
            
            mock_basic_info = MockBasicInfo(
                teeth=teeth_count,
                profile_eval_start=10.0,
                profile_eval_end=20.0,
                lead_eval_start=5.0,
                lead_eval_end=15.0
            )
            
            mock_measurement_data = MeasurementData(
                basic_info=mock_basic_info,
                profile_data=profile_right,  # 使用右齿形数据作为示例
                flank_data=helix_right,      # 使用右齿向数据作为示例
                tolerance=Tolerance()
            )
            
            # 测试PDF生成
            print("\n3. 测试PDF生成")
            try:
                import matplotlib.pyplot as plt
                from matplotlib.backends.backend_pdf import PdfPages
                
                with PdfPages('test_mka_file_analysis.pdf') as pdf:
                    report.create_page(pdf, mock_measurement_data)
                print("Successfully generated PDF report from MKA data")
            except Exception as e:
                print(f"Error generating PDF: {e}")
        else:
            print("无法从MKA文件读取数据")
            
    except Exception as e:
        print(f"Error reading MKA file: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== MKA文件分析完成 ===")

if __name__ == "__main__":
    test_mka_file_analysis()
