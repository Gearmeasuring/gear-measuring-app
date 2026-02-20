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

def load_mka_data():
    """
    加载MKA文件数据
    
    Returns:
        dict: 包含四个方向数据的字典
    """
    try:
        # 导入MKA解析功能
        from gear_analysis_refactored.utils.file_parser import parse_mka_file
        
        # MKA文件路径
        mka_file = '263751-018-WAV.mka'
        
        # 解析文件
        parsed_data = parse_mka_file(mka_file)
        
        # 获取基本信息
        gear_data = parsed_data.get('gear_data', {})
        teeth_count = gear_data.get('teeth', 87)
        
        # 获取各个方向的数据
        profile_data = parsed_data.get('profile_data', {})
        flank_data = parsed_data.get('flank_data', {})
        
        profile_left = profile_data.get('left', {})
        profile_right = profile_data.get('right', {})
        helix_left = flank_data.get('left', {})
        helix_right = flank_data.get('right', {})
        
        print(f"✓ 成功加载MKA文件")
        print(f"✓ 齿数: {teeth_count}")
        print(f"✓ 左齿形数据: {len(profile_left)}个齿")
        print(f"✓ 右齿形数据: {len(profile_right)}个齿")
        print(f"✓ 左齿向数据: {len(helix_left)}个齿")
        print(f"✓ 右齿向数据: {len(helix_right)}个齿")
        
        return {
            'teeth_count': teeth_count,
            'profile_left': profile_left,
            'profile_right': profile_right,
            'helix_left': helix_left,
            'helix_right': helix_right
        }
        
    except Exception as e:
        print(f"✗ 加载MKA文件失败: {e}")
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

def calculate_spectrum(curve, ze, max_order=500):
    """
    计算频谱
    
    Args:
        curve: 曲线数据
        ze: 齿数
        max_order: 最大阶次
    
    Returns:
        dict: {阶次: 幅值}
    """
    n = len(curve)
    if n < 8:
        return {}
    
    # 生成旋转角x轴
    x = np.linspace(0.0, 2.0 * np.pi, n, dtype=float)
    
    # 计算每个阶次的幅值
    spectrum = {}
    
    # 只考虑ZE及其倍数阶次
    for multiple in range(1, 6):
        order = ze * multiple
        if order > max_order:
            break
        
        # 计算正弦和余弦分量
        sin_component = np.mean(curve * np.sin(order * x)) * 2.0
        cos_component = np.mean(curve * np.cos(order * x)) * 2.0
        
        # 计算幅值
        amplitude = np.sqrt(sin_component**2 + cos_component**2)
        spectrum[order] = amplitude
    
    return spectrum

def analyze_direction(data_dict, ze, direction_name):
    """
    分析指定方向的数据
    
    Args:
        data_dict: 数据字典
        ze: 齿数
        direction_name: 方向名称
    
    Returns:
        dict: 分析结果
    """
    if not data_dict:
        print(f"✗ {direction_name} 数据为空")
        return None
    
    # 计算平均曲线
    avg_curve = calculate_average_curve(data_dict)
    if avg_curve is None:
        print(f"✗ {direction_name} 计算平均曲线失败")
        return None
    
    print(f"\n=== 分析 {direction_name} ===")
    print(f"✓ 平均曲线长度: {len(avg_curve)}")
    print(f"✓ 平均曲线数据范围: [{np.min(avg_curve):.4f}, {np.max(avg_curve):.4f}]")
    print(f"✓ 平均曲线标准差: {np.std(avg_curve):.4f}")
    
    # 计算频谱
    spectrum = calculate_spectrum(avg_curve, ze)
    
    if spectrum:
        # 按幅值排序
        sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
        
        print(f"✓ 分析完成，阶次分析结果:")
        for order, amp in sorted_spectrum:
            print(f"  阶次 {order}: {amp:.4f}μm")
        
        return {
            'spectrum': spectrum,
            'sorted_spectrum': sorted_spectrum,
            'curve': avg_curve
        }
    else:
        print(f"✗ {direction_name} 频谱分析失败")
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
        print("\n✓ 图表保存为 four_directions_analysis.png")
        
    except Exception as e:
        print(f"✗ 绘制图表失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """
    主函数
    """
    # 加载MKA数据
    data = load_mka_data()
    if not data:
        return
    
    teeth_count = data['teeth_count']
    
    # 分析四个方向
    results = {}
    
    results['profile_right'] = analyze_direction(data['profile_right'], teeth_count, '右齿形')
    results['profile_left'] = analyze_direction(data['profile_left'], teeth_count, '左齿形')
    results['helix_right'] = analyze_direction(data['helix_right'], teeth_count, '右齿向')
    results['helix_left'] = analyze_direction(data['helix_left'], teeth_count, '左齿向')
    
    # 验证四组数据是否不同
    print("\n=== 验证四组数据是否不同 ===")
    all_orders = []
    for key, result in results.items():
        if result and result['sorted_spectrum']:
            top_orders = [order for order, _ in result['sorted_spectrum'][:3]]
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
