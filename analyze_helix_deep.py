"""
深入分析齿向数据的问题
寻找正确的缩放因子
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


def analyze_helix_data(mka_file, sample_name, klingelnberg_ref):
    """深入分析齿向数据"""
    print(f"\n{'='*90}")
    print(f"Deep Analysis of Helix Data: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 18.6)
    helix_angle = gear_data.get('helix_angle', 25.3)
    
    pitch_diameter = module * teeth_count
    pitch_radius = pitch_diameter / 2.0
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
    base_radius = base_diameter / 2.0
    base_pitch = math.pi * base_diameter / teeth_count
    
    helix_angle_base = math.degrees(math.atan(
        math.tan(math.radians(helix_angle)) * math.cos(math.radians(pressure_angle))
    ))
    
    print(f"\nGear: Teeth={teeth_count}, Module={module}, Helix={helix_angle}°")
    print(f"Base Pitch pb = {base_pitch:.4f} mm")
    print(f"Base Helix Angle βb = {helix_angle_base:.2f}°")
    
    helix_eval_start = gear_data.get('helix_eval_start', 0)
    helix_eval_end = gear_data.get('helix_eval_end', 0)
    eval_center = (helix_eval_start + helix_eval_end) / 2.0
    
    for side in ['right', 'left']:
        side_data = flank_data.get(side, {})
        direction = f'{side}_helix'
        
        if direction not in klingelnberg_ref:
            continue
        
        ref = klingelnberg_ref[direction]
        
        print(f"\n{'='*60}")
        print(f"{side.upper()} Helix Analysis")
        print(f"{'='*60}")
        
        # 方法1：不使用角度合成，直接分析每个齿
        print(f"\nMethod 1: Per-Tooth Analysis (No Angle Synthesis)")
        
        all_spectra = {}
        for tooth_id in sorted(side_data.keys()):
            tooth_values = side_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            values = np.array(tooth_values, dtype=float)
            n = len(values)
            
            # 预处理
            x = np.arange(n)
            x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
            coeffs = np.polyfit(x_norm, values, 2)
            trend = np.polyval(coeffs, x_norm)
            corrected_values = values - trend
            
            # 直接FFT
            num_pts = 1024
            padded = np.zeros(num_pts)
            padded[:n] = corrected_values - np.mean(corrected_values)
            fft_result = np.fft.fft(padded)
            fft_amps = np.abs(fft_result) * 2 / num_pts
            
            for order in ref.keys():
                if order not in all_spectra:
                    all_spectra[order] = []
                if order < num_pts:
                    all_spectra[order].append(fft_amps[order])
        
        avg_spectrum = {order: np.mean(amps) for order, amps in all_spectra.items()}
        
        print(f"  Raw FFT Amplitudes:")
        for order in sorted(ref.keys()):
            print(f"    Order {order}: {avg_spectrum.get(order, 0):.4f}")
        
        # 方法2：使用角度合成
        print(f"\nMethod 2: With Angle Synthesis")
        
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
            corrected_values = values - trend
            
            axial_positions = np.linspace(helix_eval_start, helix_eval_end, n)
            delta_z = axial_positions - eval_center
            
            # 使用el=2.766计算角度
            el = 2.766
            delta_phi = (delta_z / (el * base_pitch)) * el * (360.0 / teeth_count)
            
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * 360.0 / teeth_count
            
            if side == 'left':
                angles = tau - delta_phi
            else:
                angles = tau + delta_phi
            
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
        for order in ref.keys():
            cos_x = np.cos(order * theta)
            sin_x = np.sin(order * theta)
            A = np.column_stack((cos_x, sin_x))
            coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
            a, b = coeffs
            amplitude = np.sqrt(a*a + b*b)
            spectrum_merged[order] = amplitude
        
        print(f"  Merged Curve Amplitudes:")
        for order in sorted(ref.keys()):
            print(f"    Order {order}: {spectrum_merged.get(order, 0):.4f}")
        
        # 寻找最佳缩放因子
        print(f"\nFinding Best Scale Factor:")
        
        best_scale = None
        best_error = float('inf')
        
        for scale in np.linspace(0.01, 2.0, 200):
            errors = []
            for order in ref.keys():
                our_amp = spectrum_merged.get(order, 0) * scale
                ref_amp = ref[order]
                error = abs(our_amp - ref_amp) / ref_amp * 100
                errors.append(error)
            avg_error = np.mean(errors)
            if avg_error < best_error:
                best_error = avg_error
                best_scale = scale
        
        print(f"  Best scale: {best_scale:.4f}")
        print(f"  Best error: {best_error:.1f}%")
        
        # 显示结果
        print(f"\n  Results with best scale ({best_scale:.4f}):")
        print(f"    {'Order':<8} {'Ours':<12} {'Klingelnberg':<12} {'Error':<10}")
        for order in sorted(ref.keys()):
            our_amp = spectrum_merged.get(order, 0) * best_scale
            ref_amp = ref[order]
            error = abs(our_amp - ref_amp) / ref_amp * 100
            print(f"    {order:<8} {our_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}%")


def main():
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    KLINGELNBERG_SAMPLE1 = {
        'right_helix': {87: 0.0900, 174: 0.1000, 261: 0.0500, 348: 0.0400, 435: 0.0300},
        'left_helix': {87: 0.1200, 89: 0.0700, 174: 0.0600, 261: 0.0500, 348: 0.0300}
    }
    
    analyze_helix_data(sample1_file, "Sample1 (ZE=87)", KLINGELNBERG_SAMPLE1)


if __name__ == "__main__":
    main()
