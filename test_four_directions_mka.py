#!/usr/bin/env python3
"""
测试左齿形、右齿形、左齿向、右齿向的阶次分析
使用真实的MKA文件数据
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('..'))

from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings
from gear_analysis_refactored.utils.file_parser import MKAFileParser, parse_mka_file

class MockMeasurementData:
    """模拟测量数据对象"""
    def __init__(self, basic_info, profile_left=None, profile_right=None, helix_left=None, helix_right=None):
        self.basic_info = basic_info
        self.profile_left = profile_left or {}
        self.profile_right = profile_right or {}
        self.helix_left = helix_left or {}
        self.helix_right = helix_right or {}

class MockBasicInfo:
    """模拟基本信息对象"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

def load_mka_data(mka_file):
    """
    从MKA文件加载数据
    
    Args:
        mka_file: MKA文件路径
    
    Returns:
        MockMeasurementData: 模拟测量数据对象
    """
    try:
        # 解析MKA文件
        parsed_data = parse_mka_file(mka_file)
        
        # 获取基本信息
        gear_data = parsed_data.get('gear_data', {})
        
        # 创建模拟基本信息对象
        mock_info = MockBasicInfo(
            teeth=gear_data.get('teeth', 87),
            module=gear_data.get('module', 1.0),
            pressure_angle=gear_data.get('pressure_angle', 20.0),
            order_no=gear_data.get('order_no', '263751-018-WAV'),
            drawing_no=gear_data.get('drawing_no', '84-T3.2.47.02.76-G-WAV'),
            date=gear_data.get('date', '14.02.25'),
            time=gear_data.get('time', '21:04:11'),
            part_name=gear_data.get('part_name', ''),
            program=gear_data.get('program', '263751-018-WAV'),
            profile_range_left=(0.0, 0.0),
            profile_eval_start_left=0.2,
            profile_eval_end_left=0.8,
            profile_range_right=(0.0, 0.0),
            profile_eval_start_right=0.2,
            profile_eval_end_right=0.8,
            lead_range_left=(0.0, 0.0),
            lead_eval_start_left=0.2,
            lead_eval_end_left=0.8,
            lead_range_right=(0.0, 0.0),
            lead_eval_start_right=0.2,
            lead_eval_end_right=0.8
        )
        
        # 获取各个方向的数据
        profile_data = parsed_data.get('profile_data', {})
        flank_data = parsed_data.get('flank_data', {})
        
        profile_left = profile_data.get('left', {})
        profile_right = profile_data.get('right', {})
        helix_left = flank_data.get('left', {})
        helix_right = flank_data.get('right', {})
        
        # 创建模拟测量数据对象
        measurement_data = MockMeasurementData(
            basic_info=mock_info,
            profile_left=profile_left,
            profile_right=profile_right,
            helix_left=helix_left,
            helix_right=helix_right
        )
        
        print(f"✓ 成功加载MKA文件: {mka_file}")
        print(f"✓ 齿数: {gear_data.get('teeth', 'N/A')}")
        print(f"✓ 左齿形数据: {len(profile_left)}个齿")
        print(f"✓ 右齿形数据: {len(profile_right)}个齿")
        print(f"✓ 左齿向数据: {len(helix_left)}个齿")
        print(f"✓ 右齿向数据: {len(helix_right)}个齿")
        
        return measurement_data
        
    except Exception as e:
        print(f"✗ 加载MKA文件失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_direction(report, measurement_data, data_type, side):
    """
    分析指定方向的数据
    
    Args:
        report: KlingelnbergRippleSpectrumReport对象
        measurement_data: 测量数据对象
        data_type: 数据类型（'profile'或'flank'）
        side: 左侧或右侧
    
    Returns:
        dict: 分析结果
    """
    try:
        # 获取对应的数据
        if data_type == 'profile':
            if side == 'right':
                data_dict = getattr(measurement_data, 'profile_right', {})
            else:
                data_dict = getattr(measurement_data, 'profile_left', {})
        else:  # flank
            if side == 'right':
                data_dict = getattr(measurement_data, 'helix_right', {})
            else:
                data_dict = getattr(measurement_data, 'helix_left', {})
        
        if not data_dict:
            print(f"✗ {side} {data_type} 数据为空")
            return None
        
        # 获取基本信息
        info = getattr(measurement_data, 'basic_info', None)
        if not info:
            print(f"✗ 缺少基本信息")
            return None
        
        # 获取齿数
        teeth_count = getattr(info, 'teeth', 0)
        if not teeth_count or teeth_count <= 0:
            print(f"✗ 齿数无效 {teeth_count}")
            return None
        
        # 计算平均曲线
        avg_curve = report._calculate_average_curve(data_dict)
        if avg_curve is None:
            print(f"✗ 计算平均曲线失败")
            return None
        
        print(f"✓ {side} {data_type} 平均曲线长度: {len(avg_curve)}")
        
        # 应用RC低通滤波器
        filtered_curve = report._apply_rc_low_pass_filter(avg_curve)
        
        # 准备正弦拟合参数
        from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import SineFitParams
        fit_params = SineFitParams(
            curve_data=filtered_curve,
            ze=teeth_count,
            max_order=500,
            max_components=50
        )
        
        # 进行频谱分析
        spectrum = report._iterative_residual_sine_fit(fit_params)
        
        if spectrum:
            # 按幅值排序
            sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
            top_10 = sorted_spectrum[:10]
            
            print(f"✓ {side} {data_type} 分析完成，前10个阶次:")
            for order, amp in top_10:
                print(f"  阶次 {order}: {amp:.4f}μm")
            
            return {
                'spectrum': spectrum,
                'top_10': top_10,
                'curve': filtered_curve
            }
        else:
            print(f"✗ {side} {data_type} 频谱分析失败")
            return None
            
    except Exception as e:
        print(f"✗ 分析{side} {data_type}失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def plot_results(results, teeth_count):
    """
    绘制分析结果
    
    Args:
        results: 分析结果字典
        teeth_count: 齿数
    """
    try:
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'齿轮波纹度频谱分析 (ZE={teeth_count})', fontsize=16)
        
        directions = [
            ('Profile Right', 'profile_right', axes[0, 0]),
            ('Profile Left', 'profile_left', axes[0, 1]),
            ('Helix Right', 'helix_right', axes[1, 0]),
            ('Helix Left', 'helix_left', axes[1, 1])
        ]
        
        for direction_name, key, ax in directions:
            if key in results and results[key]:
                result = results[key]
                spectrum = result['spectrum']
                curve = result['curve']
                
                # 绘制频谱
                orders = list(spectrum.keys())
                amplitudes = list(spectrum.values())
                
                ax.scatter(orders, amplitudes, color='red', label='Spectrum')
                
                # 标记ZE倍数阶次
                ze_multiples = [teeth_count * i for i in range(1, 6)]
                for multiple in ze_multiples:
                    if multiple in spectrum:
                        ax.axvline(x=multiple, color='blue', linestyle='--', alpha=0.5)
                        ax.text(multiple, spectrum[multiple], f'ZE*{multiple//teeth_count}', 
                                color='blue', fontsize=8, rotation=90, verticalalignment='bottom')
                
                # 找到最大阶次
                if spectrum:
                    max_order = max(spectrum, key=spectrum.get)
                    max_amplitude = spectrum[max_order]
                    
                    # 绘制最大阶次的正弦曲线
                    x = np.linspace(0.0, 2.0 * np.pi, len(curve))
                    max_sine = max_amplitude * np.sin(max_order * x)
                    
                    # 创建第二个y轴
                    ax2 = ax.twinx()
                    ax2.plot(np.linspace(0, 100, len(curve)), max_sine, color='blue', label=f'Max Order {max_order}')
                    ax2.set_ylabel('Sine Wave (μm)', color='blue')
                    ax2.tick_params(axis='y', labelcolor='blue')
                    
                    # 添加图例
                    lines1, labels1 = ax.get_legend_handles_labels()
                    lines2, labels2 = ax2.get_legend_handles_labels()
                    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
                
                ax.set_title(direction_name)
                ax.set_xlabel('Order')
                ax.set_ylabel('Amplitude (μm)')
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, 500)
            else:
                ax.set_title(direction_name)
                ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.savefig('four_directions_analysis.png', dpi=150, bbox_inches='tight')
        print("✓ 图表保存为 four_directions_analysis.png")
        
    except Exception as e:
        print(f"✗ 绘制图表失败: {e}")

def main():
    """
    主函数
    """
    # MKA文件路径
    mka_file = '263751-018-WAV.mka'
    
    # 检查文件是否存在
    if not os.path.exists(mka_file):
        print(f"✗ MKA文件不存在: {mka_file}")
        return
    
    # 加载MKA数据
    measurement_data = load_mka_data(mka_file)
    if not measurement_data:
        return
    
    # 创建报告对象
    settings = RippleSpectrumSettings()
    report = KlingelnbergRippleSpectrumReport(settings)
    
    # 分析四个方向
    results = {}
    
    print("\n=== 分析右齿形 ===")
    results['profile_right'] = analyze_direction(report, measurement_data, 'profile', 'right')
    
    print("\n=== 分析左齿形 ===")
    results['profile_left'] = analyze_direction(report, measurement_data, 'profile', 'left')
    
    print("\n=== 分析右齿向 ===")
    results['helix_right'] = analyze_direction(report, measurement_data, 'flank', 'right')
    
    print("\n=== 分析左齿向 ===")
    results['helix_left'] = analyze_direction(report, measurement_data, 'flank', 'left')
    
    # 验证四组数据是否不同
    print("\n=== 验证四组数据是否不同 ===")
    all_orders = []
    for key, result in results.items():
        if result and result['top_10']:
            top_orders = [order for order, _ in result['top_10'][:3]]
            all_orders.append((key, top_orders))
            print(f"{key} 前3阶: {top_orders}")
    
    # 检查是否所有结果都不同
    if len(all_orders) == 4:
        # 比较前3阶的组合
        combinations = [tuple(orders) for _, orders in all_orders]
        if len(set(combinations)) == 4:
            print("✓ 四组数据的前3阶组合都不同")
        else:
            print("⚠ 部分数据的前3阶组合相同")
    
    # 绘制结果
    teeth_count = getattr(measurement_data.basic_info, 'teeth', 87)
    plot_results(results, teeth_count)
    
    print("\n=== 分析完成 ===")

if __name__ == '__main__':
    main()
