"""
尝试不同的频谱分析方法
1. 直接对每个齿进行频谱分析，然后平均
2. 分析角度合成后数据分布的问题
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


def method1_per_tooth_spectrum(mka_file, sample_name, klingelnberg_ref):
    """方法1：对每个齿单独计算频谱，然后平均"""
    print(f"\n{'='*90}")
    print(f"Method 1: Per-Tooth Spectrum Analysis: {sample_name}")
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
    
    print(f"\nGear: Teeth={teeth_count}, Module={module}, Helix={helix_angle}")
    
    tan_beta0 = math.tan(math.radians(abs(helix_angle))) if abs(helix_angle) > 0.01 else 0
    eval_center = (eval_start + eval_end) / 2.0
    
    for side, side_name in [('right', 'Right Helix'), ('left', 'Left Helix')]:
        side_data = flank_data.get(side, {})
        direction = f'{side}_helix'
        
        if direction not in klingelnberg_ref:
            continue
        
        ref = klingelnberg_ref[direction]
        
        sorted_teeth = sorted(side_data.keys())
        
        all_spectra = {}
        
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
            tau = tooth_index * (360.0 / teeth_count)
            
            if side == 'left':
                angles = tau - delta_phi
            else:
                angles = tau + delta_phi
            
            angles = angles % 360.0
            
            sort_idx = np.argsort(angles)
            angles = angles[sort_idx]
            corrected_values = corrected_values[sort_idx]
            
            unique_angles, unique_indices = np.unique(np.round(angles, 4), return_index=True)
            unique_values = corrected_values[unique_indices]
            
            num_points = 1024
            interp_angles = np.linspace(0, 360, num_points, endpoint=False)
            interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
            
            angles_rad = np.radians(interp_angles)
            
            max_order = 5 * teeth_count
            for order in range(1, max_order + 1):
                cos_term = np.cos(order * angles_rad)
                sin_term = np.sin(order * angles_rad)
                
                A = np.column_stack([cos_term, sin_term])
                coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
                
                a, b = coeffs[0], coeffs[1]
                amplitude = np.sqrt(a**2 + b**2)
                
                if order not in all_spectra:
                    all_spectra[order] = []
                all_spectra[order].append(amplitude)
        
        avg_spectrum = {order: np.mean(amps) for order, amps in all_spectra.items()}
        
        print(f"\n{side_name} - Per-Tooth Average Spectrum:")
        print(f"  {'Order':<8} {'Ours':<12} {'Klingelnberg':<12} {'Error':<10}")
        
        errors = []
        for order in sorted(ref.keys()):
            our_amp = avg_spectrum.get(order, 0)
            ref_amp = ref[order]
            error = abs(our_amp - ref_amp) / ref_amp * 100
            errors.append(error)
            print(f"  {order:<8.0f} {our_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}%")
        
        print(f"  Average Error: {np.mean(errors):.1f}%")


def method2_direct_axial_spectrum(mka_file, sample_name, klingelnberg_ref):
    """方法2：直接在轴向域进行频谱分析"""
    print(f"\n{'='*90}")
    print(f"Method 2: Direct Axial Spectrum: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 26)
    eval_start = gear_data.get('helix_eval_start', 0)
    eval_end = gear_data.get('helix_eval_end', 0)
    
    for side, side_name in [('right', 'Right Helix'), ('left', 'Left Helix')]:
        side_data = flank_data.get(side, {})
        direction = f'{side}_helix'
        
        if direction not in klingelnberg_ref:
            continue
        
        ref = klingelnberg_ref[direction]
        
        sorted_teeth = sorted(side_data.keys())
        
        all_spectra = {}
        
        for tooth_id in sorted_teeth:
            tooth_values = side_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            actual_points = len(tooth_values)
            eval_values = np.array(tooth_values, dtype=float)
            
            corrected_values = eval_values - np.mean(eval_values)
            
            axial_positions = np.linspace(eval_start, eval_end, actual_points)
            axial_length = eval_end - eval_start
            
            axial_norm = (axial_positions - eval_start) / axial_length
            
            num_points = 1024
            interp_axial = np.linspace(0, 1, num_points, endpoint=False)
            interp_values = np.interp(interp_axial, axial_norm, corrected_values)
            
            fft_result = np.fft.fft(interp_values)
            amplitudes = np.abs(fft_result) * 2 / num_points
            
            for k in range(1, num_points // 2):
                if k not in all_spectra:
                    all_spectra[k] = []
                all_spectra[k].append(amplitudes[k])
        
        avg_spectrum = {k: np.mean(amps) for k, amps in all_spectra.items()}
        
        print(f"\n{side_name} - Direct Axial FFT (averaged over teeth):")
        
        top_orders = sorted(avg_spectrum.items(), key=lambda x: x[1], reverse=True)[:10]
        print(f"  Top 10 frequency components (k = cycles per tooth):")
        for k, amp in top_orders:
            print(f"    k={k}: {amp:.4f}")


def method3_angle_distribution_analysis(mka_file, sample_name):
    """方法3：分析角度合成后的数据分布"""
    print(f"\n{'='*90}")
    print(f"Method 3: Angle Distribution Analysis: {sample_name}")
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
    
    right_data = flank_data.get('right', {})
    
    if right_data:
        all_angles = []
        sorted_teeth = sorted(right_data.keys())
        
        for tooth_id in sorted_teeth:
            tooth_values = right_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            actual_points = len(tooth_values)
            axial_positions = np.linspace(eval_start, eval_end, actual_points)
            delta_z = axial_positions - eval_center
            
            if abs(helix_angle) > 0.01 and pitch_diameter > 0:
                delta_phi = np.degrees(2 * delta_z * tan_beta0 / pitch_diameter)
            else:
                delta_phi = np.zeros(actual_points)
            
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * pitch_angle
            angles = (tau + delta_phi) % 360.0
            
            all_angles.extend(angles.tolist())
        
        all_angles = np.array(all_angles)
        
        print(f"\nAngle Distribution Statistics:")
        print(f"  Total points: {len(all_angles)}")
        print(f"  Angle range: {np.min(all_angles):.2f} - {np.max(all_angles):.2f}")
        
        hist, bins = np.histogram(all_angles, bins=36)
        
        print(f"\n  Histogram (per 10 degree bin):")
        print(f"    Min points in bin: {np.min(hist)}")
        print(f"    Max points in bin: {np.max(hist)}")
        print(f"    Mean points per bin: {np.mean(hist):.1f}")
        print(f"    Std: {np.std(hist):.1f}")
        print(f"    Coefficient of Variation: {np.std(hist)/np.mean(hist)*100:.1f}%")
        
        gaps = []
        for i in range(len(bins) - 1):
            if hist[i] == 0:
                gaps.append(f"{bins[i]:.0f}-{bins[i+1]:.0f}")
        
        if gaps:
            print(f"    Empty bins: {gaps[:5]}...")
        
        overlap_count = 0
        for i in range(len(hist)):
            if hist[i] > 2 * np.mean(hist):
                overlap_count += 1
        
        print(f"    Bins with >2x average: {overlap_count}")


def main():
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE2 = {
        'right_helix': {26: 0.03, 52: 0.06, 78: 0.03, 141: 0.03, 156: 0.02},
        'left_helix': {26: 0.07, 48: 0.03, 52: 0.08, 78: 0.04, 104: 0.03, 130: 0.02, 141: 0.04, 182: 0.02}
    }
    
    method1_per_tooth_spectrum(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)
    
    method2_direct_axial_spectrum(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)
    
    method3_angle_distribution_analysis(sample2_file, "Sample2 (ZE=26)")


if __name__ == "__main__":
    main()
