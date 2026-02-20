#!/usr/bin/env python3
"""
齿轮齿形数据专门分析脚本
分析左齿形和右齿形的主导波形
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import time
from plot_ten_teeth import MKAParser, remove_outliers, remove_crowning_and_tilt


def least_squares_sine_fit(angles, deviations, wave_number):
    """
    使用最小二乘法进行正弦拟合
    
    Args:
        angles: 角度数据
        deviations: 偏差数据
        wave_number: 波数
        
    Returns:
        freq: 频率 (cycles/degree)
        amplitude: 振幅
        phase: 相位
        sine_wave: 拟合的正弦波
    """
    angles = np.array(angles)
    deviations = np.array(deviations)
    
    # 计算频率
    freq = wave_number / 360.0
    
    # 构造矩阵
    X = np.column_stack([np.sin(2 * np.pi * freq * angles), np.cos(2 * np.pi * freq * angles)])
    
    # 使用最小二乘法拟合
    try:
        # 添加正则化以提高稳定性
        A, B = np.linalg.lstsq(X, deviations, rcond=1e-10)[0]
    except:
        # 如果最小二乘法失败，使用简单的相关方法
        A, B = 0.0, 0.0
    
    # 计算振幅和相位
    amplitude = np.sqrt(A**2 + B**2)
    phase = np.arctan2(B, A)
    
    # 生成拟合的正弦波
    sine_wave = A * np.sin(2 * np.pi * freq * angles) + B * np.cos(2 * np.pi * freq * angles)
    
    return freq, amplitude, phase, sine_wave


def remove_dominant_frequency(signal, sine_wave):
    """
    从信号中移除主导频率
    
    Args:
        signal: 原始信号
        sine_wave: 主导频率的正弦波
        
    Returns:
        residual: 剩余信号
    """
    return np.array(signal) - np.array(sine_wave)


def analyze_gear_waveform(data_type='profile', data_side='left'):
    """
    齿轮齿面波纹分析算法
    使用补偿正弦函数匹配曲线，提取前10个最大振幅的波纹
    
    Args:
        data_type: 数据类型 ('profile' 或 'flank')
        data_side: 数据侧面 ('left' 或 'right')
        
    Returns:
        dominant_waveforms: 前10个最大振幅的波纹
    """
    print(f"\n=== Analyzing {data_side.capitalize()} {data_type.capitalize()} ===")
    
    # 读取MKA文件数据
    mka_file = '263751-018-WAV.mka'
    parser = MKAParser(mka_file)
    
    # 获取齿轮齿数
    teeth_count = parser.get_teeth_count()
    if teeth_count == 0:
        teeth_count = 87  # Fallback to 87 based on the data
    print(f"   - Teeth count: {teeth_count}")
    
    # 获取评价范围
    eval_ranges = parser.get_evaluation_ranges()
    
    # 计算旋转角度
    profile_angles, flank_angles = parser.calculate_rotation_angles()
    
    # 获取数据
    if data_type == 'profile':
        data = parser.profile_data
        angle_data = profile_angles
    else:  # flank
        data = parser.flank_data
        angle_data = flank_angles
    
    # 获取指定侧面的数据
    if data_side in data:
        side_data = data[data_side]
        side_angles = angle_data[data_side]
    else:
        print(f"Error: No {data_side} {data_type} data available")
        return None
    
    print(f"   - Found {len(side_data)} teeth for {data_side} {data_type}")
    
    # 提取所有齿的数据点
    all_angles = []
    all_deviations = []
    
    for tooth_id, tooth_data in side_data.items():
        # 过滤出评价范围内的数据点
        if data_type == 'profile' and 'profile' in eval_ranges:
            range_start = eval_ranges['profile']['start']
            range_end = eval_ranges['profile']['end']
        elif data_type == 'flank' and 'flank' in eval_ranges:
            range_start = eval_ranges['flank']['start']
            range_end = eval_ranges['flank']['end']
        else:
            # 如果没有评价范围，使用所有数据
            processed_data = tooth_data
            tooth_angles = side_angles.get(tooth_id, [i for i in range(len(tooth_data))])
            
            # 处理角度数据
            if len(tooth_angles) == len(processed_data):
                all_angles.extend(tooth_angles)
                all_deviations.extend(processed_data)
            continue
        
        # 计算评价范围在测量范围中的比例
        if 'start_mess' in eval_ranges[data_type] and 'end_mess' in eval_ranges[data_type]:
            range_start_mess = eval_ranges[data_type]['start_mess']
            range_end_mess = eval_ranges[data_type]['end_mess']
            
            if range_end_mess > range_start_mess:
                total_mess_range = range_end_mess - range_start_mess
                eval_start_ratio = (range_start - range_start_mess) / total_mess_range
                eval_end_ratio = (range_end - range_start_mess) / total_mess_range
                
                # 提取评价范围内的数据点
                num_points = len(tooth_data)
                start_idx = int(num_points * eval_start_ratio)
                end_idx = int(num_points * eval_end_ratio)
                
                # 确保索引有效
                start_idx = max(0, start_idx)
                end_idx = min(num_points, end_idx)
                
                # 提取评价范围内的数据点
                raw_data = tooth_data[start_idx:end_idx]
            else:
                raw_data = tooth_data
        else:
            raw_data = tooth_data
        
        # 剔除异常值
        processed_data = remove_outliers(raw_data)
        
        # 去除鼓形和倾斜
        processed_data = remove_crowning_and_tilt(processed_data)
        
        # 获取对应齿的角度数据
        tooth_angles = side_angles.get(tooth_id, [i for i in range(len(tooth_data))])
        
        # 提取评价范围内的角度数据
        if 'start_mess' in eval_ranges[data_type] and 'end_mess' in eval_ranges[data_type]:
            if range_end_mess > range_start_mess:
                tooth_angles = tooth_angles[start_idx:end_idx]
        
        # 处理角度数据
        if len(tooth_angles) == len(processed_data):
            all_angles.extend(tooth_angles)
            all_deviations.extend(processed_data)
    
    if not all_angles:
        print("Error: No data available for analysis")
        return None
    
    print(f"\n=== Data Processing ===")
    print(f"   - Total data points: {len(all_angles)}")
    
    # 排序（确保按角度顺序）
    sorted_indices = np.argsort(all_angles)
    sorted_angles = np.array(all_angles)[sorted_indices]
    sorted_deviations = np.array(all_deviations)[sorted_indices]
    
    # 去除重复的角度值
    unique_indices = np.unique(sorted_angles, return_index=True)[1]
    unique_angles = sorted_angles[unique_indices]
    unique_deviations = sorted_deviations[unique_indices]
    print(f"   - Removed {len(sorted_angles) - len(unique_angles)} duplicate angles")
    print(f"   - Total unique data points: {len(unique_angles)}")
    
    # 确保角度在0-360范围内
    unique_angles = unique_angles % 360
    
    # 重新排序
    sorted_indices = np.argsort(unique_angles)
    unique_angles = unique_angles[sorted_indices]
    unique_deviations = unique_deviations[sorted_indices]
    
    # 确保第一个和最后一个值相同（周期边界条件）
    if len(unique_deviations) > 1:
        unique_deviations[-1] = unique_deviations[0]
    
    print("\n=== Waveform Analysis ===")
    print("Extracting Dominant Waveforms...")
    
    # 存储10个主导频率和对应的振幅、相位、波数
    dominant_frequencies = []
    dominant_amplitudes = []
    dominant_phases = []
    dominant_wave_numbers = []
    extracted_sine_waves = []
    
    # 使用当前数据进行分析
    analysis_data = unique_deviations
    
    # 重复10次分析过程
    current_deviations = analysis_data.copy()
    
    for i in range(10):
        print(f"   - Extracting {i+1}th dominant waveform...")
        
        # 计算当前偏差的主导频率
        # 使用更大的波数范围以捕获更多可能的波纹
        max_waves = 500
        
        # 存储所有波数的振幅
        wave_amplitudes = []
        wave_numbers_list = []
        
        # 分析不同波数，排除已经提取过的波数
        for wave_number in range(1, max_waves + 1):
            # 跳过已经提取过的波数
            if wave_number in dominant_wave_numbers:
                continue
                
            freq, amplitude, phase, sine_wave = least_squares_sine_fit(unique_angles, current_deviations, wave_number)
            wave_amplitudes.append(amplitude)
            wave_numbers_list.append(wave_number)
            
            # 只打印振幅大于0.01的波数
            if amplitude > 0.01 and i < 3:  # 只在前3次迭代中打印详细信息
                print(f"      Wave number: {wave_number}, Frequency: {freq:.6f} cycles/degree, Amplitude: {amplitude:.4f} μm")
        
        # 找到振幅最大的波数
        if wave_amplitudes:
            max_amplitude_idx = np.argmax(wave_amplitudes)
            dominant_wave_number = wave_numbers_list[max_amplitude_idx]
            dominant_amplitude = wave_amplitudes[max_amplitude_idx]
            
            # 重新计算该波数的完整参数
            dominant_freq, dominant_amplitude, dominant_phase, dominant_sine_wave = least_squares_sine_fit(unique_angles, current_deviations, dominant_wave_number)
            
            # 存储结果
            dominant_frequencies.append(dominant_freq)
            dominant_amplitudes.append(dominant_amplitude)
            dominant_phases.append(dominant_phase)
            dominant_wave_numbers.append(dominant_wave_number)
            extracted_sine_waves.append(dominant_sine_wave)
            
            # 从偏差中剔除主导频率
            residual_signal = remove_dominant_frequency(current_deviations, dominant_sine_wave)
            
            # 更新当前偏差为剩余信号
            current_deviations = residual_signal
        else:
            # 如果没有找到新的波数，停止分析
            print("   - No new dominant waveforms found")
            break
    
    print("\n=== Result Verification ===")
    
    # 检查波纹频率是否为整数
    print("Verifying waveform frequencies...")
    valid_waveforms = []
    for i, (wave_num, amp) in enumerate(zip(dominant_wave_numbers, dominant_amplitudes)):
        if amp > 0.01:
            print(f"Wave {i+1}: Number = {wave_num}, Amplitude = {amp:.4f} μm")
            valid_waveforms.append((wave_num, amp))
    
    # 验证关键波纹与实际齿轮的噪音或偏差特征相匹配
    print("\n=== Feature Matching Verification ===")
    print(f"Gear teeth count: {teeth_count}")
    print(f"Expected fundamental wave number: {teeth_count}")
    
    # 检查是否存在与齿数相关的波纹
    found_fundamental = False
    for wave_num, amp in valid_waveforms:
        if wave_num == teeth_count:
            found_fundamental = True
            print(f"Found fundamental wave: {wave_num} (matches teeth count), Amplitude: {amp:.4f} μm")
            break
    
    if not found_fundamental:
        print(f"Warning: No fundamental wave found matching teeth count {teeth_count}")
    
    print("\n=== Analysis Complete ===")
    
    # 打印前5个主导频率
    print("\nTop 5 Dominant Waveforms:")
    for i in range(min(5, len(dominant_wave_numbers))):
        print(f"   {i+1}. Wave number: {dominant_wave_numbers[i]}, Amplitude: {dominant_amplitudes[i]:.4f} μm")
    
    # 返回主导波形数据
    dominant_waveforms = list(zip(dominant_wave_numbers, dominant_amplitudes))
    return dominant_waveforms


def main():
    """
    主函数，分析左齿形和右齿形数据
    """
    print("=== Analyzing Profile Data ===")
    print("This script will analyze left and right profile data.")
    print("Please wait, this may take several minutes...\n")
    
    # 分析左齿形
    print("="*80)
    print("=== Analyzing Left Profile ===")
    print("="*80)
    left_profile_data = analyze_gear_waveform(data_type='profile', data_side='left')
    
    # 分析右齿形
    print("\n" + "="*80)
    print("=== Analyzing Right Profile ===")
    print("="*80)
    right_profile_data = analyze_gear_waveform(data_type='profile', data_side='right')
    
    print("\n" + "="*80)
    print("=== All Analysis Complete ===")
    print("="*80)
    
    # 显示左齿形结果
    print("\n=== Left Profile Results ===")
    if left_profile_data:
        print("Top 10 Waveforms (sorted by amplitude):")
        sorted_left = sorted(left_profile_data, key=lambda x: x[1], reverse=True)
        for i, (wave_num, amp) in enumerate(sorted_left[:10]):
            print(f"   {i+1}. Wave number: {wave_num}, Amplitude: {amp:.4f} μm")
    
    # 显示右齿形结果
    print("\n=== Right Profile Results ===")
    if right_profile_data:
        print("Top 10 Waveforms (sorted by amplitude):")
        sorted_right = sorted(right_profile_data, key=lambda x: x[1], reverse=True)
        for i, (wave_num, amp) in enumerate(sorted_right[:10]):
            print(f"   {i+1}. Wave number: {wave_num}, Amplitude: {amp:.4f} μm")


if __name__ == '__main__':
    main()
