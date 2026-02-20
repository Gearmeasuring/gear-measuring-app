"""
测试内齿公式对样本2的影响
内齿的关键差异：角度合成公式的符号反转
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


def preprocess_tooth_data(values, order=3):
    """预处理齿数据"""
    if len(values) < order + 1:
        return values - np.mean(values)
    
    n = len(values)
    x = np.arange(n)
    x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
    
    coeffs = np.polyfit(x_norm, values, order)
    trend = np.polyval(coeffs, x_norm)
    
    return values - trend


def compute_spectrum(angles, values, max_order=500):
    """计算频谱"""
    angles = np.array(angles) % 360.0
    values = np.array(values)
    
    sort_idx = np.argsort(angles)
    angles = angles[sort_idx]
    values = values[sort_idx]
    
    unique_angles, unique_indices = np.unique(np.round(angles, 4), return_index=True)
    unique_values = values[unique_indices]
    
    num_points = 1024
    interp_angles = np.linspace(0, 360, num_points, endpoint=False)
    interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
    
    angles_rad = np.radians(interp_angles)
    
    spectrum = {}
    for order in range(1, max_order + 1):
        cos_term = np.cos(order * angles_rad)
        sin_term = np.sin(order * angles_rad)
        
        A = np.column_stack([cos_term, sin_term])
        coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
        
        a, b = coeffs[0], coeffs[1]
        amplitude = np.sqrt(a**2 + b**2)
        
        spectrum[order] = amplitude
    
    return spectrum


def analyze_helix_with_formula(side_data, side, teeth_count, module, helix_angle, eval_start, eval_end, 
                                preprocess_order=3, is_internal=False):
    """使用指定公式分析齿向数据"""
    pitch_diameter = module * teeth_count
    pitch_angle = 360.0 / teeth_count
    
    tan_beta0 = math.tan(math.radians(abs(helix_angle))) if abs(helix_angle) > 0.01 else 0
    eval_center = (eval_start + eval_end) / 2.0
    
    all_angles = []
    all_values = []
    
    sorted_teeth = sorted(side_data.keys())
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        actual_points = len(tooth_values)
        eval_values = np.array(tooth_values, dtype=float)
        
        corrected_values = preprocess_tooth_data(eval_values, preprocess_order)
        
        axial_positions = np.linspace(eval_start, eval_end, actual_points)
        delta_z = axial_positions - eval_center
        
        if abs(helix_angle) > 0.01 and pitch_diameter > 0:
            delta_phi = np.degrees(2 * delta_z * tan_beta0 / pitch_diameter)
        else:
            delta_phi = np.zeros(actual_points)
        
        tooth_index = int(tooth_id) - 1
        tau = tooth_index * pitch_angle
        
        if is_internal:
            if side == 'left':
                angles = tau + delta_phi
            else:
                angles = tau - delta_phi
        else:
            if side == 'left':
                angles = tau - delta_phi
            else:
                angles = tau + delta_phi
        
        all_angles.extend(angles.tolist())
        all_values.extend(corrected_values.tolist())
    
    if not all_angles:
        return None
    
    return compute_spectrum(all_angles, all_values)


def test_internal_gear_formula(mka_file, sample_name, klingelnberg_ref):
    """测试内齿公式"""
    print(f"\n{'='*90}")
    print(f"Testing Internal Gear Formula: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 26)
    module = gear_data.get('module', 1.44)
    helix_angle = gear_data.get('helix_angle', -25.0)
    eval_start = gear_data.get('helix_eval_start', 0)
    eval_end = gear_data.get('helix_eval_end', 0)
    
    print(f"\nGear Parameters:")
    print(f"  Teeth ZE = {teeth_count}")
    print(f"  Module m = {module}")
    print(f"  Helix Angle beta = {helix_angle}")
    
    for side, side_name in [('right', 'Right Helix'), ('left', 'Left Helix')]:
        side_data = flank_data.get(side, {})
        direction = f'{side}_helix'
        
        if direction not in klingelnberg_ref:
            continue
        
        ref = klingelnberg_ref[direction]
        
        spectrum_external = analyze_helix_with_formula(
            side_data, side, teeth_count, module, helix_angle, 
            eval_start, eval_end, preprocess_order=3, is_internal=False
        )
        
        spectrum_internal = analyze_helix_with_formula(
            side_data, side, teeth_count, module, helix_angle,
            eval_start, eval_end, preprocess_order=3, is_internal=True
        )
        
        print(f"\n{side_name}:")
        print(f"  {'Order':<6} {'Klingelnberg':<12} {'External':<12} {'Error%':<10} {'Internal':<12} {'Error%':<10} {'Better':<8}")
        print(f"  {'-'*75}")
        
        errors_external = []
        errors_internal = []
        
        for order in sorted(ref.keys()):
            ref_amp = ref[order]
            
            amp_ext = spectrum_external.get(order, 0) if spectrum_external else 0
            error_ext = abs(amp_ext - ref_amp) / ref_amp * 100 if ref_amp > 0 else 100
            errors_external.append(error_ext)
            
            amp_int = spectrum_internal.get(order, 0) if spectrum_internal else 0
            error_int = abs(amp_int - ref_amp) / ref_amp * 100 if ref_amp > 0 else 100
            errors_internal.append(error_int)
            
            better = 'INTERNAL' if error_int < error_ext else 'EXTERNAL' if error_ext < error_int else 'TIE'
            print(f"  {order:<6.0f} {ref_amp:<12.4f} {amp_ext:<12.4f} {error_ext:<10.1f}% {amp_int:<12.4f} {error_int:<10.1f}% {better}")
        
        avg_ext = np.mean(errors_external)
        avg_int = np.mean(errors_internal)
        winner = 'INTERNAL FORMULA' if avg_int < avg_ext else 'EXTERNAL FORMULA' if avg_ext < avg_int else 'TIE'
        print(f"  {'-'*75}")
        print(f"  Average: External={avg_ext:.1f}%, Internal={avg_int:.1f}% -> {winner}")


def test_internal_with_per_tooth(mka_file, sample_name, klingelnberg_ref):
    """测试内齿公式 + 每个齿单独计算频谱"""
    print(f"\n{'='*90}")
    print(f"Testing Internal Formula + Per-Tooth Method: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 26)
    module = gear_data.get('module', 1.44)
    helix_angle = gear_data.get('helix_angle', -25.0)
    eval_start = gear_data.get('helix_eval_start', 0)
    eval_end = gear_data.get('helix_eval_end', 0)
    
    pitch_diameter = module * teeth_count
    pitch_angle = 360.0 / teeth_count
    
    tan_beta0 = math.tan(math.radians(abs(helix_angle))) if abs(helix_angle) > 0.01 else 0
    eval_center = (eval_start + eval_end) / 2.0
    
    for side, side_name in [('right', 'Right Helix'), ('left', 'Left Helix')]:
        side_data = flank_data.get(side, {})
        direction = f'{side}_helix'
        
        if direction not in klingelnberg_ref:
            continue
        
        ref = klingelnberg_ref[direction]
        
        all_spectra = {}
        
        sorted_teeth = sorted(side_data.keys())
        
        for tooth_id in sorted_teeth:
            tooth_values = side_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            actual_points = len(tooth_values)
            eval_values = np.array(tooth_values, dtype=float)
            
            corrected_values = eval_values - np.mean(eval_values)
            
            axial_positions = np.linspace(eval_start, eval_end, actual_points)
            delta_z = axial_positions - eval_center
            
            if abs(helix_angle) > 0.01 and pitch_diameter > 0:
                delta_phi = np.degrees(2 * delta_z * tan_beta0 / pitch_diameter)
            else:
                delta_phi = np.zeros(actual_points)
            
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * pitch_angle
            
            if side == 'left':
                angles = tau + delta_phi
            else:
                angles = tau - delta_phi
            
            spectrum = compute_spectrum(angles, corrected_values)
            
            for order, amp in spectrum.items():
                if order not in all_spectra:
                    all_spectra[order] = []
                all_spectra[order].append(amp)
        
        avg_spectrum = {order: np.mean(amps) for order, amps in all_spectra.items()}
        
        print(f"\n{side_name} (Internal Formula + Per-Tooth Average):")
        print(f"  {'Order':<8} {'Ours':<12} {'Klingelnberg':<12} {'Error':<10}")
        
        errors = []
        for order in sorted(ref.keys()):
            our_amp = avg_spectrum.get(order, 0)
            ref_amp = ref[order]
            error = abs(our_amp - ref_amp) / ref_amp * 100
            errors.append(error)
            print(f"  {order:<8.0f} {our_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}%")
        
        print(f"  Average Error: {np.mean(errors):.1f}%")


def main():
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE2 = {
        'right_helix': {26: 0.03, 52: 0.06, 78: 0.03, 141: 0.03, 156: 0.02},
        'left_helix': {26: 0.07, 48: 0.03, 52: 0.08, 78: 0.04, 104: 0.03, 130: 0.02, 141: 0.04, 182: 0.02}
    }
    
    test_internal_gear_formula(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)
    
    test_internal_with_per_tooth(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)
    
    print(f"\n{'='*90}")
    print("CONCLUSION")
    print(f"{'='*90}")
    print("""
If the internal gear formula improves results significantly, 
it confirms that Sample2 is an internal gear.

Internal Gear Formula Changes:
  Right flank: phi = tau - delta_phi (instead of tau + delta_phi)
  Left flank:  phi = tau + delta_phi (instead of tau - delta_phi)

This reverses the sign of the helix angle contribution.
""")


if __name__ == "__main__":
    main()
