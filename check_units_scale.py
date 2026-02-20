"""
检查Klingelnberg参考数据的单位问题
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


def check_data_units_and_scale(mka_file, sample_name, klingelnberg_ref):
    """检查数据单位和缩放"""
    print(f"\n{'='*90}")
    print(f"Check Data Units and Scale: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    
    teeth_count = gear_data.get('teeth', 26)
    module = gear_data.get('module', 1.44)
    
    print(f"\nGear: Teeth={teeth_count}, Module={module}")
    
    # 检查原始数据范围
    side = 'right'
    side_data = profile_data.get(side, {})
    direction = f'{side}_profile'
    ref = klingelnberg_ref[direction]
    
    if side_data:
        all_values = []
        for tooth_id in sorted(side_data.keys()):
            tooth_values = side_data[tooth_id]
            if tooth_values is None:
                continue
            values = np.array(tooth_values, dtype=float)
            all_values.extend(values.tolist())
        
        all_values = np.array(all_values)
        
        print(f"\nRaw Data Statistics:")
        print(f"  Mean: {np.mean(all_values):.4f}")
        print(f"  Std: {np.std(all_values):.4f}")
        print(f"  Range: {np.max(all_values) - np.min(all_values):.4f}")
        print(f"  Min: {np.min(all_values):.4f}")
        print(f"  Max: {np.max(all_values):.4f}")
        
        # 检查单位
        print(f"\nUnit Analysis:")
        if np.std(all_values) > 1:
            print(f"  Data appears to be in micrometers (um)")
            print(f"  Typical profile deviation: 1-10 um")
        else:
            print(f"  Data appears to be in millimeters (mm)")
            print(f"  Typical profile deviation: 0.001-0.01 mm")
        
        # 检查Klingelnberg参考数据的单位
        print(f"\nKlingelnberg Reference Data:")
        print(f"  Order 26: {ref[26]:.4f}")
        
        # 如果数据是um，Klingelnberg参考值也应该是um
        # 如果数据是mm，需要转换
        
        # 计算我们算法得到的振幅
        pressure_angle = gear_data.get('pressure_angle', 17.0)
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
            
            # 预处理
            x = np.arange(n)
            x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
            coeffs = np.polyfit(x_norm, values, 2)
            trend = np.polyval(coeffs, x_norm)
            residual1 = values - trend
            coeffs2 = np.polyfit(x_norm, residual1, 1)
            trend2 = np.polyval(coeffs2, x_norm)
            corrected_values = residual1 - trend2
            
            # 计算渐开线极角
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
            all_preprocessed.extend(corrected_values.tolist())
        
        all_angles = np.array(all_angles)
        all_preprocessed = np.array(all_preprocessed)
        
        print(f"\nPreprocessed Data Statistics:")
        print(f"  Mean: {np.mean(all_preprocessed):.4f}")
        print(f"  Std: {np.std(all_preprocessed):.4f}")
        print(f"  Range: {np.max(all_preprocessed) - np.min(all_preprocessed):.4f}")
        
        # 计算频谱
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
        
        # 计算ZE阶次的振幅
        order = teeth_count
        cos_x = np.cos(order * theta)
        sin_x = np.sin(order * theta)
        A = np.column_stack((cos_x, sin_x))
        coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
        a, b = coeffs
        our_amplitude = np.sqrt(a*a + b*b)
        
        ref_amplitude = ref[teeth_count]
        
        print(f"\nAmplitude Comparison (Order {teeth_count}):")
        print(f"  Our amplitude: {our_amplitude:.4f}")
        print(f"  Klingelnberg: {ref_amplitude:.4f}")
        print(f"  Ratio: {our_amplitude / ref_amplitude:.2f}")
        
        # 测试不同的单位转换
        print(f"\nUnit Conversion Tests:")
        print(f"  If data is um and Klingelnberg is um: ratio = {our_amplitude / ref_amplitude:.2f}")
        print(f"  If data is mm and Klingelnberg is um: ratio = {our_amplitude * 1000 / ref_amplitude:.2f}")
        print(f"  If data is um and Klingelnberg is mm: ratio = {our_amplitude / (ref_amplitude * 1000):.4f}")


def main():
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    KLINGELNBERG_SAMPLE2 = {
        'right_profile': {26: 0.19, 52: 0.07, 78: 0.10, 104: 0.05, 130: 0.05, 156: 0.06, 182: 0.08},
    }
    
    check_data_units_and_scale(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)


if __name__ == "__main__":
    main()
