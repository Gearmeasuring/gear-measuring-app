"""
波纹度频谱分析 V14 - 修复齿数缺失问题

关键修复：
1. 确保闭合曲线覆盖完整360°
2. 如果有齿缺失，用相邻齿插值填充
3. 搜索所有阶次，迭代提取最大幅值
4. 评价时考虑所有阶次≥ZE的成分
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


def remove_crown_and_slope(data):
    """剔除鼓形和斜率偏差"""
    n = len(data)
    y = np.array(data, dtype=float)
    x = np.linspace(-1, 1, n)
    
    A_crown = np.column_stack((x**2, x, np.ones(n)))
    coeffs_crown, _, _, _ = np.linalg.lstsq(A_crown, y, rcond=None)
    a, b, c = coeffs_crown
    crown = a * x**2 + b * x + c
    y_no_crown = y - crown
    
    A_slope = np.column_stack((x, np.ones(n)))
    coeffs_slope, _, _, _ = np.linalg.lstsq(A_slope, y_no_crown, rcond=None)
    k, d = coeffs_slope
    slope = k * x + d
    y_corrected = y_no_crown - slope
    
    return y_corrected


def iterative_sine_fit_all_orders(curve_data, teeth_count, max_components=10, max_order=500):
    """迭代最小二乘法提取频谱 - 搜索所有阶次"""
    n = len(curve_data)
    if n < 8:
        return {}
    
    x = np.linspace(0.0, 1.0, n, dtype=float)
    residual = np.array(curve_data, dtype=float)
    residual = residual - np.mean(residual)
    spectrum_results = {}
    
    amplitude_threshold = 0.0001
    
    for iteration in range(max_components):
        best_order = None
        best_amplitude = 0.0
        best_coeffs = None
        
        for order in range(1, max_order + 1):
            if order in spectrum_results:
                continue
            
            try:
                sin_x = np.sin(2.0 * np.pi * order * x)
                cos_x = np.cos(2.0 * np.pi * order * x)
                A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
                
                coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
                a, b, c = coeffs
                amplitude = np.sqrt(a*a + b*b)
                
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
    
    return spectrum_results


def build_closed_curve_complete(all_tooth_data, teeth_count, base_diameter, data_type='profile', 
                                 eval_start=0, eval_end=0, helix_angle=0, pitch_diameter=0):
    """
    构建完整闭合曲线 - 确保覆盖完整360°
    
    如果有齿缺失，用相邻齿平均值填充
    """
    if not all_tooth_data:
        return None, None
    
    angle_per_tooth = 360.0 / teeth_count
    base_circumference = math.pi * base_diameter
    
    tooth_data_dict = {}
    for tooth_idx, tooth_data in enumerate(all_tooth_data):
        if tooth_data is not None and len(tooth_data) > 5:
            tooth_data_dict[tooth_idx] = tooth_data
    
    print(f"    有效齿数据: {len(tooth_data_dict)} 齿")
    
    all_angles = []
    all_values = []
    
    for tooth_idx in range(teeth_count):
        if tooth_idx in tooth_data_dict:
            tooth_data = tooth_data_dict[tooth_idx]
        else:
            prev_idx = (tooth_idx - 1) % teeth_count
            next_idx = (tooth_idx + 1) % teeth_count
            
            if prev_idx in tooth_data_dict and next_idx in tooth_data_dict:
                prev_data = tooth_data_dict[prev_idx]
                next_data = tooth_data_dict[next_idx]
                n = max(len(prev_data), len(next_data))
                tooth_data = np.zeros(n)
                for i in range(n):
                    pi = min(i, len(prev_data)-1)
                    ni = min(i, len(next_data)-1)
                    tooth_data[i] = (prev_data[pi] + next_data[ni]) / 2
                print(f"    齿 {tooth_idx+1} 缺失，用相邻齿插值填充")
            elif prev_idx in tooth_data_dict:
                tooth_data = tooth_data_dict[prev_idx]
                print(f"    齿 {tooth_idx+1} 缺失，用前一齿数据填充")
            elif next_idx in tooth_data_dict:
                tooth_data = tooth_data_dict[next_idx]
                print(f"    齿 {tooth_idx+1} 缺失，用后一齿数据填充")
            else:
                continue
        
        corrected_data = remove_crown_and_slope(tooth_data)
        
        tooth_center = tooth_idx * angle_per_tooth
        n_points = len(corrected_data)
        
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
        all_values.extend(corrected_data)
    
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
    print("波纹度频谱分析 V14 (完整闭合曲线)")
    print("="*70)
    print("\n关键算法:")
    print("1. Profile: 展长 s(d) → 旋转角 ξ = s/(π×db)×360°")
    print("2. Helix: 轴向位置 z → 旋转角 α₂ = 2×Δz×tan(β₀)/D₀")
    print("3. 构建完整360°闭合曲线（缺失齿用插值填充）")
    print("4. 迭代提取：每次提取幅值最大的阶次")
    print("5. 评价：只考虑阶次≥ZE的成分")
    
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
    
    d1, d2 = 174.822, 180.603
    b1, b2 = 2.1, 39.9
    pb = math.pi * base_diameter / teeth_count
    beta_b = math.asin(math.sin(beta) * math.cos(alpha_n))
    
    lu = math.sqrt(max(0, (d1/2)**2 - (base_diameter/2)**2))
    lo = math.sqrt(max(0, (d2/2)**2 - (base_diameter/2)**2))
    la = lo - lu
    ep = la / pb
    
    lb = b2 - b1
    el = (lb * math.tan(beta_b)) / pb
    
    print(f"\n【齿轮参数】")
    print(f"  齿数 ZE = {teeth_count}")
    print(f"  模数 m = {module} mm")
    print(f"  压力角 α = {pressure_angle}°")
    print(f"  螺旋角 β = {helix_angle}°")
    print(f"  节圆直径 d = {pitch_diameter:.4f} mm")
    print(f"  基圆直径 db = {base_diameter:.4f} mm")
    print(f"\n【评价参数】")
    print(f"  ep = {ep:.4f}")
    print(f"  el = {el:.4f}")
    
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    results = {}
    
    directions = [
        ('left', 'profile', '左齿形', profile_data, d1, d2),
        ('right', 'profile', '右齿形', profile_data, d1, d2),
        ('left', 'flank', '左齿向', flank_data, b1, b2),
        ('right', 'flank', '右齿向', flank_data, b1, b2)
    ]
    
    print(f"\nKlingelnberg报告参考值:")
    print(f"  左齿形 87阶: 0.14 μm")
    print(f"  右齿形 87阶: 0.15 μm")
    print(f"  左齿向 87阶: 0.12 μm")
    print(f"  右齿向 87阶: 0.09 μm")
    
    for side, data_type, name, data_source, eval_start, eval_end in directions:
        print(f"\n{'='*70}")
        print(f"【{name}】")
        print('='*70)
        
        data_dict = data_source.get(side, {})
        
        if not data_dict:
            print(f"  无数据")
            continue
        
        all_tooth_data = []
        tooth_indices = sorted(data_dict.keys())
        for tooth_id in tooth_indices:
            tooth_data = data_dict[tooth_id]
            if isinstance(tooth_data, dict):
                values = tooth_data.get('values', [])
            else:
                values = tooth_data
            if values and len(values) > 5:
                all_tooth_data.append((tooth_id, np.array(values, dtype=float)))
        
        if len(all_tooth_data) < 5:
            print(f"  数据不足 ({len(all_tooth_data)}齿)")
            continue
        
        print(f"  原始数据齿数: {len(all_tooth_data)}")
        
        tooth_data_list = [None] * teeth_count
        for tooth_id, data in all_tooth_data:
            if 0 <= tooth_id < teeth_count:
                tooth_data_list[tooth_id] = data
        
        angles, values = build_closed_curve_complete(
            tooth_data_list, teeth_count, base_diameter, 
            data_type, eval_start, eval_end, helix_angle, pitch_diameter
        )
        
        if angles is None or len(angles) < 100:
            print(f"  闭合曲线构建失败")
            continue
        
        print(f"  闭合曲线点数: {len(angles)}")
        print(f"  角度范围: {np.min(angles):.2f}° ~ {np.max(angles):.2f}°")
        print(f"  数据范围: {np.min(values):.2f} ~ {np.max(values):.2f} μm")
        
        spectrum = iterative_sine_fit_all_orders(values, teeth_count, max_components=10, max_order=500)
        sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n  提取的前10个较大阶次:")
        for i, (order, amp) in enumerate(sorted_spectrum[:10], 1):
            marker = " ★" if order >= teeth_count else ""
            print(f"    {i}. 阶次 {order:3d}: 幅值 = {amp:.4f} μm{marker}")
        
        high_order_spectrum = [(o, a) for o, a in sorted_spectrum if o >= teeth_count]
        print(f"\n  阶次≥ZE ({teeth_count}) 的成分:")
        for i, (order, amp) in enumerate(high_order_spectrum[:5], 1):
            print(f"    {i}. 阶次 {order:3d}: 幅值 = {amp:.4f} μm")
        
        order_87_amp = spectrum.get(87, 0)
        print(f"\n  87阶幅值: {order_87_amp:.4f} μm")
        
        results[name] = {
            'order_87': order_87_amp,
            'spectrum': sorted_spectrum,
            'high_order': high_order_spectrum
        }
    
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
