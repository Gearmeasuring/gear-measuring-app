#!/usr/bin/env python3
"""
左齿形去鼓形、倾斜后的评价范围内的曲线，按照旋转角的公式合并，生成图表查看每一段曲线是否正常
"""

import numpy as np
import matplotlib.pyplot as plt
from parse_mka_file import MKAParser


def remove_crowning_single(data):
    """
    去除鼓形误差（单个齿面）
    使用二次多项式拟合来去除鼓形
    """
    values = np.array(data)
    x = np.linspace(0, 1, len(values))
    
    # 拟合二次多项式
    coeffs = np.polyfit(x, values, 2)
    crowning = np.polyval(coeffs, x)
    
    # 去除鼓形
    values_no_crowning = values - crowning
    
    return values_no_crowning.tolist()


def remove_slope_single(data):
    """
    去除倾斜误差（单个齿面）
    使用线性拟合来去除倾斜
    """
    values = np.array(data)
    x = np.linspace(0, 1, len(values))
    
    # 拟合线性多项式
    coeffs = np.polyfit(x, values, 1)
    slope = np.polyval(coeffs, x)
    
    # 去除倾斜
    values_no_slope = values - slope
    
    return values_no_slope.tolist()


def preprocess_single_tooth(data):
    """
    单个齿面数据预处理
    去除鼓形和倾斜
    """
    # 首先去除鼓形
    data_no_crowning = remove_crowning_single(data)
    # 然后去除倾斜
    data_processed = remove_slope_single(data_no_crowning)
    
    return data_processed


def calculate_rotation_angles_for_tooth(tooth_index, num_points, teeth_count):
    """
    为单个齿计算旋转角
    """
    # 计算每个齿的角度范围
    angle_per_tooth = 360.0 / teeth_count
    # 计算当前齿的起始角度
    start_angle = tooth_index * angle_per_tooth
    # 生成旋转角数组
    rotation_angles = np.linspace(start_angle, start_angle + angle_per_tooth, num_points)
    return rotation_angles


def get_evaluation_range_indices(data_length, eval_ranges):
    """
    根据评价范围计算数据索引范围
    """
    profile_start = eval_ranges['profile']['start']
    profile_end = eval_ranges['profile']['end']
    profile_start_mess = eval_ranges['profile']['start_mess']
    profile_end_mess = eval_ranges['profile']['end_mess']
    
    if profile_start > 0 and profile_end > profile_start and profile_start_mess >= 0 and profile_end_mess > profile_start_mess:
        # 计算评价范围在测量范围内的比例
        total_mess_range = profile_end_mess - profile_start_mess
        eval_start_offset = profile_start - profile_start_mess
        eval_end_offset = profile_end - profile_start_mess
        
        # 计算索引范围
        start_idx = int(data_length * (eval_start_offset / total_mess_range))
        end_idx = int(data_length * (eval_end_offset / total_mess_range))
        
        # 确保索引有效
        start_idx = max(0, min(start_idx, data_length - 1))
        end_idx = max(start_idx + 1, min(end_idx, data_length))
    else:
        # 回退到中间40%
        start_idx = int(data_length * 0.3)
        end_idx = int(data_length * 0.7)
    
    return start_idx, end_idx


def process_and_merge_left_profile_evaluation_range():
    """
    处理左齿形评价范围内的数据，去鼓形和倾斜，然后按照旋转角公式合并
    """
    print("=== 处理左齿形评价范围内的数据，去鼓形和倾斜，按照旋转角公式合并 ===")
    
    # 读取MKA文件
    file_path = '263751-018-WAV.mka'
    parser = MKAParser(file_path)
    
    # 获取齿轮参数
    teeth_count = parser.get_teeth_count()
    if teeth_count == 0:
        teeth_count = 87  # 回退值
    
    print(f"齿轮齿数: {teeth_count}")
    
    # 获取评价范围
    eval_ranges = parser.get_evaluation_ranges()
    print(f"齿形评价范围: {eval_ranges['profile']['start']:.3f} - {eval_ranges['profile']['end']:.3f} mm")
    print(f"齿形测量范围: {eval_ranges['profile']['start_mess']:.3f} - {eval_ranges['profile']['end_mess']:.3f} mm")
    
    # 获取左齿形数据
    left_profile_data = parser.profile_data['left']
    
    print(f"左齿形数量: {len(left_profile_data)}")
    
    # 按齿号顺序排序
    def extract_number(tooth_id):
        # 提取数字部分
        num_part = ''.join(filter(str.isdigit, tooth_id))
        # 提取字母部分（如果有）
        alpha_part = ''.join(filter(str.isalpha, tooth_id))
        # 对于纯数字齿号，返回整数
        if not alpha_part:
            return (int(num_part), '')
        # 对于带字母的齿号（如1a, 1b），返回元组以便正确排序
        return (int(num_part), alpha_part)
    
    sorted_tooth_ids = sorted(left_profile_data.keys(), key=extract_number)
    print(f"排序后的齿号: {sorted_tooth_ids[:5]}...{sorted_tooth_ids[-5:]} ")
    
    # 只保留前87个齿
    if len(sorted_tooth_ids) > 87:
        sorted_tooth_ids = sorted_tooth_ids[:87]
        print(f"只保留前87个齿: {sorted_tooth_ids[:5]}...{sorted_tooth_ids[-5:]} ")
    
    # 处理每个齿的评价范围内的数据
    merged_rotation_angles = []
    merged_processed_data = []
    tooth_boundaries = []  # 记录每个齿的起始索引
    processed_data_per_tooth = []  # 存储每个齿的处理后数据
    rotation_angles_per_tooth = []  # 存储每个齿的旋转角
    evaluation_ranges_per_tooth = []  # 存储每个齿的评价范围索引
    
    for i, tooth_id in enumerate(sorted_tooth_ids):
        # 获取原始数据
        raw_data = left_profile_data[tooth_id]
        num_points = len(raw_data)
        
        # 获取评价范围索引
        start_idx, end_idx = get_evaluation_range_indices(num_points, eval_ranges)
        evaluation_ranges_per_tooth.append((start_idx, end_idx))
        
        # 提取评价范围内的数据
        eval_data = raw_data[start_idx:end_idx]
        
        # 预处理数据（去鼓形和倾斜）
        processed_data = preprocess_single_tooth(eval_data)
        processed_data_per_tooth.append(processed_data)
        
        # 计算旋转角（基于评价范围内的数据点数量）
        rotation_angles = calculate_rotation_angles_for_tooth(i, len(processed_data), len(sorted_tooth_ids))
        rotation_angles_per_tooth.append(rotation_angles)
        
        # 记录齿边界
        tooth_boundaries.append(len(merged_rotation_angles))
        
        # 合并数据
        merged_rotation_angles.extend(rotation_angles.tolist())
        merged_processed_data.extend(processed_data)
        
        # 打印进度
        if (i + 1) % 10 == 0:
            print(f"处理齿 {tooth_id} ({i+1}/{len(sorted_tooth_ids)}), 评价范围索引: {start_idx}-{end_idx}")
    
    print(f"\n处理完成！")
    print(f"合并后的数据点数量: {len(merged_processed_data)}")
    print(f"齿边界数量: {len(tooth_boundaries)}")
    
    return (
        merged_rotation_angles, 
        merged_processed_data, 
        tooth_boundaries, 
        sorted_tooth_ids,
        processed_data_per_tooth,
        rotation_angles_per_tooth,
        evaluation_ranges_per_tooth
    )


def plot_merged_left_profile_evaluation_range():
    """
    生成合并后的左齿形评价范围内的曲线图表
    """
    # 处理和合并数据
    (
        merged_rotation_angles, 
        merged_processed_data, 
        tooth_boundaries, 
        sorted_tooth_ids,
        processed_data_per_tooth,
        rotation_angles_per_tooth,
        evaluation_ranges_per_tooth
    ) = process_and_merge_left_profile_evaluation_range()
    
    # 创建合并图表
    fig = plt.figure(figsize=(15, 10))
    
    # 上部分：合并后的曲线
    ax1 = fig.add_subplot(211)
    ax1.plot(merged_rotation_angles, merged_processed_data, color='blue', linewidth=1.0, alpha=0.8)
    ax1.set_title(f'Merged Left Profile Curve (Evaluation Range) (z = {len(sorted_tooth_ids)})', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Rotation Angle (degrees)', fontsize=10)
    ax1.set_ylabel('Deviation (mm)', fontsize=10)
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # 添加齿边界标记
    for boundary_idx in tooth_boundaries:
        if boundary_idx < len(merged_rotation_angles):
            angle = merged_rotation_angles[boundary_idx]
            ax1.axvline(x=angle, color='red', linestyle='-', linewidth=1.0, alpha=0.7)
    
    # 添加齿号标记
    for i, (boundary_idx, tooth_id) in enumerate(zip(tooth_boundaries, sorted_tooth_ids)):
        if i % 10 == 0 and boundary_idx < len(merged_rotation_angles):
            angle = merged_rotation_angles[boundary_idx]
            ax1.text(angle, ax1.get_ylim()[1] * 0.9, f'T{tooth_id}', 
                     rotation=90, verticalalignment='top', 
                     fontsize=8, color='red', alpha=0.8)
    
    # 下部分：前几个齿的单独曲线
    ax2 = fig.add_subplot(212)
    
    # 绘制前5个齿的曲线
    colors = ['red', 'green', 'blue', 'purple', 'orange']
    for i in range(min(5, len(sorted_tooth_ids))):
        tooth_id = sorted_tooth_ids[i]
        rotation_angles = rotation_angles_per_tooth[i]
        processed_data = processed_data_per_tooth[i]
        start_idx, end_idx = evaluation_ranges_per_tooth[i]
        
        ax2.plot(rotation_angles, processed_data, color=colors[i % len(colors)], 
                 linewidth=1.0, alpha=0.7, label=f'Tooth {tooth_id} (range: {start_idx}-{end_idx})')
    
    ax2.set_title('First 5 Teeth Profiles (Evaluation Range, After Correction)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Rotation Angle (degrees)', fontsize=10)
    ax2.set_ylabel('Deviation (mm)', fontsize=10)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.legend()
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    output_file = 'left_profile_evaluation_range_merged.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n=== 图表生成完成 ===")
    print(f"合并后的左齿形评价范围曲线图表已保存为: {output_file}")
    
    # 关闭图表
    plt.close(fig)


def plot_individual_teeth_evaluation_range():
    """
    生成每个齿的评价范围内的单独图表，以便详细查看每一段曲线
    """
    print("\n=== 生成每个齿的评价范围内的单独图表 ===")
    
    # 读取MKA文件
    file_path = '263751-018-WAV.mka'
    parser = MKAParser(file_path)
    
    # 获取评价范围
    eval_ranges = parser.get_evaluation_ranges()
    
    # 获取左齿形数据
    left_profile_data = parser.profile_data['left']
    
    # 按齿号顺序排序
    def extract_number(tooth_id):
        # 提取数字部分
        num_part = ''.join(filter(str.isdigit, tooth_id))
        # 提取字母部分（如果有）
        alpha_part = ''.join(filter(str.isalpha, tooth_id))
        # 对于纯数字齿号，返回整数
        if not alpha_part:
            return (int(num_part), '')
        # 对于带字母的齿号（如1a, 1b），返回元组以便正确排序
        return (int(num_part), alpha_part)
    
    sorted_tooth_ids = sorted(left_profile_data.keys(), key=extract_number)
    
    # 只保留前87个齿
    if len(sorted_tooth_ids) > 87:
        sorted_tooth_ids = sorted_tooth_ids[:87]
    
    # 处理前10个齿，生成单独图表
    for i, tooth_id in enumerate(sorted_tooth_ids[:10]):
        # 获取原始数据
        raw_data = left_profile_data[tooth_id]
        
        # 获取评价范围索引
        start_idx, end_idx = get_evaluation_range_indices(len(raw_data), eval_ranges)
        
        # 提取评价范围内的数据
        eval_data = raw_data[start_idx:end_idx]
        
        # 预处理数据（去鼓形和倾斜）
        processed_data = preprocess_single_tooth(eval_data)
        
        # 计算旋转角
        rotation_angles = calculate_rotation_angles_for_tooth(i, len(processed_data), len(sorted_tooth_ids))
        
        # 创建图表
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # 绘制原始数据（评价范围内）
        ax.plot(rotation_angles, eval_data, color='blue', linewidth=1.0, alpha=0.7, label='Raw Data (Evaluation Range)')
        
        # 绘制处理后的数据
        ax.plot(rotation_angles, processed_data, color='red', linewidth=1.2, alpha=0.9, label='Processed Data')
        
        # 添加标题和标签
        ax.set_title(f'Tooth {tooth_id} - Evaluation Range (Indices: {start_idx}-{end_idx})', fontsize=12, fontweight='bold')
        ax.set_xlabel('Rotation Angle (degrees)', fontsize=10)
        ax.set_ylabel('Deviation (mm)', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend()
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        output_file = f'tooth_{tooth_id}_evaluation_correction.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"生成齿 {tooth_id} 的评价范围图表: {output_file}")
        
        # 关闭图表
        plt.close(fig)
    
    # 处理用户指定的齿号：20, 28, 35, 43, 57, 62
    specified_teeth = ['20', '28', '35', '43', '57', '62']
    print(f"\n=== 生成用户指定齿号的评价范围图表 ===")
    
    for tooth_id in specified_teeth:
        if tooth_id in left_profile_data:
            # 获取原始数据
            raw_data = left_profile_data[tooth_id]
            
            # 获取评价范围索引
            start_idx, end_idx = get_evaluation_range_indices(len(raw_data), eval_ranges)
            
            # 提取评价范围内的数据
            eval_data = raw_data[start_idx:end_idx]
            
            # 预处理数据（去鼓形和倾斜）
            processed_data = preprocess_single_tooth(eval_data)
            
            # 找到该齿号在排序后的列表中的索引
            tooth_index = None
            for i, tid in enumerate(sorted_tooth_ids):
                if tid == tooth_id:
                    tooth_index = i
                    break
            
            if tooth_index is not None:
                # 计算旋转角
                rotation_angles = calculate_rotation_angles_for_tooth(tooth_index, len(processed_data), len(sorted_tooth_ids))
                
                # 创建图表
                fig = plt.figure(figsize=(10, 6))
                ax = fig.add_subplot(111)
                
                # 绘制原始数据（评价范围内）
                ax.plot(rotation_angles, eval_data, color='blue', linewidth=1.0, alpha=0.7, label='Raw Data (Evaluation Range)')
                
                # 绘制处理后的数据
                ax.plot(rotation_angles, processed_data, color='red', linewidth=1.2, alpha=0.9, label='Processed Data')
                
                # 添加标题和标签
                ax.set_title(f'Tooth {tooth_id} - Evaluation Range (Indices: {start_idx}-{end_idx})', fontsize=12, fontweight='bold')
                ax.set_xlabel('Rotation Angle (degrees)', fontsize=10)
                ax.set_ylabel('Deviation (mm)', fontsize=10)
                ax.grid(True, alpha=0.3, linestyle='--')
                ax.legend()
                
                # 调整布局
                plt.tight_layout()
                
                # 保存图表
                output_file = f'tooth_{tooth_id}_evaluation_correction.png'
                plt.savefig(output_file, dpi=150, bbox_inches='tight')
                print(f"生成齿 {tooth_id} 的评价范围图表: {output_file}")
                
                # 关闭图表
                plt.close(fig)
            else:
                print(f"齿 {tooth_id} 不在排序后的齿号列表中")
        else:
            print(f"齿 {tooth_id} 不在原始数据中")


if __name__ == '__main__':
    plot_merged_left_profile_evaluation_range()
    plot_individual_teeth_evaluation_range()
