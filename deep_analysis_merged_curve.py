"""
深入分析合并曲线特性，找出高阶谐波不匹配的原因
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import math
from scipy import signal
import warnings
warnings.filterwarnings('ignore')

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file

Klingelnberg_REFERENCE = {
    'left_profile': {87: 0.1400, 174: 0.0500, 261: 0.0600, 348: 0.0300, 435: 0.0400},
    'right_profile': {87: 0.1500, 174: 0.0500, 261: 0.0600, 348: 0.0700, 435: 0.0300},
    'left_helix': {87: 0.1200, 89: 0.0700, 174: 0.0600, 261: 0.0500, 348: 0.0300},
    'right_helix': {87: 0.0900, 174: 0.1000, 261: 0.0500, 348: 0.0400, 435: 0.0300}
}

class DeepAnalyzer:
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
    
    def calculate_involute_angle(self, radius):
        if radius <= self.base_radius or self.base_radius <= 0:
            return 0.0
        cos_alpha = self.base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        alpha = math.acos(cos_alpha)
        return math.tan(alpha) - alpha
    
    def build_raw_merged_curve(self, side_data, data_type, side, eval_start, eval_end, meas_start, meas_end):
        if not side_data:
            return None, None, None
        
        sorted_teeth = sorted(side_data.keys())
        
        all_angles = []
        all_values = []
        all_tooth_ids = []
        
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
            
            if eval_points < 3:
                continue
            
            tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
            tau = tooth_index * self.pitch_angle
            
            if data_type == 'profile':
                if eval_start > 0 and eval_end > 0:
                    radii = np.linspace(eval_start/2, eval_end/2, eval_points)
                else:
                    radii = np.linspace(self.pitch_radius * 0.95, self.pitch_radius * 1.05, eval_points)
                
                xi_angles = np.array([math.degrees(self.calculate_involute_angle(r)) for r in radii])
                
                if side == 'left':
                    angles = tau - xi_angles
                else:
                    angles = tau + xi_angles
            else:
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
            
            all_angles.extend(angles.tolist())
            all_values.extend(eval_values.tolist())
            all_tooth_ids.extend([tooth_id] * eval_points)
        
        if not all_angles:
            return None, None, None
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        all_tooth_ids = np.array(all_tooth_ids)
        
        all_angles = all_angles % 360.0
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        all_tooth_ids = all_tooth_ids[sort_idx]
        
        return all_angles, all_values, all_tooth_ids
    
    def preprocess_per_tooth(self, angles, values, tooth_ids, method='weighted', poly_order=2):
        unique_teeth = np.unique(tooth_ids)
        corrected_angles = []
        corrected_values = []
        
        for tooth_id in unique_teeth:
            mask = tooth_ids == tooth_id
            tooth_angles = angles[mask]
            tooth_values = values[mask]
            
            if len(tooth_values) < 3:
                continue
            
            n = len(tooth_values)
            x = np.arange(n)
            x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
            
            if method == 'weighted':
                weights = np.exp(-0.5 * ((x_norm) / 1.5)**2)
                coeffs = np.polyfit(x_norm, tooth_values, poly_order, w=weights)
            else:
                coeffs = np.polyfit(x_norm, tooth_values, poly_order)
            
            trend = np.polyval(coeffs, x_norm)
            corrected = tooth_values - trend
            
            corrected_angles.extend(tooth_angles.tolist())
            corrected_values.extend(corrected.tolist())
        
        return np.array(corrected_angles), np.array(corrected_values)
    
    def preprocess_global(self, angles, values, poly_order=2):
        n = len(values)
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        coeffs = np.polyfit(x_norm, values, poly_order)
        trend = np.polyval(coeffs, x_norm)
        
        return values - trend
    
    def compute_spectrum(self, angles, values, max_order=None):
        if max_order is None:
            max_order = 5 * self.teeth_count
        
        unique_angles, unique_indices = np.unique(np.round(angles, 3), return_index=True)
        unique_values = values[unique_indices]
        
        num_points = max(1024, 2 * max_order + 10)
        interp_angles = np.linspace(0, 360, num_points, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        angles_rad = np.radians(interp_angles)
        
        spectrum = {}
        for order in range(1, max_order + 1):
            cos_term = np.cos(order * angles_rad)
            sin_term = np.sin(order * angles_rad)
            
            A = np.column_stack([cos_term, sin_term])
            coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
            
            a, b = coeffs[0], coeffs[1]
            amplitude = np.sqrt(a**2 + b**2)
            
            spectrum[order] = amplitude
        
        return spectrum, interp_angles, interp_values

def main():
    mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    print("解析MKA文件...")
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 0.0)
    base_diameter = gear_data.get('base_diameter', 0.0)
    
    analyzer = DeepAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    print(f"齿轮参数: ZE={teeth_count}, m={module}")
    
    print("\n" + "=" * 90)
    print("分析Left Profile的合并曲线特性")
    print("=" * 90)
    
    side_data = profile_data.get('left', {})
    eval_start = gear_data.get('profile_eval_start', 0)
    eval_end = gear_data.get('profile_eval_end', 0)
    meas_start = gear_data.get('profile_meas_start', 0)
    meas_end = gear_data.get('profile_meas_end', 0)
    
    angles, values, tooth_ids = analyzer.build_raw_merged_curve(
        side_data, 'profile', 'left', eval_start, eval_end, meas_start, meas_end
    )
    
    print(f"\n原始数据:")
    print(f"  总点数: {len(angles)}")
    print(f"  角度范围: [{angles.min():.2f}, {angles.max():.2f}]")
    print(f"  值范围: [{values.min():.3f}, {values.max():.3f}]")
    print(f"  唯一齿数: {len(np.unique(tooth_ids))}")
    
    print("\n测试不同预处理方法:")
    
    methods = [
        ('无预处理', None),
        ('每齿加权预处理', 'per_tooth_weighted'),
        ('每齿普通预处理', 'per_tooth_normal'),
        ('全局预处理', 'global'),
    ]
    
    results = {}
    
    for method_name, method in methods:
        if method is None:
            processed_angles = angles
            processed_values = values
        elif method == 'per_tooth_weighted':
            processed_angles, processed_values = analyzer.preprocess_per_tooth(
                angles, values, tooth_ids, method='weighted'
            )
        elif method == 'per_tooth_normal':
            processed_angles, processed_values = analyzer.preprocess_per_tooth(
                angles, values, tooth_ids, method='normal'
            )
        elif method == 'global':
            processed_values = analyzer.preprocess_global(angles, values)
            processed_angles = angles
        
        spectrum, interp_angles, interp_values = analyzer.compute_spectrum(processed_angles, processed_values)
        
        ref = Klingelnberg_REFERENCE['left_profile']
        errors = []
        for order, ref_amp in ref.items():
            our_amp = spectrum.get(order, 0)
            if our_amp > 0:
                error = abs(our_amp - ref_amp) / ref_amp * 100
                errors.append(error)
        
        avg_error = np.mean(errors) if errors else 100
        results[method_name] = {
            'spectrum': spectrum,
            'avg_error': avg_error,
            'interp_angles': interp_angles,
            'interp_values': interp_values
        }
        
        print(f"\n{method_name}:")
        print(f"  平均误差: {avg_error:.1f}%")
        print(f"  87阶次: {spectrum.get(87, 0):.4f} (参考: {ref[87]:.4f})")
        print(f"  174阶次: {spectrum.get(174, 0):.4f} (参考: {ref[174]:.4f})")
        print(f"  261阶次: {spectrum.get(261, 0):.4f} (参考: {ref[261]:.4f})")
        print(f"  348阶次: {spectrum.get(348, 0):.4f} (参考: {ref[348]:.4f})")
        print(f"  435阶次: {spectrum.get(435, 0):.4f} (参考: {ref[435]:.4f})")
    
    print("\n" + "=" * 90)
    print("分析齿间差异")
    print("=" * 90)
    
    unique_teeth = np.unique(tooth_ids)
    print(f"\n分析前5个齿的原始数据特性:")
    
    for tooth_id in unique_teeth[:5]:
        mask = tooth_ids == tooth_id
        tooth_values = values[mask]
        tooth_angles = angles[mask]
        
        print(f"\n齿 {tooth_id}:")
        print(f"  点数: {len(tooth_values)}")
        print(f"  角度范围: [{tooth_angles.min():.2f}, {tooth_angles.max():.2f}]")
        print(f"  值范围: [{tooth_values.min():.3f}, {tooth_values.max():.3f}]")
        print(f"  均值: {tooth_values.mean():.3f}, 标准差: {tooth_values.std():.3f}")
    
    fig, axes = plt.subplots(3, 2, figsize=(16, 14))
    
    axes[0, 0].scatter(angles, values, c=tooth_ids, cmap='tab20', s=1, alpha=0.5)
    axes[0, 0].set_xlabel('角度 (°)')
    axes[0, 0].set_ylabel('偏差 (μm)')
    axes[0, 0].set_title('原始合并曲线 (按齿着色)')
    axes[0, 0].set_xlim(0, 360)
    axes[0, 0].grid(True, alpha=0.3)
    
    best_method = min(results.keys(), key=lambda k: results[k]['avg_error'])
    best_data = results[best_method]
    
    axes[0, 1].plot(best_data['interp_angles'], best_data['interp_values'], 'b-', linewidth=0.5)
    axes[0, 1].set_xlabel('角度 (°)')
    axes[0, 1].set_ylabel('偏差 (μm)')
    axes[0, 1].set_title(f'最佳预处理后曲线 ({best_method})')
    axes[0, 1].set_xlim(0, 360)
    axes[0, 1].grid(True, alpha=0.3)
    
    ref = Klingelnberg_REFERENCE['left_profile']
    ref_orders = sorted(ref.keys())
    ref_amplitudes = [ref[o] for o in ref_orders]
    
    for i, (method_name, data) in enumerate(results.items()):
        ax = axes[1, i] if i < 2 else axes[2, i-2]
        
        our_amplitudes = [data['spectrum'].get(o, 0) for o in ref_orders]
        
        x = np.arange(len(ref_orders))
        width = 0.35
        
        ax.bar(x - width/2, our_amplitudes, width, label='我们的结果', color='steelblue', alpha=0.8)
        ax.bar(x + width/2, ref_amplitudes, width, label='Klingelnberg', color='coral', alpha=0.8)
        
        ax.set_xlabel('阶次')
        ax.set_ylabel('振幅 (μm)')
        ax.set_title(f'{method_name}\n平均误差: {data["avg_error"]:.1f}%')
        ax.set_xticks(x)
        ax.set_xticklabels([str(int(o)) for o in ref_orders])
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis='y')
    
    axes[2, 0].bar(range(len(results)), [results[m]['avg_error'] for m in results.keys()], color='steelblue')
    axes[2, 0].set_xticks(range(len(results)))
    axes[2, 0].set_xticklabels(list(results.keys()), rotation=45, ha='right', fontsize=9)
    axes[2, 0].set_ylabel('平均误差 (%)')
    axes[2, 0].set_title('不同预处理方法的平均误差')
    axes[2, 0].grid(True, alpha=0.3, axis='y')
    
    all_orders = list(range(1, 200))
    best_spectrum = results[best_method]['spectrum']
    all_amplitudes = [best_spectrum.get(o, 0) for o in all_orders]
    
    axes[2, 1].bar(all_orders, all_amplitudes, width=1.0, color='steelblue', alpha=0.6)
    axes[2, 1].scatter(ref_orders, ref_amplitudes, color='red', s=100, zorder=5, label='Klingelnberg参考')
    axes[2, 1].set_xlabel('阶次')
    axes[2, 1].set_ylabel('振幅 (μm)')
    axes[2, 1].set_title(f'完整频谱 (1-200阶次) - {best_method}')
    axes[2, 1].legend()
    axes[2, 1].grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    output_path = os.path.join(current_dir, "deep_analysis_merged_curve.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n分析图已保存: {output_path}")
    
    return results

if __name__ == "__main__":
    results = main()
