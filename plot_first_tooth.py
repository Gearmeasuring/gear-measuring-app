#!/usr/bin/env python3
"""
生成齿形的第一齿在旋转角上的图表
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from parse_mka_file import MKAParser


def plot_first_tooth():
    """
    生成齿形的第一齿在旋转角上的图表
    """
    # 读取MKA文件数据
    mka_file = '263751-018-WAV.mka'
    parser = MKAParser(mka_file)
    
    # 获取齿轮齿数
    teeth_count = parser.get_teeth_count()
    if teeth_count == 0:
        teeth_count = 87  # Fallback to 87 based on the data
    
    print(f"Gear teeth count: {teeth_count}")
    
    # 获取评价范围
    eval_ranges = parser.get_evaluation_ranges()
    print(f"Evaluation ranges: {eval_ranges}")
    
    # 获取原始齿形数据
    profile_data = parser.profile_data
    
    # 提取第一齿的齿形数据
    first_tooth_data = {}
    for side in ['left', 'right']:
        # 查找第一齿的数据
        for tooth_id, data in profile_data[side].items():
            # 检查是否是第一齿
            tooth_num_match = re.search(r'\d+', tooth_id)
            if tooth_num_match:
                tooth_num = int(tooth_num_match.group(0))
                if tooth_num == 1:
                    first_tooth_data[side] = data
                    break
    
    # 计算旋转角度
    profile_angles, flank_angles = parser.calculate_rotation_angles()
    
    # 提取第一齿的旋转角度
    first_tooth_angles = {}
    for side in ['left', 'right']:
        # 查找第一齿的角度数据
        for tooth_id, angles in profile_angles[side].items():
            # 检查是否是第一齿
            tooth_num_match = re.search(r'\d+', tooth_id)
            if tooth_num_match:
                tooth_num = int(tooth_num_match.group(0))
                if tooth_num == 1:
                    first_tooth_angles[side] = angles
                    break
    
    # 创建PDF报告
    output_pdf = 'first_tooth_profile_263751-018-WAV.pdf'
    
    with PdfPages(output_pdf) as pdf:
        # 创建分析页面
        fig = plt.figure(figsize=(10, 6), dpi=150)
        fig.suptitle(f'First Tooth Profile - Rotation Angle Analysis (Teeth Count: {teeth_count})', fontsize=16, fontweight='bold')
        
        # 创建子图
        gs = fig.add_gridspec(2, 1, height_ratios=[1, 1])
        
        # 数据集颜色
        colors = ['blue', 'red']
        
        # 数据集标签
        sides = [('Left Profile', 'left'), ('Right Profile', 'right')]
        
        for i, (title, side) in enumerate(sides):
            if side in first_tooth_data and side in first_tooth_angles:
                # 提取数据
                data = first_tooth_data[side]
                angles = first_tooth_angles[side]
                
                if angles and data:
                    # 创建子图
                    ax = fig.add_subplot(gs[i])
                    ax.set_title(f'{title} - First Tooth', fontsize=14, fontweight='bold')
                    ax.set_xlabel('Rotation Angle (degrees)', fontsize=10)
                    ax.set_ylabel('Deviation (μm)', fontsize=10)
                    ax.tick_params(axis='both', labelsize=9)
                    ax.grid(True, alpha=0.3, linestyle='--')
                    
                    # 绘制数据
                    ax.plot(angles, data, color=colors[i], linewidth=1.0, marker='o', markersize=3)
                    
                    # 添加测量范围标记
                    if 'profile' in eval_ranges:
                        profile_start = eval_ranges['profile']['start']
                        profile_end = eval_ranges['profile']['end']
                        ax.axvspan(profile_start, profile_end, alpha=0.2, color=colors[i])
                        ax.text(profile_start, ax.get_ylim()[1] * 0.9, f'Eval Start: {profile_start}', 
                                ha='left', va='top', fontsize=8, color=colors[i])
                        ax.text(profile_end, ax.get_ylim()[1] * 0.9, f'Eval End: {profile_end}', 
                                ha='right', va='top', fontsize=8, color=colors[i])
                    
                    # 隐藏右侧和顶部边框
                    ax.spines['right'].set_visible(False)
                    ax.spines['top'].set_visible(False)
                else:
                    # 无数据时的处理
                    ax = fig.add_subplot(gs[i])
                    ax.set_title(f'{title} - First Tooth', fontsize=14, fontweight='bold')
                    ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
                    ax.set_xlabel('Rotation Angle (degrees)', fontsize=10)
                    ax.set_ylabel('Deviation (μm)', fontsize=10)
            else:
                # 无数据时的处理
                ax = fig.add_subplot(gs[i])
                ax.set_title(f'{title} - First Tooth', fontsize=14, fontweight='bold')
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
                ax.set_xlabel('Rotation Angle (degrees)', fontsize=10)
                ax.set_ylabel('Deviation (μm)', fontsize=10)
        
        # 调整布局
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # 添加页面到PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    print(f"First tooth profile analysis completed. Results saved to: {output_pdf}")


if __name__ == '__main__':
    import re
    plot_first_tooth()
