"""
迭代正弦波分解算法演示
展示算法的核心步骤：
1. 计算选定频率范围内补偿正弦波函数的振幅
2. 振幅最大的补偿正弦波被视为第一主导频率
3. 将该主导正弦波函数从偏差曲线中剔除
4. 对剩余偏差进行重新分析
5. 经过10个周期后，得到包含10个最大振幅的频谱
"""

import os
import sys
import numpy as np
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file
from gear_ripple_algorithm import GearRippleAnalyzer


def main():
    # 读取MKA文件
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    if not os.path.exists(mka_file):
        mka_file = os.path.join(current_dir, '004-xiaoxiao1.mka')
    
    print('='*70)
    print('齿轮波纹度分析 - 迭代正弦波分解算法演示')
    print('='*70)
    
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    # 提取齿轮参数
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 0.0)
    
    # 创建分析器
    analyzer = GearRippleAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle
    )
    
    # 获取评价范围参数
    profile_eval_start = gear_data.get('profile_eval_start', 0)
    profile_eval_end = gear_data.get('profile_eval_end', 0)
    profile_meas_start = gear_data.get('profile_meas_start', 0)
    profile_meas_end = gear_data.get('profile_meas_end', 0)
    
    helix_eval_start = gear_data.get('helix_eval_start', 0)
    helix_eval_end = gear_data.get('helix_eval_end', 0)
    helix_meas_start = gear_data.get('helix_meas_start', 0)
    helix_meas_end = gear_data.get('helix_meas_end', 0)
    
    # 分析左齿形
    print()
    print('='*70)
    print('分析左齿形 - 迭代正弦波分解过程')
    print('='*70)
    
    left_profile_curve = analyzer.build_merged_curve(
        profile_data, 'profile', 'left',
        profile_eval_start, profile_eval_end,
        profile_meas_start, profile_meas_end
    )
    
    if left_profile_curve:
        interp_angles, interp_values = analyzer.interpolate_curve(left_profile_curve[0], left_profile_curve[1])
        spectrum = analyzer.iterative_sine_decomposition(interp_angles, interp_values, num_components=10, verbose=True)
        high_order = analyzer.calculate_high_order_undulation(spectrum)
        
        print()
        print('='*70)
        print('频谱分析结果')
        print('='*70)
        print()
        print('前10个主导频率:')
        for i, (order, amp, phase) in enumerate(zip(spectrum['orders'], spectrum['amplitudes'], spectrum['phases'])):
            is_high = '★高阶' if order >= teeth_count else ''
            print(f'  {i+1}. 阶次={order:3d}, 振幅={amp:.4f} um, 相位={np.degrees(phase):6.1f}° {is_high}')
        
        print()
        print(f'高阶波纹度评价 (阶次 >= {teeth_count}):')
        print(f'  高阶分量: {list(high_order["high_order_waves"])}')
        print(f'  高阶总振幅 W = {high_order["total_high_order_amplitude"]:.4f} um')
        print(f'  高阶RMS = {high_order["high_order_rms"]:.4f} um')
    
    # 分析左齿向
    print()
    print('='*70)
    print('分析左齿向 - 迭代正弦波分解过程')
    print('='*70)
    
    left_helix_curve = analyzer.build_merged_curve(
        flank_data, 'helix', 'left',
        helix_eval_start, helix_eval_end,
        helix_meas_start, helix_meas_end
    )
    
    if left_helix_curve:
        interp_angles, interp_values = analyzer.interpolate_curve(left_helix_curve[0], left_helix_curve[1])
        spectrum = analyzer.iterative_sine_decomposition(interp_angles, interp_values, num_components=10, verbose=True)
        high_order = analyzer.calculate_high_order_undulation(spectrum)
        
        print()
        print('='*70)
        print('频谱分析结果')
        print('='*70)
        print()
        print('前10个主导频率:')
        for i, (order, amp, phase) in enumerate(zip(spectrum['orders'], spectrum['amplitudes'], spectrum['phases'])):
            is_high = '★高阶' if order >= teeth_count else ''
            print(f'  {i+1}. 阶次={order:3d}, 振幅={amp:.4f} um, 相位={np.degrees(phase):6.1f}° {is_high}')
        
        print()
        print(f'高阶波纹度评价 (阶次 >= {teeth_count}):')
        print(f'  高阶分量: {list(high_order["high_order_waves"])}')
        print(f'  高阶总振幅 W = {high_order["total_high_order_amplitude"]:.4f} um')
        print(f'  高阶RMS = {high_order["high_order_rms"]:.4f} um')
    
    # 算法说明
    print()
    print('='*70)
    print('算法说明')
    print('='*70)
    print('''
迭代正弦波分解算法核心步骤:
1. 计算选定频率范围内补偿正弦波函数的振幅
2. 振幅最大的补偿正弦波被视为第一主导频率
3. 将该主导正弦波函数从偏差曲线中剔除
4. 对剩余偏差进行重新分析
5. 经过10个周期后，得到包含10个最大振幅的频谱

最小二乘法拟合公式:
  y = A*sin(order*theta) + B*cos(order*theta)
  振幅 = sqrt(A^2 + B^2)
  相位 = arctan2(A, B)

高阶波纹度评价:
  高阶分量 = 波数 >= ZE(齿数) 的所有分量
  W值 = 高阶总振幅 = sum(高阶分量振幅)
  RMS值 = sqrt(mean(高阶重构信号^2))
''')


if __name__ == '__main__':
    main()
