#!/usr/bin/env python3
"""
对每种数据类型的齿轮齿面波纹按幅值排序并显示波数
包括：左齿形、右齿形、左齿向、右齿向
"""
from plot_ten_teeth import analyze_gear_waveform


def sort_waveforms_by_amplitude():
    """
    对每种数据类型的齿轮齿面波纹按幅值排序并显示波数
    """
    print("=== Sorting Waveforms by Amplitude ===")
    print("This script will analyze all four data types and sort waveforms by amplitude.")
    print("Please wait, this may take several minutes...\n")
    
    # 分析左齿形
    print("\n" + "="*80)
    print("=== Left Profile (Sorted by Amplitude) ===")
    print("="*80)
    left_profile_pdf, left_profile_amplitudes, left_profile_wave_numbers = analyze_gear_waveform(data_type='profile', data_side='left')
    
    # 按幅值排序左齿形数据
    left_profile_sorted = sorted(zip(left_profile_amplitudes, left_profile_wave_numbers), reverse=True, key=lambda x: x[0])
    print("\nLeft Profile Waveforms (Sorted by Amplitude):")
    print("Rank  | Amplitude (μm) | Wave Number")
    print("------|----------------|-----------")
    for i, (amp, wave_num) in enumerate(left_profile_sorted[:10], 1):
        print(f"{i:4d}  | {amp:13.4f} | {wave_num:10d}")
    
    # 分析右齿形
    print("\n" + "="*80)
    print("=== Right Profile (Sorted by Amplitude) ===")
    print("="*80)
    right_profile_pdf, right_profile_amplitudes, right_profile_wave_numbers = analyze_gear_waveform(data_type='profile', data_side='right')
    
    # 按幅值排序右齿形数据
    right_profile_sorted = sorted(zip(right_profile_amplitudes, right_profile_wave_numbers), reverse=True, key=lambda x: x[0])
    print("\nRight Profile Waveforms (Sorted by Amplitude):")
    print("Rank  | Amplitude (μm) | Wave Number")
    print("------|----------------|-----------")
    for i, (amp, wave_num) in enumerate(right_profile_sorted[:10], 1):
        print(f"{i:4d}  | {amp:13.4f} | {wave_num:10d}")
    
    # 分析左齿向
    print("\n" + "="*80)
    print("=== Left Flank (Sorted by Amplitude) ===")
    print("="*80)
    left_flank_pdf, left_flank_amplitudes, left_flank_wave_numbers = analyze_gear_waveform(data_type='flank', data_side='left')
    
    # 按幅值排序左齿向数据
    left_flank_sorted = sorted(zip(left_flank_amplitudes, left_flank_wave_numbers), reverse=True, key=lambda x: x[0])
    print("\nLeft Flank Waveforms (Sorted by Amplitude):")
    print("Rank  | Amplitude (μm) | Wave Number")
    print("------|----------------|-----------")
    for i, (amp, wave_num) in enumerate(left_flank_sorted[:10], 1):
        print(f"{i:4d}  | {amp:13.4f} | {wave_num:10d}")
    
    # 分析右齿向
    print("\n" + "="*80)
    print("=== Right Flank (Sorted by Amplitude) ===")
    print("="*80)
    right_flank_pdf, right_flank_amplitudes, right_flank_wave_numbers = analyze_gear_waveform(data_type='flank', data_side='right')
    
    # 按幅值排序右齿向数据
    right_flank_sorted = sorted(zip(right_flank_amplitudes, right_flank_wave_numbers), reverse=True, key=lambda x: x[0])
    print("\nRight Flank Waveforms (Sorted by Amplitude):")
    print("Rank  | Amplitude (μm) | Wave Number")
    print("------|----------------|-----------")
    for i, (amp, wave_num) in enumerate(right_flank_sorted[:10], 1):
        print(f"{i:4d}  | {amp:13.4f} | {wave_num:10d}")
    
    print("\n" + "="*80)
    print("=== Analysis Complete ===")
    print("="*80)
    print("\nGenerated PDF files:")
    print(f"- Left Profile: {left_profile_pdf}")
    print(f"- Right Profile: {right_profile_pdf}")
    print(f"- Left Flank: {left_flank_pdf}")
    print(f"- Right Flank: {right_flank_pdf}")


if __name__ == '__main__':
    sort_waveforms_by_amplitude()
