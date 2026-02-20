"""
深入分析合并曲线和频谱计算
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


def analyze_merged_curve(mka_file, sample_name, klingelnberg_ref):
    """分析合并曲线"""
    print(f"\n{'='*90}")
    print(f"Analyze Merged Curve: {sample_name}")
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
    
    print(f"\nGear: Teeth={teeth_count}, Module={module}")
    
    for side in ['right', 'left']:
        side_data = profile_data.get(side, {})
        if not side_data:
            continue
        
        direction = f'{side}_profile'
        if direction not in klingelnberg_ref:
            continue
        
        ref = klingelnberg_ref[direction]
        
        print(f"\n{side.upper()} Profile:")
        
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
            
            if side == 'left':
                angles = tau - xi_angles
            else:
                angles = tau + xi_angles
            
            all_angles.extend(angles.tolist())
            all_values.extend(corrected_values.tolist())
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        
        print(f"  Total points: {len(all_angles)}")
        print(f"  Angle range: {np.min(all_angles):.2f} to {np.max(all_angles):.2f}")
        
        all_angles = all_angles % 360.0
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        
        unique_angles, unique_indices = np.unique(np.round(all_angles, 4), return_index=True)
        unique_values = all_values[unique_indices]
        
        print(f"  Unique points: {len(unique_angles)}")
        
        num_points = 1024
        interp_angles = np.linspace(0, 360, num_points, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        theta = np.radians(interp_angles)
        
        print(f"\n  Spectrum Analysis:")
        print(f"    Order  Ours       Klingelnberg  Error")
        
        errors = []
        for order in sorted(ref.keys()):
            cos_x = np.cos(order * theta)
            sin_x = np.sin(order * theta)
            A = np.column_stack((cos_x, sin_x))
            coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
            a, b = coeffs
            amplitude = np.sqrt(a*a + b*b)
            
            ref_amp = ref[order]
            error = abs(amplitude - ref_amp) / ref_amp * 100 if ref_amp > 0 else 100
            errors.append(error)
            print(f"    {order:<6} {amplitude:.4f}     {ref_amp:.4f}        {error:.1f}%")
        
        print(f"  Average Error: {np.mean(errors):.1f}%")


def main():
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE2 = {
        'right_profile': {26: 0.19, 52: 0.07, 78: 0.10, 104: 0.05, 130: 0.05, 156: 0.06, 182: 0.08},
        'left_profile': {22: 0.03, 26: 0.24, 44: 0.04, 52: 0.19, 78: 0.09, 104: 0.16, 130: 0.09, 156: 0.06, 182: 0.08}
    }
    
    analyze_merged_curve(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)


if __name__ == "__main__":
    main()
