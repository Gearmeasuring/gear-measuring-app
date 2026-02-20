"""
波纹度频谱分析 V11 - 使用平均曲线方法

关键修正：
1. 先截取评价范围内的数据
2. 计算所有齿的平均曲线
3. 对平均曲线进行频谱分析
"""
import os
import sys
import math
import numpy as np
import warnings
warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


def extract_eval_range(values, eval_markers):
    """根据评价范围标记点截取数据"""
    if not eval_markers or len(eval_markers) != 4:
        return values
    
    start_meas, start_eval, end_eval, end_meas = eval_markers
    n_points = len(values)
    total_len = abs(end_meas - start_meas)
    
    if total_len <= 0:
        return values
    
    dist_to_start = abs(start_eval - start_meas)
    dist_to_end = abs(end_eval - start_meas)
    
    idx_start = int(n_points * (dist_to_start / total_len))
    idx_end = int(n_points * (dist_to_end / total_len))
    
    idx_start = max(0, min(idx_start, n_points - 1))
    idx_end = max(0, min(idx_end, n_points - 1))
    
    if idx_end > idx_start + 5:
        return values[idx_start:idx_end]
    
    return values


def remove_outliers_and_slope_deviations(data, threshold=2.0, slope_threshold=0.03):
    """剔除单个峰值和斜率偏差"""
    if data is None or len(data) < 5:
        return data
    
    original_data = np.array(data, dtype=float)
    n = len(original_data)
    
    mean_val = np.mean(original_data)
    std_val = np.std(original_data)
    data_array = original_data.copy()
    
    if std_val > 0:
        z_scores = np.abs((data_array - mean_val) / std_val)
        outlier_mask = z_scores < threshold
        data_array = data_array[outlier_mask]
        
        if len(data_array) < 5:
            data_array = original_data.copy()
    
    if len(data_array) >= 5:
        x = np.arange(len(data_array))
        slope = np.polyfit(x, data_array, 1)[0]
        
        if abs(slope) > slope_threshold:
            trend = np.polyval(np.polyfit(x, data_array, 1), x)
            data_array = data_array - trend
    
    return data_array


def calculate_average_curve(data_dict, eval_markers=None):
    """
    计算平均曲线（所有齿的平均，在评价范围内）
    与原始代码一致的方法
    """
    if not data_dict:
        return None
    
    all_curves = []
    
    for tooth_num, values in data_dict.items():
        if values is None:
            continue
        
        # 处理不同数据格式
        if isinstance(values, dict):
            if 'values' in values:
                vals = np.array(values['values'], dtype=float)
            else:
                continue
        elif isinstance(values, (list, tuple, np.ndarray)):
            vals = np.array(values, dtype=float)
        else:
            continue
        
        if len(vals) == 0:
            continue
        
        # 提取评价范围
        if eval_markers and len(eval_markers) == 4:
            vals = extract_eval_range(vals, eval_markers)
        
        # 剔除单个峰值和斜率偏差
        vals = remove_outliers_and_slope_deviations(vals, slope_threshold=0.03)
        
        if len(vals) >= 8:
            all_curves.append(vals)
    
    if len(all_curves) == 0:
        return None
    
    # 对齐所有曲线到相同长度（使用最短长度）
    min_len = min(len(c) for c in all_curves)
    if min_len < 8:
        return None
    
    aligned_curves = [c[:min_len] for c in all_curves]
    
    # 计算平均
    avg_curve = np.mean(aligned_curves, axis=0)
    
    return avg_curve


def iterative_sine_fit_klingelnberg(curve_data, teeth_count, max_components=10):
    """迭代最小二乘法提取频谱"""
    n = len(curve_data)
    if n < 8:
        return {}
    
    x = np.linspace(0.0, 1.0, n, dtype=float)
    residual = np.array(curve_data, dtype=float)
    spectrum_results = {}
    
    max_iterations = 15
    amplitude_threshold = 0.001
    
    for iteration in range(max_iterations):
        candidate_orders = set()
        max_ze_multiple = 10
        for mult in range(1, max_ze_multiple + 1):
            freq = teeth_count * mult
            if freq not in spectrum_results:
                candidate_orders.add(freq)
        
        candidate_orders = sorted(candidate_orders)
        if len(candidate_orders) == 0:
            break
        
        best_order = None
        best_amplitude = 0.0
        best_coeffs = None
        
        for order in candidate_orders:
            try:
                sin_x = np.sin(2.0 * np.pi * order * x)
                cos_x = np.cos(2.0 * np.pi * order * x)
                A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
                
                coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
                a, b, c = coeffs
                amplitude = np.sqrt(a*a + b*b)
                
                if amplitude > 10.0:
                    continue
                
                if amplitude > best_amplitude:
                    best_amplitude = amplitude
                    best_order = order
                    best_coeffs = (a, b, c)
            except:
                continue
        
        if best_order is None or best_amplitude < amplitude_threshold:
            break
        
        spectrum_results[int(best_order)] = best_amplitude
        
        a, b, c = best_coeffs
        fitted_wave = a * np.sin(2.0 * np.pi * best_order * x) + b * np.cos(2.0 * np.pi * best_order * x) + c
        residual = residual - fitted_wave
        
        if len(spectrum_results) >= max_components:
            break
    
    return spectrum_results


def analyze_ripple(mka_file):
    """分析波纹度"""
    print("="*70)
    print("波纹度频谱分析 V11 (平均曲线方法)")
    print("="*70)
    print("\n关键修正:")
    print("1. 先截取评价范围内的数据")
    print("2. 计算所有齿的平均曲线")
    print("3. 对平均曲线进行频谱分析")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    
    print(f"\n【齿轮参数】")
    print(f"  齿数 ZE = {teeth_count}")
    
    # 评价范围标记点
    profile_eval_markers = (174.24, 174.822, 180.603, 182.775)
    helix_eval_markers = (0.0, 2.1, 39.9, 42.0)
    
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    results = {}
    
    directions = [
        ('left', 'profile', '左齿形', profile_data, profile_eval_markers),
        ('right', 'profile', '右齿形', profile_data, profile_eval_markers),
        ('left', 'flank', '左齿向', flank_data, helix_eval_markers),
        ('right', 'flank', '右齿向', flank_data, helix_eval_markers)
    ]
    
    print(f"\nKlingelnberg报告参考值:")
    print(f"  左齿形 87阶: 0.14 μm")
    print(f"  右齿形 87阶: 0.15 μm")
    print(f"  左齿向 87阶: 0.12 μm")
    print(f"  右齿向 87阶: 0.09 μm")
    
    for side, data_type, name, data_source, eval_markers in directions:
        print(f"\n{'='*70}")
        print(f"【{name}】")
        print('='*70)
        
        data_dict = data_source.get(side, {})
        
        if not data_dict:
            print(f"  无数据")
            continue
        
        print(f"  数据齿数: {len(data_dict)}")
        print(f"  评价范围: {eval_markers}")
        
        # 计算平均曲线（使用评价范围截取）
        avg_curve = calculate_average_curve(data_dict, eval_markers)
        
        if avg_curve is None or len(avg_curve) < 8:
            print(f"  平均曲线计算失败")
            continue
        
        print(f"  平均曲线点数: {len(avg_curve)}")
        print(f"  数据范围: {np.min(avg_curve):.2f} ~ {np.max(avg_curve):.2f} μm")
        
        # 计算频谱
        spectrum = iterative_sine_fit_klingelnberg(avg_curve, teeth_count, max_components=10)
        sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n  提取的阶次 (ZE整数倍):")
        for i, (order, amp) in enumerate(sorted_spectrum[:5], 1):
            print(f"    {i}. 阶次 {order:3d} (ZE×{order//teeth_count}): 幅值 = {amp:.4f} μm")
        
        order_87_amp = spectrum.get(87, 0)
        print(f"\n  87阶幅值: {order_87_amp:.4f} μm")
        
        results[name] = {
            'order_87': order_87_amp,
            'spectrum': sorted_spectrum
        }
    
    # 打印对比汇总
    print("\n" + "="*70)
    print("对比汇总")
    print("="*70)
    print(f"\n{'曲线':<10} {'我们的结果':<15} {'Klingelnberg':<15} {'比率':<10}")
    print("-"*50)
    
    klingelnberg_values = {
        '左齿形': 0.14,
        '右齿形': 0.15,
        '左齿向': 0.12,
        '右齿向': 0.09
    }
    
    for name, data in results.items():
        our_val = data['order_87']
        k_val = klingelnberg_values.get(name, 0)
        ratio = our_val / k_val if k_val > 0 else 0
        print(f"{name:<10} {our_val:<15.4f} {k_val:<15.2f} {ratio:<10.2f}x")
    
    return results


def main():
    mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    if not os.path.exists(mka_file):
        print(f"文件不存在: {mka_file}")
        return
    
    analyze_ripple(mka_file)


if __name__ == "__main__":
    main()
