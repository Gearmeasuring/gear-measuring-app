"""
分析齿形(Profile)和齿向(Helix)合并曲线的不同特性

关键区别：
1. 齿形(Profile):
   - 只测量渐开线的一段(评价范围)
   - 各齿之间有间隙是正常的
   - 角度范围有限(约1°左右)
   - 公式: φ = τ ± ξ

2. 齿向(Helix):
   - 测量整个齿宽
   - 应该覆盖完整的0-360°
   - 角度范围大(约12-25°)
   - 公式: φ = τ ± Δφ
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import math

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


class RippleAnalyzer:
    def __init__(self, teeth_count, module, pressure_angle=20.0, helix_angle=0.0, base_diameter=0.0):
        self.teeth_count = teeth_count
        self.module = module
        self.pressure_angle = pressure_angle
        self.helix_angle = helix_angle
        
        self.pitch_diameter = module * teeth_count
        self.pitch_radius = self.pitch_diameter / 2.0
        self.pitch_angle = 360.0 / teeth_count
        
        if base_diameter > 0:
            self.base_diameter = base_diameter
        else:
            self.base_diameter = self.pitch_diameter * math.cos(math.radians(pressure_angle))
        
        self.base_radius = self.base_diameter / 2.0
    
    def remove_slope_and_crowning(self, data):
        if len(data) < 3:
            return data
        data = np.array(data, dtype=float)
        n = len(data)
        x = np.arange(n, dtype=float)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        crowning_coeffs = np.polyfit(x_norm, data, 2)
        crowning_curve = np.polyval(crowning_coeffs, x_norm)
        data_after_crowning = data - crowning_curve
        
        slope_coeffs = np.polyfit(x_norm, data_after_crowning, 1)
        slope_curve = np.polyval(slope_coeffs, x_norm)
        corrected_data = data_after_crowning - slope_curve
        
        return corrected_data
    
    def calculate_involute_angle(self, radius):
        if radius <= self.base_radius or self.base_radius <= 0:
            return 0.0
        cos_alpha = self.base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        alpha = math.acos(cos_alpha)
        return math.tan(alpha) - alpha
    
    def analyze_tooth(self, tooth_values, tooth_id, data_type, side,
                      eval_start, eval_end, meas_start, meas_end):
        """分析单个齿的数据"""
        actual_points = len(tooth_values)
        
        # 计算评价范围索引
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
        
        if eval_points < 3:
            return None
        
        corrected_values = self.remove_slope_and_crowning(eval_values)
        
        tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
        tau = tooth_index * self.pitch_angle
        
        if data_type == 'profile':
            # 齿形
            if eval_start > 0 and eval_end > 0:
                radii = np.linspace(eval_start/2, eval_end/2, eval_points)
            else:
                radii = np.linspace(self.pitch_radius * 0.95, self.pitch_radius * 1.05, eval_points)
            
            xi_angles = np.array([math.degrees(self.calculate_involute_angle(r)) for r in radii])
            
            if side == 'left':
                angles = tau - xi_angles
            else:
                angles = tau + xi_angles
            
            angle_span = abs(angles.max() - angles.min())
            
        else:  # helix
            if abs(self.helix_angle) > 0.01 and self.pitch_diameter > 0:
                axial_positions = np.linspace(eval_start, eval_end, eval_points)
                eval_center = (eval_start + eval_end) / 2.0
                delta_z = axial_positions - eval_center
                tan_beta0 = math.tan(math.radians(self.helix_angle))
                delta_phi = np.degrees(2 * delta_z * tan_beta0 / self.pitch_diameter)
            else:
                delta_phi = np.linspace(0, 1, eval_points)
            
            if side == 'left':
                angles = tau - delta_phi
            else:
                angles = tau + delta_phi
            
            angle_span = abs(angles.max() - angles.min())
        
        return {
            'tooth_id': tooth_id,
            'tooth_index': tooth_index,
            'tau': tau,
            'angles': angles,
            'values': corrected_values,
            'angle_span': angle_span,
            'angle_min': angles.min(),
            'angle_max': angles.max()
        }


def main():
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    if not os.path.exists(mka_file):
        mka_file = os.path.join(current_dir, '004-xiaoxiao1.mka')
    
    print("="*70)
    print("齿形(Profile) vs 齿向(Helix) 合并曲线特性分析")
    print("="*70)
    print(f"文件: {mka_file}")
    print()
    
    parsed_data = parse_mka_file(mka_file)
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 0.0)
    base_diameter = gear_data.get('base_diameter', 0.0)
    
    analyzer = RippleAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    profile_eval_start = gear_data.get('profile_eval_start', 0)
    profile_eval_end = gear_data.get('profile_eval_end', 0)
    profile_meas_start = gear_data.get('profile_meas_start', 0)
    profile_meas_end = gear_data.get('profile_meas_end', 0)
    
    helix_eval_start = gear_data.get('helix_eval_start', 0)
    helix_eval_end = gear_data.get('helix_eval_end', 0)
    helix_meas_start = gear_data.get('helix_meas_start', 0)
    helix_meas_end = gear_data.get('helix_meas_end', 0)
    
    print(f"齿轮参数: ZE={teeth_count}, m={module}, β={helix_angle}°")
    print(f"节距角 τ = {analyzer.pitch_angle:.4f}°")
    print()
    
    # 分析前5个齿
    side = 'left'
    num_teeth_to_analyze = 5
    
    # 分析齿形
    print("="*70)
    print("齿形(Profile)分析")
    print("="*70)
    
    profile_side_data = profile_data.get(side, {})
    profile_teeth = sorted(profile_side_data.keys())[:num_teeth_to_analyze]
    
    profile_results = []
    for tooth_id in profile_teeth:
        tooth_values = profile_side_data[tooth_id]
        result = analyzer.analyze_tooth(
            tooth_values, tooth_id, 'profile', side,
            profile_eval_start, profile_eval_end,
            profile_meas_start, profile_meas_end
        )
        if result:
            profile_results.append(result)
            print(f"齿{tooth_id}: τ={result['tau']:.2f}°, "
                  f"φ=[{result['angle_min']:.2f}°, {result['angle_max']:.2f}°], "
                  f"跨度={result['angle_span']:.2f}°")
    
    # 分析齿向
    print()
    print("="*70)
    print("齿向(Helix)分析")
    print("="*70)
    
    helix_side_data = flank_data.get(side, {})
    helix_teeth = sorted(helix_side_data.keys())[:num_teeth_to_analyze]
    
    helix_results = []
    for tooth_id in helix_teeth:
        tooth_values = helix_side_data[tooth_id]
        result = analyzer.analyze_tooth(
            tooth_values, tooth_id, 'helix', side,
            helix_eval_start, helix_eval_end,
            helix_meas_start, helix_meas_end
        )
        if result:
            helix_results.append(result)
            print(f"齿{tooth_id}: τ={result['tau']:.2f}°, "
                  f"φ=[{result['angle_min']:.2f}°, {result['angle_max']:.2f}°], "
                  f"跨度={result['angle_span']:.2f}°")
    
    # 创建对比图
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.25)
    
    # 图1: 齿形 - 前5个齿的详细视图
    ax1 = fig.add_subplot(gs[0, 0])
    colors = plt.cm.tab10(np.linspace(0, 1, len(profile_results)))
    
    for idx, result in enumerate(profile_results):
        ax1.plot(result['angles'], result['values'], 
                color=colors[idx], linewidth=1.5, 
                label=f"Tooth {result['tooth_id']} (τ={result['tau']:.1f}°)")
    
    ax1.set_xlabel('Rotation Angle φ (deg)', fontsize=10)
    ax1.set_ylabel('Profile Deviation (μm)', fontsize=10)
    ax1.set_title('Profile: First 5 Teeth (With Gaps - Normal)', fontsize=11, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # 图2: 齿向 - 前5个齿的详细视图
    ax2 = fig.add_subplot(gs[0, 1])
    
    for idx, result in enumerate(helix_results):
        ax2.plot(result['angles'], result['values'], 
                color=colors[idx], linewidth=1.5,
                label=f"Tooth {result['tooth_id']} (τ={result['tau']:.1f}°)")
    
    ax2.set_xlabel('Rotation Angle φ (deg)', fontsize=10)
    ax2.set_ylabel('Helix Deviation (μm)', fontsize=10)
    ax2.set_title('Helix: First 5 Teeth (Continuous - Overlapping)', fontsize=11, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # 图3: 齿形 - 角度范围对比
    ax3 = fig.add_subplot(gs[1, 0])
    
    for idx, result in enumerate(profile_results):
        ax3.barh(idx, result['angle_span'], left=result['angle_min'], 
                alpha=0.7, color=colors[idx], edgecolor='black')
        ax3.plot(result['tau'], idx, 'ro', markersize=6)
    
    ax3.set_xlabel('Rotation Angle φ (deg)', fontsize=10)
    ax3.set_ylabel('Tooth Index', fontsize=10)
    ax3.set_title('Profile: Angle Range per Tooth (Small Span, With Gaps)', fontsize=11, fontweight='bold')
    ax3.set_yticks(range(len(profile_results)))
    ax3.set_yticklabels([f"Tooth {r['tooth_id']}" for r in profile_results])
    ax3.grid(True, alpha=0.3, axis='x')
    
    # 图4: 齿向 - 角度范围对比
    ax4 = fig.add_subplot(gs[1, 1])
    
    for idx, result in enumerate(helix_results):
        ax4.barh(idx, result['angle_span'], left=result['angle_min'], 
                alpha=0.7, color=colors[idx], edgecolor='black')
        ax4.plot(result['tau'], idx, 'ro', markersize=6)
    
    ax4.set_xlabel('Rotation Angle φ (deg)', fontsize=10)
    ax4.set_ylabel('Tooth Index', fontsize=10)
    ax4.set_title('Helix: Angle Range per Tooth (Large Span, Overlapping)', fontsize=11, fontweight='bold')
    ax4.set_yticks(range(len(helix_results)))
    ax4.set_yticklabels([f"Tooth {r['tooth_id']}" for r in helix_results])
    ax4.grid(True, alpha=0.3, axis='x')
    
    # 图5: 齿形 - 完整合并曲线
    ax5 = fig.add_subplot(gs[2, 0])
    
    all_profile_angles = []
    all_profile_values = []
    for result in profile_results:
        all_profile_angles.extend(result['angles'].tolist())
        all_profile_values.extend(result['values'].tolist())
    
    all_profile_angles = np.array(all_profile_angles)
    all_profile_values = np.array(all_profile_values)
    all_profile_angles = all_profile_angles % 360.0
    sort_idx = np.argsort(all_profile_angles)
    all_profile_angles = all_profile_angles[sort_idx]
    all_profile_values = all_profile_values[sort_idx]
    
    ax5.plot(all_profile_angles, all_profile_values, 'b-', linewidth=0.8, alpha=0.7)
    ax5.set_xlabel('Rotation Angle φ (deg)', fontsize=10)
    ax5.set_ylabel('Profile Deviation (μm)', fontsize=10)
    ax5.set_title('Profile: Merged Curve (Gaps between teeth are NORMAL)', fontsize=11, fontweight='bold')
    ax5.set_xlim(0, 360)
    ax5.grid(True, alpha=0.3)
    
    # 图6: 齿向 - 完整合并曲线
    ax6 = fig.add_subplot(gs[2, 1])
    
    all_helix_angles = []
    all_helix_values = []
    for result in helix_results:
        all_helix_angles.extend(result['angles'].tolist())
        all_helix_values.extend(result['values'].tolist())
    
    all_helix_angles = np.array(all_helix_angles)
    all_helix_values = np.array(all_helix_values)
    all_helix_angles = all_helix_angles % 360.0
    sort_idx = np.argsort(all_helix_angles)
    all_helix_angles = all_helix_angles[sort_idx]
    all_helix_values = all_helix_values[sort_idx]
    
    ax6.plot(all_helix_angles, all_helix_values, 'r-', linewidth=0.8, alpha=0.7)
    ax6.set_xlabel('Rotation Angle φ (deg)', fontsize=10)
    ax6.set_ylabel('Helix Deviation (μm)', fontsize=10)
    ax6.set_title('Helix: Merged Curve (Continuous coverage is EXPECTED)', fontsize=11, fontweight='bold')
    ax6.set_xlim(0, 360)
    ax6.grid(True, alpha=0.3)
    
    # 添加说明
    explanation = """
Key Differences:

Profile (Involute):
- Measures only a segment of the involute curve (evaluation range)
- Small angle span (~1° per tooth)
- Gaps between teeth are NORMAL
- Formula: φ = τ ± ξ

Helix (Spiral):
- Measures the entire face width
- Large angle span (~12-25° per tooth)
- Continuous coverage with overlap
- Formula: φ = τ ± Δφ
    """
    
    fig.text(0.5, 0.02, explanation, ha='center', fontsize=9, 
            fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.savefig(os.path.join(current_dir, 'profile_vs_helix_comparison.png'), 
                dpi=150, bbox_inches='tight')
    print(f"\n保存: profile_vs_helix_comparison.png")
    plt.close()
    
    print()
    print("="*70)
    print("结论")
    print("="*70)
    print()
    print("齿形(Profile):")
    print("  - 测量范围: 渐开线的一段(评价范围)")
    print("  - 角度跨度: 约1°左右")
    print("  - 齿间关系: 有间隙是正常的")
    print("  - 合并曲线: 各齿数据不连续")
    print()
    print("齿向(Helix):")
    print("  - 测量范围: 整个齿宽")
    print("  - 角度跨度: 约12-25°")
    print("  - 齿间关系: 应该有重叠")
    print("  - 合并曲线: 各齿数据连续拼接")
    print()
    print("两种测量方式的不同特性决定了合并曲线的不同表现！")


if __name__ == '__main__':
    main()
