"""
波纹度频谱分析 V9 - 使用原始代码的简单角度映射
关键修正：使用简单的线性角度映射，而不是复杂的展长映射
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


def build_closed_curve_simple(all_tooth_data, teeth_count):
    """
    构建闭合曲线 - 使用原始代码的简单角度映射
    
    关键修正：不使用复杂的展长到角度映射，而是使用简单的线性角度映射
    """
    if not all_tooth_data:
        return None
    
    min_len = min(len(d) for d in all_tooth_data)
    if min_len < 8:
        min_len = 8
    
    total_angle = 2.0 * math.pi
    angle_per_tooth = total_angle / float(teeth_count)
    
    n_global = max(400, min_len * len(all_tooth_data) * 2)
    
    sum_arr = np.zeros(n_global, dtype=float)
    cnt_arr = np.zeros(n_global, dtype=float)
    
    for tooth_idx, segment in enumerate(all_tooth_data):
        seg = np.asarray(segment, dtype=float)
        if len(seg) > min_len:
            seg = seg[:min_len]
        
        # 预处理
        seg = remove_outliers_and_slope_deviations(seg, threshold=2.0, slope_threshold=0.03)
        
        # 计算当前齿的旋转角偏移
        tooth_offset = float(tooth_idx) * angle_per_tooth
        
        # 生成当前齿的局部旋转角（0到angle_per_tooth）- 简单线性映射！
        local_angles = np.linspace(0.0, angle_per_tooth, len(seg), dtype=float)
        
        # 计算全局旋转角
        global_angles = (tooth_offset + local_angles) % total_angle
        
        # 映射到全局数组索引
        indices = np.round((global_angles / total_angle) * n_global).astype(int) % n_global
        
        # 累加数据到全局数组
        np.add.at(sum_arr, indices, seg)
        np.add.at(cnt_arr, indices, 1.0)
    
    # 计算平均值
    with np.errstate(divide='ignore', invalid='ignore'):
        common = np.where(cnt_arr > 0, sum_arr / cnt_arr, 0.0)
    
    return common


def analyze_ripple(mka_file):
    """分析波纹度"""
    print("="*70)
    print("波纹度频谱分析 V9 (简单角度映射)")
    print("="*70)
    print("\n关键修正:")
    print("1. 使用简单的线性角度映射（与原始代码一致）")
    print("2. 不使用复杂的展长到角度映射")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    
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
        
        data_dict = data_source.get(side, {})
        
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
        
        # 使用简单的角度映射构建闭合曲线
        closed_curve = build_closed_curve_simple(all_tooth_data, teeth_count)
        
        if closed_curve is None or len(closed_curve) < 100:
            print(f"  闭合曲线构建失败")
            continue
        
        print(f"  闭合曲线点数: {len(closed_curve)}")
        print(f"  数据范围: {np.min(closed_curve):.2f} ~ {np.max(closed_curve):.2f} μm")
        
        # 计算频谱
        spectrum = iterative_sine_fit_klingelnberg(closed_curve, teeth_count, max_components=10)
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
