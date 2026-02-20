"""
波纹度频谱分析 V7 - 调整RC滤波器参数
尝试不同的ratio值来匹配Klingelnberg报告
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


def apply_rc_low_pass_filter(data, fs=10000.0, ratio=1500.0, fc_multiplier=10.0):
    """Klingelnberg RC 低通滤波器"""
    if data is None or len(data) <= 1:
        return data
    
    data = np.array(data, dtype=float)
    n = len(data)
    
    fc_base = fs / ratio
    fc_eff = fc_base * fc_multiplier
    fc_eff = max(fc_eff, 100.0)
    
    dt = 1.0 / fs
    rc = 1.0 / (2.0 * np.pi * fc_eff)
    alpha = dt / (rc + dt)
    alpha = min(1.0, max(0.0, alpha))
    
    y = np.zeros_like(data)
    y[0] = data[0]
    for i in range(1, n):
        y[i] = alpha * data[i] + (1.0 - alpha) * y[i - 1]
    
    return y


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
    """构建闭合曲线"""
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


def test_different_filter_params(mka_file):
    """测试不同的滤波器参数"""
    print("="*70)
    print("测试不同RC滤波器参数")
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
    
    profile_eval_start = gear_data.get('profile_eval_start', 174.822)
    profile_eval_end = gear_data.get('profile_eval_end', 180.603)
    helix_eval_start = gear_data.get('helix_eval_start', 2.1)
    helix_eval_end = gear_data.get('helix_eval_end', 39.9)
    
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    # 测试不同的滤波器参数组合
    filter_params = [
        {'ratio': 1500, 'fc_multiplier': 10.0, 'name': 'ratio=1500, fc_mult=10'},
        {'ratio': 5000, 'fc_multiplier': 10.0, 'name': 'ratio=5000, fc_mult=10'},
        {'ratio': 10000, 'fc_multiplier': 10.0, 'name': 'ratio=10000, fc_mult=10'},
        {'ratio': 1500, 'fc_multiplier': 5.0, 'name': 'ratio=1500, fc_mult=5'},
        {'ratio': 1500, 'fc_multiplier': 3.0, 'name': 'ratio=1500, fc_mult=3'},
        {'ratio': 1500, 'fc_multiplier': 1.0, 'name': 'ratio=1500, fc_mult=1'},
    ]
    
    # 只测试左齿形
    data_dict = profile_data.get('left', {})
    all_tooth_data = []
    for tooth_id in sorted(data_dict.keys()):
        tooth_data = data_dict[tooth_id]
        if isinstance(tooth_data, dict):
            values = tooth_data.get('values', [])
        else:
            values = tooth_data
        if values and len(values) > 5:
            all_tooth_data.append(np.array(values, dtype=float))
    
    angles, values = build_closed_curve(
        all_tooth_data, teeth_count, base_diameter, 
        'profile', profile_eval_start, profile_eval_end, helix_angle, pitch_diameter
    )
    
    print(f"\n左齿形数据:")
    print(f"  闭合曲线点数: {len(angles)}")
    print(f"  数据范围: {np.min(values):.2f} ~ {np.max(values):.2f} μm")
    
    print(f"\nKlingelnberg报告 87阶幅值: 0.14 μm")
    print(f"\n不同滤波器参数测试结果:")
    print("-"*70)
    
    for params in filter_params:
        filtered_values = apply_rc_low_pass_filter(
            values, 
            ratio=params['ratio'], 
            fc_multiplier=params['fc_multiplier']
        )
        
        spectrum = iterative_sine_fit_klingelnberg(filtered_values, teeth_count)
        sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
        
        order_87_amp = spectrum.get(87, 0)
        ratio_to_report = order_87_amp / 0.14 if order_87_amp > 0 else 0
        
        print(f"\n{params['name']}:")
        print(f"  87阶幅值: {order_87_amp:.4f} μm")
        print(f"  与报告比率: {ratio_to_report:.2f}x")
        print(f"  前3阶: ", end="")
        for order, amp in sorted_spectrum[:3]:
            print(f"{order}阶={amp:.4f}μm ", end="")
        print()


def main():
    mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    if not os.path.exists(mka_file):
        print(f"文件不存在: {mka_file}")
        return
    
    test_different_filter_params(mka_file)


if __name__ == "__main__":
    main()
