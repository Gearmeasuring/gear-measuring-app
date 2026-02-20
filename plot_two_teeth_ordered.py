#!/usr/bin/env python3
"""
生成齿形的前两个齿在旋转角上的图表（第一齿排在第二齿前面）
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from parse_mka_file import MKAParser
import re


def plot_two_teeth_ordered():
    """
    生成齿形的前两个齿在旋转角上的图表（第一齿排在第二齿前面）
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
    
    # 提取前两个齿的齿形数据（只取左侧）
    teeth_data = {}
    teeth_ids = {}
    side = 'left'  # 只使用左侧数据
    
    # 查找前两个齿的数据
    for tooth_id, data in profile_data[side].items():
        # 检查齿号
        tooth_num_match = re.search(r'\d+', tooth_id)
        if tooth_num_match:
            tooth_num = int(tooth_num_match.group(0))
            if tooth_num in [1, 2]:
                teeth_data[tooth_num] = data
                teeth_ids[tooth_num] = tooth_id
                # 如果已经找到两个齿的数据，就停止搜索
                if len(teeth_data) == 2:
                    break
    
    if len(teeth_data) < 2:
        print(f"Found only {len(teeth_data)} teeth data, expected 2")
        return
    
    print(f"Found teeth data: {teeth_ids}")
    for tooth_num, data in teeth_data.items():
        print(f"Tooth {tooth_num} data points: {len(data)}")
    
    # 计算旋转角度
    profile_angles, flank_angles = parser.calculate_rotation_angles()
    
    # 提取前两个齿的旋转角度
    teeth_angles = {}
    for tooth_id, angles in profile_angles[side].items():
        # 检查齿号
        tooth_num_match = re.search(r'\d+', tooth_id)
        if tooth_num_match:
            tooth_num = int(tooth_num_match.group(0))
            if tooth_num in [1, 2]:
                teeth_angles[tooth_num] = angles
                # 如果已经找到两个齿的角度数据，就停止搜索
                if len(teeth_angles) == 2:
                    break
    
    if len(teeth_angles) < 2:
        print(f"Found only {len(teeth_angles)} teeth angles, expected 2")
        return
    
    for tooth_num, angles in teeth_angles.items():
        print(f"Tooth {tooth_num} angle points: {len(angles)}")
    
    # 过滤出评价范围内的数据点
    eval_teeth_data = {}
    eval_teeth_angles = {}
    
    if 'profile' in eval_ranges:
        profile_start = eval_ranges['profile']['start']
        profile_end = eval_ranges['profile']['end']
        print(f"Profile evaluation range: {profile_start} - {profile_end} mm")
        
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
            
            # 为每个齿过滤数据点
            for tooth_num in [1, 2]:
                if tooth_num in teeth_data:
                    # 假设数据点是均匀分布的
                    num_points = len(teeth_data[tooth_num])
                    start_idx = int(num_points * eval_start_ratio)
                    end_idx = int(num_points * eval_end_ratio)
                    
                    # 确保索引有效
                    start_idx = max(0, start_idx)
                    end_idx = min(num_points, end_idx)
                    
                    print(f"Tooth {tooth_num}: Filtering data points from index {start_idx} to {end_idx}")
                    
                    # 提取评价范围内的数据点
                    eval_teeth_data[tooth_num] = teeth_data[tooth_num][start_idx:end_idx]
                    eval_teeth_angles[tooth_num] = teeth_angles[tooth_num][start_idx:end_idx]
    
    # 如果没有过滤出数据点，使用原始数据
    for tooth_num in [1, 2]:
        if tooth_num not in eval_teeth_data and tooth_num in teeth_data:
            print(f"Tooth {tooth_num}: No evaluation range data found, using all data points")
            eval_teeth_data[tooth_num] = teeth_data[tooth_num]
            eval_teeth_angles[tooth_num] = teeth_angles[tooth_num]
    
    # 调整第一齿的角度，使其排在第二齿前面
    # 检查第一齿的角度是否接近360度
    adjusted_teeth_angles = {}
    for tooth_num, angles in eval_teeth_angles.items():
        if angles:
            min_angle = min(angles)
            max_angle = max(angles)
            print(f"Original Tooth {tooth_num} angle range: {min_angle:.2f} to {max_angle:.2f} degrees")
            
            # 如果第一齿的角度接近360度，减去360度使其变为负数
            if tooth_num == 1:
                adjusted_angles = [angle - 360 if angle > 350 else angle for angle in angles]
                adjusted_teeth_angles[tooth_num] = adjusted_angles
                adjusted_min = min(adjusted_angles)
                adjusted_max = max(adjusted_angles)
                print(f"Adjusted Tooth {tooth_num} angle range: {adjusted_min:.2f} to {adjusted_max:.2f} degrees")
            else:
                adjusted_teeth_angles[tooth_num] = angles
    
    # 计算所有齿的调整后角度范围
    all_angles = []
    for tooth_num, angles in adjusted_teeth_angles.items():
        if angles:
            all_angles.extend(angles)
            print(f"Tooth {tooth_num} evaluation range data points: {len(eval_teeth_data[tooth_num])}")
    
    if all_angles:
        overall_min_angle = min(all_angles)
        overall_max_angle = max(all_angles)
        print(f"Overall adjusted angle range: {overall_min_angle:.2f} to {overall_max_angle:.2f} degrees")
    else:
        print("No angles available")
        return
    
    # 创建PDF报告
    output_pdf = 'two_teeth_profile_263751-018-WAV_ordered.pdf'
    
    with PdfPages(output_pdf) as pdf:
        # 创建分析页面
        fig = plt.figure(figsize=(12, 8), dpi=150)
        fig.suptitle(f'Two Teeth Profile - Rotation Angle Analysis (Teeth Count: {teeth_count})', fontsize=16, fontweight='bold')
        
        # 创建子图
        ax = fig.add_subplot(1, 1, 1)
        ax.set_title(f'{side.capitalize()} Profile - First Two Teeth (Ordered)', fontsize=14, fontweight='bold')
        ax.set_xlabel('Rotation Angle (degrees)', fontsize=12)
        ax.set_ylabel('Deviation (μm)', fontsize=12)
        ax.tick_params(axis='both', labelsize=10)
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 为每个齿使用不同的颜色
        colors = {1: 'blue', 2: 'red'}
        
        # 按齿号顺序绘制每个齿的数据
        for tooth_num in [1, 2]:
            if tooth_num in eval_teeth_data and tooth_num in adjusted_teeth_angles:
                ax.plot(adjusted_teeth_angles[tooth_num], eval_teeth_data[tooth_num], 
                        color=colors[tooth_num], linewidth=1.0, marker='o', markersize=4, 
                        label=f'Tooth {tooth_num} ({teeth_ids[tooth_num]})')
        
        # 添加图例
        ax.legend(fontsize=10, loc='upper right')
        
        # 设置X轴范围，显示两个齿的角度范围
        # 添加一些边距，确保数据完全显示
        margin = angle_per_tooth * 0.5
        ax.set_xlim(overall_min_angle - margin, overall_max_angle + margin)
        
        # 隐藏右侧和顶部边框
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        
        # 调整布局
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # 添加页面到PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    print(f"Ordered two teeth profile analysis completed. Results saved to: {output_pdf}")


if __name__ == '__main__':
    plot_two_teeth_ordered()
