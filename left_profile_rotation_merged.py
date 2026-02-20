#!/usr/bin/env python3
"""
左齿形去鼓形、倾斜后的每一个曲线，按照旋转角的公式合并，生成图表查看每一段曲线是否正常
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


def process_and_merge_left_profile():
    """
    处理左齿形数据，去鼓形和倾斜，然后按照旋转角公式合并
    """
    print("=== 处理左齿形数据，去鼓形和倾斜，按照旋转角公式合并 ===")
    
    # 读取MKA文件
    file_path = '263751-018-WAV.mka'
    parser = MKAParser(file_path)
    
    # 获取齿轮参数
    teeth_count = parser.get_teeth_count()
    if teeth_count == 0:
        teeth_count = 87  # 回退值
    
    print(f"齿轮齿数: {teeth_count}")
    
    # 获取左齿形数据
    left_profile_data = parser.profile_data['left']
    
    print(f"左齿形数量: {len(left_profile_data)}")
    
    # 按齿号顺序排序
    def extract_number(tooth_id):
        return int(''.join(filter(str.isdigit, tooth_id)))
    
    sorted_tooth_ids = sorted(left_profile_data.keys(), key=extract_number)
    print(f"排序后的齿号: {sorted_tooth_ids[:5]}...{sorted_tooth_ids[-5:]}")
    
    # 处理每个齿的数据
    merged_rotation_angles = []
    merged_processed_data = []
    tooth_boundaries = []  # 记录每个齿的起始索引
    processed_data_per_tooth = []  # 存储每个齿的处理后数据
    rotation_angles_per_tooth = []  # 存储每个齿的旋转角
    
    for i, tooth_id in enumerate(sorted_tooth_ids):
        # 获取原始数据
        raw_data = left_profile_data[tooth_id]
        num_points = len(raw_data)
        
        # 预处理数据（去鼓形和倾斜）
        processed_data = preprocess_single_tooth(raw_data)
        processed_data_per_tooth.append(processed_data)
        
        # 计算旋转角
        rotation_angles = calculate_rotation_angles_for_tooth(i, num_points, len(sorted_tooth_ids))
        rotation_angles_per_tooth.append(rotation_angles)
        
        # 记录齿边界
        tooth_boundaries.append(len(merged_rotation_angles))
        
        # 合并数据
        merged_rotation_angles.extend(rotation_angles.tolist())
        merged_processed_data.extend(processed_data)
        
        # 打印进度
        if (i + 1) % 10 == 0:
            print(f"处理齿 {tooth_id} ({i+1}/{len(sorted_tooth_ids)})")
    
    print(f"\n处理完成！")
    print(f"合并后的数据点数量: {len(merged_processed_data)}")
    print(f"齿边界数量: {len(tooth_boundaries)}")
    
    return (
        merged_rotation_angles, 
        merged_processed_data, 
        tooth_boundaries, 
        sorted_tooth_ids,
        processed_data_per_tooth,
        rotation_angles_per_tooth
    )


def plot_merged_left_profile():
    """
    生成合并后的左齿形曲线图表
    """
    # 处理和合并数据
    (
        merged_rotation_angles, 
        merged_processed_data, 
        tooth_boundaries, 
        sorted_tooth_ids,
        processed_data_per_tooth,
        rotation_angles_per_tooth
    ) = process_and_merge_left_profile()
    
    # 创建合并图表
    fig = plt.figure(figsize=(15, 10))
    
    # 上部分：合并后的曲线
    ax1 = fig.add_subplot(211)
    ax1.plot(merged_rotation_angles, merged_processed_data, color='blue', linewidth=1.0, alpha=0.8)
    ax1.set_title(f'Merged Left Profile Curve (z = {len(sorted_tooth_ids)})', fontsize=12, fontweight='bold')
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
        
        ax2.plot(rotation_angles, processed_data, color=colors[i % len(colors)], 
                 linewidth=1.0, alpha=0.7, label=f'Tooth {tooth_id}')
    
    ax2.set_title('First 5 Teeth Profiles (After Correction)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Rotation Angle (degrees)', fontsize=10)
    ax2.set_ylabel('Deviation (mm)', fontsize=10)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.legend()
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    output_file = 'left_profile_rotation_merged.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n=== 图表生成完成 ===")
    print(f"合并后的左齿形曲线图表已保存为: {output_file}")
    
    # 关闭图表
    plt.close(fig)


def plot_individual_teeth():
    """
    生成每个齿的单独图表，以便详细查看每一段曲线
    """
    print("\n=== 生成每个齿的单独图表 ===")
    
    # 读取MKA文件
    file_path = '263751-018-WAV.mka'
    parser = MKAParser(file_path)
    
    # 获取左齿形数据
    left_profile_data = parser.profile_data['left']
    
    # 按齿号顺序排序
    def extract_number(tooth_id):
        return int(''.join(filter(str.isdigit, tooth_id)))
    
    sorted_tooth_ids = sorted(left_profile_data.keys(), key=extract_number)
    
    # 处理前10个齿，生成单独图表
    for i, tooth_id in enumerate(sorted_tooth_ids[:10]):
        # 获取原始数据
        raw_data = left_profile_data[tooth_id]
        
        # 预处理数据（去鼓形和倾斜）
        processed_data = preprocess_single_tooth(raw_data)
        
        # 计算旋转角
        rotation_angles = calculate_rotation_angles_for_tooth(i, len(raw_data), len(sorted_tooth_ids))
        
        # 创建图表
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # 绘制原始数据
        ax.plot(rotation_angles, raw_data, color='blue', linewidth=1.0, alpha=0.7, label='Raw Data')
        
        # 绘制处理后的数据
        ax.plot(rotation_angles, processed_data, color='red', linewidth=1.2, alpha=0.9, label='Processed Data')
        
        # 添加标题和标签
        ax.set_title(f'Tooth {tooth_id} - Before vs After Correction', fontsize=12, fontweight='bold')
        ax.set_xlabel('Rotation Angle (degrees)', fontsize=10)
        ax.set_ylabel('Deviation (mm)', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend()
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        output_file = f'tooth_{tooth_id}_correction.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"生成齿 {tooth_id} 的图表: {output_file}")
        
        # 关闭图表
        plt.close(fig)


if __name__ == '__main__':
    plot_merged_left_profile()
    plot_individual_teeth()
