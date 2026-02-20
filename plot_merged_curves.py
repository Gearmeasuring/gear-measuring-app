"""
可视化旋转角合并的齿形和齿向曲线
"""
import os
import sys
import numpy as np
import math
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def calculate_involute_angle(base_radius, radius):
    """计算渐开线极角"""
    if radius <= base_radius or base_radius <= 0:
        return 0.0
    cos_alpha = base_radius / radius
    if cos_alpha >= 1.0:
        return 0.0
    alpha = math.acos(cos_alpha)
    return math.degrees(math.tan(alpha) - alpha)


def preprocess_tooth_data(values):
    """预处理：去除鼓形和斜率偏差"""
    if len(values) < 5:
        return values - np.mean(values)
    
    n = len(values)
    x = np.arange(n)
    x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
    
    coeffs2 = np.polyfit(x_norm, values, 2)
    trend2 = np.polyval(coeffs2, x_norm)
    residual1 = values - trend2
    
    coeffs1 = np.polyfit(x_norm, residual1, 1)
    trend1 = np.polyval(coeffs1, x_norm)
    residual2 = residual1 - trend1
    
    return residual2


def build_profile_merged_curve(gear_data, profile_data, side):
    """构建齿形合并曲线"""
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    
    pitch_diameter = module * teeth_count
    pitch_radius = pitch_diameter / 2.0
    pitch_angle = 360.0 / teeth_count
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
    base_radius = base_diameter / 2.0
    
    side_data = profile_data.get(side, {})
    if not side_data:
        return None, None, None
    
    sorted_teeth = sorted(side_data.keys())
    
    all_angles = []
    all_values = []
    tooth_boundaries = []
    
    eval_start = gear_data.get('profile_eval_start', 0)
    eval_end = gear_data.get('profile_eval_end', 0)
    meas_start = gear_data.get('profile_meas_start', 0)
    meas_end = gear_data.get('profile_meas_end', 0)
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
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
        
        if eval_points < 5:
            continue
        
        corrected_values = preprocess_tooth_data(eval_values)
        
        tooth_index = int(tooth_id) - 1
        tau = tooth_index * pitch_angle
        
        if eval_start > 0 and eval_end > 0:
            radii = np.linspace(eval_start/2, eval_end/2, eval_points)
        else:
            radii = np.linspace(pitch_radius * 0.95, pitch_radius * 1.05, eval_points)
        
        xi_angles = np.array([calculate_involute_angle(base_radius, r) for r in radii])
        
        if side == 'left':
            angles = tau - xi_angles
        else:
            angles = tau + xi_angles
        
        tooth_boundaries.append((angles[0], angles[-1], tooth_id))
        
        all_angles.extend(angles.tolist())
        all_values.extend(corrected_values.tolist())
    
    if not all_angles:
        return None, None, None
    
    all_angles = np.array(all_angles)
    all_values = np.array(all_values)
    
    all_angles = all_angles % 360.0
    sort_idx = np.argsort(all_angles)
    
    return all_angles[sort_idx], all_values[sort_idx], tooth_boundaries


def build_helix_merged_curve(gear_data, flank_data, side):
    """构建齿向合并曲线"""
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    helix_angle = gear_data.get('helix_angle', 0.0)
    
    pitch_diameter = module * teeth_count
    pitch_angle = 360.0 / teeth_count
    
    side_data = flank_data.get(side, {})
    if not side_data:
        return None, None, None
    
    sorted_teeth = sorted(side_data.keys())
    
    all_angles = []
    all_values = []
    tooth_boundaries = []
    
    eval_start = gear_data.get('helix_eval_start', 0)
    eval_end = gear_data.get('helix_eval_end', 0)
    eval_center = (eval_start + eval_end) / 2.0
    tan_beta0 = math.tan(math.radians(helix_angle)) if abs(helix_angle) > 0.01 else 0
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        actual_points = len(tooth_values)
        eval_values = np.array(tooth_values, dtype=float)
        
        corrected_values = preprocess_tooth_data(eval_values)
        
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
        
        tooth_boundaries.append((angles[0], angles[-1], tooth_id))
        
        all_angles.extend(angles.tolist())
        all_values.extend(corrected_values.tolist())
    
    if not all_angles:
        return None, None, None
    
    all_angles = np.array(all_angles)
    all_values = np.array(all_values)
    
    all_angles = all_angles % 360.0
    sort_idx = np.argsort(all_angles)
    
    return all_angles[sort_idx], all_values[sort_idx], tooth_boundaries


def plot_merged_curves(mka_file, sample_name):
    """绘制合并曲线"""
    print(f"\n{'='*90}")
    print(f"Plotting Merged Curves: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    helix_angle = gear_data.get('helix_angle', 0.0)
    
    print(f"\nGear: Teeth={teeth_count}, Module={module}, Helix={helix_angle}")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'{sample_name} - Merged Curves', fontsize=14)
    
    colors = plt.cm.tab20(np.linspace(0, 1, teeth_count))
    
    for idx, (side, ax_row) in enumerate(zip(['right', 'left'], axes)):
        for col, (data_type, ax) in enumerate(zip(['profile', 'helix'], ax_row)):
            if data_type == 'profile':
                angles, values, boundaries = build_profile_merged_curve(gear_data, profile_data, side)
                title = f'{side.capitalize()} Profile (Involute)'
                xlabel = 'Rotation Angle (degrees)'
            else:
                angles, values, boundaries = build_helix_merged_curve(gear_data, flank_data, side)
                title = f'{side.capitalize()} Helix (Spiral)'
                xlabel = 'Rotation Angle (degrees)'
            
            if angles is None:
                ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(title)
                continue
            
            ax.plot(angles, values, 'b-', linewidth=0.5, alpha=0.7)
            
            for i, (start, end, tooth_id) in enumerate(boundaries[:min(10, len(boundaries))]):
                color_idx = int(tooth_id) - 1
                ax.axvline(x=start % 360, color=colors[color_idx % 20], linestyle='--', alpha=0.3, linewidth=0.5)
                ax.axvline(x=end % 360, color=colors[color_idx % 20], linestyle='--', alpha=0.3, linewidth=0.5)
            
            ax.set_xlabel(xlabel)
            ax.set_ylabel('Deviation (um)')
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0, 360)
            
            print(f"\n{title}:")
            print(f"  Points: {len(angles)}")
            print(f"  Angle range: {np.min(angles):.1f} - {np.max(angles):.1f} deg")
            print(f"  Value range: {np.min(values):.4f} - {np.max(values):.4f} um")
            print(f"  Value std: {np.std(values):.4f} um")
    
    plt.tight_layout()
    
    output_file = mka_file.replace('.mka', '_merged_curves.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nSaved: {output_file}")
    
    plt.show()
    
    return output_file


def main():
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    plot_merged_curves(sample1_file, "Sample1 (ZE=87)")
    plot_merged_curves(sample2_file, "Sample2 (ZE=26)")


if __name__ == "__main__":
    main()
