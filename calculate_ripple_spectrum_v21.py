"""
波纹度频谱分析 V21 - 按ep/el排列并归一化到360°

关键理解：
- ep = 1.454 → 齿形评价长度是1.454个基节
- el = 2.766 → 齿向评价长度是2.766个基节
- 所有齿的数据按 ep/el × 360°/ZE 的角度范围排列
- 然后归一化到360°范围进行频谱分析
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


def build_curve_by_ep_el_normalized(all_tooth_data, teeth_count, ep_or_el, data_type='profile'):
    """
    按ep/el排列并归一化到360°
    
    每个齿的数据对应 ep_or_el 个基节的角度范围
    所有齿的数据按此范围排列，然后归一化到360°
    """
    if not all_tooth_data:
        return None, None
    
    angle_per_tooth = 360.0 / teeth_count
    angle_per_data = ep_or_el * angle_per_tooth
    
    print(f"    每齿角度间隔: {angle_per_tooth:.4f}°")
    print(f"    每齿数据角度范围: {angle_per_data:.4f}° (ep/el × 360°/ZE)")
    
    all_angles = []
    all_values = []
    
    for tooth_idx, tooth_data in enumerate(all_tooth_data):
        if tooth_data is None or len(tooth_data) < 5:
            continue
        
        corrected_data = remove_crown_and_slope(tooth_data)
        
        angle_start = tooth_idx * angle_per_data
        n_points = len(corrected_data)
        
        angle_range = np.linspace(angle_start, angle_start + angle_per_data, n_points)
        
        all_angles.extend(angle_range)
        all_values.extend(corrected_data)
    
    all_angles = np.array(all_angles)
    all_values = np.array(all_values)
    sort_idx = np.argsort(all_angles)
    all_angles = all_angles[sort_idx]
    all_values = all_values[sort_idx]
    
    total_angle_range = all_angles[-1] - all_angles[0]
    print(f"    原始总角度范围: {total_angle_range:.2f}°")
    
    normalized_angles = (all_angles - all_angles[0]) / total_angle_range * 360.0
    print(f"    归一化到360°范围")
    
    unique_angles = np.unique(np.round(normalized_angles, 2))
    avg_values = []
    for angle in unique_angles:
        mask = np.abs(normalized_angles - angle) < 0.05
        if np.any(mask):
            avg_values.append(np.mean(all_values[mask]))
    
    return unique_angles, np.array(avg_values)


def analyze_ripple(mka_file):
    """分析波纹度"""
    print("="*70)
    print("波纹度频谱分析 V21 (按ep/el排列并归一化到360°)")
    print("="*70)
    print("\n关键理解:")
    print("1. ep = 1.454 → 齿形评价长度是1.454个基节")
    print("2. el = 2.766 → 齿向评价长度是2.766个基节")
    print("3. 所有齿的数据按 ep/el × 360°/ZE 的角度范围排列")
    print("4. 然后归一化到360°范围进行频谱分析")
    
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
    print(f"  基节 pb = {pb:.4f} mm")
    print(f"\n【评价参数】")
    print(f"  ep = {ep:.4f}")
    print(f"  el = {el:.4f}")
    
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    results = {}
    
    print(f"\nKlingelnberg报告参考值:")
    print(f"  左齿形 87阶: 0.14 μm")
    print(f"  右齿形 87阶: 0.15 μm")
    print(f"  左齿向 87阶: 0.12 μm")
    print(f"  右齿向 87阶: 0.09 μm")
    
    directions = [
        ('left', 'profile', '左齿形', profile_data, ep),
        ('right', 'profile', '右齿形', profile_data, ep),
        ('left', 'flank', '左齿向', flank_data, el),
        ('right', 'flank', '右齿向', flank_data, el)
    ]
    
    for side, data_type, name, data_source, ep_or_el in directions:
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
        
        angles, values = build_curve_by_ep_el_normalized(
            all_tooth_data, teeth_count, ep_or_el, data_type
        )
        
        if angles is None or len(angles) < 100:
            print(f"  曲线构建失败")
            continue
        
        print(f"  曲线点数: {len(angles)}")
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
