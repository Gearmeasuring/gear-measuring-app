"""
步骤2：检查高阶次频谱提取问题
分析为什么156、182等阶次振幅为0
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


def analyze_spectrum_extraction(mka_file, sample_name, klingelnberg_ref):
    """分析频谱提取问题"""
    print(f"\n{'='*90}")
    print(f"Spectrum Extraction Analysis: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    
    teeth_count = gear_data.get('teeth', 26)
    module = gear_data.get('module', 1.44)
    pressure_angle = gear_data.get('pressure_angle', 17.0)
    
    pitch_diameter = module * teeth_count
    pitch_radius = pitch_diameter / 2.0
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
    base_radius = base_diameter / 2.0
    pitch_angle = 360.0 / teeth_count
    
    print(f"\nGear: Teeth={teeth_count}")
    
    side = 'right'
    side_data = profile_data.get(side, {})
    direction = f'{side}_profile'
    ref = klingelnberg_ref[direction]
    
    # 构建合并曲线
    all_angles = []
    all_values = []
    
    for tooth_id in sorted(side_data.keys()):
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        values = np.array(tooth_values, dtype=float)
        n = len(values)
        
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        coeffs = np.polyfit(x_norm, values, 2)
        trend = np.polyval(coeffs, x_norm)
        residual1 = values - trend
        coeffs2 = np.polyfit(x_norm, residual1, 1)
        trend2 = np.polyval(coeffs2, x_norm)
        corrected_values = residual1 - trend2
        
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
    
    print(f"\nMethod 1: Iterative Decomposition (current method)")
    
    residual = np.array(interp_values, dtype=float)
    spectrum_iterative = {}
    
    for iteration in range(15):
        best_order = None
        best_amplitude = 0.0
        best_coeffs = None
        
        for order in range(1, 5 * teeth_count + 1):
            if order in spectrum_iterative:
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
        
        if best_order is None or best_amplitude < 0.001:
            break
        
        spectrum_iterative[best_order] = best_amplitude
        
        a, b = best_coeffs
        fitted_wave = a * np.cos(best_order * theta) + b * np.sin(best_order * theta)
        residual = residual - fitted_wave
        
        print(f"  Iter {iteration+1}: Order {best_order}, Amp {best_amplitude:.4f}")
    
    print(f"\nMethod 2: Direct FFT")
    fft_result = np.fft.fft(interp_values)
    fft_amplitudes = np.abs(fft_result) * 2 / num_points
    
    print(f"\nComparison with Klingelnberg Reference:")
    print(f"  {'Order':<8} {'Iterative':<12} {'FFT':<12} {'Klingelnberg':<12} {'Iter%':<10} {'FFT%':<10}")
    print(f"  {'-'*70}")
    
    for order in sorted(ref.keys()):
        iter_amp = spectrum_iterative.get(order, 0)
        fft_amp = fft_amplitudes[order] if order < num_points else 0
        ref_amp = ref[order]
        
        iter_error = abs(iter_amp - ref_amp) / ref_amp * 100 if ref_amp > 0 else 100
        fft_error = abs(fft_amp - ref_amp) / ref_amp * 100 if ref_amp > 0 else 100
        
        print(f"  {order:<8} {iter_amp:<12.4f} {fft_amp:<12.4f} {ref_amp:<12.4f} {iter_error:<10.1f}% {fft_error:<10.1f}%")
    
    print(f"\nMethod 3: Direct Least Squares (no iteration)")
    spectrum_direct = {}
    for order in sorted(ref.keys()):
        cos_x = np.cos(order * theta)
        sin_x = np.sin(order * theta)
        A = np.column_stack((cos_x, sin_x))
        coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
        a, b = coeffs
        amplitude = np.sqrt(a*a + b*b)
        spectrum_direct[order] = amplitude
    
    print(f"\n  {'Order':<8} {'Direct LS':<12} {'Klingelnberg':<12} {'Error':<10}")
    for order in sorted(ref.keys()):
        direct_amp = spectrum_direct[order]
        ref_amp = ref[order]
        error = abs(direct_amp - ref_amp) / ref_amp * 100 if ref_amp > 0 else 100
        print(f"  {order:<8} {direct_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}%")
    
    print(f"\nKey Observation:")
    print(f"  - Iterative method only extracts the LARGEST amplitude at each step")
    print(f"  - This means high-order components (156, 182) are never extracted")
    print(f"  - Because they are smaller than lower-order components")
    print(f"  - Solution: Use direct least squares for ALL orders of interest")


def main():
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE2 = {
        'right_profile': {26: 0.19, 52: 0.07, 78: 0.10, 104: 0.05, 130: 0.05, 156: 0.06, 182: 0.08},
    }
    
    analyze_spectrum_extraction(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)


if __name__ == "__main__":
    main()
