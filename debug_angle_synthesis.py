"""
调试角度合成公式
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


def debug_angle_synthesis(mka_file, sample_name):
    """调试角度合成"""
    print(f"\n{'='*90}")
    print(f"Debug Angle Synthesis: {sample_name}")
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
    print(f"Pitch Diameter: {pitch_diameter:.3f}")
    print(f"Base Diameter: {base_diameter:.3f}")
    
    for side in ['right', 'left']:
        side_data = profile_data.get(side, {})
        if not side_data:
            continue
        
        print(f"\n{side.upper()} Profile:")
        
        tooth_id = list(sorted(side_data.keys()))[0]
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
        
        print(f"  Tooth {tooth_id}: {n} points")
        print(f"  Original: mean={np.mean(values):.4f}, std={np.std(values):.4f}")
        print(f"  Corrected: mean={np.mean(corrected_values):.4f}, std={np.std(corrected_values):.4f}")
        
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
        
        print(f"  Tau (pitch angle) = {tau:.2f}")
        print(f"  Xi range: {np.min(xi_angles):.2f} to {np.max(xi_angles):.2f}")
        
        if side == 'left':
            angles_v1 = tau - xi_angles
            angles_v2 = tau + xi_angles
        else:
            angles_v1 = tau + xi_angles
            angles_v2 = tau - xi_angles
        
        angles_v1 = angles_v1 % 360.0
        angles_v2 = angles_v2 % 360.0
        
        print(f"  Version 1 (phi = tau {'-' if side=='left' else '+'} xi): {np.min(angles_v1):.2f} to {np.max(angles_v1):.2f}")
        print(f"  Version 2 (phi = tau {'+' if side=='left' else '-'} xi): {np.min(angles_v2):.2f} to {np.max(angles_v2):.2f}")
        
        def compute_spectrum(angles, values):
            angles = angles % 360.0
            sort_idx = np.argsort(angles)
            angles = angles[sort_idx]
            values = values[sort_idx]
            
            unique_angles, unique_indices = np.unique(np.round(angles, 4), return_index=True)
            unique_values = values[unique_indices]
            
            num_points = 1024
            interp_angles = np.linspace(0, 360, num_points, endpoint=False)
            interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
            
            theta = np.radians(interp_angles)
            
            spectrum = {}
            for order in [26, 52, 78]:
                cos_x = np.cos(order * theta)
                sin_x = np.sin(order * theta)
                A = np.column_stack((cos_x, sin_x))
                coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
                a, b = coeffs
                amplitude = np.sqrt(a*a + b*b)
                spectrum[order] = amplitude
            
            return spectrum
        
        spectrum_v1 = compute_spectrum(angles_v1, corrected_values)
        spectrum_v2 = compute_spectrum(angles_v2, corrected_values)
        
        print(f"\n  Spectrum Comparison:")
        print(f"    Order  V1        V2")
        for order in [26, 52, 78]:
            print(f"    {order:<6} {spectrum_v1[order]:.4f}    {spectrum_v2[order]:.4f}")


def main():
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    debug_angle_synthesis(sample2_file, "Sample2 (ZE=26)")


if __name__ == "__main__":
    main()
