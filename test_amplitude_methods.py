"""
测试不同的振幅计算方法
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


def test_amplitude_methods(mka_file, sample_name, klingelnberg_ref):
    """测试不同的振幅计算方法"""
    print(f"\n{'='*90}")
    print(f"Test Amplitude Methods: {sample_name}")
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
    
    # 方法1：每个齿单独计算频谱然后平均
    print(f"\nMethod 1: Per-Tooth Spectrum Average")
    
    all_spectra = {}
    sorted_teeth = sorted(side_data.keys())
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        values = np.array(tooth_values, dtype=float)
        n = len(values)
        
        # 仅去均值
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
    
    print(f"  {'Order':<8} {'Ours':<12} {'Klingelnberg':<12} {'Error':<10}")
    errors = []
    for order in sorted(ref.keys()):
        our_amp = avg_spectrum.get(order, 0)
        ref_amp = ref[order]
        error = abs(our_amp - ref_amp) / ref_amp * 100 if ref_amp > 0 else 100
        errors.append(error)
        print(f"  {order:<8} {our_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}%")
    print(f"  Average Error: {np.mean(errors):.1f}%")
    
    # 方法2：检查数据范围
    print(f"\nMethod 2: Check Data Range")
    
    all_values = []
    for tooth_id in sorted_teeth[:5]:
        tooth_values = side_data[tooth_id]
        if tooth_values is None:
            continue
        values = np.array(tooth_values, dtype=float)
        all_values.extend(values.tolist())
    
    all_values = np.array(all_values)
    print(f"  Data range: {np.min(all_values):.4f} to {np.max(all_values):.4f}")
    print(f"  Data std: {np.std(all_values):.4f}")
    
    # 方法3：检查振幅比例
    print(f"\nMethod 3: Amplitude Ratio Analysis")
    
    our_26 = avg_spectrum.get(26, 0)
    ref_26 = ref[26]
    ratio = our_26 / ref_26 if ref_26 > 0 else 0
    
    print(f"  Our 26-order amplitude: {our_26:.4f}")
    print(f"  Klingelnberg 26-order: {ref_26:.4f}")
    print(f"  Ratio: {ratio:.2f}")
    
    # 方法4：检查是否需要除以齿数
    print(f"\nMethod 4: Divide by Teeth Count")
    scaled_amp = our_26 * teeth_count
    print(f"  Scaled amplitude (×{teeth_count}): {scaled_amp:.4f}")
    
    # 方法5：检查是否需要除以sqrt(teeth_count)
    print(f"\nMethod 5: Divide by sqrt(Teeth Count)")
    scaled_amp2 = our_26 * np.sqrt(teeth_count)
    print(f"  Scaled amplitude (×sqrt({teeth_count})): {scaled_amp2:.4f}")


def main():
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE2 = {
        'right_profile': {26: 0.19, 52: 0.07, 78: 0.10, 104: 0.05, 130: 0.05, 156: 0.06, 182: 0.08},
    }
    
    test_amplitude_methods(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)


if __name__ == "__main__":
    main()
