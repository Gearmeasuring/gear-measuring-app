"""
波纹度频谱分析 V8 - 使用原始代码的预处理方法
"""
import os
import sys
import math
import numpy as np
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


def remove_outliers_and_slope_deviations(data, threshold=2.0, slope_threshold=0.03):
    """
    剔除单个峰值和斜率偏差 - 与原始代码一致
    
    Args:
        data: 输入数据数组
        threshold: 异常值检测阈值（标准差倍数）
        slope_threshold: 斜率偏差检测阈值
    """
    if data is None or len(data) < 5:
        return data
    
    original_data = np.array(data, dtype=float)
    n = len(original_data)
    
    # 1. 剔除单个峰值（异常值）
    mean_val = np.mean(original_data)
    std_val = np.std(original_data)
    data_array = original_data.copy()
    
    if std_val > 0:
        z_scores = np.abs((data_array - mean_val) / std_val)
        outlier_mask = z_scores < threshold
        data_array = data_array[outlier_mask]
        
        if len(data_array) < 5:
            data_array = original_data.copy()
    
    # 2. 剔除斜率偏差
    if len(data_array) >= 5:
        x = np.arange(len(data_array))
        slope = np.polyfit(x, data_array, 1)[0]
        
        if abs(slope) > slope_threshold:
            trend = np.polyval(np.polyfit(x, data_array, 1), x)
            data_array = data_array - trend
    
    return data_array


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


def build_closed_curve(all_tooth_data, teeth_count, base_diameter, data_type='profile', 
                       eval_start=0, eval_end=0, helix_angle=0, pitch_diameter=0):
    """构建闭合曲线 - 使用原始代码的预处理方法"""
    if not all_tooth_data:
        return None, None
    
    angle_per_tooth = 360.0 / teeth_count
    base_circumference = math.pi * base_diameter
    
    all_angles = []
    all_values = []
    
    for tooth_idx, tooth_data in enumerate(all_tooth_data):
        if tooth_data is None or len(tooth_data) < 5:
            continue
        
        # 使用原始代码的预处理方法
        processed_data = remove_outliers_and_slope_deviations(tooth_data, threshold=2.0, slope_threshold=0.03)
        
        tooth_center = tooth_idx * angle_per_tooth
        n_points = len(processed_data)
        
        if data_type == 'profile':
            roll_start = math.sqrt(max(0, (eval_start/2)**2 - (base_diameter/2)**2))
            roll_end = math.sqrt(max(0, (eval_end/2)**2 - (base_diameter/2)**2))
            roll_range = np.linspace(roll_start, roll_end, n_points)
            
            xi = (roll_range / base_circumference) * 360.0
            xi = xi - (xi[-1] - xi[0]) / 2
            alpha = xi + tooth_center
        else:
            axial_range = np.linspace(eval_start, eval_end, n_points)
            z0 = (eval_start + eval_end) / 2
            tan_beta = math.tan(math.radians(helix_angle))
            alpha2 = np.degrees((2.0 * (axial_range - z0) * tan_beta) / pitch_diameter)
            alpha = alpha2 + tooth_center
        
        all_angles.extend(alpha)
        all_values.extend(processed_data)
    
    all_angles = np.array(all_angles)
    all_values = np.array(all_values)
    sort_idx = np.argsort(all_angles)
    all_angles = all_angles[sort_idx]
    all_values = all_values[sort_idx]
    
    unique_angles = np.unique(np.round(all_angles, 2))
    avg_values = []
    for angle in unique_angles:
        mask = np.abs(all_angles - angle) < 0.05
        if np.any(mask):
            avg_values.append(np.mean(all_values[mask]))
    
    return unique_angles, np.array(avg_values)


def analyze_ripple(mka_file):
    """分析波纹度"""
    print("="*70)
    print("波纹度频谱分析 V8 (原始预处理方法)")
    print("="*70)
    print("\n关键修正:")
    print("1. 使用Z-score方法剔除异常值 (threshold=2.0)")
    print("2. 去除线性趋势 (slope_threshold=0.03)")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 18.6)
    helix_angle = gear_data.get('helix_angle', 25.3)
    
    beta = math.radians(helix_angle)
    alpha_n = math.radians(pressure_angle)
    alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta))
    pitch_diameter = teeth_count * module / math.cos(beta)
    base_diameter = pitch_diameter * math.cos(alpha_t)
    
    profile_eval_start = gear_data.get('profile_eval_start', 174.822)
    profile_eval_end = gear_data.get('profile_eval_end', 180.603)
    helix_eval_start = gear_data.get('helix_eval_start', 2.1)
    helix_eval_end = gear_data.get('helix_eval_end', 39.9)
    
    print(f"\n【齿轮参数】")
    print(f"  齿数 ZE = {teeth_count}")
    
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    results = {}
    
    directions = [
        ('left', 'profile', '左齿形', profile_data),
        ('right', 'profile', '右齿形', profile_data),
        ('left', 'flank', '左齿向', flank_data),
        ('right', 'flank', '右齿向', flank_data)
    ]
    
    print(f"\nKlingelnberg报告参考值:")
    print(f"  左齿形 87阶: 0.14 μm")
    print(f"  右齿形 87阶: 0.15 μm")
    print(f"  左齿向 87阶: 0.12 μm")
    print(f"  右齿向 87阶: 0.09 μm")
    
    for side, data_type, name, data_source in directions:
        print(f"\n{'='*70}")
        print(f"【{name}】")
        print('='*70)
        
        if data_type == 'profile':
            data_dict = data_source.get(side, {})
            eval_start = profile_eval_start
            eval_end = profile_eval_end
        else:
            data_dict = data_source.get(side, {})
            eval_start = helix_eval_start
            eval_end = helix_eval_end
        
        if not data_dict:
            print(f"  无数据")
            continue
        
        all_tooth_data = []
        for tooth_id in sorted(data_dict.keys()):
            tooth_data = data_dict[tooth_id]
            if isinstance(tooth_data, dict):
                values = tooth_data.get('values', [])
            else:
                values = tooth_data
            if values and len(values) > 5:
                all_tooth_data.append(np.array(values, dtype=float))
        
        if len(all_tooth_data) < 5:
            print(f"  数据不足 ({len(all_tooth_data)}齿)")
            continue
        
        print(f"  有效齿数: {len(all_tooth_data)}")
        
        angles, values = build_closed_curve(
            all_tooth_data, teeth_count, base_diameter, 
            data_type, eval_start, eval_end, helix_angle, pitch_diameter
        )
        
        if angles is None or len(angles) < 100:
            print(f"  闭合曲线构建失败")
            continue
        
        print(f"  闭合曲线点数: {len(angles)}")
        print(f"  数据范围: {np.min(values):.2f} ~ {np.max(values):.2f} μm")
        
        # 不使用滤波器
        spectrum = iterative_sine_fit_klingelnberg(values, teeth_count, max_components=10)
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
