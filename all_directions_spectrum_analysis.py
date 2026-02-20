#!/usr/bin/env python3
"""
全方向频谱分析脚本 - 包含左齿形、右齿形、左齿向、右齿向
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


def get_evaluation_range_indices(data_length, eval_ranges, direction):
    """
    根据评价范围计算数据索引范围
    direction: 'profile' or 'lead'
    """
    if direction == 'profile':
        start = eval_ranges['profile']['start']
        end = eval_ranges['profile']['end']
        start_mess = eval_ranges['profile']['start_mess']
        end_mess = eval_ranges['profile']['end_mess']
    else:  # lead
        # 尝试使用 lead 评价范围，如果不存在则使用 profile
        if 'lead' in eval_ranges:
            start = eval_ranges['lead']['start']
            end = eval_ranges['lead']['end']
            start_mess = eval_ranges['lead']['start_mess']
            end_mess = eval_ranges['lead']['end_mess']
        else:
            # 回退到使用 profile 评价范围
            start = eval_ranges['profile']['start']
            end = eval_ranges['profile']['end']
            start_mess = eval_ranges['profile']['start_mess']
            end_mess = eval_ranges['profile']['end_mess']
    
    if start > 0 and end > start and start_mess >= 0 and end_mess > start_mess:
        # 计算评价范围在测量范围内的比例
        total_mess_range = end_mess - start_mess
        eval_start_offset = start - start_mess
        eval_end_offset = end - start_mess
        
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


def calculate_spectrum(data, sampling_rate=1.0):
    """
    计算频谱
    """
    # 应用汉宁窗
    window = np.hanning(len(data))
    windowed_data = data * window
    
    # 计算FFT
    fft_result = np.fft.fft(windowed_data)
    freq = np.fft.fftfreq(len(data), d=1/sampling_rate)
    
    # 只取正频率部分
    positive_freq_idx = freq > 0
    freq = freq[positive_freq_idx]
    magnitude = np.abs(fft_result[positive_freq_idx])
    
    return freq, magnitude


def process_direction_data(data_dict, eval_ranges, direction):
    """
    处理单个方向的数据
    """
    print(f"=== 处理{direction}数据 ===")
    
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
    
    sorted_tooth_ids = sorted(data_dict.keys(), key=extract_number)
    print(f"排序后的齿号: {sorted_tooth_ids[:5]}...{sorted_tooth_ids[-5:]} ")
    
    # 只保留前87个齿
    if len(sorted_tooth_ids) > 87:
        sorted_tooth_ids = sorted_tooth_ids[:87]
        print(f"只保留前87个齿: {sorted_tooth_ids[:5]}...{sorted_tooth_ids[-5:]} ")
    
    # 处理每个齿的数据
    merged_data = []
    
    for i, tooth_id in enumerate(sorted_tooth_ids):
        # 获取原始数据
        raw_data = data_dict[tooth_id]
        num_points = len(raw_data)
        
        # 获取评价范围索引
        start_idx, end_idx = get_evaluation_range_indices(num_points, eval_ranges, direction)
        
        # 提取评价范围内的数据
        eval_data = raw_data[start_idx:end_idx]
        
        # 预处理数据（去鼓形和倾斜）
        processed_data = preprocess_single_tooth(eval_data)
        
        # 合并数据
        merged_data.extend(processed_data)
        
        # 打印进度
        if (i + 1) % 10 == 0:
            print(f"处理齿 {tooth_id} ({i+1}/{len(sorted_tooth_ids)}), 评价范围索引: {start_idx}-{end_idx}")
    
    print(f"处理完成！合并后的数据点数量: {len(merged_data)}")
    
    return merged_data


def generate_spectrum_analysis():
    """
    生成全方向频谱分析图表
    """
    print("=== 全方向频谱分析 ===")
    
    # 读取MKA文件
    file_path = '263751-018-WAV.mka'
    parser = MKAParser(file_path)
    
    # 获取评价范围
    eval_ranges = parser.get_evaluation_ranges()
    print(f"齿形评价范围: {eval_ranges['profile']['start']:.3f} - {eval_ranges['profile']['end']:.3f} mm")
    # 检查是否有 lead 评价范围
    if 'lead' in eval_ranges:
        print(f"齿向评价范围: {eval_ranges['lead']['start']:.3f} - {eval_ranges['lead']['end']:.3f} mm")
    else:
        print("警告: 没有找到齿向评价范围，将使用齿形评价范围作为替代")
    
    # 处理四个方向的数据
    directions = {
        'left_profile': {
            'data': parser.profile_data['left'],
            'name': '左齿形',
            'direction': 'profile',
            'color': 'blue'
        },
        'right_profile': {
            'data': parser.profile_data['right'],
            'name': '右齿形',
            'direction': 'profile',
            'color': 'red'
        },
        'left_flank': {
            'data': parser.flank_data['left'],
            'name': '左齿向',
            'direction': 'lead',
            'color': 'green'
        },
        'right_flank': {
            'data': parser.flank_data['right'],
            'name': '右齿向',
            'direction': 'lead',
            'color': 'purple'
        }
    }
    
    # 处理每个方向
    spectrum_data = {}
    for key, info in directions.items():
        if info['data']:
            merged_data = process_direction_data(info['data'], eval_ranges, info['direction'])
            # 计算频谱
            freq, magnitude = calculate_spectrum(merged_data)
            spectrum_data[key] = {
                'freq': freq,
                'magnitude': magnitude,
                'name': info['name'],
                'color': info['color']
            }
        else:
            print(f"警告: {info['name']}数据为空")
    
    # 生成频谱分析图表
    print("\n=== 生成频谱分析图表 ===")
    
    # 创建大图表
    fig = plt.figure(figsize=(15, 12))
    
    # 创建四个子图
    ax1 = fig.add_subplot(221)
    ax2 = fig.add_subplot(222)
    ax3 = fig.add_subplot(223)
    ax4 = fig.add_subplot(224)
    
    subplots = [ax1, ax2, ax3, ax4]
    
    # 绘制每个方向的频谱
    for i, (key, data) in enumerate(spectrum_data.items()):
        if i < len(subplots):
            ax = subplots[i]
            ax.plot(data['freq'], data['magnitude'], color=data['color'], linewidth=1.0, alpha=0.8)
            ax.set_title(f'{data["name"]} 频谱分析', fontsize=12, fontweight='bold')
            ax.set_xlabel('频率 (Hz)', fontsize=10)
            ax.set_ylabel('幅值', fontsize=10)
            ax.grid(True, alpha=0.3, linestyle='--')
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    output_file = 'all_directions_spectrum_analysis.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"频谱分析图表已保存为: {output_file}")
    
    # 关闭图表
    plt.close(fig)
    
    # 生成合并频谱图表
    print("\n=== 生成合并频谱图表 ===")
    
    fig2 = plt.figure(figsize=(15, 8))
    ax = fig2.add_subplot(111)
    
    # 绘制所有方向的频谱在同一个图表上
    for key, data in spectrum_data.items():
        ax.plot(data['freq'], data['magnitude'], color=data['color'], linewidth=1.0, alpha=0.8, label=data['name'])
    
    ax.set_title('全方向频谱对比分析', fontsize=14, fontweight='bold')
    ax.set_xlabel('频率 (Hz)', fontsize=12)
    ax.set_ylabel('幅值', fontsize=12)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend()
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    output_file2 = 'all_directions_spectrum_comparison.png'
    plt.savefig(output_file2, dpi=150, bbox_inches='tight')
    print(f"合并频谱对比图表已保存为: {output_file2}")
    
    # 关闭图表
    plt.close(fig2)


if __name__ == '__main__':
    generate_spectrum_analysis()
