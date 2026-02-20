"""
测试迭代分解方法
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


def iterative_decomposition_test(mka_file, sample_name, klingelnberg_ref):
    """测试迭代分解方法"""
    print(f"\n{'='*90}")
    print(f"Iterative Decomposition Test: {sample_name}")
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
    
    # 构建合并曲线
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
    
    # 迭代分解
    print(f"\nIterative Decomposition:")
    
    residual = np.array(interp_values, dtype=float)
    spectrum = {}
    max_order = 5 * teeth_count
    
    for iteration in range(10):
        best_order = None
        best_amplitude = 0.0
        best_coeffs = None
        
        for order in range(1, max_order + 1):
            if order in spectrum:
                continue
            
            cos_x = np.cos(order * theta)
            sin_x = np.sin(order * theta)
            A = np.column_stack((cos_x, sin_x))
            coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
            a, b = coeffs
            amplitude = np.sqrt(a*a + b*b)
            
            if amplitude > best_amplitude:
                best_amplitude = amplitude
                best_order = order
                best_coeffs = (a, b)
        
        if best_order is None:
            break
        
        spectrum[best_order] = best_amplitude
        
        a, b = best_coeffs
        fitted_wave = a * np.cos(best_order * theta) + b * np.sin(best_order * theta)
        residual = residual - fitted_wave
        
        print(f"  Iteration {iteration+1}: Order {best_order}, Amplitude {best_amplitude:.4f}")
    
    print(f"\nComparison with Klingelnberg:")
    print(f"  {'Order':<8} {'Ours':<12} {'Klingelnberg':<12} {'Error':<10}")
    
    errors = []
    for order in sorted(ref.keys()):
        our_amp = spectrum.get(order, 0)
        ref_amp = ref[order]
        error = abs(our_amp - ref_amp) / ref_amp * 100 if ref_amp > 0 else 100
        errors.append(error)
        print(f"  {order:<8} {our_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}%")
    
    print(f"\n  Average Error: {np.mean(errors):.1f}%")


def main():
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE2 = {
        'right_profile': {26: 0.19, 52: 0.07, 78: 0.10, 104: 0.05, 130: 0.05, 156: 0.06, 182: 0.08},
    }
    
    iterative_decomposition_test(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)


if __name__ == "__main__":
    main()
