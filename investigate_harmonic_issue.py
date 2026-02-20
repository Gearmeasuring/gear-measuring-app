"""
深入调查174阶次振幅偏高的问题
分析可能的原因：
1. 数据特性
2. 预处理方法
3. 频谱分析方法
4. 振幅计算方式
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

Klingelnberg_REFERENCE = {
    'left_profile': {87: 0.1400, 174: 0.0500, 261: 0.0600, 348: 0.0300, 435: 0.0400},
    'right_profile': {87: 0.1500, 174: 0.0500, 261: 0.0600, 348: 0.0700, 435: 0.0300},
    'left_helix': {87: 0.1200, 89: 0.0700, 174: 0.0600, 261: 0.0500, 348: 0.0300},
    'right_helix': {87: 0.0900, 174: 0.1000, 261: 0.0500, 348: 0.0400, 435: 0.0300}
}

class DeepInvestigator:
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
    
    def preprocess_tooth_data(self, values, method='poly', order=2):
        if len(values) < 5:
            return values
        
        n = len(values)
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        if method == 'poly':
            coeffs = np.polyfit(x_norm, values, order)
            trend = np.polyval(coeffs, x_norm)
        elif method == 'weighted_poly':
            weights = np.exp(-0.5 * ((x_norm) / 1.5)**2)
            coeffs = np.polyfit(x_norm, values, order, w=weights)
            trend = np.polyval(coeffs, x_norm)
        else:
            return values
        
        return values - trend
    
    def build_merged_curve(self, side_data, data_type, side, eval_start, eval_end, 
                          meas_start, meas_end, preprocess_method='poly', preprocess_order=2):
        if not side_data:
            return None, None, None
        
        sorted_teeth = sorted(side_data.keys())
        
        all_angles = []
        all_values = []
        all_raw_values = []
        
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
            
            corrected_values = self.preprocess_tooth_data(
                eval_values, method=preprocess_method, order=preprocess_order
            )
            
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
            all_values.extend(corrected_values.tolist())
            all_raw_values.extend(eval_values.tolist())
        
        if not all_angles:
            return None, None, None
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        all_raw_values = np.array(all_raw_values)
        
        all_angles = all_angles % 360.0
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        all_raw_values = all_raw_values[sort_idx]
        
        return all_angles, all_values, all_raw_values
    
    def compute_full_spectrum(self, angles, values, max_order=None):
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
    
    def iterative_decomposition(self, angles, values, n_cycles=10):
        angles_rad = np.radians(angles)
        residual = values.copy()
        
        components = []
        
        for cycle in range(n_cycles):
            best_order = 0
            best_amplitude = 0
            best_fitted = None
            
            for order in range(1, 5 * self.teeth_count + 1):
                if any(abs(c['order'] - order) < 0.5 for c in components):
                    continue
                
                cos_term = np.cos(order * angles_rad)
                sin_term = np.sin(order * angles_rad)
                
                A = np.column_stack([cos_term, sin_term])
                coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
                
                a, b = coeffs[0], coeffs[1]
                amplitude = np.sqrt(a**2 + b**2)
                
                if amplitude > best_amplitude:
                    best_amplitude = amplitude
                    best_order = order
                    best_fitted = a * cos_term + b * sin_term
            
            if best_amplitude < 0.001 or best_order == 0:
                break
            
            components.append({
                'order': best_order,
                'amplitude': best_amplitude,
                'cycle': cycle + 1
            })
            
            residual = residual - best_fitted
        
        components.sort(key=lambda x: x['amplitude'], reverse=True)
        return components

def main():
    mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    print("=" * 90)
    print("深入调查174阶次振幅偏高的问题")
    print("=" * 90)
    
    print("\n解析MKA文件...")
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 0.0)
    base_diameter = gear_data.get('base_diameter', 0.0)
    
    investigator = DeepInvestigator(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    print(f"\n齿轮参数: ZE={teeth_count}, m={module}")
    
    # 分析Left Profile
    print("\n" + "=" * 90)
    print("分析 Left Profile")
    print("=" * 90)
    
    side_data = profile_data.get('left', {})
    eval_start = gear_data.get('profile_eval_start', 0)
    eval_end = gear_data.get('profile_eval_end', 0)
    meas_start = gear_data.get('profile_meas_start', 0)
    meas_end = gear_data.get('profile_meas_end', 0)
    
    # 获取原始和预处理后的数据
    angles, values, raw_values = investigator.build_merged_curve(
        side_data, 'profile', 'left', eval_start, eval_end, meas_start, meas_end,
        preprocess_method='poly', preprocess_order=3
    )
    
    print(f"\n数据统计:")
    print(f"  总点数: {len(angles)}")
    print(f"  原始数据范围: [{raw_values.min():.3f}, {raw_values.max():.3f}]")
    print(f"  预处理后范围: [{values.min():.3f}, {values.max():.3f}]")
    
    # 计算频谱
    spectrum, interp_angles, interp_values = investigator.compute_full_spectrum(angles, values)
    
    print(f"\n关键阶次振幅:")
    print(f"  87阶次: {spectrum.get(87, 0):.4f} (Klingelnberg: 0.1400)")
    print(f"  174阶次: {spectrum.get(174, 0):.4f} (Klingelnberg: 0.0500)")
    print(f"  261阶次: {spectrum.get(261, 0):.4f} (Klingelnberg: 0.0600)")
    print(f"  348阶次: {spectrum.get(348, 0):.4f} (Klingelnberg: 0.0300)")
    print(f"  435阶次: {spectrum.get(435, 0):.4f} (Klingelnberg: 0.0400)")
    
    # 计算振幅比例
    print(f"\n振幅比例分析:")
    print(f"  174/87 比例: {spectrum.get(174, 0)/spectrum.get(87, 0):.3f} (Klingelnberg: {0.0500/0.1400:.3f})")
    print(f"  261/87 比例: {spectrum.get(261, 0)/spectrum.get(87, 0):.3f} (Klingelnberg: {0.0600/0.1400:.3f})")
    print(f"  348/87 比例: {spectrum.get(348, 0)/spectrum.get(87, 0):.3f} (Klingelnberg: {0.0300/0.1400:.3f})")
    
    # 迭代分解
    print("\n" + "=" * 90)
    print("迭代正弦波分解结果")
    print("=" * 90)
    
    components = investigator.iterative_decomposition(interp_angles, interp_values, n_cycles=15)
    
    print(f"\n前15个主要分量:")
    for i, c in enumerate(components[:15]):
        in_ref = "★" if c['order'] in [87, 174, 261, 348, 435] else ""
        print(f"  #{i+1}: 阶次={c['order']:<4.0f}, 振幅={c['amplitude']:.4f}, 迭代={c['cycle']} {in_ref}")
    
    # 分析：检查是否存在谐波泄漏
    print("\n" + "=" * 90)
    print("谐波泄漏分析")
    print("=" * 90)
    
    # 检查87阶次是否在第一次迭代就被提取
    first_cycle = next((c for c in components if c['cycle'] == 1), None)
    print(f"\n第一次迭代提取的阶次: {first_cycle['order'] if first_cycle else 'N/A'}")
    
    # 检查174阶次的提取顺序
    order_174 = next((c for c in components if abs(c['order'] - 174) < 0.5), None)
    if order_174:
        print(f"174阶次在第 {order_174['cycle']} 次迭代被提取")
    
    # 尝试不同的预处理方法
    print("\n" + "=" * 90)
    print("测试不同预处理方法对174阶次的影响")
    print("=" * 90)
    
    preprocess_methods = [
        ('poly_order_1', 'poly', 1),
        ('poly_order_2', 'poly', 2),
        ('poly_order_3', 'poly', 3),
        ('poly_order_4', 'poly', 4),
        ('weighted_poly_2', 'weighted_poly', 2),
        ('weighted_poly_3', 'weighted_poly', 3),
    ]
    
    for method_name, method, order in preprocess_methods:
        angles, values, _ = investigator.build_merged_curve(
            side_data, 'profile', 'left', eval_start, eval_end, meas_start, meas_end,
            preprocess_method=method, preprocess_order=order
        )
        
        spectrum, _, _ = investigator.compute_full_spectrum(angles, values)
        
        amp_87 = spectrum.get(87, 0)
        amp_174 = spectrum.get(174, 0)
        ratio = amp_174 / amp_87 if amp_87 > 0 else 0
        
        print(f"\n{method_name}:")
        print(f"  87阶次: {amp_87:.4f}, 174阶次: {amp_174:.4f}, 比例: {ratio:.3f}")
        print(f"  Klingelnberg比例: {0.0500/0.1400:.3f}")
    
    # 分析原始数据的谐波含量
    print("\n" + "=" * 90)
    print("原始数据（无预处理）的谐波含量")
    print("=" * 90)
    
    angles, values, raw_values = investigator.build_merged_curve(
        side_data, 'profile', 'left', eval_start, eval_end, meas_start, meas_end,
        preprocess_method='poly', preprocess_order=3
    )
    
    # 不预处理的频谱
    spectrum_raw, _, _ = investigator.compute_full_spectrum(angles, raw_values)
    
    print(f"\n无预处理时:")
    print(f"  87阶次: {spectrum_raw.get(87, 0):.4f}")
    print(f"  174阶次: {spectrum_raw.get(174, 0):.4f}")
    print(f"  比例: {spectrum_raw.get(174, 0)/spectrum_raw.get(87, 0) if spectrum_raw.get(87, 0) > 0 else 0:.3f}")
    
    # 生成分析图
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    
    # 原始合并曲线
    ax = axes[0, 0]
    ax.scatter(angles, raw_values, s=1, alpha=0.5, label='原始数据')
    ax.set_xlabel('角度 (°)')
    ax.set_ylabel('偏差 (μm)')
    ax.set_title('原始合并曲线')
    ax.set_xlim(0, 360)
    ax.grid(True, alpha=0.3)
    
    # 预处理后合并曲线
    ax = axes[0, 1]
    ax.plot(interp_angles, interp_values, 'b-', linewidth=0.5)
    ax.set_xlabel('角度 (°)')
    ax.set_ylabel('偏差 (μm)')
    ax.set_title('预处理后合并曲线')
    ax.set_xlim(0, 360)
    ax.grid(True, alpha=0.3)
    
    # 频谱图
    ax = axes[0, 2]
    orders = list(range(1, 200))
    amplitudes = [spectrum.get(o, 0) for o in orders]
    ax.bar(orders, amplitudes, width=1.0, color='steelblue', alpha=0.6)
    ax.axvline(x=87, color='red', linestyle='--', label='87阶次')
    ax.axvline(x=174, color='orange', linestyle='--', label='174阶次')
    ax.set_xlabel('阶次')
    ax.set_ylabel('振幅 (μm)')
    ax.set_title('频谱 (1-200阶次)')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # 对数频谱
    ax = axes[1, 0]
    ax.semilogy(orders, [max(a, 0.001) for a in amplitudes], 'b-', linewidth=0.5)
    ax.axvline(x=87, color='red', linestyle='--', label='87阶次')
    ax.axvline(x=174, color='orange', linestyle='--', label='174阶次')
    ax.set_xlabel('阶次')
    ax.set_ylabel('振幅 (μm) - 对数')
    ax.set_title('对数频谱')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 谐波比例对比
    ax = axes[1, 1]
    harmonic_orders = [87, 174, 261, 348, 435]
    our_amps = [spectrum.get(o, 0) for o in harmonic_orders]
    ref_amps = [Klingelnberg_REFERENCE['left_profile'].get(o, 0) for o in harmonic_orders]
    
    x = np.arange(len(harmonic_orders))
    width = 0.35
    ax.bar(x - width/2, our_amps, width, label='我们的结果', color='steelblue')
    ax.bar(x + width/2, ref_amps, width, label='Klingelnberg', color='coral')
    ax.set_xlabel('阶次')
    ax.set_ylabel('振幅 (μm)')
    ax.set_title('谐波振幅对比')
    ax.set_xticks(x)
    ax.set_xticklabels([str(o) for o in harmonic_orders])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # 振幅比例对比
    ax = axes[1, 2]
    our_ratios = [spectrum.get(o, 0)/spectrum.get(87, 0) if spectrum.get(87, 0) > 0 else 0 for o in [174, 261, 348, 435]]
    ref_ratios = [Klingelnberg_REFERENCE['left_profile'].get(o, 0)/Klingelnberg_REFERENCE['left_profile'].get(87, 0) for o in [174, 261, 348, 435]]
    
    x = np.arange(4)
    ax.bar(x - width/2, our_ratios, width, label='我们的比例', color='steelblue')
    ax.bar(x + width/2, ref_ratios, width, label='Klingelnberg比例', color='coral')
    ax.set_xlabel('阶次')
    ax.set_ylabel('相对于87阶次的振幅比例')
    ax.set_title('谐波比例对比')
    ax.set_xticks(x)
    ax.set_xticklabels(['174', '261', '348', '435'])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    output_path = os.path.join(current_dir, "harmonic_investigation.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n分析图已保存: {output_path}")

if __name__ == "__main__":
    main()
