"""
按PDF参数合并曲线并可视化
PDF参数：
- ep = 1.454
- el = 2.766
- lo = 33.578
- lu = 24.775
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


def preprocess_tooth_data(values, order=2):
    """预处理"""
    if len(values) < order + 1:
        return values - np.mean(values)
    
    n = len(values)
    x = np.arange(n)
    x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
    
    coeffs = np.polyfit(x_norm, values, order)
    trend = np.polyval(coeffs, x_norm)
    
    return values - trend


def build_profile_curve_with_ep(gear_data, profile_data, side, ep):
    """使用ep参数构建齿形合并曲线"""
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 18.6)
    
    pitch_diameter = module * teeth_count
    pitch_radius = pitch_diameter / 2.0
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
    base_radius = base_diameter / 2.0
    base_pitch = math.pi * base_diameter / teeth_count
    pitch_angle = 360.0 / teeth_count
    
    # 使用ep计算评价长度
    eval_length = ep * base_pitch
    print(f"  Profile eval length from ep: {eval_length:.3f} mm (ep={ep})")
    
    side_data = profile_data.get(side, {})
    if not side_data:
        return None, None
    
    sorted_teeth = sorted(side_data.keys())
    
    all_angles = []
    all_values = []
    tooth_boundaries = []
    
    eval_start = gear_data.get('profile_eval_start', 0)
    eval_end = gear_data.get('profile_eval_end', 0)
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        values = np.array(tooth_values, dtype=float)
        n = len(values)
        
        corrected_values = preprocess_tooth_data(values, order=2)
        
        tooth_index = int(tooth_id) - 1
        tau = tooth_index * pitch_angle
        
        if eval_start > 0 and eval_end > 0:
            radii = np.linspace(eval_start/2, eval_end/2, n)
        else:
            radii = np.linspace(pitch_radius * 0.95, pitch_radius * 1.05, n)
        
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


def build_helix_curve_with_el(gear_data, flank_data, side, el):
    """使用el参数构建齿向合并曲线"""
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 18.6)
    helix_angle = gear_data.get('helix_angle', 25.3)
    
    pitch_diameter = module * teeth_count
    base_diameter = pitch_diameter * math.cos(math.radians(pressure_angle))
    base_pitch = math.pi * base_diameter / teeth_count
    pitch_angle = 360.0 / teeth_count
    
    # 基圆螺旋角
    helix_angle_base = math.degrees(math.atan(
        math.tan(math.radians(helix_angle)) * math.cos(math.radians(pressure_angle))
    ))
    
    # 使用el计算等效评价长度
    eval_length = abs(el) * base_pitch
    print(f"  Helix eval length from el: {eval_length:.3f} mm (el={el})")
    
    side_data = flank_data.get(side, {})
    if not side_data:
        return None, None, None
    
    sorted_teeth = sorted(side_data.keys())
    
    all_angles = []
    all_values = []
    tooth_boundaries = []
    
    helix_eval_start = gear_data.get('helix_eval_start', 0)
    helix_eval_end = gear_data.get('helix_eval_end', 0)
    eval_center = (helix_eval_start + helix_eval_end) / 2.0
    
    for tooth_id in sorted_teeth:
        tooth_values = side_data[tooth_id]
        if tooth_values is None or len(tooth_values) == 0:
            continue
        
        values = np.array(tooth_values, dtype=float)
        n = len(values)
        
        corrected_values = preprocess_tooth_data(values, order=2)
        
        axial_positions = np.linspace(helix_eval_start, helix_eval_end, n)
        delta_z = axial_positions - eval_center
        
        # 使用el计算角度
        if abs(helix_angle_base) > 0.01:
            delta_phi = (delta_z / eval_length) * el * (360.0 / teeth_count)
        else:
            delta_phi = np.zeros(n)
        
        tooth_index = int(tooth_id) - 1
        tau = tooth_index * pitch_angle
        
        if side == 'left':
            angles = tau - delta_phi
        else:
            angles = tau + delta_phi
        
        tooth_boundaries.append((np.min(angles), np.max(angles), tooth_id))
        
        all_angles.extend(angles.tolist())
        all_values.extend(corrected_values.tolist())
    
    if not all_angles:
        return None, None, None
    
    all_angles = np.array(all_angles)
    all_values = np.array(all_values)
    
    all_angles = all_angles % 360.0
    sort_idx = np.argsort(all_angles)
    
    return all_angles[sort_idx], all_values[sort_idx], tooth_boundaries


def plot_merged_curves_with_pdf_params(mka_file, sample_name):
    """使用PDF参数绘制合并曲线"""
    print(f"\n{'='*90}")
    print(f"Plotting Merged Curves with PDF Parameters: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 18.6)
    helix_angle = gear_data.get('helix_angle', 25.3)
    
    # PDF参数
    ep = 1.454
    el = 2.766
    
    print(f"\nGear: Teeth={teeth_count}, Module={module}, Helix={helix_angle}°")
    print(f"PDF Parameters: ep={ep}, el={el}")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'{sample_name} - Merged Curves (PDF params: ep={ep}, el={el})', fontsize=14)
    
    colors = plt.cm.tab20(np.linspace(0, 1, teeth_count))
    
    for idx, (side, ax_row) in enumerate(zip(['right', 'left'], axes)):
        for col, (data_type, ax) in enumerate(zip(['profile', 'helix'], ax_row)):
            if data_type == 'profile':
                angles, values, boundaries = build_profile_curve_with_ep(gear_data, profile_data, side, ep)
                title = f'{side.capitalize()} Profile (ep={ep})'
            else:
                angles, values, boundaries = build_helix_curve_with_el(gear_data, flank_data, side, el)
                title = f'{side.capitalize()} Helix (el={el})'
            
            if angles is None:
                ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(title)
                continue
            
            ax.plot(angles, values, 'b-', linewidth=0.5, alpha=0.7)
            
            # 标记每个齿的边界
            for i, (start, end, tooth_id) in enumerate(boundaries[:min(10, len(boundaries))]):
                color_idx = int(tooth_id) - 1
                ax.axvline(x=start % 360, color=colors[color_idx % 20], linestyle='--', alpha=0.3, linewidth=0.5)
                ax.axvline(x=end % 360, color=colors[color_idx % 20], linestyle='--', alpha=0.3, linewidth=0.5)
            
            ax.set_xlabel('Rotation Angle (degrees)')
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
    
    output_file = mka_file.replace('.mka', '_pdf_merged_curves.png')
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nSaved: {output_file}")
    
    plt.show()
    
    return output_file


def main():
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    plot_merged_curves_with_pdf_params(sample1_file, "Sample1 (ZE=87)")


if __name__ == "__main__":
    main()
