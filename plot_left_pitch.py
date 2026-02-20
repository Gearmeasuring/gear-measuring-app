#!/usr/bin/env python3
"""
绘制左齿面的周节图形
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from parse_mka_file import MKAParser
import re


def plot_left_pitch():
    """
    绘制左齿面的周节图形
    """
    # 读取MKA文件数据
    mka_file = '263751-018-WAV.mka'
    parser = MKAParser(mka_file)
    
    # 获取齿轮齿数
    teeth_count = parser.get_teeth_count()
    if teeth_count == 0:
        teeth_count = 87  # 基于数据的默认值
    
    print(f"Gear teeth count: {teeth_count}")
    
    # 获取左齿面的周节数据
    side = 'left'  # 只使用左侧数据
    pitch_data = parser.pitch_data[side]
    
    # 按齿号顺序组织数据
    ordered_pitch_data = {}
    for tooth_id, data in pitch_data.items():
        # 检查齿号
        tooth_num_match = re.search(r'\d+', tooth_id)
        if tooth_num_match:
            tooth_num = int(tooth_num_match.group(0))
            ordered_pitch_data[tooth_num] = data
    
    # 按齿号排序
    sorted_tooth_nums = sorted(ordered_pitch_data.keys())
    
    found_teeth = len(sorted_tooth_nums)
    print(f"Found {found_teeth} teeth pitch data for left side")
    if found_teeth < teeth_count:
        print(f"Only found teeth: {sorted_tooth_nums}")
        # 继续运行，显示找到的齿
    
    # 准备绘制数据
    tooth_numbers = []
    pitch_deviations = []
    
    for tooth_num in sorted_tooth_nums:
        data = ordered_pitch_data[tooth_num]
        if data:
            # 使用第一个周节偏差值（通常每个齿只有一个值）
            deviation = data[0]
            tooth_numbers.append(tooth_num)
            pitch_deviations.append(deviation)
            print(f"Tooth {tooth_num} pitch deviation: {deviation:.4f} μm")
    
    if not tooth_numbers:
        print("No pitch data found for left side")
        return
    
    # 创建PDF报告
    output_pdf = 'left_pitch_profile_263751-018-WAV.pdf'
    
    with PdfPages(output_pdf) as pdf:
        # 创建分析页面
        fig = plt.figure(figsize=(15, 10), dpi=150)
        fig.suptitle(f'Left Side Pitch Profile - Rotation Angle Analysis (Teeth Count: {teeth_count})', fontsize=16, fontweight='bold')
        
        # 创建子图
        ax = fig.add_subplot(1, 1, 1)
        ax.set_title(f'Left Profile - Pitch Deviation', fontsize=14, fontweight='bold')
        ax.set_xlabel('Tooth Number', fontsize=12)
        ax.set_ylabel('Pitch Deviation (μm)', fontsize=12)
        ax.tick_params(axis='both', labelsize=10)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 绘制周节偏差数据
        ax.plot(tooth_numbers, pitch_deviations, 'b-', linewidth=1.5, marker='o', markersize=4)
        
        # 添加零线
        ax.axhline(y=0, color='red', linestyle='--', linewidth=1.0)
        
        # 设置X轴范围，显示所有齿的范围
        # 添加一些边距，确保数据完全显示
        margin = 1
        ax.set_xlim(min(tooth_numbers) - margin, max(tooth_numbers) + margin)
        
        # 隐藏右侧和顶部边框
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        
        # 调整布局
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # 添加页面到PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    print(f"Left side pitch profile analysis completed. Results saved to: {output_pdf}")


if __name__ == '__main__':
    plot_left_pitch()
