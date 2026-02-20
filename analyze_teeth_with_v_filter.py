#!/usr/bin/env python3
"""
分析所有87个齿的左右齿形和齿向数据，应用V形下凹异常过滤，并生成所有曲线的对比图表
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from parse_mka_file import MKAParser
import re
import time


def filter_abnormal_deviation(data, angles=None, normal_threshold=1.5, window_size=3):
    """
    精准识别和修复齿廓偏差中的下凹区域（V形凹陷）
    只处理负值异常，保持其他正常数据不变
    :param data: 偏差数据列表
    :param angles: 角度数据列表（可选）
    :param normal_threshold: 正常偏差范围阈值（负值绝对值大于此值视为下凹）
    :param window_size: 局部中值滤波窗口大小（奇数，建议3-5）
    :return: 过滤后的新数据列表
    """
    if len(data) < 3:
        return data
    
    # 转换为numpy数组
    data_array = np.array(data)
    
    # 步骤1：只标记负值且绝对值超出正常阈值的下凹点
    # 只处理负值异常（下凹），正值保持不变
    abnormal_mask = (data_array < -normal_threshold)
    
    # 步骤2：精准识别V形下凹模式
    # V形下凹的特征：中间点显著低于两侧点，形成明显的V形
    v_shape_mask = np.zeros_like(abnormal_mask, dtype=bool)
    
    for i in range(1, len(data_array) - 1):
        if abnormal_mask[i]:
            # 检查是否形成V形：中间点低于两侧点
            if data_array[i] < data_array[i-1] and data_array[i] < data_array[i+1]:
                # 计算两侧点的平均值，确保中间点显著低于两侧
                avg_surrounding = (data_array[i-1] + data_array[i+1]) / 2
                # 增强V形识别的灵敏度
                if avg_surrounding - data_array[i] > normal_threshold * 0.3:
                    v_shape_mask[i] = True
    
    # 步骤3：扩展识别范围，处理更复杂的V形模式
    # 检查连续的下凹点，识别更宽的V形区域
    extended_mask = np.copy(v_shape_mask)
    for i in range(2, len(data_array) - 2):
        # 检查是否形成更宽的V形模式
        if (data_array[i] < -normal_threshold and
            data_array[i] < data_array[i-2] and
            data_array[i] < data_array[i-1] and
            data_array[i] < data_array[i+1] and
            data_array[i] < data_array[i+2]):
            # 计算周围点的平均值
            avg_surrounding = (data_array[i-2] + data_array[i-1] + data_array[i+1] + data_array[i+2]) / 4
            if avg_surrounding - data_array[i] > normal_threshold * 0.4:
                extended_mask[i] = True
    
    # 计算真正的V形下凹点数量
    num_v_dips = np.sum(extended_mask)
    if num_v_dips > 0:
        print(f"Filtered {num_v_dips} V-shaped dips")
    
    # 步骤4：对每个V形下凹点，用周围正常数据的中值替换
    filtered_data = data_array.copy()
    
    for i in np.where(extended_mask)[0]:
        # 确定窗口范围（避免越界）
        start = max(0, i - window_size//2)
        end = min(len(data_array), i + window_size//2 + 1)
        # 取窗口内非下凹数据（正值或绝对值小于阈值的负值）
        window_data = data_array[start:end]
        valid_data = window_data[window_data >= -normal_threshold]
        # 替换异常值（若窗口内无有效数据，用0替代）
        if len(valid_data) > 0:
            filtered_data[i] = np.median(valid_data)
        else:
            filtered_data[i] = 0
    
    # 步骤5：进一步平滑处理，确保修复后的曲线自然
    # 对修复点的周围进行轻微平滑，避免突兀
    for i in np.where(extended_mask)[0]:
        # 只处理修复点的直接邻居
        for j in range(max(0, i-1), min(len(filtered_data), i+2)):
            if j != i:
                # 计算修复点与邻居点的平均值，实现自然过渡
                avg_val = (filtered_data[i] + filtered_data[j]) / 2
                # 只在邻居点不是异常点时进行平滑
                if data_array[j] >= -normal_threshold:
                    filtered_data[j] = (filtered_data[j] + avg_val) / 2
    
    # 转换回列表并返回
    return filtered_data.tolist()


def remove_outliers(data):
    """
    使用 IQR 和 3σ 方法检测异常值
    将异常值点之间用直线连接，保持曲线连续性
    
    Args:
        data: 齿形数据点列表
        
    Returns:
        处理后的数据点列表
    """
    if len(data) < 3:
        return data
    
    # 转换为numpy数组以便于计算
    data_array = np.array(data)
    
    # 创建掩码，标记异常值
    outlier_mask = np.zeros(len(data_array), dtype=bool)
    
    # 方法1：使用 3σ 原则检测异常值
    mean = np.mean(data_array)
    std = np.std(data_array)
    if std > 0:
        # 3σ 原则：超出均值±3倍标准差的数据视为异常值
        sigma_mask = np.abs(data_array - mean) > 3 * std
        outlier_mask = outlier_mask | sigma_mask
    
    # 方法2：使用 IQR 方法检测异常值
    q1 = np.percentile(data_array, 25)
    q3 = np.percentile(data_array, 75)
    iqr = q3 - q1
    if iqr > 0:
        # IQR 方法：超出四分位数范围±1.5倍IQR的数据视为异常值
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        iqr_mask = (data_array < lower_bound) | (data_array > upper_bound)
        outlier_mask = outlier_mask | iqr_mask
    
    # 方法3：检测明显的突出点（绝对值大于2的点）
    peak_mask = np.abs(data_array) > 2
    outlier_mask = outlier_mask | peak_mask
    
    # 计算异常值的数量
    num_outliers = np.sum(outlier_mask)
    print(f"Removed {num_outliers} outliers from data")
    
    # 创建处理后的数据数组
    processed_data = data_array.copy()
    
    # 查找异常值的开始和结束位置
    if num_outliers > 0:
        # 找到所有非异常值的索引
        valid_indices = np.where(~outlier_mask)[0]
        
        if len(valid_indices) >= 2:
            # 对每个异常值点，使用前后最近的有效点进行线性插值
            for i in range(len(data_array)):
                if outlier_mask[i]:
                    # 找到左侧最近的有效点
                    left_indices = valid_indices[valid_indices < i]
                    left_idx = left_indices[-1] if len(left_indices) > 0 else None
                    
                    # 找到右侧最近的有效点
                    right_indices = valid_indices[valid_indices > i]
                    right_idx = right_indices[0] if len(right_indices) > 0 else None
                    
                    # 如果左右都有有效点，进行线性插值
                    if left_idx is not None and right_idx is not None:
                        # 计算插值权重
                        t = (i - left_idx) / (right_idx - left_idx)
                        # 线性插值
                        processed_data[i] = data_array[left_idx] * (1 - t) + data_array[right_idx] * t
                    elif left_idx is not None:
                        # 只有左侧有有效点，使用左侧值
                        processed_data[i] = data_array[left_idx]
                    elif right_idx is not None:
                        # 只有右侧有有效点，使用右侧值
                        processed_data[i] = data_array[right_idx]
                    else:
                        # 没有有效点，使用均值
                        processed_data[i] = mean
    
    # 转换回列表并返回
    return processed_data.tolist()


def remove_crowning_and_tilt(data):
    """
    去除齿形曲线中的鼓形和倾斜
    
    Args:
        data: 齿形数据点列表
        
    Returns:
        去除鼓形和倾斜后的齿形数据点列表
    """
    if len(data) < 5:
        return data
    
    # 转换为numpy数组
    data_array = np.array(data)
    
    # 创建x坐标（数据点索引）
    x = np.arange(len(data_array))
    
    # 拟合二次曲线，用于去除鼓形和倾斜
    # 二次曲线可以同时捕捉线性（倾斜）和二次（鼓形）分量
    coefficients = np.polyfit(x, data_array, 2)
    
    # 生成拟合曲线
    fitted_curve = np.polyval(coefficients, x)
    
    # 从原始数据中减去拟合曲线，得到去除鼓形和倾斜后的数据
    corrected_data = data_array - fitted_curve
    
    # 计算去除的倾斜和鼓形程度
    # 线性分量（倾斜）：系数[1]
    # 二次分量（鼓形）：系数[0]
    print(f"Removed tilt: {coefficients[1]:.4f} μm/unit, crown: {coefficients[0]:.4f} μm/unit²")
    
    # 转换回列表并返回
    return corrected_data.tolist()


def analyze_all_teeth_with_v_filter():
    """
    分析所有87个齿的左右齿形和齿向数据，应用V形下凹异常过滤，并生成所有曲线的对比图表
    """
    print("\n=== Analyzing All 87 Teeth with V-shaped Dip Filter ===")
    
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
    
    # 获取齿形和齿向数据
    profile_data = parser.profile_data
    flank_data = parser.flank_data
    
    # 获取旋转角度
    profile_angles, flank_angles = parser.calculate_rotation_angles()
    
    # 处理左右两侧
    sides = ['left', 'right']
    
    for data_side in sides:
        print(f"\n=== Processing {data_side.capitalize()} Side ===")
        
        # 存储所有齿的数据
        all_teeth_data = {}
        
        # 遍历1-87个齿
        for tooth_num in range(1, teeth_count + 1):
            print(f"\nProcessing tooth {tooth_num}...")
            
            # 存储当前齿的数据
            tooth_data = {
                'profile': [],
                'flank': [],
                'profile_angles': [],
                'flank_angles': []
            }
            
            # 查找当前齿的齿形数据
            if data_side in profile_data:
                for tooth_id, data in profile_data[data_side].items():
                    tooth_num_match = re.search(r'\d+', tooth_id)
                    if tooth_num_match:
                        current_tooth = int(tooth_num_match.group(0))
                        if current_tooth == tooth_num:
                            print(f"Found profile data for tooth {tooth_num}: {tooth_id}")
                            tooth_data['profile'] = data
                            break
            
            # 查找当前齿的齿向数据
            if data_side in flank_data:
                for tooth_id, data in flank_data[data_side].items():
                    tooth_num_match = re.search(r'\d+', tooth_id)
                    if tooth_num_match:
                        current_tooth = int(tooth_num_match.group(0))
                        if current_tooth == tooth_num:
                            print(f"Found flank data for tooth {tooth_num}: {tooth_id}")
                            tooth_data['flank'] = data
                            break
            
            # 查找当前齿的齿形旋转角度
            if data_side in profile_angles:
                for angle_tooth_id, angles in profile_angles[data_side].items():
                    tooth_num_match = re.search(r'\d+', angle_tooth_id)
                    if tooth_num_match:
                        current_tooth = int(tooth_num_match.group(0))
                        if current_tooth == tooth_num:
                            print(f"Found profile angles for tooth {tooth_num}: {angle_tooth_id}")
                            tooth_data['profile_angles'] = angles
                            break
            
            # 查找当前齿的齿向旋转角度
            if data_side in flank_angles:
                for angle_tooth_id, angles in flank_angles[data_side].items():
                    tooth_num_match = re.search(r'\d+', angle_tooth_id)
                    if tooth_num_match:
                        current_tooth = int(tooth_num_match.group(0))
                        if current_tooth == tooth_num:
                            print(f"Found flank angles for tooth {tooth_num}: {angle_tooth_id}")
                            tooth_data['flank_angles'] = angles
                            break
            
            # 过滤出评价范围内的数据点
            if 'profile' in eval_ranges and tooth_data['profile']:
                range_start = eval_ranges['profile']['start']
                range_end = eval_ranges['profile']['end']
                
                # 获取测量范围
                range_start_mess = eval_ranges['profile']['start_mess']
                range_end_mess = eval_ranges['profile']['end_mess']
                
                # 计算评价范围在测量范围中的比例
                if range_end_mess > range_start_mess:
                    total_mess_range = range_end_mess - range_start_mess
                    eval_start_ratio = (range_start - range_start_mess) / total_mess_range
                    eval_end_ratio = (range_end - range_start_mess) / total_mess_range
                    
                    # 提取评价范围内的数据点
                    num_points = len(tooth_data['profile'])
                    start_idx = int(num_points * eval_start_ratio)
                    end_idx = int(num_points * eval_end_ratio)
                    
                    # 确保索引有效
                    start_idx = max(0, start_idx)
                    end_idx = min(num_points, end_idx)
                    
                    # 提取评价范围内的数据点
                    raw_data = tooth_data['profile'][start_idx:end_idx]
                    # 应用V形下凹异常过滤
                    filtered_data = filter_abnormal_deviation(raw_data, normal_threshold=0.5, window_size=5)
                    # 剔除异常值
                    processed_data = remove_outliers(filtered_data)
                    # 去除鼓形和倾斜
                    processed_data = remove_crowning_and_tilt(processed_data)
                    tooth_data['profile'] = processed_data
                    
                    # 确保角度数据与处理后的数据长度匹配
                    if tooth_data['profile_angles']:
                        if len(processed_data) == len(raw_data):
                            tooth_data['profile_angles'] = tooth_data['profile_angles'][start_idx:end_idx]
            
            if 'flank' in eval_ranges and tooth_data['flank']:
                range_start = eval_ranges['flank']['start']
                range_end = eval_ranges['flank']['end']
                
                # 获取测量范围
                range_start_mess = eval_ranges['flank']['start_mess']
                range_end_mess = eval_ranges['flank']['end_mess']
                
                # 计算评价范围在测量范围中的比例
                if range_end_mess > range_start_mess:
                    total_mess_range = range_end_mess - range_start_mess
                    eval_start_ratio = (range_start - range_start_mess) / total_mess_range
                    eval_end_ratio = (range_end - range_start_mess) / total_mess_range
                    
                    # 提取评价范围内的数据点
                    num_points = len(tooth_data['flank'])
                    start_idx = int(num_points * eval_start_ratio)
                    end_idx = int(num_points * eval_end_ratio)
                    
                    # 确保索引有效
                    start_idx = max(0, start_idx)
                    end_idx = min(num_points, end_idx)
                    
                    # 提取评价范围内的数据点
                    raw_data = tooth_data['flank'][start_idx:end_idx]
                    # 应用V形下凹异常过滤
                    filtered_data = filter_abnormal_deviation(raw_data, normal_threshold=0.5, window_size=5)
                    # 剔除异常值
                    processed_data = remove_outliers(filtered_data)
                    # 去除鼓形和倾斜
                    processed_data = remove_crowning_and_tilt(processed_data)
                    tooth_data['flank'] = processed_data
                    
                    # 确保角度数据与处理后的数据长度匹配
                    if tooth_data['flank_angles']:
                        if len(processed_data) == len(raw_data):
                            tooth_data['flank_angles'] = tooth_data['flank_angles'][start_idx:end_idx]
            
            # 调整角度范围，使其在0-360度范围内
            if tooth_data['profile_angles']:
                min_angle = min(tooth_data['profile_angles'])
                tooth_data['profile_angles'] = [angle - min_angle for angle in tooth_data['profile_angles']]
            
            if tooth_data['flank_angles']:
                min_angle = min(tooth_data['flank_angles'])
                tooth_data['flank_angles'] = [angle - min_angle for angle in tooth_data['flank_angles']]
            
            # 存储当前齿的数据
            all_teeth_data[tooth_num] = tooth_data
        
        # 创建对比图表
        timestamp = time.strftime('%H%M%S')
        output_pdf = f'all_teeth_with_v_filter_{data_side}_{timestamp}.pdf'
        
        with PdfPages(output_pdf) as pdf:
            # 为每个齿创建对比页面
            for tooth_num, tooth_data in all_teeth_data.items():
                print(f"Creating chart for tooth {tooth_num}...")
                
                # 创建对比页面
                fig = plt.figure(figsize=(15, 10), dpi=150)
                fig.suptitle(f'Tooth {tooth_num} Profile vs Flank Comparison ({data_side.capitalize()})', fontsize=16, fontweight='bold')
                
                # 创建子图
                ax = fig.add_subplot(1, 1, 1)
                ax.set_title(f'Profile (齿形) vs Flank (齿向) - Tooth {tooth_num}', fontsize=14, fontweight='bold')
                ax.set_xlabel('Normalized Angle (degrees)', fontsize=12)
                ax.set_ylabel('Deviation (μm)', fontsize=12)
                ax.tick_params(axis='both', labelsize=10)
                ax.grid(True, alpha=0.3, linestyle='--')
                
                # 绘制齿形曲线
                if tooth_data['profile'] and tooth_data['profile_angles']:
                    ax.plot(tooth_data['profile_angles'], tooth_data['profile'], 
                            color='blue', linewidth=1.5, marker='o', markersize=3, 
                            label='Profile (齿形)')
                
                # 绘制齿向曲线
                if tooth_data['flank'] and tooth_data['flank_angles']:
                    ax.plot(tooth_data['flank_angles'], tooth_data['flank'], 
                            color='green', linewidth=1.5, marker='s', markersize=3, 
                            label='Flank (齿向)')
                
                # 添加图例
                ax.legend(fontsize=10, loc='upper right')
                
                # 隐藏右侧和顶部边框
                ax.spines['right'].set_visible(False)
                ax.spines['top'].set_visible(False)
                
                # 调整布局
                plt.tight_layout(rect=[0, 0.03, 1, 0.95])
                
                # 添加页面到PDF
                pdf.savefig(fig, bbox_inches='tight')
                plt.close(fig)
        
        print(f"\n{data_side.capitalize()} side processing completed. Results saved to: {output_pdf}")


if __name__ == '__main__':
    # 分析所有87个齿的齿形和齿向数据，应用V形下凹异常过滤
    analyze_all_teeth_with_v_filter()
    
    print("\n=== All analysis completed ===")
