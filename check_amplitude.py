"""
检查振幅计算方法
"""
import os
import sys
import numpy as np
import math
import warnings
warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


def check_amplitude_calculation(mka_file, sample_name, klingelnberg_ref):
    """检查振幅计算方法"""
    print(f"\n{'='*90}")
    print(f"Check Amplitude Calculation: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    
    teeth_count = gear_data.get('teeth', 26)
    module = gear_data.get('module', 1.44)
    pressure_angle = gear_data.get('pressure_angle', 17.0)
    
    pitch_diameter = module * teeth_count
    pitch_radius = pitch_diameter / 2.0
    pitch_angle = 360.0 / teeth_count
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
    base_radius = base_diameter / 2.0
    
    side = 'right'
    side_data = profile_data.get(side, {})
    direction = f'{side}_profile'
    ref = klingelnberg_ref[direction]
    
    print(f"\n{side.upper()} Profile:")
    
    # 方法1：合并曲线法
    all_angles = []
    all_values = []
    
    sorted_teeth = sorted(side_data.keys())
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        values = np.array(tooth_values, dtype=float)
        n = len(values)
        
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        coeffs = np.polyfit(x_norm, values, 3)
        trend = np.polyval(coeffs, x_norm)
        corrected_values = values - trend
        
        eval_start = gear_data.get('profile_eval_start', 0)
        eval_end = gear_data.get('profile_eval_end', 0)
        
        if eval_start > 0 and eval_end > 0:
            radii = np.linspace(eval_start/2, eval_end/2, n)
        else:
            radii = np.linspace(pitch_radius * 0.95, pitch_radius * 1.05, n)
        
        xi_angles = []
        for r in radii:
            if r <= base_radius or base_radius <= 0:
                xi = 0
            else:
                cos_alpha = base_radius / r
                if cos_alpha >= 1.0:
                    xi = 0
                else:
                    alpha = math.acos(cos_alpha)
                    xi = math.degrees(math.tan(alpha) - alpha)
            xi_angles.append(xi)
        xi_angles = np.array(xi_angles)
        
        tooth_index = int(tooth_id) - 1
        tau = tooth_index * pitch_angle
        angles = tau + xi_angles
        
        all_angles.extend(angles.tolist())
        all_values.extend(corrected_values.tolist())
    
    all_angles = np.array(all_angles)
    all_values = np.array(all_values)
    
    all_angles = all_angles % 360.0
    sort_idx = np.argsort(all_angles)
    all_angles = all_angles[sort_idx]
    all_values = all_values[sort_idx]
    
    unique_angles, unique_indices = np.unique(np.round(all_angles, 4), return_index=True)
    unique_values = all_values[unique_indices]
    
    num_points = 1024
    interp_angles = np.linspace(0, 360, num_points, endpoint=False)
    interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
    
    theta = np.radians(interp_angles)
    
    # 方法A：标准最小二乘法
    print(f"\n  Method A: Standard Least Squares")
    for order in [26]:
        cos_x = np.cos(order * theta)
        sin_x = np.sin(order * theta)
        A = np.column_stack((cos_x, sin_x))
        coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
        a, b = coeffs
        amplitude = np.sqrt(a*a + b*b)
        print(f"    Order {order}: amplitude = {amplitude:.4f}")
    
    # 方法B：FFT方法
    print(f"\n  Method B: FFT")
    fft_result = np.fft.fft(interp_values)
    fft_amplitudes = np.abs(fft_result) * 2 / num_points
    for order in [26]:
        print(f"    Order {order}: FFT amplitude = {fft_amplitudes[order]:.4f}")
    
    # 方法C：每个齿单独计算然后平均
    print(f"\n  Method C: Per-Tooth Average")
    all_spectra = {}
    for tooth_id in sorted_teeth[:10]:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        values = np.array(tooth_values, dtype=float)
        n = len(values)
        
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        coeffs = np.polyfit(x_norm, values, 3)
        trend = np.polyval(coeffs, x_norm)
        corrected_values = values - trend
        
        eval_start = gear_data.get('profile_eval_start', 0)
        eval_end = gear_data.get('profile_eval_end', 0)
        
        if eval_start > 0 and eval_end > 0:
            radii = np.linspace(eval_start/2, eval_end/2, n)
        else:
            radii = np.linspace(pitch_radius * 0.95, pitch_radius * 1.05, n)
        
        xi_angles = []
        for r in radii:
            if r <= base_radius or base_radius <= 0:
                xi = 0
            else:
                cos_alpha = base_radius / r
                if cos_alpha >= 1.0:
                    xi = 0
                else:
                    alpha = math.acos(cos_alpha)
                    xi = math.degrees(math.tan(alpha) - alpha)
            xi_angles.append(xi)
        xi_angles = np.array(xi_angles)
        
        tooth_index = int(tooth_id) - 1
        tau = tooth_index * pitch_angle
        angles = (tau + xi_angles) % 360.0
        
        sort_idx = np.argsort(angles)
        angles = angles[sort_idx]
        corrected_values = corrected_values[sort_idx]
        
        unique_angles, unique_indices = np.unique(np.round(angles, 4), return_index=True)
        unique_values = corrected_values[unique_indices]
        
        num_pts = 1024
        interp_ang = np.linspace(0, 360, num_pts, endpoint=False)
        interp_val = np.interp(interp_ang, unique_angles, unique_values, period=360)
        
        theta_t = np.radians(interp_ang)
        
        for order in [26]:
            cos_x = np.cos(order * theta_t)
            sin_x = np.sin(order * theta_t)
            A = np.column_stack((cos_x, sin_x))
            coeffs, _, _, _ = np.linalg.lstsq(A, interp_val, rcond=None)
            a, b = coeffs
            amplitude = np.sqrt(a*a + b*b)
            
            if order not in all_spectra:
                all_spectra[order] = []
            all_spectra[order].append(amplitude)
    
    for order in [26]:
        avg_amp = np.mean(all_spectra[order])
        print(f"    Order {order}: average amplitude = {avg_amp:.4f}")
    
    # 方法D：去均值后不做多项式预处理
    print(f"\n  Method D: Mean Removal Only (No Polynomial)")
    all_angles2 = []
    all_values2 = []
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        values = np.array(tooth_values, dtype=float)
        corrected_values = values - np.mean(values)
        
        n = len(values)
        eval_start = gear_data.get('profile_eval_start', 0)
        eval_end = gear_data.get('profile_eval_end', 0)
        
        if eval_start > 0 and eval_end > 0:
            radii = np.linspace(eval_start/2, eval_end/2, n)
        else:
            radii = np.linspace(pitch_radius * 0.95, pitch_radius * 1.05, n)
        
        xi_angles = []
        for r in radii:
            if r <= base_radius or base_radius <= 0:
                xi = 0
            else:
                cos_alpha = base_radius / r
                if cos_alpha >= 1.0:
                    xi = 0
                else:
                    alpha = math.acos(cos_alpha)
                    xi = math.degrees(math.tan(alpha) - alpha)
            xi_angles.append(xi)
        xi_angles = np.array(xi_angles)
        
        tooth_index = int(tooth_id) - 1
        tau = tooth_index * pitch_angle
        angles = tau + xi_angles
        
        all_angles2.extend(angles.tolist())
        all_values2.extend(corrected_values.tolist())
    
    all_angles2 = np.array(all_angles2)
    all_values2 = np.array(all_values2)
    
    all_angles2 = all_angles2 % 360.0
    sort_idx = np.argsort(all_angles2)
    all_angles2 = all_angles2[sort_idx]
    all_values2 = all_values2[sort_idx]
    
    unique_angles2, unique_indices2 = np.unique(np.round(all_angles2, 4), return_index=True)
    unique_values2 = all_values2[unique_indices2]
    
    interp_angles2 = np.linspace(0, 360, num_points, endpoint=False)
    interp_values2 = np.interp(interp_angles2, unique_angles2, unique_values2, period=360)
    
    theta2 = np.radians(interp_angles2)
    
    for order in [26]:
        cos_x = np.cos(order * theta2)
        sin_x = np.sin(order * theta2)
        A = np.column_stack((cos_x, sin_x))
        coeffs, _, _, _ = np.linalg.lstsq(A, interp_values2, rcond=None)
        a, b = coeffs
        amplitude = np.sqrt(a*a + b*b)
        print(f"    Order {order}: amplitude = {amplitude:.4f}")
    
    print(f"\n  Klingelnberg Reference:")
    print(f"    Order 26: {ref[26]:.4f}")
    
    print(f"\n  Amplitude Ratios:")
    print(f"    Method A / Klingelnberg = {1.7910 / ref[26]:.2f}")
    print(f"    Method C / Klingelnberg = {0.0670 / ref[26]:.2f}")


def main():
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE2 = {
        'right_profile': {26: 0.19, 52: 0.07, 78: 0.10, 104: 0.05, 130: 0.05, 156: 0.06, 182: 0.08},
    }
    
    check_amplitude_calculation(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)


if __name__ == "__main__":
    main()
