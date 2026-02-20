"""
波纹度频谱分析 V13 - 尝试不同的预处理方法

测试不同的预处理方法：
1. 不剔除鼓形和斜率
2. 只剔除斜率
3. 只剔除鼓形
4. 原始方法（剔除鼓形和斜率）
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


def iterative_sine_fit(curve_data, teeth_count, max_components=10):
    """迭代最小二乘法提取频谱"""
    n = len(curve_data)
    if n < 8:
        return {}
    
    x = np.linspace(0.0, 1.0, n, dtype=float)
    residual = np.array(curve_data, dtype=float)
    residual = residual - np.mean(residual)
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


def preprocess_none(data):
    """不进行预处理"""
    return np.array(data, dtype=float) - np.mean(data)


def preprocess_slope_only(data):
    """只剔除斜率"""
    n = len(data)
    y = np.array(data, dtype=float)
    x = np.linspace(-1, 1, n)
    
    A = np.column_stack((x, np.ones(n)))
    coeffs, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    k, d = coeffs
    slope = k * x + d
    y_corrected = y - slope
    
    return y_corrected - np.mean(y_corrected)


def preprocess_crown_only(data):
    """只剔除鼓形"""
    n = len(data)
    y = np.array(data, dtype=float)
    x = np.linspace(-1, 1, n)
    
    A = np.column_stack((x**2, np.ones(n)))
    coeffs, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    a, c = coeffs
    crown = a * x**2 + c
    y_corrected = y - crown
    
    return y_corrected - np.mean(y_corrected)


def preprocess_crown_and_slope(data):
    """剔除鼓形和斜率"""
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


def build_closed_curve_with_preprocess(all_tooth_data, teeth_count, base_diameter, data_type, 
                                        eval_start, eval_end, helix_angle, pitch_diameter, preprocess_func):
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
        
        corrected_data = preprocess_func(tooth_data)
        
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


def test_preprocess_methods(mka_file):
    """测试不同的预处理方法"""
    print("="*70)
    print("测试不同预处理方法")
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
    
    preprocess_methods = [
        ('不预处理', preprocess_none),
        ('只剔除斜率', preprocess_slope_only),
        ('只剔除鼓形', preprocess_crown_only),
        ('剔除鼓形+斜率', preprocess_crown_and_slope)
    ]
    
    klingelnberg_values = {'左齿形': 0.14, '右齿形': 0.15, '左齿向': 0.12, '右齿向': 0.09}
    
    print(f"\nKlingelnberg报告参考值:")
    print(f"  左齿形 87阶: 0.14 μm")
    print(f"  右齿形 87阶: 0.15 μm")
    print(f"  左齿向 87阶: 0.12 μm")
    print(f"  右齿向 87阶: 0.09 μm")
    
    print(f"\n" + "="*70)
    print("测试结果")
    print("="*70)
    
    for method_name, preprocess_func in preprocess_methods:
        print(f"\n【{method_name}】")
        print("-"*50)
        
        results = {}
        
        directions = [
            ('left', 'profile', '左齿形', profile_data, d1, d2),
            ('right', 'profile', '右齿形', profile_data, d1, d2),
            ('left', 'flank', '左齿向', flank_data, b1, b2),
            ('right', 'flank', '右齿向', flank_data, b1, b2)
        ]
        
        for side, data_type, name, data_source, eval_start, eval_end in directions:
            data_dict = data_source.get(side, {})
            
            if not data_dict:
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
            
            angles, values = build_closed_curve_with_preprocess(
                all_tooth_data, teeth_count, base_diameter, 
                data_type, eval_start, eval_end, helix_angle, pitch_diameter, preprocess_func
            )
            
            if angles is None or len(angles) < 100:
                continue
            
            spectrum = iterative_sine_fit(values, teeth_count, max_components=10)
            order_87_amp = spectrum.get(87, 0)
            
            results[name] = order_87_amp
        
        # 打印结果
        print(f"{'曲线':<10} {'结果':<12} {'报告值':<12} {'比率':<10}")
        for name, amp in results.items():
            k_val = klingelnberg_values.get(name, 0)
            ratio = amp / k_val if k_val > 0 else 0
            print(f"{name:<10} {amp:<12.4f} {k_val:<12.2f} {ratio:<10.2f}x")


def main():
    mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    if not os.path.exists(mka_file):
        print(f"文件不存在: {mka_file}")
        return
    
    test_preprocess_methods(mka_file)


if __name__ == "__main__":
    main()
