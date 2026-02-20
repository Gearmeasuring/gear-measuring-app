#!/usr/bin/env python3
"""
分析所有四种数据类型的齿轮齿面波纹
包括：左齿形、右齿形、左齿向、右齿向
"""
from plot_ten_teeth import analyze_gear_waveform


def main():
    """
    主函数，分析所有四种数据类型的齿轮齿面波纹
    """
    print("=== Analyzing All Gear Tooth Surface Waveforms ===")
    print("\nThis script will analyze the dominant waveforms for:")
    print("1. Left Profile")
    print("2. Right Profile")
    print("3. Left Flank")
    print("4. Right Flank")
    print("\nPlease wait, this may take several minutes...\n")
    
    # 分析左齿形
    print("\n" + "="*80)
    print("=== Analyzing Left Profile ===")
    print("="*80)
    left_profile_result = analyze_gear_waveform(data_type='profile', data_side='left')
    
    # 分析右齿形
    print("\n" + "="*80)
    print("=== Analyzing Right Profile ===")
    print("="*80)
    right_profile_result = analyze_gear_waveform(data_type='profile', data_side='right')
    
    # 分析左齿向
    print("\n" + "="*80)
    print("=== Analyzing Left Flank ===")
    print("="*80)
    left_flank_result = analyze_gear_waveform(data_type='flank', data_side='left')
    
    # 分析右齿向
    print("\n" + "="*80)
    print("=== Analyzing Right Flank ===")
    print("="*80)
    right_flank_result = analyze_gear_waveform(data_type='flank', data_side='right')
    
    print("\n" + "="*80)
    print("=== Analysis Complete ===")
    print("="*80)
    print("\nResults:")
    print(f"Left Profile: {left_profile_result}")
    print(f"Right Profile: {right_profile_result}")
    print(f"Left Flank: {left_flank_result}")
    print(f"Right Flank: {right_flank_result}")
    print("\nPlease check the generated PDF files for detailed analysis.")


if __name__ == '__main__':
    main()
