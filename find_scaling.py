"""
测试不同的缩放因子
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


def find_best_scaling(mka_file, sample_name, klingelnberg_ref):
    """寻找最佳缩放因子"""
    print(f"\n{'='*90}")
    print(f"Find Best Scaling Factor: {sample_name}")
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
    
    for side in ['right', 'left']:
        side_data = profile_data.get(side, {})
        direction = f'{side}_profile'
        
        if direction not in klingelnberg_ref:
            continue
        
        ref = klingelnberg_ref[direction]
        
        # 每个齿单独计算频谱然后平均
        all_spectra = {}
        sorted_teeth = sorted(side_data.keys())
        
        for tooth_id in sorted_teeth:
            tooth_values = side_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            values = np.array(tooth_values, dtype=float)
            n = len(values)
            
            corrected_values = values - np.mean(values)
            
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
            
            theta = np.radians(interp_ang)
            
            for order in range(1, 200):
                cos_x = np.cos(order * theta)
                sin_x = np.sin(order * theta)
                A = np.column_stack((cos_x, sin_x))
                coeffs, _, _, _ = np.linalg.lstsq(A, interp_val, rcond=None)
                a, b = coeffs
                amplitude = np.sqrt(a*a + b*b)
                
                if order not in all_spectra:
                    all_spectra[order] = []
                all_spectra[order].append(amplitude)
        
        avg_spectrum = {order: np.mean(amps) for order, amps in all_spectra.items()}
        
        print(f"\n{side.upper()} Profile:")
        
        # 寻找最佳缩放因子
        best_factor = None
        best_error = float('inf')
        
        for factor in np.linspace(0.5, 5.0, 46):
            errors = []
            for order in ref.keys():
                our_amp = avg_spectrum.get(order, 0) * factor
                ref_amp = ref[order]
                error = abs(our_amp - ref_amp) / ref_amp * 100
                errors.append(error)
            
            avg_error = np.mean(errors)
            if avg_error < best_error:
                best_error = avg_error
                best_factor = factor
        
        print(f"  Best scaling factor: {best_factor:.2f}")
        print(f"  Best average error: {best_error:.1f}%")
        
        print(f"\n  {'Order':<8} {'Ours×Factor':<12} {'Klingelnberg':<12} {'Error':<10}")
        for order in sorted(ref.keys()):
            our_amp = avg_spectrum.get(order, 0) * best_factor
            ref_amp = ref[order]
            error = abs(our_amp - ref_amp) / ref_amp * 100
            print(f"  {order:<8} {our_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}%")


def main():
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE2 = {
        'right_profile': {26: 0.19, 52: 0.07, 78: 0.10, 104: 0.05, 130: 0.05, 156: 0.06, 182: 0.08},
        'left_profile': {22: 0.03, 26: 0.24, 44: 0.04, 52: 0.19, 78: 0.09, 104: 0.16, 130: 0.09, 156: 0.06, 182: 0.08},
    }
    
    find_best_scaling(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)


if __name__ == "__main__":
    main()
