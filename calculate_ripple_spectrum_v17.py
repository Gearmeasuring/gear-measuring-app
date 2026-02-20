"""
波纹度频谱分析 V17 - 检查数据单位和缩放

关键发现：
- 齿向数据已非常接近（1.16x-1.17x）
- 齿形数据差距约5-7倍

可能原因：
1. 数据单位问题
2. 数据缩放因子
3. 评价范围处理方式不同
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


def build_closed_curve_with_eval_range(all_tooth_data, teeth_count, base_diameter, data_type='profile', 
                                        eval_start=0, eval_end=0, helix_angle=0, pitch_diameter=0):
    """构建闭合曲线 - 只使用评价范围内的数据"""
    if not all_tooth_data:
        return None, None
    
    angle_per_tooth = 360.0 / teeth_count
    base_circumference = math.pi * base_diameter
    
    all_angles = []
    all_values = []
    
    for tooth_idx, tooth_data in enumerate(all_tooth_data):
        if tooth_data is None or len(tooth_data) < 5:
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


def analyze_data_characteristics(mka_file):
    """分析数据特征"""
    print("="*70)
    print("波纹度频谱分析 V17 - 数据特征分析")
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
    b1, b2 = 2.1, 39.9
    
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    print(f"\n【数据特征分析】")
    
    for side, data_type, name, data_source, eval_start, eval_end in [
        ('left', 'profile', '左齿形', profile_data, d1, d2),
        ('right', 'profile', '右齿形', profile_data, d1, d2),
        ('left', 'flank', '左齿向', flank_data, b1, b2),
        ('right', 'flank', '右齿向', flank_data, b1, b2)
    ]:
        print(f"\n{name}:")
        
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
            continue
        
        all_values = np.concatenate(all_tooth_data)
        
        print(f"  齿数: {len(all_tooth_data)}")
        print(f"  每齿点数: {len(all_tooth_data[0]) if all_tooth_data else 0}")
        print(f"  原始数据范围: {np.min(all_values):.4f} ~ {np.max(all_values):.4f}")
        print(f"  原始数据标准差: {np.std(all_values):.4f}")
        print(f"  原始数据均值: {np.mean(all_values):.4f}")
        
        corrected_data = [remove_crown_and_slope(d) for d in all_tooth_data]
        all_corrected = np.concatenate(corrected_data)
        print(f"  修正后数据范围: {np.min(all_corrected):.4f} ~ {np.max(all_corrected):.4f}")
        print(f"  修正后数据标准差: {np.std(all_corrected):.4f}")
        
        angles, values = build_closed_curve_with_eval_range(
            all_tooth_data, teeth_count, base_diameter, 
            data_type, eval_start, eval_end, helix_angle, pitch_diameter
        )
        
        if angles is not None:
            print(f"  闭合曲线点数: {len(angles)}")
            print(f"  闭合曲线角度范围: {np.min(angles):.2f}° ~ {np.max(angles):.2f}°")
            print(f"  闭合曲线数据范围: {np.min(values):.4f} ~ {np.max(values):.4f}")
            print(f"  闭合曲线数据标准差: {np.std(values):.4f}")
            
            spectrum = iterative_sine_fit_all_orders(values, teeth_count, max_components=10, max_order=500)
            sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
            
            print(f"  前5阶次:")
            for i, (order, amp) in enumerate(sorted_spectrum[:5], 1):
                print(f"    {i}. 阶次 {order:3d}: 幅值 = {amp:.4f} μm")
            
            order_87_amp = spectrum.get(87, 0)
            print(f"  87阶幅值: {order_87_amp:.4f} μm")
    
    print("\n" + "="*70)
    print("Klingelnberg报告参考值:")
    print("  左齿形 87阶: 0.14 μm")
    print("  右齿形 87阶: 0.15 μm")
    print("  左齿向 87阶: 0.12 μm")
    print("  右齿向 87阶: 0.09 μm")
    
    print("\n" + "="*70)
    print("比率分析:")
    print("  齿形数据比率 ≈ 5-7x")
    print("  齿向数据比率 ≈ 1.16x")
    print("\n  可能原因:")
    print("  1. 齿形数据可能需要额外的缩放因子")
    print("  2. Klingelnberg可能对齿形数据使用了不同的处理方式")
    print("  3. 数据源可能不同")


def main():
    mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    if not os.path.exists(mka_file):
        print(f"文件不存在: {mka_file}")
        return
    
    analyze_data_characteristics(mka_file)


if __name__ == "__main__":
    main()
