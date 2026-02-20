"""
步骤1：确认Klingelnberg参考值单位并统一
对比两个样本的数据单位和参考值
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


def analyze_unit_consistency(mka_file, sample_name, klingelnberg_ref):
    """分析单位一致性"""
    print(f"\n{'='*90}")
    print(f"Unit Consistency Analysis: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    
    print(f"\nGear: Teeth={teeth_count}, Module={module}")
    
    # 检查原始数据范围
    for side in ['right', 'left']:
        side_data = profile_data.get(side, {})
        direction = f'{side}_profile'
        
        if direction not in klingelnberg_ref:
            continue
        
        ref = klingelnberg_ref[direction]
        
        if not side_data:
            continue
        
        all_values = []
        for tooth_id in sorted(side_data.keys()):
            tooth_values = side_data[tooth_id]
            if tooth_values is None:
                continue
            values = np.array(tooth_values, dtype=float)
            all_values.extend(values.tolist())
        
        all_values = np.array(all_values)
        
        print(f"\n{side.upper()} Profile:")
        print(f"  Raw Data:")
        print(f"    Mean: {np.mean(all_values):.4f}")
        print(f"    Std: {np.std(all_values):.4f}")
        print(f"    Range: {np.max(all_values) - np.min(all_values):.4f}")
        
        # Klingelnberg参考值
        ref_values = list(ref.values())
        print(f"  Klingelnberg Reference:")
        print(f"    Values: {ref_values}")
        print(f"    Mean: {np.mean(ref_values):.4f}")
        print(f"    Max: {np.max(ref_values):.4f}")
        
        # 计算振幅比例
        pressure_angle = gear_data.get('pressure_angle', 20.0)
        pitch_diameter = module * teeth_count
        pitch_radius = pitch_diameter / 2.0
        base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
        base_radius = base_diameter / 2.0
        pitch_angle = 360.0 / teeth_count
        
        all_angles = []
        all_preprocessed = []
        
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
            all_preprocessed.extend(corrected_values.tolist())
        
        all_angles = np.array(all_angles)
        all_preprocessed = np.array(all_preprocessed)
        
        all_angles = all_angles % 360.0
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_preprocessed = all_preprocessed[sort_idx]
        
        unique_angles, unique_indices = np.unique(np.round(all_angles, 4), return_index=True)
        unique_values = all_preprocessed[unique_indices]
        
        num_points = 1024
        interp_angles = np.linspace(0, 360, num_points, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        theta = np.radians(interp_angles)
        
        # 计算ZE阶次振幅
        order = teeth_count
        cos_x = np.cos(order * theta)
        sin_x = np.sin(order * theta)
        A = np.column_stack((cos_x, sin_x))
        coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
        a, b = coeffs
        our_amplitude = np.sqrt(a*a + b*b)
        
        ref_amplitude = ref.get(teeth_count, 0)
        
        print(f"\n  Amplitude Comparison (Order {teeth_count}):")
        print(f"    Our amplitude: {our_amplitude:.4f}")
        print(f"    Klingelnberg: {ref_amplitude:.4f}")
        
        if ref_amplitude > 0:
            ratio = our_amplitude / ref_amplitude
            print(f"    Ratio (ours/ref): {ratio:.2f}")
            
            # 判断单位
            if ratio > 5:
                print(f"    -> Data is likely in um, Klingelnberg in mm (need to divide by 1000)")
                scale_factor = 0.001
            elif ratio < 0.2:
                print(f"    -> Data is likely in mm, Klingelnberg in um (need to multiply by 1000)")
                scale_factor = 1000
            else:
                print(f"    -> Same unit, scale factor ~1")
                scale_factor = 1.0
            
            scaled_amplitude = our_amplitude * scale_factor
            print(f"    Scaled amplitude: {scaled_amplitude:.4f}")
            print(f"    Error after scaling: {abs(scaled_amplitude - ref_amplitude) / ref_amplitude * 100:.1f}%")


def main():
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE1 = {
        'left_profile': {87: 0.1400, 174: 0.0500, 261: 0.0600, 348: 0.0300, 435: 0.0400},
        'right_profile': {87: 0.1500, 174: 0.0500, 261: 0.0600, 348: 0.0700, 435: 0.0300},
    }
    
    KLINGELNBERG_SAMPLE2 = {
        'right_profile': {26: 0.19, 52: 0.07, 78: 0.10, 104: 0.05, 130: 0.05, 156: 0.06, 182: 0.08},
        'left_profile': {22: 0.03, 26: 0.24, 44: 0.04, 52: 0.19, 78: 0.09, 104: 0.16, 130: 0.09, 156: 0.06, 182: 0.08},
    }
    
    analyze_unit_consistency(sample1_file, "Sample1 (ZE=87)", KLINGELNBERG_SAMPLE1)
    analyze_unit_consistency(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)


if __name__ == "__main__":
    main()
