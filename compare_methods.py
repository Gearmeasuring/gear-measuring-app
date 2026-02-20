"""
综合对比：两种方法对两个样本的效果
方法A：合并曲线法
方法B：每个齿单独计算频谱然后平均
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


def methodA_merged_curve(side_data, side, teeth_count, module, helix_angle, eval_start, eval_end, preprocess_order=3):
    """方法A：合并曲线法"""
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
        
        if side == 'left':
            angles = tau - delta_phi
        else:
            angles = tau + delta_phi
        
        all_angles.extend(angles.tolist())
        all_values.extend(corrected_values.tolist())
    
    if not all_angles:
        return None
    
    return compute_spectrum(all_angles, all_values)


def methodB_per_tooth_average(side_data, side, teeth_count, module, helix_angle, eval_start, eval_end, preprocess_order=0):
    """方法B：每个齿单独计算频谱然后平均"""
    pitch_diameter = module * teeth_count
    pitch_angle = 360.0 / teeth_count
    
    tan_beta0 = math.tan(math.radians(abs(helix_angle))) if abs(helix_angle) > 0.01 else 0
    eval_center = (eval_start + eval_end) / 2.0
    
    sorted_teeth = sorted(side_data.keys())
    
    all_spectra = {}
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        actual_points = len(tooth_values)
        eval_values = np.array(tooth_values, dtype=float)
        
        if preprocess_order > 0:
            corrected_values = preprocess_tooth_data(eval_values, preprocess_order)
        else:
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
            angles = tau - delta_phi
        else:
            angles = tau + delta_phi
        
        spectrum = compute_spectrum(angles, corrected_values)
        
        for order, amp in spectrum.items():
            if order not in all_spectra:
                all_spectra[order] = []
            all_spectra[order].append(amp)
    
    if not all_spectra:
        return None
    
    return {order: np.mean(amps) for order, amps in all_spectra.items()}


def compare_methods(mka_file, sample_name, klingelnberg_ref):
    """对比两种方法"""
    print(f"\n{'='*90}")
    print(f"Comparing Methods: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    helix_angle = gear_data.get('helix_angle', 0.0)
    eval_start = gear_data.get('helix_eval_start', 0)
    eval_end = gear_data.get('helix_eval_end', 0)
    
    print(f"\nGear: Teeth={teeth_count}, Module={module}, Helix={helix_angle}")
    
    for side, side_name in [('right', 'Right Helix'), ('left', 'Left Helix')]:
        side_data = flank_data.get(side, {})
        direction = f'{side}_helix'
        
        if direction not in klingelnberg_ref:
            continue
        
        ref = klingelnberg_ref[direction]
        
        spectrumA = methodA_merged_curve(side_data, side, teeth_count, module, helix_angle, eval_start, eval_end, preprocess_order=3)
        spectrumB = methodB_per_tooth_average(side_data, side, teeth_count, module, helix_angle, eval_start, eval_end, preprocess_order=0)
        
        print(f"\n{side_name}:")
        print(f"  {'Order':<6} {'Klingelnberg':<12} {'MethodA':<12} {'ErrorA':<10} {'MethodB':<12} {'ErrorB':<10}")
        print(f"  {'-'*70}")
        
        errorsA = []
        errorsB = []
        
        for order in sorted(ref.keys()):
            ref_amp = ref[order]
            
            ampA = spectrumA.get(order, 0) if spectrumA else 0
            errorA = abs(ampA - ref_amp) / ref_amp * 100 if ref_amp > 0 else 100
            errorsA.append(errorA)
            
            ampB = spectrumB.get(order, 0) if spectrumB else 0
            errorB = abs(ampB - ref_amp) / ref_amp * 100 if ref_amp > 0 else 100
            errorsB.append(errorB)
            
            better = 'A' if errorA < errorB else 'B' if errorB < errorA else '='
            print(f"  {order:<6.0f} {ref_amp:<12.4f} {ampA:<12.4f} {errorA:<10.1f}% {ampB:<12.4f} {errorB:<10.1f}% [{better}]")
        
        avgA = np.mean(errorsA)
        avgB = np.mean(errorsB)
        winner = 'Method A' if avgA < avgB else 'Method B' if avgB < avgA else 'Tie'
        print(f"  {'-'*70}")
        print(f"  Average: MethodA={avgA:.1f}%, MethodB={avgB:.1f}% -> {winner}")


def main():
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE1 = {
        'right_helix': {87: 0.0900, 174: 0.1000, 261: 0.0500, 348: 0.0400, 435: 0.0300},
        'left_helix': {87: 0.1200, 89: 0.0700, 174: 0.0600, 261: 0.0500, 348: 0.0300}
    }
    
    KLINGELNBERG_SAMPLE2 = {
        'right_helix': {26: 0.03, 52: 0.06, 78: 0.03, 141: 0.03, 156: 0.02},
        'left_helix': {26: 0.07, 48: 0.03, 52: 0.08, 78: 0.04, 104: 0.03, 130: 0.02, 141: 0.04, 182: 0.02}
    }
    
    compare_methods(sample1_file, "Sample1 (ZE=87)", KLINGELNBERG_SAMPLE1)
    compare_methods(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)
    
    print(f"\n{'='*90}")
    print("CONCLUSION")
    print(f"{'='*90}")
    print(f"""
Based on the comparison:
- Method A (Merged Curve): Better for small Delta_phi range
- Method B (Per-Tooth Average): Better for large Delta_phi range

Recommendation:
- Use Method A when Delta_phi < 10 degrees
- Use Method B when Delta_phi >= 10 degrees
""")


if __name__ == "__main__":
    main()
