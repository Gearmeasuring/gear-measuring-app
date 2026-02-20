"""
调试脚本 - 检查数据结构和阶次计算
"""
import os
import sys
import numpy as np
import math
from scipy import signal, interpolate

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file

def main():
    mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    print("解析MKA文件...")
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    print(f"\n齿轮数据:")
    for key, value in gear_data.items():
        print(f"  {key}: {value}")
    
    print(f"\nProfile数据结构:")
    print(f"  左侧齿数: {list(profile_data.get('left', {}).keys())[:5]}...")
    print(f"  右侧齿数: {list(profile_data.get('right', {}).keys())[:5]}...")
    
    if profile_data.get('left'):
        first_tooth = list(profile_data['left'].keys())[0]
        first_data = profile_data['left'][first_tooth]
        print(f"  左侧第一齿数据点数: {len(first_data)}")
        print(f"  数据样本: {first_data[:5]}...")
    
    print(f"\nFlank数据结构:")
    print(f"  左侧齿数: {list(flank_data.get('left', {}).keys())[:5]}...")
    print(f"  右侧齿数: {list(flank_data.get('right', {}).keys())[:5]}...")
    
    if flank_data.get('left'):
        first_tooth = list(flank_data['left'].keys())[0]
        first_data = flank_data['left'][first_tooth]
        print(f"  左侧第一齿数据点数: {len(first_data)}")
        print(f"  数据样本: {first_data[:5]}...")
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 0.0)
    base_diameter = gear_data.get('base_diameter', 0.0)
    
    pitch_diameter = module * teeth_count
    pitch_radius = pitch_diameter / 2.0
    pitch_angle = 360.0 / teeth_count
    
    if base_diameter > 0:
        base_radius = base_diameter / 2.0
    else:
        base_radius = pitch_diameter * math.cos(math.radians(pressure_angle)) / 2.0
    
    print(f"\n计算参数:")
    print(f"  节圆直径: {pitch_diameter:.3f}")
    print(f"  节圆半径: {pitch_radius:.3f}")
    print(f"  基圆半径: {base_radius:.3f}")
    print(f"  节距角: {pitch_angle:.4f}°")
    
    def calculate_involute_angle(radius):
        if radius <= base_radius or base_radius <= 0:
            return 0.0
        cos_alpha = base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        alpha = math.acos(cos_alpha)
        return math.tan(alpha) - alpha
    
    print("\n测试Profile合并曲线...")
    
    eval_start = gear_data.get('profile_eval_start', 0)
    eval_end = gear_data.get('profile_eval_end', 0)
    meas_start = gear_data.get('profile_meas_start', 0)
    meas_end = gear_data.get('profile_meas_end', 0)
    
    print(f"  eval_start: {eval_start}, eval_end: {eval_end}")
    print(f"  meas_start: {meas_start}, meas_end: {meas_end}")
    
    all_angles = []
    all_values = []
    
    left_profile = profile_data.get('left', {})
    sorted_teeth = sorted(left_profile.keys())
    
    for tooth_id in sorted_teeth[:3]:
        tooth_values = left_profile[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        actual_points = len(tooth_values)
        
        if meas_end > meas_start and eval_end > eval_start:
            eval_start_ratio = (eval_start - meas_start) / (meas_end - meas_start)
            eval_end_ratio = (eval_end - meas_start) / (meas_end - meas_start)
            start_idx = int(actual_points * max(0.0, min(1.0, eval_start_ratio)))
            end_idx = int(actual_points * max(0.0, min(1.0, eval_end_ratio)))
        else:
            start_idx = 0
            end_idx = actual_points
        
        eval_values = np.array(tooth_values[start_idx:end_idx], dtype=float)
        eval_points = len(eval_values)
        
        print(f"\n  齿 {tooth_id}:")
        print(f"    原始点数: {actual_points}, 评估点数: {eval_points}")
        print(f"    数据范围: [{eval_values.min():.3f}, {eval_values.max():.3f}]")
        
        x = np.arange(eval_points)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        coeffs = np.polyfit(x_norm, eval_values, 2)
        trend = np.polyval(coeffs, x_norm)
        corrected_values = eval_values - trend
        
        print(f"    预处理后范围: [{corrected_values.min():.3f}, {corrected_values.max():.3f}]")
        
        tooth_index = int(tooth_id) - 1 if str(tooth_id).isdigit() else 0
        tau = tooth_index * pitch_angle
        
        if eval_start > 0 and eval_end > 0:
            radii = np.linspace(eval_start/2, eval_end/2, eval_points)
        else:
            radii = np.linspace(pitch_radius * 0.95, pitch_radius * 1.05, eval_points)
        
        xi_angles = np.array([math.degrees(calculate_involute_angle(r)) for r in radii])
        
        print(f"    tau = {tau:.2f}°, xi_angles范围: [{xi_angles.min():.2f}, {xi_angles.max():.2f}]")
        
        angles = tau - xi_angles
        
        print(f"    角度范围: [{angles.min():.2f}, {angles.max():.2f}]")
        
        all_angles.extend(angles.tolist())
        all_values.extend(corrected_values.tolist())
    
    if all_angles:
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        
        all_angles = all_angles % 360.0
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        
        print(f"\n合并曲线:")
        print(f"  总点数: {len(all_angles)}")
        print(f"  角度范围: [{all_angles.min():.2f}, {all_angles.max():.2f}]")
        print(f"  值范围: [{all_values.min():.3f}, {all_values.max():.3f}]")
        
        unique_angles, unique_idx = np.unique(np.round(all_angles, 3), return_index=True)
        unique_values = all_values[unique_idx]
        
        print(f"  唯一角度点数: {len(unique_angles)}")
        
        interp_angles = np.linspace(0, 360, 1024, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        print(f"\n插值后:")
        print(f"  点数: {len(interp_angles)}")
        print(f"  值范围: [{interp_values.min():.3f}, {interp_values.max():.3f}]")
        
        b, a = signal.butter(4, 0.2, btype='low')
        filtered = signal.filtfilt(b, a, interp_values)
        
        print(f"\n滤波后:")
        print(f"  值范围: [{filtered.min():.3f}, {filtered.max():.3f}]")
        
        angles_rad = np.radians(interp_angles)
        residual = filtered.copy()
        
        print(f"\n迭代分解测试:")
        for i in range(5):
            best_order = 0
            best_amplitude = 0
            best_phase = 0
            
            for order in range(1, 5 * teeth_count + 1):
                cos_term = np.cos(order * angles_rad)
                sin_term = np.sin(order * angles_rad)
                
                A = np.column_stack([cos_term, sin_term])
                coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
                
                a, b = coeffs[0], coeffs[1]
                amplitude = np.sqrt(a**2 + b**2)
                
                if amplitude > best_amplitude:
                    best_amplitude = amplitude
                    best_order = order
                    best_phase = np.degrees(np.arctan2(a, b))
            
            print(f"  #{i+1}: 阶次={best_order}, 振幅={best_amplitude:.4f}")
            
            cos_term = np.cos(best_order * angles_rad)
            sin_term = np.sin(best_order * angles_rad)
            A = np.column_stack([cos_term, sin_term])
            coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
            fitted = coeffs[0] * cos_term + coeffs[1] * sin_term
            residual = residual - fitted

if __name__ == "__main__":
    main()
