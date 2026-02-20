#!/usr/bin/env python3
"""
左齿面去鼓形、去倾斜的评价范围曲线图生成
以展长为标识
"""

import numpy as np
import matplotlib.pyplot as plt
from parse_mka_file import MKAParser


def calculate_profile_length(data, module):
    """
    计算展长数据
    基于模数和数据点索引计算展长
    """
    num_points = len(data)
    # 计算总展长（基于模数的合理值）
    total_length = module * np.pi / 4  # 假设展长为四分之一圆周
    # 生成展长数组
    profile_length = np.linspace(0, total_length, num_points)
    return profile_length


def remove_crowning_single(data, profile_length):
    """
    去除鼓形误差（单个齿面）
    使用二次多项式拟合来去除鼓形
    """
    values = np.array(data)
    
    # 拟合二次多项式
    coeffs = np.polyfit(profile_length, values, 2)
    crowning = np.polyval(coeffs, profile_length)
    
    # 去除鼓形
    values_no_crowning = values - crowning
    
    return values_no_crowning.tolist()


def remove_slope_single(data, profile_length):
    """
    去除倾斜误差（单个齿面）
    使用线性拟合来去除倾斜
    """
    values = np.array(data)
    
    # 拟合线性多项式
    coeffs = np.polyfit(profile_length, values, 1)
    slope = np.polyval(coeffs, profile_length)
    
    # 去除倾斜
    values_no_slope = values - slope
    
    return values_no_slope.tolist()


def preprocess_single_tooth(data, profile_length):
    """
    单个齿面数据预处理
    去除鼓形和倾斜
    """
    # 首先去除鼓形
    data_no_crowning = remove_crowning_single(data, profile_length)
    # 然后去除倾斜
    data_processed = remove_slope_single(data_no_crowning, profile_length)
    
    return data_processed


def get_left_flank_evaluation_data(parser):
    """
    获取左齿面的评价范围数据
    """
    # 获取评价范围
    eval_ranges = parser.get_evaluation_ranges()
    flank_start = eval_ranges['flank']['start']
    flank_end = eval_ranges['flank']['end']
    flank_start_mess = eval_ranges['flank']['start_mess']
    flank_end_mess = eval_ranges['flank']['end_mess']
    
    print(f"左齿面评价范围: {flank_start:.3f} - {flank_end:.3f} mm")
    print(f"左齿面测量范围: {flank_start_mess:.3f} - {flank_end_mess:.3f} mm")
    
    # 获取左齿面数据
    left_flank_data = parser.flank_data['left']
    
    return left_flank_data, eval_ranges


def get_evaluation_range_indices(data_length, eval_ranges):
    """
    根据评价范围计算数据索引范围
    """
    flank_start = eval_ranges['flank']['start']
    flank_end = eval_ranges['flank']['end']
    flank_start_mess = eval_ranges['flank']['start_mess']
    flank_end_mess = eval_ranges['flank']['end_mess']
    
    if flank_start > 0 and flank_end > flank_start and flank_start_mess >= 0 and flank_end_mess > flank_start_mess:
        # 计算评价范围在测量范围内的比例
        total_mess_range = flank_end_mess - flank_start_mess
        eval_start_offset = flank_start - flank_start_mess
        eval_end_offset = flank_end - flank_start_mess
        
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


def plot_left_flank_correction():
    """
    生成左齿面去鼓形、去倾斜的评价范围曲线图
    """
    print("=== 左齿面去鼓形、去倾斜的评价范围曲线图生成 ===")
    
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
    
    print(f"齿轮齿数: {teeth_count}")
    print(f"模数: {module}")
    
    # 获取左齿面数据和评价范围
    left_flank_data, eval_ranges = get_left_flank_evaluation_data(parser)
    
    if not left_flank_data:
        print("错误: 没有找到左侧齿面数据")
        return
    
    print(f"左齿面数量: {len(left_flank_data)}")
    
    # 为每个左齿面生成曲线图
    for tooth_id, raw_data in left_flank_data.items():
        print(f"\n处理齿面: {tooth_id}")
        print(f"原始数据点数量: {len(raw_data)}")
        
        # 计算评价范围索引
        start_idx, end_idx = get_evaluation_range_indices(len(raw_data), eval_ranges)
        print(f"评价范围索引: {start_idx} - {end_idx}")
        
        # 提取评价范围内的数据
        eval_data = raw_data[start_idx:end_idx]
        print(f"评价范围内数据点数量: {len(eval_data)}")
        
        if len(eval_data) < 10:
            print(f"警告: 齿面 {tooth_id} 评价范围内数据点太少，跳过处理")
            continue
        
        # 计算展长数据
        profile_length = calculate_profile_length(eval_data, module)
        
        # 预处理数据
        processed_data = preprocess_single_tooth(eval_data, profile_length)
        
        # 创建图表
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # 绘制原始数据
        ax.plot(profile_length, eval_data, label='原始数据', color='blue', linewidth=1.0, alpha=0.7)
        
        # 绘制处理后的数据
        ax.plot(profile_length, processed_data, label='去鼓形和倾斜后', color='red', linewidth=1.2, alpha=0.9)
        
        # 添加标题和标签
        ax.set_title(f'左齿面 {tooth_id} 去鼓形和倾斜处理', fontsize=12, fontweight='bold')
        ax.set_xlabel('展长 (mm)', fontsize=10)
        ax.set_ylabel('偏差 (mm)', fontsize=10)
        
        # 添加图例
        ax.legend()
        
        # 添加网格
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        output_file = f'left_flank_{tooth_id}_corrected.png'
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"图表已保存为: {output_file}")
        
        # 关闭图表以节省内存
        plt.close(fig)
    
    print("\n=== 所有左齿面处理完成 ===")


def plot_combined_left_flank_correction():
    """
    生成所有左齿面的组合曲线图
    """
    print("\n=== 生成所有左齿面的组合曲线图 ===")
    
    # 读取MKA文件
    file_path = '263751-018-WAV.mka'
    parser = MKAParser(file_path)
    
    # 获取齿轮参数
    module = parser.get_module()
    if module == 0:
        module = 1.859  # 回退值
    
    # 获取左齿面数据和评价范围
    left_flank_data, eval_ranges = get_left_flank_evaluation_data(parser)
    
    if not left_flank_data:
        print("错误: 没有找到左侧齿面数据")
        return
    
    # 创建组合图表
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111)
    
    # 为每个左齿面绘制曲线
    colors = plt.cm.tab20(np.linspace(0, 1, min(len(left_flank_data), 20)))
    
    for i, (tooth_id, raw_data) in enumerate(left_flank_data.items()):
        # 计算评价范围索引
        start_idx, end_idx = get_evaluation_range_indices(len(raw_data), eval_ranges)
        
        # 提取评价范围内的数据
        eval_data = raw_data[start_idx:end_idx]
        
        if len(eval_data) < 10:
            continue
        
        # 计算展长数据
        profile_length = calculate_profile_length(eval_data, module)
        
        # 预处理数据
        processed_data = preprocess_single_tooth(eval_data, profile_length)
        
        # 绘制处理后的数据
        color = colors[i % len(colors)]
        ax.plot(profile_length, processed_data, label=f'齿面 {tooth_id}', 
                color=color, linewidth=0.8, alpha=0.6)
    
    # 添加标题和标签
    ax.set_title('所有左齿面去鼓形和倾斜处理（评价范围）', fontsize=12, fontweight='bold')
    ax.set_xlabel('展长 (mm)', fontsize=10)
    ax.set_ylabel('偏差 (mm)', fontsize=10)
    
    # 添加图例（仅显示前10个）
    handles, labels = ax.get_legend_handles_labels()
    if len(labels) > 10:
        ax.legend(handles[:10], labels[:10], loc='best', fontsize=8)
        ax.text(0.95, 0.05, f'... 共 {len(labels)} 个齿面', 
                transform=ax.transAxes, ha='right', fontsize=8, color='gray')
    else:
        ax.legend(loc='best', fontsize=8)
    
    # 添加网格
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    output_file = 'all_left_flank_corrected_combined.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"组合图表已保存为: {output_file}")
    
    # 关闭图表
    plt.close(fig)


if __name__ == '__main__':
    plot_left_flank_correction()
    plot_combined_left_flank_correction()
