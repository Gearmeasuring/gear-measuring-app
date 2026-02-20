"""
检查数据单位和缩放问题
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


def check_data_units(mka_file, sample_name):
    """检查数据单位"""
    print(f"\n{'='*90}")
    print(f"Check Data Units: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    
    teeth_count = gear_data.get('teeth', 26)
    module = gear_data.get('module', 1.44)
    
    print(f"\nGear: Teeth={teeth_count}, Module={module}")
    
    side = 'right'
    side_data = profile_data.get(side, {})
    
    if side_data:
        sorted_teeth = sorted(side_data.keys())
        
        print(f"\nRaw Data Statistics (first 3 teeth):")
        for tooth_id in sorted_teeth[:3]:
            tooth_values = side_data[tooth_id]
            if tooth_values is None:
                continue
            
            values = np.array(tooth_values, dtype=float)
            print(f"  Tooth {tooth_id}:")
            print(f"    Mean: {np.mean(values):.4f}")
            print(f"    Std: {np.std(values):.4f}")
            print(f"    Range: {np.max(values) - np.min(values):.4f}")
            print(f"    Min: {np.min(values):.4f}, Max: {np.max(values):.4f}")
    
    # 检查是否需要单位转换
    print(f"\nUnit Analysis:")
    print(f"  If data is in mm, typical deviation range is 0.001-0.01 mm (1-10 μm)")
    print(f"  If data is in μm, typical deviation range is 1-10 μm")
    
    if side_data:
        tooth_id = sorted_teeth[0]
        values = np.array(side_data[tooth_id], dtype=float)
        data_range = np.max(values) - np.min(values)
        
        print(f"\n  Actual data range: {data_range:.4f}")
        
        if data_range > 1:
            print(f"  -> Data appears to be in μm (range > 1)")
        else:
            print(f"  -> Data appears to be in mm (range < 1)")
    
    # 检查振幅计算
    print(f"\nAmplitude Calculation Analysis:")
    print(f"  For merged curve method:")
    print(f"    - Total points: 12480 (26 teeth × 480 points)")
    print(f"    - Angle range: 0-360 degrees")
    print(f"    - Each tooth covers ~5 degrees of involute angle")
    print(f"    - Teeth are separated by {360/teeth_count:.1f} degrees")
    
    print(f"\n  Possible issues:")
    print(f"    1. Angle gaps between teeth may cause spectral leakage")
    print(f"    2. Polynomial preprocessing may affect amplitude")
    print(f"    3. Need to verify if amplitude should be divided by sqrt(2)")


def test_amplitude_scaling(mka_file, sample_name, klingelnberg_ref):
    """测试振幅缩放"""
    print(f"\n{'='*90}")
    print(f"Test Amplitude Scaling: {sample_name}")
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
        angles = tau + xi_angles
        
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
    
    # 计算原始振幅
    order = 26
    cos_x = np.cos(order * theta)
    sin_x = np.sin(order * theta)
    A = np.column_stack((cos_x, sin_x))
    coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
    a, b = coeffs
    raw_amplitude = np.sqrt(a*a + b*b)
    
    ref_amp = ref[order]
    
    print(f"\n  Order {order}:")
    print(f"    Raw amplitude: {raw_amplitude:.4f}")
    print(f"    Klingelnberg: {ref_amp:.4f}")
    print(f"    Ratio: {raw_amplitude / ref_amp:.2f}")
    
    # 测试不同的缩放因子
    print(f"\n  Testing scaling factors:")
    for factor in [1, 2, np.sqrt(2), teeth_count, np.sqrt(teeth_count), num_points/360]:
        scaled = raw_amplitude / factor
        error = abs(scaled - ref_amp) / ref_amp * 100
        print(f"    Divide by {factor:.2f}: {scaled:.4f} (error: {error:.1f}%)")


def main():
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE2 = {
        'right_profile': {26: 0.19, 52: 0.07, 78: 0.10, 104: 0.05, 130: 0.05, 156: 0.06, 182: 0.08},
    }
    
    check_data_units(sample2_file, "Sample2 (ZE=26)")
    test_amplitude_scaling(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)


if __name__ == "__main__":
    main()
