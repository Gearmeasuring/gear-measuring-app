"""
深入分析齿向数据问题并尝试不同的优化策略
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import math
import warnings
warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


def analyze_raw_data_characteristics(mka_file, sample_name):
    """分析原始数据特性"""
    print(f"\n{'='*90}")
    print(f"Raw Data Analysis: {sample_name}")
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
    
    print(f"\nGear Parameters:")
    print(f"  Teeth: {teeth_count}")
    print(f"  Module: {module}")
    print(f"  Helix Angle: {helix_angle}")
    print(f"  Pitch Diameter: {pitch_diameter:.3f}")
    print(f"  Eval Range: {eval_start:.2f} - {eval_end:.2f} mm")
    
    right_data = flank_data.get('right', {})
    if right_data:
        sorted_teeth = sorted(right_data.keys())[:5]
        
        print(f"\nRight Helix - First 5 Teeth Raw Data Stats:")
        for tooth_id in sorted_teeth:
            tooth_values = right_data[tooth_id]
            if tooth_values is None:
                continue
            
            values = np.array(tooth_values, dtype=float)
            
            print(f"\n  Tooth {tooth_id}:")
            print(f"    Points: {len(values)}")
            print(f"    Mean: {np.mean(values):.4f}")
            print(f"    Std: {np.std(values):.4f}")
            print(f"    Range: {np.max(values) - np.min(values):.4f}")
            print(f"    Min: {np.min(values):.4f}, Max: {np.max(values):.4f}")
            
            n = len(values)
            x = np.arange(n)
            
            for order in [1, 2, 3, 4, 5]:
                x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
                coeffs = np.polyfit(x_norm, values, order)
                trend = np.polyval(coeffs, x_norm)
                residual = values - trend
                residual_std = np.std(residual)
                print(f"    Order {order} residual std: {residual_std:.4f}")


def test_different_preprocessing(mka_file, sample_name, klingelnberg_ref):
    """测试不同预处理方法的效果"""
    print(f"\n{'='*90}")
    print(f"Testing Different Preprocessing: {sample_name}")
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
    
    if 'right_helix' not in klingelnberg_ref:
        return
    
    ref = klingelnberg_ref['right_helix']
    
    print(f"\nRight Helix - Testing different preprocessing orders:")
    
    for preprocess_order in [0, 1, 2, 3, 4, 5, 6]:
        all_angles = []
        all_values = []
        
        sorted_teeth = sorted(right_data.keys())
        
        for tooth_id in sorted_teeth:
            tooth_values = right_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            actual_points = len(tooth_values)
            eval_values = np.array(tooth_values, dtype=float)
            
            if preprocess_order > 0:
                n = len(eval_values)
                x = np.arange(n)
                x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
                coeffs = np.polyfit(x_norm, eval_values, preprocess_order)
                trend = np.polyval(coeffs, x_norm)
                corrected_values = eval_values - trend
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
            angles = tau + delta_phi
            
            all_angles.extend(angles.tolist())
            all_values.extend(corrected_values.tolist())
        
        if not all_angles:
            continue
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        
        all_angles = all_angles % 360.0
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        
        unique_angles, unique_indices = np.unique(np.round(all_angles, 4), return_index=True)
        unique_values = all_values[unique_indices]
        
        num_points = max(2048, 10 * teeth_count)
        interp_angles = np.linspace(0, 360, num_points, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        angles_rad = np.radians(interp_angles)
        
        errors = []
        for order in sorted(ref.keys()):
            cos_term = np.cos(order * angles_rad)
            sin_term = np.sin(order * angles_rad)
            
            A = np.column_stack([cos_term, sin_term])
            coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
            
            a, b = coeffs[0], coeffs[1]
            amplitude = np.sqrt(a**2 + b**2)
            
            ref_amp = ref[order]
            error = abs(amplitude - ref_amp) / ref_amp * 100
            errors.append(error)
        
        avg_error = np.mean(errors)
        print(f"  Order {preprocess_order}: Avg Error = {avg_error:.1f}%")


def test_no_preprocessing_helix(mka_file, sample_name, klingelnberg_ref):
    """测试不进行预处理的效果（仅去均值）"""
    print(f"\n{'='*90}")
    print(f"Testing No Polynomial Preprocessing: {sample_name}")
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
        
        all_angles = []
        all_values = []
        
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
                angles = tau - delta_phi
            else:
                angles = tau + delta_phi
            
            all_angles.extend(angles.tolist())
            all_values.extend(corrected_values.tolist())
        
        if not all_angles:
            continue
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        
        all_angles = all_angles % 360.0
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        
        unique_angles, unique_indices = np.unique(np.round(all_angles, 4), return_index=True)
        unique_values = all_values[unique_indices]
        
        num_points = max(2048, 10 * teeth_count)
        interp_angles = np.linspace(0, 360, num_points, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        angles_rad = np.radians(interp_angles)
        
        print(f"\n{side_name} (Mean removal only):")
        print(f"  {'Order':<8} {'Ours':<12} {'Klingelnberg':<12} {'Error':<10}")
        
        errors = []
        for order in sorted(ref.keys()):
            cos_term = np.cos(order * angles_rad)
            sin_term = np.sin(order * angles_rad)
            
            A = np.column_stack([cos_term, sin_term])
            coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
            
            a, b = coeffs[0], coeffs[1]
            amplitude = np.sqrt(a**2 + b**2)
            
            ref_amp = ref[order]
            error = abs(amplitude - ref_amp) / ref_amp * 100
            errors.append(error)
            print(f"  {order:<8.0f} {amplitude:<12.4f} {ref_amp:<12.4f} {error:<10.1f}%")
        
        print(f"  Average Error: {np.mean(errors):.1f}%")


def main():
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE2 = {
        'right_helix': {26: 0.03, 52: 0.06, 78: 0.03, 141: 0.03, 156: 0.02},
        'left_helix': {26: 0.07, 48: 0.03, 52: 0.08, 78: 0.04, 104: 0.03, 130: 0.02, 141: 0.04, 182: 0.02}
    }
    
    analyze_raw_data_characteristics(sample2_file, "Sample2 (ZE=26)")
    
    test_different_preprocessing(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)
    
    test_no_preprocessing_helix(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)


if __name__ == "__main__":
    main()
