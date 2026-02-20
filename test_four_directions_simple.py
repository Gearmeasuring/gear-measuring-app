#!/usr/bin/env python3
"""
测试左齿形、右齿形、左齿向、右齿向的阶次分析
使用真实的MKA文件数据
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath('.'))

# 直接使用齿轮波纹度软件的核心功能
class MockMeasurementData:
    """模拟测量数据对象"""
    def __init__(self, basic_info, profile_left=None, profile_right=None, helix_left=None, helix_right=None):
        self.basic_info = basic_info
        self.profile_left = profile_left or {}
        self.profile_right = profile_right or {}
        self.helix_left = helix_left or {}
        self.helix_right = helix_right or {}

class MockBasicInfo:
    """模拟基本信息对象"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

def parse_mka_file_simple(mka_file):
    """
    简单解析MKA文件
    
    Args:
        mka_file: MKA文件路径
    
    Returns:
        dict: 解析后的数据
    """
    try:
        # 直接使用齿轮波纹度软件中的MKA解析功能
        import sys
        sys.path.insert(0, os.path.abspath('.'))
        
        # 导入解析器
        from gear_analysis_refactored.utils.file_parser import parse_mka_file
        
        # 解析文件
        parsed_data = parse_mka_file(mka_file)
        return parsed_data
    except Exception as e:
        print(f"✗ 解析MKA文件失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def calculate_average_curve(data_dict):
    """
    计算平均曲线
    
    Args:
        data_dict: 齿数据字典
    
    Returns:
        np.ndarray: 平均曲线
    """
    if not data_dict:
        return None
    
    all_curves = []
    
    for tooth_num, values in data_dict.items():
        if values is None:
            continue
        
        vals = np.array(values, dtype=float)
        if len(vals) >= 8:
            # 对每个齿的数据进行去均值处理
            vals = vals - np.mean(vals)
            all_curves.append(vals)
    
    if not all_curves:
        return None
    
    # 对齐所有曲线到相同长度
    min_len = min(len(c) for c in all_curves)
    aligned_curves = [c[:min_len] for c in all_curves]
    
    # 计算平均
    avg_curve = np.mean(aligned_curves, axis=0)
    return avg_curve

def apply_rc_low_pass_filter(data, dt=None):
    """
    应用RC低通滤波器
    
    Args:
        data: 输入数据
        dt: 点间距
    
    Returns:
        np.ndarray: 滤波后的数据
    """
    if data is None or len(data) <= 1:
        return data
    
    data_len = len(data)
    x = np.array(data, dtype=float)
    y = np.zeros_like(x)
    y[0] = x[0]
    
    # 简单的RC低通滤波器实现
    alpha = 0.1  # 滤波系数
    for i in range(1, data_len):
        y[i] = alpha * x[i] + (1.0 - alpha) * y[i - 1]
    
    return y

def iterative_residual_sine_fit(curve_data, ze, max_order=500, max_components=50):
    """
    迭代残差法正弦拟合频谱分析
    
    Args:
        curve_data: 曲线数据
        ze: 齿数
        max_order: 最大阶次
        max_components: 最大分量数
    
    Returns:
        dict: {阶次: 幅值}
    """
    n = len(curve_data)
    if n < 8:
        return {}
    
    # 生成旋转角x轴
    x = np.linspace(0.0, 2.0 * np.pi, n, dtype=float)
    
    # 初始化残差信号为原始信号
    residual = np.array(curve_data, dtype=float)
    
    # 存储提取的频谱分量
    spectrum_results = {}
    
    # 迭代提取最大阶次
    for iteration in range(max_components):
        # 生成候选阶次：只包含大于或等于ZE的高阶次
        candidate_orders = set()
        
        # 添加ZE及其倍数
        for multiple in range(1, 7):
            order = ze * multiple
            if 1 <= order <= max_order:
                candidate_orders.add(order)
        
        # 添加ZE倍数附近的阶次
        for multiple in range(1, 7):
            center_order = ze * multiple
            for offset in range(-10, 11):
                order = center_order + offset
                if ze <= order <= max_order:
                    candidate_orders.add(order)
        
        # 转换为排序后的列表
        candidate_orders = sorted(candidate_orders)
        
        if not candidate_orders:
            break
        
        # 对每个候选阶次进行正弦拟合
        order_amplitudes = {}
        
        for order in candidate_orders:
            try:
                # 构建矩阵 A = [sin(order*x), cos(order*x), 1]
                sin_x = np.sin(float(order) * x)
                cos_x = np.cos(float(order) * x)
                
                # 计算系数
                a = 2.0 * np.mean(residual * sin_x)
                b = 2.0 * np.mean(residual * cos_x)
                
                # 计算幅值
                amplitude = float(np.sqrt(a * a + b * b))
                
                # 检查幅值是否合理
                max_reasonable_amplitude = 10.0
                if amplitude > max_reasonable_amplitude:
                    continue
                
                order_amplitudes[order] = amplitude
                
            except Exception as e:
                print(f"✗ 拟合阶次 {order} 失败: {e}")
                continue
        
        if not order_amplitudes:
            break
        
        # 按优先级选择最佳阶次：优先选择ZE倍数阶次
        ze_multiple_orders = {order: amp for order, amp in order_amplitudes.items() if order % ze == 0}
        other_orders = {order: amp for order, amp in order_amplitudes.items() if order % ze != 0}
        
        if ze_multiple_orders:
            best_order = max(ze_multiple_orders, key=ze_multiple_orders.get)
            best_amplitude = ze_multiple_orders[best_order]
        else:
            best_order = max(other_orders, key=other_orders.get)
            best_amplitude = other_orders[best_order]
        
        # 保存提取的频谱分量
        spectrum_results[best_order] = best_amplitude
        
        # 从残差信号中移除已提取的正弦波
        a = 2.0 * np.mean(residual * np.sin(float(best_order) * x))
        b = 2.0 * np.mean(residual * np.cos(float(best_order) * x))
        c = np.mean(residual)
        fitted_wave = a * np.sin(float(best_order) * x) + b * np.cos(float(best_order) * x) + c
        residual = residual - fitted_wave
        
        # 检查残差信号是否已经足够小
        residual_rms = np.sqrt(np.mean(np.square(residual)))
        if residual_rms < 0.001:
            break
    
    return spectrum_results

def analyze_direction(data_dict, ze):
    """
    分析指定方向的数据
    
    Args:
        data_dict: 数据字典
        ze: 齿数
    
    Returns:
        dict: 分析结果
    """
    if not data_dict:
        print(f"✗ 数据为空")
        return None
    
    # 计算平均曲线
    avg_curve = calculate_average_curve(data_dict)
    if avg_curve is None:
        print(f"✗ 计算平均曲线失败")
        return None
    
    print(f"✓ 平均曲线长度: {len(avg_curve)}")
    print(f"✓ 平均曲线数据范围: [{np.min(avg_curve):.4f}, {np.max(avg_curve):.4f}]")
    print(f"✓ 平均曲线标准差: {np.std(avg_curve):.4f}")
    
    # 应用RC低通滤波器
    filtered_curve = apply_rc_low_pass_filter(avg_curve)
    print(f"✓ 滤波后数据范围: [{np.min(filtered_curve):.4f}, {np.max(filtered_curve):.4f}]")
    print(f"✓ 滤波后数据标准差: {np.std(filtered_curve):.4f}")
    
    # 进行频谱分析
    spectrum = iterative_residual_sine_fit(filtered_curve, ze)
    
    if spectrum:
        # 按幅值排序
        sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
        top_10 = sorted_spectrum[:10]
        
        print(f"✓ 分析完成，前10个阶次:")
        for order, amp in top_10:
            print(f"  阶次 {order}: {amp:.4f}μm")
        
        return {
            'spectrum': spectrum,
            'top_10': top_10,
            'curve': filtered_curve
        }
    else:
        print(f"✗ 频谱分析失败")
        return None

def plot_results(results, teeth_count):
    """
    绘制分析结果
    
    Args:
        results: 分析结果字典
        teeth_count: 齿数
    """
    try:
        # 创建图表
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'齿轮波纹度频谱分析 (ZE={teeth_count})', fontsize=16)
        
        directions = [
            ('Profile Right', 'profile_right', axes[0, 0]),
            ('Profile Left', 'profile_left', axes[0, 1]),
            ('Helix Right', 'helix_right', axes[1, 0]),
            ('Helix Left', 'helix_left', axes[1, 1])
        ]
        
        for direction_name, key, ax in directions:
            if key in results and results[key]:
                result = results[key]
                spectrum = result['spectrum']
                curve = result['curve']
                
                # 绘制频谱
                orders = list(spectrum.keys())
                amplitudes = list(spectrum.values())
                
                ax.scatter(orders, amplitudes, color='red', label='Spectrum')
                
                # 标记ZE倍数阶次
                ze_multiples = [teeth_count * i for i in range(1, 6)]
                for multiple in ze_multiples:
                    if multiple in spectrum:
                        ax.axvline(x=multiple, color='blue', linestyle='--', alpha=0.5)
                        ax.text(multiple, spectrum[multiple], f'ZE*{multiple//teeth_count}', 
                                color='blue', fontsize=8, rotation=90, verticalalignment='bottom')
                
                # 找到最大阶次
                if spectrum:
                    max_order = max(spectrum, key=spectrum.get)
                    max_amplitude = spectrum[max_order]
                    
                    # 绘制最大阶次的正弦曲线
                    x = np.linspace(0.0, 2.0 * np.pi, len(curve))
                    max_sine = max_amplitude * np.sin(max_order * x)
                    
                    # 创建第二个y轴
                    ax2 = ax.twinx()
                    ax2.plot(np.linspace(0, 100, len(curve)), max_sine, color='blue', label=f'Max Order {max_order}')
                    ax2.set_ylabel('Sine Wave (μm)', color='blue')
                    ax2.tick_params(axis='y', labelcolor='blue')
                    
                    # 添加图例
                    lines1, labels1 = ax.get_legend_handles_labels()
                    lines2, labels2 = ax2.get_legend_handles_labels()
                    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
                
                ax.set_title(direction_name)
                ax.set_xlabel('Order')
                ax.set_ylabel('Amplitude (μm)')
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, 500)
            else:
                ax.set_title(direction_name)
                ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.savefig('four_directions_analysis.png', dpi=150, bbox_inches='tight')
        print("✓ 图表保存为 four_directions_analysis.png")
        
    except Exception as e:
        print(f"✗ 绘制图表失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """
    主函数
    """
    # MKA文件路径
    mka_file = '263751-018-WAV.mka'
    
    # 检查文件是否存在
    if not os.path.exists(mka_file):
        print(f"✗ MKA文件不存在: {mka_file}")
        return
    
    # 解析MKA文件
    print(f"=== 解析MKA文件: {mka_file} ===")
    parsed_data = parse_mka_file_simple(mka_file)
    if not parsed_data:
        return
    
    # 获取基本信息
    gear_data = parsed_data.get('gear_data', {})
    teeth_count = gear_data.get('teeth', 87)
    print(f"✓ 齿数: {teeth_count}")
    
    # 获取各个方向的数据
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    profile_left = profile_data.get('left', {})
    profile_right = profile_data.get('right', {})
    helix_left = flank_data.get('left', {})
    helix_right = flank_data.get('right', {})
    
    print(f"✓ 左齿形数据: {len(profile_left)}个齿")
    print(f"✓ 右齿形数据: {len(profile_right)}个齿")
    print(f"✓ 左齿向数据: {len(helix_left)}个齿")
    print(f"✓ 右齿向数据: {len(helix_right)}个齿")
    
    # 分析四个方向
    results = {}
    
    print("\n=== 分析右齿形 ===")
    results['profile_right'] = analyze_direction(profile_right, teeth_count)
    
    print("\n=== 分析左齿形 ===")
    results['profile_left'] = analyze_direction(profile_left, teeth_count)
    
    print("\n=== 分析右齿向 ===")
    results['helix_right'] = analyze_direction(helix_right, teeth_count)
    
    print("\n=== 分析左齿向 ===")
    results['helix_left'] = analyze_direction(helix_left, teeth_count)
    
    # 验证四组数据是否不同
    print("\n=== 验证四组数据是否不同 ===")
    all_orders = []
    for key, result in results.items():
        if result and result['top_10']:
            top_orders = [order for order, _ in result['top_10'][:3]]
            all_orders.append((key, top_orders))
            print(f"{key} 前3阶: {top_orders}")
    
    # 检查是否所有结果都不同
    if len(all_orders) == 4:
        # 比较前3阶的组合
        combinations = [tuple(orders) for _, orders in all_orders]
        if len(set(combinations)) == 4:
            print("✓ 四组数据的前3阶组合都不同")
        else:
            print("⚠ 部分数据的前3阶组合相同")
    
    # 绘制结果
    plot_results(results, teeth_count)
    
    print("\n=== 分析完成 ===")

if __name__ == '__main__':
    main()
