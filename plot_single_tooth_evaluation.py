#!/usr/bin/env python3
"""
生成齿形的第一齿在旋转角上的图表（只显示评价范围内的数据点）
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from parse_mka_file import MKAParser
import re


def plot_single_tooth_evaluation():
    """
    生成齿形的第一齿在旋转角上的图表（只显示评价范围内的数据点）
    """
    # 读取MKA文件数据
    mka_file = '263751-018-WAV.mka'
    parser = MKAParser(mka_file)
    
    # 获取齿轮齿数
    teeth_count = parser.get_teeth_count()
    if teeth_count == 0:
        teeth_count = 87  # Fallback to 87 based on the data
    
    print(f"Gear teeth count: {teeth_count}")
    
    # 计算每个齿的角度范围
    angle_per_tooth = 360.0 / teeth_count
    print(f"Angle per tooth: {angle_per_tooth:.4f} degrees")
    
    # 获取评价范围
    eval_ranges = parser.get_evaluation_ranges()
    print(f"Evaluation ranges: {eval_ranges}")
    
    # 获取原始齿形数据
    profile_data = parser.profile_data
    
    # 提取第一齿的齿形数据（只取左侧）
    first_tooth_data = None
    first_tooth_id = None
    side = 'left'  # 只使用左侧数据
    
    # 查找第一齿的数据
    for tooth_id, data in profile_data[side].items():
        # 检查是否是第一齿
        tooth_num_match = re.search(r'\d+', tooth_id)
        if tooth_num_match:
            tooth_num = int(tooth_num_match.group(0))
            if tooth_num == 1:
                first_tooth_data = data
                first_tooth_id = tooth_id
                break
    
    if not first_tooth_data:
        print(f"No data found for first tooth on {side} side")
        return
    
    print(f"Found first tooth data: {first_tooth_id}")
    print(f"Number of data points: {len(first_tooth_data)}")
    
    # 计算旋转角度
    profile_angles, flank_angles = parser.calculate_rotation_angles()
    
    # 提取第一齿的旋转角度
    first_tooth_angles = None
    for tooth_id, angles in profile_angles[side].items():
        # 检查是否是第一齿
        tooth_num_match = re.search(r'\d+', tooth_id)
        if tooth_num_match:
            tooth_num = int(tooth_num_match.group(0))
            if tooth_num == 1:
                first_tooth_angles = angles
                break
    
    if not first_tooth_angles:
        print(f"No angles found for first tooth on {side} side")
        return
    
    print(f"Number of angle points: {len(first_tooth_angles)}")
    
    # 确保数据点和角度点数量一致
    min_length = min(len(first_tooth_data), len(first_tooth_angles))
    first_tooth_data = first_tooth_data[:min_length]
    first_tooth_angles = first_tooth_angles[:min_length]
    
    # 过滤出评价范围内的数据点
    eval_data = []
    eval_angles = []
    
    if 'profile' in eval_ranges:
        profile_start = eval_ranges['profile']['start']
        profile_end = eval_ranges['profile']['end']
        print(f"Profile evaluation range: {profile_start} - {profile_end} mm")
        
        # 注意：这里需要根据实际情况映射评价范围到角度范围
        # 由于评价范围是线性尺寸（mm），而我们使用的是角度（度），
        # 我们需要根据测量范围的比例来计算对应的角度范围
        
        # 获取测量范围
        profile_start_mess = eval_ranges['profile']['start_mess']
        profile_end_mess = eval_ranges['profile']['end_mess']
        print(f"Profile measurement range: {profile_start_mess} - {profile_end_mess} mm")
        
        # 计算评价范围在测量范围中的比例
        if profile_end_mess > profile_start_mess:
            total_mess_range = profile_end_mess - profile_start_mess
            eval_start_ratio = (profile_start - profile_start_mess) / total_mess_range
            eval_end_ratio = (profile_end - profile_start_mess) / total_mess_range
            
            print(f"Evaluation range ratio: {eval_start_ratio:.4f} - {eval_end_ratio:.4f}")
            
            # 根据比例过滤数据点
            # 假设数据点是均匀分布的
            num_points = len(first_tooth_data)
            start_idx = int(num_points * eval_start_ratio)
            end_idx = int(num_points * eval_end_ratio)
            
            # 确保索引有效
            start_idx = max(0, start_idx)
            end_idx = min(num_points, end_idx)
            
            print(f"Filtering data points from index {start_idx} to {end_idx}")
            
            # 提取评价范围内的数据点
            eval_data = first_tooth_data[start_idx:end_idx]
            eval_angles = first_tooth_angles[start_idx:end_idx]
    
    # 如果没有过滤出数据点，使用原始数据
    if not eval_data:
        print("No evaluation range data found, using all data points")
        eval_data = first_tooth_data
        eval_angles = first_tooth_angles
    
    print(f"Number of evaluation range data points: {len(eval_data)}")
    
    # 计算评价范围内数据的角度范围
    if eval_angles:
        min_angle = min(eval_angles)
        max_angle = max(eval_angles)
        print(f"Evaluation range angle range: {min_angle:.2f} to {max_angle:.2f} degrees")
    else:
        print("No evaluation range angles available")
        return
    
    # 创建PDF报告
    output_pdf = 'single_tooth_profile_263751-018-WAV_evaluation.pdf'
    
    with PdfPages(output_pdf) as pdf:
        # 创建分析页面
        fig = plt.figure(figsize=(12, 8), dpi=150)
        fig.suptitle(f'First Tooth Profile - Evaluation Range Only (Teeth Count: {teeth_count})', fontsize=16, fontweight='bold')
        
        # 创建子图
        ax = fig.add_subplot(1, 1, 1)
        ax.set_title(f'{side.capitalize()} Profile - First Tooth ({first_tooth_id}) - Evaluation Range', fontsize=14, fontweight='bold')
        ax.set_xlabel('Rotation Angle (degrees)', fontsize=12)
        ax.set_ylabel('Deviation (μm)', fontsize=12)
        ax.tick_params(axis='both', labelsize=10)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 绘制评价范围内的数据
        ax.plot(eval_angles, eval_data, color='blue', linewidth=1.0, marker='o', markersize=4)
        
        # 设置X轴范围，只显示评价范围内的角度范围
        # 添加一些边距，确保数据完全显示
        margin = angle_per_tooth * 0.2
        ax.set_xlim(min_angle - margin, max_angle + margin)
        
        # 添加评价范围标签
        ax.text((min_angle + max_angle) / 2, ax.get_ylim()[1] * 0.95, 
                f'Evaluation Range: {min_angle:.2f}° to {max_angle:.2f}°', 
                ha='center', va='top', 
                fontsize=10, fontweight='bold', color='red')
        
        # 隐藏右侧和顶部边框
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        
        # 调整布局
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # 添加页面到PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    print(f"Single tooth evaluation range analysis completed. Results saved to: {output_pdf}")


if __name__ == '__main__':
    plot_single_tooth_evaluation()
