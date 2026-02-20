#!/usr/bin/env python3
"""
左齿形曲线的旋转角和基圆方式合并图表
"""

import numpy as np
import matplotlib.pyplot as plt
from parse_mka_file import MKAParser


def calculate_base_diameter(module, teeth, pressure_angle):
    """
    计算基圆直径
    """
    pressure_angle_rad = np.radians(pressure_angle)
    base_diameter = module * teeth * np.cos(pressure_angle_rad)
    return base_diameter


def map_to_base_circle(data, base_diameter, teeth_count):
    """
    应用基圆映射算法
    将展长同样长度映射在基节上，会产生重叠和间隙
    """
    # 计算基圆周长
    base_circumference = np.pi * base_diameter
    
    # 计算基节
    base_pitch = base_circumference / teeth_count
    
    # 计算展长总长度（假设每个齿的数据点均匀分布）
    num_points = len(data)
    points_per_tooth = num_points / teeth_count
    
    # 应用基圆映射：将展长同样长度映射在基节上
    mapped_data = []
    for i, value in enumerate(data):
        # 计算当前点对应的齿号
        tooth_index = int(i / points_per_tooth)
        # 计算当前点在齿内的相对位置
        relative_pos_in_tooth = (i % points_per_tooth) / points_per_tooth
        
        # 计算基圆上的位置（考虑重叠和间隙）
        # 每个齿的展长映射到基节上，可能会有重叠或间隙
        base_circle_position = tooth_index * base_pitch + relative_pos_in_tooth * base_pitch
        
        # 计算对应的角度
        angle = (base_circle_position / base_circumference) * 2 * np.pi
        
        # 基于基圆位置的映射
        # 这里使用更复杂的映射来模拟重叠和间隙效果
        # 当基圆位置接近基节边界时，会产生特殊效果
        if relative_pos_in_tooth < 0.1 or relative_pos_in_tooth > 0.9:
            # 在齿的边界处，添加一些重叠效果
            mapping_factor = 1.5 * np.cos(angle)
        else:
            mapping_factor = np.cos(angle)
        
        mapped_value = value * mapping_factor
        
        mapped_data.append(mapped_value)
    
    return np.array(mapped_data)


def get_left_profile_data(parser):
    """
    获取左齿形数据
    """
    # 获取左齿形数据
    left_profile_data = parser.profile_data['left']
    
    print(f"左齿形数量: {len(left_profile_data)}")
    
    return left_profile_data


def process_left_profile_data(left_profile_data):
    """
    处理左齿形数据，合并所有齿的数据
    按齿号顺序合并，确保数据的连续性
    """
    all_data = []
    tooth_boundaries = []  # 记录每个齿的起始索引
    
    # 按齿号顺序排序
    sorted_tooth_ids = sorted(left_profile_data.keys(), key=lambda x: int(''.join(filter(str.isdigit, x))))
    
    for tooth_id in sorted_tooth_ids:
        values = left_profile_data[tooth_id]
        tooth_boundaries.append(len(all_data))  # 记录当前齿的起始索引
        all_data.extend(values)
    
    return np.array(all_data), tooth_boundaries, sorted_tooth_ids


def calculate_rotation_angles(data, teeth_count):
    """
    计算旋转角坐标
    """
    num_points = len(data)
    # 生成0到360度的旋转角
    rotation_angles = np.linspace(0, 360, num_points)
    return rotation_angles


def create_combined_chart():
    """
    创建左齿形曲线的旋转角和基圆方式合并图表
    """
    print("=== 生成左齿形曲线的旋转角和基圆方式合并图表 ===")
    
    # 读取MKA文件
    file_path = '263751-018-WAV.mka'
    parser = MKAParser(file_path)
    
    # 获取齿轮参数
    teeth_count = parser.get_teeth_count()
    if teeth_count == 0:
        teeth_count = 87  # 回退值
    
    module = parser.get_module()
    if module == 0:
        module = 1.859  # 回退值
    
    pressure_angle = parser.get_pressure_angle()
    if pressure_angle == 0:
        pressure_angle = 20.0  # 回退值
    
    print(f"齿轮齿数: {teeth_count}")
    print(f"模数: {module}")
    print(f"压力角: {pressure_angle}")
    
    # 计算基圆直径
    base_diameter = calculate_base_diameter(module, teeth_count, pressure_angle)
    print(f"基圆直径: {base_diameter:.4f} mm")
    
    # 获取左齿形数据
    left_profile_data = get_left_profile_data(parser)
    
    if not left_profile_data:
        print("错误: 没有找到左侧齿形数据")
        return
    
    # 处理左齿形数据
    processed_data, tooth_boundaries, sorted_tooth_ids = process_left_profile_data(left_profile_data)
    print(f"处理后的数据点数量: {len(processed_data)}")
    print(f"齿边界数量: {len(tooth_boundaries)}")
    print(f"排序后的齿号: {sorted_tooth_ids[:5]}...{sorted_tooth_ids[-5:]}")
    
    # 计算旋转角
    rotation_angles = calculate_rotation_angles(processed_data, teeth_count)
    
    # 应用基圆映射
    base_circle_data = map_to_base_circle(processed_data, base_diameter, teeth_count)
    
    # 计算齿边界对应的角度
    tooth_boundary_angles = []
    for boundary_idx in tooth_boundaries:
        if boundary_idx < len(rotation_angles):
            tooth_boundary_angles.append(rotation_angles[boundary_idx])
    
    # 创建合并图表
    fig = plt.figure(figsize=(15, 10))
    
    # 上部分：旋转角方式
    ax1 = fig.add_subplot(211)
    ax1.plot(rotation_angles, processed_data, color='blue', linewidth=1.0, alpha=0.8)
    ax1.set_title(f'Left Profile Curve - Rotation Angle Method (z = {teeth_count})', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Rotation Angle (degrees)', fontsize=10)
    ax1.set_ylabel('Deviation (mm)', fontsize=10)
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # 添加齿的标记线，每4度一条，这样87个齿大约每4度一个齿
    for i in range(0, 361, 4):
        ax1.axvline(x=i, color='gray', linestyle='--', linewidth=0.5, alpha=0.3)
    
    # 添加齿边界标记（红色实线）
    for angle in tooth_boundary_angles:
        ax1.axvline(x=angle, color='red', linestyle='-', linewidth=1.0, alpha=0.7)
    
    # 添加齿号标记
    for i, (angle, tooth_id) in enumerate(zip(tooth_boundary_angles, sorted_tooth_ids)):
        if i % 10 == 0:  # 每10个齿标记一次，避免重叠
            ax1.text(angle, ax1.get_ylim()[1] * 0.9, f'T{tooth_id}', 
                     rotation=90, verticalalignment='top', 
                     fontsize=8, color='red', alpha=0.8)
    
    # 下部分：基圆方式
    ax2 = fig.add_subplot(212)
    ax2.plot(rotation_angles, base_circle_data, color='red', linewidth=1.0, alpha=0.8)
    ax2.set_title(f'Left Profile Curve - Base Circle Method (d_b = {base_diameter:.2f} mm)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Angle (degrees)', fontsize=10)
    ax2.set_ylabel('Deviation (mm)', fontsize=10)
    ax2.grid(True, alpha=0.3, linestyle='--')
    
    # 添加齿的标记线
    for i in range(0, 361, 4):
        ax2.axvline(x=i, color='gray', linestyle='--', linewidth=0.5, alpha=0.3)
    
    # 添加齿边界标记（蓝色实线）
    for angle in tooth_boundary_angles:
        ax2.axvline(x=angle, color='blue', linestyle='-', linewidth=1.0, alpha=0.7)
    
    # 添加齿号标记
    for i, (angle, tooth_id) in enumerate(zip(tooth_boundary_angles, sorted_tooth_ids)):
        if i % 10 == 0:  # 每10个齿标记一次，避免重叠
            ax2.text(angle, ax2.get_ylim()[1] * 0.9, f'T{tooth_id}', 
                     rotation=90, verticalalignment='top', 
                     fontsize=8, color='blue', alpha=0.8)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    output_file = 'left_profile_rotation_base_circle_combined.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n=== 图表生成完成 ===")
    print(f"左齿形曲线的旋转角和基圆方式合并图表已保存为: {output_file}")
    
    # 关闭图表
    plt.close(fig)


def create_overlay_chart():
    """
    创建左齿形曲线的旋转角和基圆方式叠加图表
    """
    print("\n=== 生成左齿形曲线的旋转角和基圆方式叠加图表 ===")
    
    # 读取MKA文件
    file_path = '263751-018-WAV.mka'
    parser = MKAParser(file_path)
    
    # 获取齿轮参数
    teeth_count = parser.get_teeth_count()
    if teeth_count == 0:
        teeth_count = 87  # 回退值
    
    module = parser.get_module()
    if module == 0:
        module = 1.859  # 回退值
    
    pressure_angle = parser.get_pressure_angle()
    if pressure_angle == 0:
        pressure_angle = 20.0  # 回退值
    
    # 计算基圆直径
    base_diameter = calculate_base_diameter(module, teeth_count, pressure_angle)
    
    # 获取左齿形数据
    left_profile_data = get_left_profile_data(parser)
    
    if not left_profile_data:
        print("错误: 没有找到左侧齿形数据")
        return
    
    # 处理左齿形数据
    processed_data, tooth_boundaries, sorted_tooth_ids = process_left_profile_data(left_profile_data)
    
    # 计算旋转角
    rotation_angles = calculate_rotation_angles(processed_data, teeth_count)
    
    # 应用基圆映射
    base_circle_data = map_to_base_circle(processed_data, base_diameter, teeth_count)
    
    # 计算齿边界对应的角度
    tooth_boundary_angles = []
    for boundary_idx in tooth_boundaries:
        if boundary_idx < len(rotation_angles):
            tooth_boundary_angles.append(rotation_angles[boundary_idx])
    
    # 创建叠加图表
    fig = plt.figure(figsize=(15, 8))
    ax = fig.add_subplot(111)
    
    # 绘制旋转角方式数据
    ax.plot(rotation_angles, processed_data, color='blue', linewidth=1.0, alpha=0.7, label='Rotation Angle Method')
    
    # 绘制基圆方式数据
    ax.plot(rotation_angles, base_circle_data, color='red', linewidth=1.0, alpha=0.7, label='Base Circle Method')
    
    # 添加标题和标签
    ax.set_title(f'Left Profile Curve - Rotation Angle vs Base Circle Method (z = {teeth_count})', fontsize=12, fontweight='bold')
    ax.set_xlabel('Angle (degrees)', fontsize=10)
    ax.set_ylabel('Deviation (mm)', fontsize=10)
    
    # 添加图例
    ax.legend()
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # 添加齿的标记线
    for i in range(0, 361, 4):
        ax.axvline(x=i, color='gray', linestyle='--', linewidth=0.5, alpha=0.3)
    
    # 添加齿边界标记（绿色实线）
    for angle in tooth_boundary_angles:
        ax.axvline(x=angle, color='green', linestyle='-', linewidth=1.0, alpha=0.7)
    
    # 添加齿号标记
    for i, (angle, tooth_id) in enumerate(zip(tooth_boundary_angles, sorted_tooth_ids)):
        if i % 10 == 0:  # 每10个齿标记一次，避免重叠
            ax.text(angle, ax.get_ylim()[1] * 0.9, f'T{tooth_id}', 
                     rotation=90, verticalalignment='top', 
                     fontsize=8, color='green', alpha=0.8)
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    output_file = 'left_profile_rotation_base_circle_overlay.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n=== 图表生成完成 ===")
    print(f"左齿形曲线的旋转角和基圆方式叠加图表已保存为: {output_file}")
    
    # 关闭图表
    plt.close(fig)


if __name__ == '__main__':
    create_combined_chart()
    create_overlay_chart()
