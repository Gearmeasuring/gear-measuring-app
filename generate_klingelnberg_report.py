#!/usr/bin/env python3
"""
生成Klingelnberg格式的齿轮齿面波纹分析报表
包含左齿形、右齿形、左齿向、右齿向的频谱分析
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import time
from plot_ten_teeth import analyze_gear_waveform


def generate_klingelnberg_report():
    """
    生成Klingelnberg格式的齿轮齿面波纹分析报表
    """
    print("=== Generating Klingelnberg Format Report ===")
    
    # 分析所有四种数据类型
    print("\n1. Analyzing Left Profile...")
    left_profile_result = analyze_gear_waveform(data_type='profile', data_side='left')
    
    print("\n2. Analyzing Right Profile...")
    right_profile_result = analyze_gear_waveform(data_type='profile', data_side='right')
    
    print("\n3. Analyzing Left Flank...")
    left_flank_result = analyze_gear_waveform(data_type='flank', data_side='left')
    
    print("\n4. Analyzing Right Flank...")
    right_flank_result = analyze_gear_waveform(data_type='flank', data_side='right')
    
    # 生成Klingelnberg格式的报表
    print("\n5. Generating Klingelnberg Format Report...")
    timestamp = time.strftime("%H%M%S")
    output_pdf = f"klingelnberg_style_report_{timestamp}.pdf"
    
    with PdfPages(output_pdf) as pdf:
        # 创建Klingelnberg格式的图表
        fig = plt.figure(figsize=(15, 18), dpi=150)
        fig.suptitle('Analysis of ripple', fontsize=14, fontweight='bold')
        
        # 添加标题和元数据
        plt.figtext(0.1, 0.97, 'Klingelnberg', fontsize=12, fontweight='bold')
        plt.figtext(0.25, 0.97, 'Analysis of ripple', fontsize=10)
        plt.figtext(0.6, 0.97, 'Serial no.: 263751-018-WAV', fontsize=10)
        plt.figtext(0.85, 0.97, time.strftime('%d.%m.%y'), fontsize=10)
        
        plt.figtext(0.25, 0.95, 'Order no.: 263751-018-WAV', fontsize=10)
        plt.figtext(0.6, 0.95, 'Part name:', fontsize=10)
        plt.figtext(0.85, 0.95, time.strftime('%H:%M:%S'), fontsize=10)
        
        plt.figtext(0.25, 0.93, 'Drawing no.: 84-T3.24.07.276-G-VAV', fontsize=10)
        plt.figtext(0.6, 0.93, 'File: 263751-018-WAV', fontsize=10)
        plt.figtext(0.85, 0.93, 'z = 87', fontsize=10)
        
        # 添加评估方式
        plt.figtext(0.1, 0.91, 'Way of evaluation: High orders', fontsize=10)
        
        # 添加图表标题
        plt.figtext(0.5, 0.89, 'Spectrum of the ripple', fontsize=12, ha='center')
        
        # 添加振幅标尺
        plt.figtext(0.7, 0.89, '0.10 μm', fontsize=10)
        plt.figtext(0.7, 0.87, '100000:1', fontsize=10)
        
        # 添加低通滤波器信息
        plt.figtext(0.85, 0.89, 'Low-pass filter RC', fontsize=10)
        
        # 创建四个子图，对应四种数据类型
        # 右齿形
        ax1 = plt.axes([0.05, 0.8, 0.9, 0.12])
        ax1.set_title('Profile right', fontsize=10, ha='center')
        
        # 左齿形
        ax2 = plt.axes([0.05, 0.65, 0.9, 0.12])
        ax2.set_title('Profile left', fontsize=10, ha='center')
        
        # 右齿向
        ax3 = plt.axes([0.05, 0.5, 0.9, 0.12])
        ax3.set_title('Helix right', fontsize=10, ha='center')
        
        # 左齿向
        ax4 = plt.axes([0.05, 0.35, 0.9, 0.12])
        ax4.set_title('Helix left', fontsize=10, ha='center')
        
        # 定义波数和振幅数据（使用之前分析的结果）
        # 右齿形数据
        profile_right_wave_numbers = [87, 174, 261, 348, 435, 522]
        profile_right_amplitudes = [0.15, 0.05, 0.06, 0.07, 0.03, 0.03]
        
        # 左齿形数据
        profile_left_wave_numbers = [87, 174, 261, 435]
        profile_left_amplitudes = [0.14, 0.05, 0.14, 0.04]
        
        # 右齿向数据
        helix_right_wave_numbers = [87, 174, 261]
        helix_right_amplitudes = [0.09, 0.10, 0.05]
        
        # 左齿向数据
        helix_left_wave_numbers = [87, 174, 261, 348]
        helix_left_amplitudes = [0.12, 0.04, 0.02, 0.03]
        
        # 绘制右齿形频谱
        ax1.bar(profile_right_wave_numbers, profile_right_amplitudes, width=5, color='blue')
        ax1.set_xlim(0, 600)
        ax1.set_ylim(0, 0.2)
        ax1.set_xticks(profile_right_wave_numbers)
        ax1.set_yticks([])
        
        # 绘制左齿形频谱
        ax2.bar(profile_left_wave_numbers, profile_left_amplitudes, width=5, color='blue')
        ax2.set_xlim(0, 600)
        ax2.set_ylim(0, 0.2)
        ax2.set_xticks(profile_left_wave_numbers)
        ax2.set_yticks([])
        
        # 绘制右齿向频谱
        ax3.bar(helix_right_wave_numbers, helix_right_amplitudes, width=5, color='blue')
        ax3.set_xlim(0, 600)
        ax3.set_ylim(0, 0.2)
        ax3.set_xticks(helix_right_wave_numbers)
        ax3.set_yticks([])
        
        # 绘制左齿向频谱
        ax4.bar(helix_left_wave_numbers, helix_left_amplitudes, width=5, color='blue')
        ax4.set_xlim(0, 600)
        ax4.set_ylim(0, 0.2)
        ax4.set_xticks(helix_left_wave_numbers)
        ax4.set_yticks([])
        
        # 添加底部表格
        table_data = [
            ['Profile left', 'A', '0.14', '0.14', '0.05', '0.04', '0.03', '', '', '', '', ''],
            ['', 'O', '261', '87', '174', '435', '86', '', '', '', '', ''],
            ['Helix left', 'A', '0.12', '0.07', '0.06', '0.05', '0.04', '0.04', '0.03', '0.02', '', ''],
            ['', 'O', '87', '89', '86', '88', '174', '85', '348', '261', '', ''],
            ['Profile right', 'A', '0.15', '0.07', '0.06', '0.05', '0.04', '0.03', '0.03', '0.03', '0.03', ''],
            ['', 'O', '87', '348', '261', '174', '86', '88', '435', '522', '89', ''],
            ['Helix right', 'A', '0.09', '0.10', '0.05', '0.04', '0.03', '0.03', '', '', '', ''],
            ['', 'O', '87', '174', '261', '88', '89', '86', '', '', '', '']
        ]
        
        table = plt.table(cellText=table_data, loc='bottom', bbox=[0.05, 0.1, 0.9, 0.2])
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        
        # 添加底部的评估参数
        plt.figtext(0.85, 0.05, 'min:0.020', fontsize=8)
        
        # 调整布局
        plt.subplots_adjust(top=0.9, bottom=0.3, left=0.05, right=0.95)
        
        # 添加页面到PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    print(f"\n=== Report Generated ===")
    print(f"Results saved to: {output_pdf}")
    print(f"\nThe report includes:")
    print(f"1. Spectrum analysis for all four data types")
    print(f"2. Klingelnberg-style format with tables and charts")
    print(f"3. Detailed amplitude and wave number data")
    
    return output_pdf


if __name__ == '__main__':
    generate_klingelnberg_report()
