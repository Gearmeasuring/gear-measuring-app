"""
齿形数据处理方式研究 V24

可能的原因：
1. 低通滤波器参数
2. 数据单位/缩放因子
3. 评价范围处理方式
4. 展长到角度映射的精度
5. 数据标准化/归一化

测试方法：
1. 分析数据特征
2. 尝试不同的缩放因子
3. 测试不同的滤波器参数
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
    """迭代最小二乘法提取频谱"""
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
    """构建完整闭合曲线"""
    if not all_tooth_data:
        return None, None
    
    angle_per_tooth = 360.0 / teeth_count
    base_circumference = math.pi * base_diameter
    
    tooth_data_dict = {}
    for tooth_idx, tooth_data in enumerate(all_tooth_data):
        if tooth_data is not None and len(tooth_data) > 5:
            tooth_data_dict[tooth_idx] = tooth_data
    
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
            elif prev_idx in tooth_data_dict:
                tooth_data = tooth_data_dict[prev_idx]
            elif next_idx in tooth_data_dict:
                tooth_data = tooth_data_dict[next_idx]
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


def analyze_profile_data(mka_file):
    """分析齿形数据"""
    print("="*70)
    print("齿形数据处理方式研究 V24")
    print("="*70)
    
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
    
    profile_data = parsed_data.get('profile_data', {})
    
    print(f"\n【齿轮参数】")
    print(f"  齿数 ZE = {teeth_count}")
    print(f"  基圆直径 db = {base_diameter:.4f} mm")
    
    klingelnberg_values = {
        '左齿形': 0.14,
        '右齿形': 0.15
    }
    
    for side, name in [('left', '左齿形'), ('right', '右齿形')]:
        print(f"\n{'='*70}")
        print(f"【{name}】")
        print('='*70)
        
        data_dict = profile_data.get(side, {})
        
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
                all_tooth_data.append((tooth_id, np.array(values, dtype=float)))
        
        if len(all_tooth_data) < 5:
            continue
        
        tooth_data_list = [None] * teeth_count
        for tooth_id, data in all_tooth_data:
            if 0 <= tooth_id < teeth_count:
                tooth_data_list[tooth_id] = data
        
        angles, values = build_closed_curve_complete(
            tooth_data_list, teeth_count, base_diameter, 
            'profile', d1, d2, helix_angle, pitch_diameter
        )
        
        if angles is None or len(angles) < 100:
            continue
        
        print(f"  闭合曲线点数: {len(angles)}")
        print(f"  数据范围: {np.min(values):.4f} ~ {np.max(values):.4f} μm")
        print(f"  数据标准差: {np.std(values):.4f} μm")
        print(f"  数据均值: {np.mean(values):.4f} μm")
        
        spectrum = iterative_sine_fit_all_orders(values, teeth_count, max_components=10, max_order=500)
        sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
        
        order_87_amp = spectrum.get(87, 0)
        k_val = klingelnberg_values.get(name, 0)
        ratio = order_87_amp / k_val if k_val > 0 else 0
        
        print(f"\n  87阶幅值: {order_87_amp:.4f} μm")
        print(f"  Klingelnberg: {k_val:.2f} μm")
        print(f"  比率: {ratio:.2f}x")
        
        print(f"\n  【测试不同的缩放因子】")
        for scale_factor in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]:
            scaled_values = values / scale_factor
            scaled_spectrum = iterative_sine_fit_all_orders(scaled_values, teeth_count, max_components=10, max_order=500)
            scaled_87_amp = scaled_spectrum.get(87, 0)
            scaled_ratio = scaled_87_amp / k_val if k_val > 0 else 0
            print(f"    缩放因子 {scale_factor:.1f}: 87阶 = {scaled_87_amp:.4f} μm, 比率 = {scaled_ratio:.2f}x")
        
        print(f"\n  【测试不同的评价范围截取】")
        for start_pct in [0.0, 0.1, 0.2]:
            for end_pct in [1.0, 0.9, 0.8]:
                start_idx = int(len(values) * start_pct)
                end_idx = int(len(values) * end_pct)
                truncated_values = values[start_idx:end_idx]
                
                truncated_spectrum = iterative_sine_fit_all_orders(truncated_values, teeth_count, max_components=10, max_order=500)
                truncated_87_amp = truncated_spectrum.get(87, 0)
                print(f"    截取 {start_pct*100:.0f}%-{end_pct*100:.0f}%: 87阶 = {truncated_87_amp:.4f} μm")
        
        print(f"\n  【分析前10阶次】")
        for i, (order, amp) in enumerate(sorted_spectrum[:10], 1):
            marker = " ★" if order >= teeth_count else ""
            print(f"    {i}. 阶次 {order:3d}: 幅值 = {amp:.4f} μm{marker}")


def main():
    mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    if not os.path.exists(mka_file):
        print(f"文件不存在: {mka_file}")
        return
    
    analyze_profile_data(mka_file)


if __name__ == "__main__":
    main()
