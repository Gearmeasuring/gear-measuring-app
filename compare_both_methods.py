"""
重新分析振幅计算方法
对比合并曲线法和每个齿单独计算频谱法
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


def analyze_both_methods(mka_file, sample_name, klingelnberg_ref):
    """对比两种方法"""
    print(f"\n{'='*90}")
    print(f"Compare Both Methods: {sample_name}")
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
    
    for side in ['right', 'left']:
        side_data = profile_data.get(side, {})
        direction = f'{side}_profile'
        
        if direction not in klingelnberg_ref:
            continue
        
        ref = klingelnberg_ref[direction]
        
        print(f"\n{'='*60}")
        print(f"{side.upper()} Profile")
        print(f"{'='*60}")
        
        # 方法A：合并曲线法
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
            
            if side == 'left':
                angles = tau - xi_angles
            else:
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
        
        spectrum_merged = {}
        for order in sorted(ref.keys()):
            cos_x = np.cos(order * theta)
            sin_x = np.sin(order * theta)
            A = np.column_stack((cos_x, sin_x))
            coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
            a, b = coeffs
            amplitude = np.sqrt(a*a + b*b)
            spectrum_merged[order] = amplitude
        
        # 方法B：每个齿单独计算频谱然后平均
        all_spectra = {}
        
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
            xi_angles = np.array(xi_angles)
            
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * pitch_angle
            
            if side == 'left':
                angles = (tau - xi_angles) % 360.0
            else:
                angles = (tau + xi_angles) % 360.0
            
            sort_idx = np.argsort(angles)
            angles = angles[sort_idx]
            corrected_values = corrected_values[sort_idx]
            
            unique_angles, unique_indices = np.unique(np.round(angles, 4), return_index=True)
            unique_values = corrected_values[unique_indices]
            
            if len(unique_angles) < 2:
                continue
            
            num_pts = 1024
            interp_ang = np.linspace(0, 360, num_pts, endpoint=False)
            interp_val = np.interp(interp_ang, unique_angles, unique_values, period=360)
            
            theta_t = np.radians(interp_ang)
            
            for order in sorted(ref.keys()):
                cos_x = np.cos(order * theta_t)
                sin_x = np.sin(order * theta_t)
                A = np.column_stack((cos_x, sin_x))
                coeffs, _, _, _ = np.linalg.lstsq(A, interp_val, rcond=None)
                a, b = coeffs
                amplitude = np.sqrt(a*a + b*b)
                
                if order not in all_spectra:
                    all_spectra[order] = []
                all_spectra[order].append(amplitude)
        
        spectrum_per_tooth = {order: np.mean(amps) for order, amps in all_spectra.items()}
        
        # 寻找最佳缩放因子
        print(f"\nMethod A: Merged Curve")
        best_scale_a = None
        best_error_a = float('inf')
        for scale in np.linspace(0.01, 0.3, 60):
            errors = []
            for order in ref.keys():
                our_amp = spectrum_merged.get(order, 0) * scale
                ref_amp = ref[order]
                error = abs(our_amp - ref_amp) / ref_amp * 100
                errors.append(error)
            avg_error = np.mean(errors)
            if avg_error < best_error_a:
                best_error_a = avg_error
                best_scale_a = scale
        
        print(f"  Best scale: {best_scale_a:.4f}, Error: {best_error_a:.1f}%")
        
        print(f"\nMethod B: Per-Tooth Average")
        best_scale_b = None
        best_error_b = float('inf')
        for scale in np.linspace(1, 10, 90):
            errors = []
            for order in ref.keys():
                our_amp = spectrum_per_tooth.get(order, 0) * scale
                ref_amp = ref[order]
                error = abs(our_amp - ref_amp) / ref_amp * 100
                errors.append(error)
            avg_error = np.mean(errors)
            if avg_error < best_error_b:
                best_error_b = avg_error
                best_scale_b = scale
        
        print(f"  Best scale: {best_scale_b:.4f}, Error: {best_error_b:.1f}%")
        
        # 显示最佳结果
        print(f"\nBest Results Comparison:")
        print(f"  {'Order':<8} {'Merged':<12} {'PerTooth':<12} {'Klingelnberg':<12}")
        for order in sorted(ref.keys()):
            merged_amp = spectrum_merged.get(order, 0) * best_scale_a
            per_tooth_amp = spectrum_per_tooth.get(order, 0) * best_scale_b
            ref_amp = ref[order]
            print(f"  {order:<8} {merged_amp:<12.4f} {per_tooth_amp:<12.4f} {ref_amp:<12.4f}")
        
        # 分析缩放因子
        print(f"\nScale Factor Analysis:")
        print(f"  Merged scale: {best_scale_a:.4f}")
        print(f"  PerTooth scale: {best_scale_b:.4f}")
        print(f"  Ratio (PerTooth/Merged): {best_scale_b/best_scale_a:.2f}")
        print(f"  sqrt(ZE): {np.sqrt(teeth_count):.2f}")
        print(f"  ZE: {teeth_count}")


def main():
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE2 = {
        'right_profile': {26: 0.19, 52: 0.07, 78: 0.10, 104: 0.05, 130: 0.05, 156: 0.06, 182: 0.08},
        'left_profile': {22: 0.03, 26: 0.24, 44: 0.04, 52: 0.19, 78: 0.09, 104: 0.16, 130: 0.09, 156: 0.06, 182: 0.08},
    }
    
    analyze_both_methods(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)


if __name__ == "__main__":
    main()
