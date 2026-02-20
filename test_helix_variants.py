"""
测试不同的螺旋角处理方式
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


def analyze_helix_variants(side_data, side, teeth_count, module, helix_angle, eval_start, eval_end, variant='standard'):
    """使用不同变体分析齿向数据"""
    pitch_diameter = module * teeth_count
    pitch_angle = 360.0 / teeth_count
    
    eval_center = (eval_start + eval_end) / 2.0
    
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
            tan_beta0 = math.tan(math.radians(abs(helix_angle)))
            delta_phi = np.degrees(2 * delta_z * tan_beta0 / pitch_diameter)
        else:
            delta_phi = np.zeros(actual_points)
        
        tooth_index = int(tooth_id) - 1
        tau = tooth_index * pitch_angle
        
        if variant == 'standard':
            if side == 'left':
                angles = tau - delta_phi
            else:
                angles = tau + delta_phi
        elif variant == 'reversed':
            if side == 'left':
                angles = tau + delta_phi
            else:
                angles = tau - delta_phi
        elif variant == 'no_delta_phi':
            angles = np.full(actual_points, tau)
        elif variant == 'signed_helix':
            tan_beta0_signed = math.tan(math.radians(helix_angle))
            delta_phi_signed = np.degrees(2 * delta_z * tan_beta0_signed / pitch_diameter)
            if side == 'left':
                angles = tau - delta_phi_signed
            else:
                angles = tau + delta_phi_signed
        
        spectrum = compute_spectrum(angles, corrected_values)
        
        for order, amp in spectrum.items():
            if order not in all_spectra:
                all_spectra[order] = []
            all_spectra[order].append(amp)
    
    if not all_spectra:
        return None
    
    return {order: np.mean(amps) for order, amps in all_spectra.items()}


def test_all_variants(mka_file, sample_name, klingelnberg_ref):
    """测试所有变体"""
    print(f"\n{'='*90}")
    print(f"Testing All Helix Angle Variants: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 26)
    module = gear_data.get('module', 1.44)
    helix_angle = gear_data.get('helix_angle', -25.0)
    eval_start = gear_data.get('helix_eval_start', 0)
    eval_end = gear_data.get('helix_eval_end', 0)
    
    print(f"\nGear: Teeth={teeth_count}, Module={module}, Helix={helix_angle}")
    
    variants = ['standard', 'reversed', 'no_delta_phi', 'signed_helix']
    variant_names = {
        'standard': 'Standard (abs(helix_angle))',
        'reversed': 'Reversed (internal gear formula)',
        'no_delta_phi': 'No Delta_phi (ignore helix)',
        'signed_helix': 'Signed Helix (use actual sign)'
    }
    
    for side, side_name in [('right', 'Right Helix'), ('left', 'Left Helix')]:
        side_data = flank_data.get(side, {})
        direction = f'{side}_helix'
        
        if direction not in klingelnberg_ref:
            continue
        
        ref = klingelnberg_ref[direction]
        
        print(f"\n{side_name}:")
        print(f"  {'Order':<6} {'Klingelnberg':<12}", end='')
        for v in variants:
            print(f" {v:<15}", end='')
        print()
        print(f"  {'-'*80}")
        
        all_errors = {v: [] for v in variants}
        
        for order in sorted(ref.keys()):
            ref_amp = ref[order]
            print(f"  {order:<6.0f} {ref_amp:<12.4f}", end='')
            
            for v in variants:
                spectrum = analyze_helix_variants(
                    side_data, side, teeth_count, module, helix_angle,
                    eval_start, eval_end, variant=v
                )
                amp = spectrum.get(order, 0) if spectrum else 0
                error = abs(amp - ref_amp) / ref_amp * 100 if ref_amp > 0 else 100
                all_errors[v].append(error)
                print(f" {error:<14.1f}%", end='')
            print()
        
        print(f"  {'-'*80}")
        print(f"  {'Average':<6} {'':<12}", end='')
        best_avg = float('inf')
        best_variant = None
        for v in variants:
            avg = np.mean(all_errors[v])
            if avg < best_avg:
                best_avg = avg
                best_variant = v
            print(f" {avg:<14.1f}%", end='')
        print(f"  -> Best: {variant_names[best_variant]}")


def main():
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE2 = {
        'right_helix': {26: 0.03, 52: 0.06, 78: 0.03, 141: 0.03, 156: 0.02},
        'left_helix': {26: 0.07, 48: 0.03, 52: 0.08, 78: 0.04, 104: 0.03, 130: 0.02, 141: 0.04, 182: 0.02}
    }
    
    test_all_variants(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)
    
    print(f"\n{'='*90}")
    print("ANALYSIS")
    print(f"{'='*90}")
    print("""
Variant Descriptions:
  - Standard: Use abs(helix_angle), standard formula
  - Reversed: Internal gear formula (swap +/- for delta_phi)
  - No Delta_phi: Ignore helix angle contribution entirely
  - Signed Helix: Use actual helix angle sign (negative for left-hand)

If 'No Delta_phi' gives best results, the helix angle synthesis 
may not be needed for this type of analysis.
""")


if __name__ == "__main__":
    main()
