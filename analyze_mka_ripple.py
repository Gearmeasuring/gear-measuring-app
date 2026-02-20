#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析MKA文件的第一主导阶次
"""

import os
import sys

# 添加正确的Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gear_analysis_refactored'))

import numpy as np
from reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, SpectrumParams
from models.gear_data import GearMeasurementData
from utils.file_parser import MKAFileParser

class MKAFirstOrderAnalyzer:
    """
    分析MKA文件的第一主导阶次
    """
    
    def __init__(self):
        """
        初始化分析器
        """
        self.report = KlingelnbergRippleSpectrumReport()
    
    def analyze_mka_file(self, mka_file_path):
        """
        分析MKA文件，找出第一主导阶次
        
        Args:
            mka_file_path: MKA文件路径
            
        Returns:
            dict: 包含第一主导阶次信息的字典
        """
        try:
            # 解析MKA文件
            print(f"正在解析MKA文件: {mka_file_path}")
            from utils.file_parser import parse_mka_file
            from models.gear_data import create_gear_data_from_dict
            
            # 解析文件获取字典数据
            parsed_data = parse_mka_file(mka_file_path)
            
            if not parsed_data:
                print("解析MKA文件失败")
                return None
            
            # 从字典创建GearMeasurementData对象
            gear_data = create_gear_data_from_dict(parsed_data)
            
            # 获取基本信息
            basic_info = gear_data.basic_info
            teeth_count = getattr(basic_info, 'teeth', 0)
            
            if not teeth_count:
                print("无法获取齿数信息")
                return None
            
            print(f"齿数: {teeth_count}")
            
            # 分析Profile右侧数据
            print("\n分析Profile右侧数据...")
            profile_data = getattr(gear_data, 'profile_data', None)
            profile_right_data = getattr(profile_data, 'right', {}) if profile_data else {}
            profile_right_result = self._analyze_data(profile_right_data, teeth_count, 'profile', 'right', basic_info)
            
            # 分析Profile左侧数据
            print("\n分析Profile左侧数据...")
            profile_left_data = getattr(profile_data, 'left', {}) if profile_data else {}
            profile_left_result = self._analyze_data(profile_left_data, teeth_count, 'profile', 'left', basic_info)
            
            # 分析Helix右侧数据
            print("\n分析Helix右侧数据...")
            flank_data = getattr(gear_data, 'flank_data', None)
            helix_right_data = getattr(flank_data, 'right', {}) if flank_data else {}
            helix_right_result = self._analyze_data(helix_right_data, teeth_count, 'flank', 'right', basic_info)
            
            # 分析Helix左侧数据
            print("\n分析Helix左侧数据...")
            helix_left_data = getattr(flank_data, 'left', {}) if flank_data else {}
            helix_left_result = self._analyze_data(helix_left_data, teeth_count, 'flank', 'left', basic_info)
            
            # 综合结果
            results = {
                'profile_right': profile_right_result,
                'profile_left': profile_left_result,
                'helix_right': helix_right_result,
                'helix_left': helix_left_result
            }
            
            return results
            
        except Exception as e:
            print(f"分析过程中出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _analyze_data(self, data_dict, teeth_count, data_type, side, basic_info):
        """
        分析特定类型的数据
        
        Args:
            data_dict: 数据字典
            teeth_count: 齿数
            data_type: 数据类型 ('profile' 或 'flank')
            side: 左侧或右侧
            basic_info: 基本信息对象
            
        Returns:
            dict: 分析结果
        """
        if not data_dict:
            print(f"{data_type} {side} 没有数据")
            return None
        
        # 获取评价范围标记
        markers_attr = f"profile_markers_{side}" if data_type == 'profile' else f"lead_markers_{side}"
        eval_markers = getattr(basic_info, markers_attr, None)
        
        # 获取评价长度和基圆直径
        from reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport
        report = KlingelnbergRippleSpectrumReport()
        eval_length = report._get_eval_length(basic_info, data_type, side, eval_markers)
        base_diameter = report._get_base_diameter(basic_info)
        
        # 创建频谱计算参数
        params = SpectrumParams(
            data_dict=data_dict,
            teeth_count=teeth_count,
            eval_markers=eval_markers,
            max_order=7 * teeth_count,
            eval_length=eval_length,
            base_diameter=base_diameter,
            max_components=11,
            side=side,
            data_type=data_type,
            info=basic_info
        )
        
        # 计算频谱
        orders, amplitudes = report._calculate_spectrum(params)
        
        if len(orders) == 0:
            print(f"{data_type} {side} 未找到阶次")
            return None
        
        # 找到第一主导阶次（按幅值排序）
        if len(orders) > 0:
            # 按幅值降序排序
            sorted_indices = np.argsort(amplitudes)[::-1]
            sorted_orders = orders[sorted_indices]
            sorted_amplitudes = amplitudes[sorted_indices]
            
            first_order = sorted_orders[0]
            first_amplitude = sorted_amplitudes[0]
            
            # 计算频率 (假设旋转速度为1转/秒)
            frequency = first_order  # 阶次就是每转的波数
            
            print(f"{data_type} {side} 第一主导阶次: {first_order}")
            print(f"幅值: {first_amplitude:.4f} μm")
            print(f"频率: {frequency} 波/转")
            
            return {
                'first_order': first_order,
                'amplitude': first_amplitude,
                'frequency': frequency,
                'all_orders': sorted_orders.tolist(),
                'all_amplitudes': sorted_amplitudes.tolist()
            }
        
        return None

def main():
    """
    主函数
    """
    mka_file_path = r"e:\python\gear measuring software - 20251217\gear measuring software - 20251217\263751-018-WAV.mka"
    
    if not os.path.exists(mka_file_path):
        print(f"MKA文件不存在: {mka_file_path}")
        return
    
    analyzer = MKAFirstOrderAnalyzer()
    results = analyzer.analyze_mka_file(mka_file_path)
    
    if results:
        print("\n=== 分析结果汇总 ===")
        for key, result in results.items():
            if result:
                print(f"\n{key}:")
                print(f"  第一主导阶次: {result['first_order']}")
                print(f"  幅值: {result['amplitude']:.4f} μm")
                print(f"  频率: {result['frequency']} 波/转")
            else:
                print(f"\n{key}: 无有效结果")

if __name__ == "__main__":
    main()
