#!/usr/bin/env python3
"""
提取所有四种数据类型的齿轮齿面波纹振幅值
找出最大的十个振幅值并排序
"""
import numpy as np
from plot_ten_teeth import analyze_gear_waveform


def extract_top_amplitudes():
    """
    提取所有四种数据类型的齿轮齿面波纹振幅值
    找出最大的十个振幅值并排序
    """
    print("=== Extracting Top 10 Amplitudes ===")
    print("This script will analyze all four data types and extract the top 10 amplitudes.")
    print("Please wait, this may take several minutes...\n")
    
    # 存储所有振幅值
    all_amplitudes = []
    
    # 分析左齿形
    print("\nAnalyzing Left Profile...")
    left_profile_pdf, left_profile_amplitudes = analyze_gear_waveform(data_type='profile', data_side='left')
    print(f"   - Left Profile PDF: {left_profile_pdf}")
    print(f"   - Left Profile Amplitudes: {[round(a, 4) for a in left_profile_amplitudes[:5]]}...")
    
    # 分析右齿形
    print("\nAnalyzing Right Profile...")
    right_profile_pdf, right_profile_amplitudes = analyze_gear_waveform(data_type='profile', data_side='right')
    print(f"   - Right Profile PDF: {right_profile_pdf}")
    print(f"   - Right Profile Amplitudes: {[round(a, 4) for a in right_profile_amplitudes[:5]]}...")
    
    # 分析左齿向
    print("\nAnalyzing Left Flank...")
    left_flank_pdf, left_flank_amplitudes = analyze_gear_waveform(data_type='flank', data_side='left')
    print(f"   - Left Flank PDF: {left_flank_pdf}")
    print(f"   - Left Flank Amplitudes: {[round(a, 4) for a in left_flank_amplitudes[:5]]}...")
    
    # 分析右齿向
    print("\nAnalyzing Right Flank...")
    right_flank_pdf, right_flank_amplitudes = analyze_gear_waveform(data_type='flank', data_side='right')
    print(f"   - Right Flank PDF: {right_flank_pdf}")
    print(f"   - Right Flank Amplitudes: {[round(a, 4) for a in right_flank_amplitudes[:5]]}...")
    
    # 合并所有振幅值
    all_amplitudes.extend(left_profile_amplitudes)
    all_amplitudes.extend(right_profile_amplitudes)
    all_amplitudes.extend(left_flank_amplitudes)
    all_amplitudes.extend(right_flank_amplitudes)
    
    # 去重并排序
    unique_amplitudes = list(set(all_amplitudes))
    unique_amplitudes.sort(reverse=True)
    
    # 提取最大的十个振幅值
    top_ten_amplitudes = unique_amplitudes[:10]
    
    # 打印结果
    print("\n" + "="*80)
    print("=== Top 10 Amplitudes (Sorted) ===")
    print("="*80)
    for i, amp in enumerate(top_ten_amplitudes, 1):
        print(f"{i:2d}. {amp:.4f} μm")
    print("="*80)
    
    return top_ten_amplitudes


if __name__ == '__main__':
    extract_top_amplitudes()
