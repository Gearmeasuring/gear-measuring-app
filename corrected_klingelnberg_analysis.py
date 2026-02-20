"""
根据Klingelnberg论文修正的波纹度分析算法
关键修正: 预处理在曲线合并之前进行 (per-tooth preprocessing before merging)
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

class CorrectedKlingelnbergAnalyzer:
    """
    修正后的Klingelnberg波纹度分析器
    关键修正: 每齿预处理在合并曲线之前进行
    """
    
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
        """计算渐开线展开角"""
        if radius <= self.base_radius or self.base_radius <= 0:
            return 0.0
        cos_alpha = self.base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        alpha = math.acos(cos_alpha)
        return math.tan(alpha) - alpha
    
    def preprocess_tooth_data(self, values, method='poly', order=2):
        """
        单齿预处理 - 去除鼓形和斜率
        根据论文，这必须在曲线合并之前进行
        """
        if len(values) < 5:
            return values
        
        n = len(values)
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        if method == 'poly':
            # 多项式拟合去除趋势
            coeffs = np.polyfit(x_norm, values, order)
            trend = np.polyval(coeffs, x_norm)
        elif method == 'weighted_poly':
            # 加权多项式拟合
            weights = np.exp(-0.5 * ((x_norm) / 1.5)**2)
            coeffs = np.polyfit(x_norm, values, order, w=weights)
            trend = np.polyval(coeffs, x_norm)
        elif method == 'linear':
            # 仅去除线性趋势（斜率）
            coeffs = np.polyfit(x_norm, values, 1)
            trend = np.polyval(coeffs, x_norm)
        else:
            return values
        
        return values - trend
    
    def build_merged_curve_corrected(self, side_data, data_type, side, eval_start, eval_end, 
                                     meas_start, meas_end, preprocess_method='poly', 
                                     preprocess_order=2):
        """
        构建合并曲线 - 修正版
        关键: 每齿预处理在合并之前进行
        """
        if not side_data:
            return None, None
        
        sorted_teeth = sorted(side_data.keys())
        
        all_angles = []
        all_values = []
        
        for tooth_id in sorted_teeth:
            tooth_values = side_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            actual_points = len(tooth_values)
            
            # 提取评估区域数据
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
            
            # ========== 关键修正: 在合并之前进行每齿预处理 ==========
            corrected_values = self.preprocess_tooth_data(
                eval_values, method=preprocess_method, order=preprocess_order
            )
            
            # 计算齿的节距角
            tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
            tau = tooth_index * self.pitch_angle
            
            # 根据数据类型计算旋转角度
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
        
        if not all_angles:
            return None, None
        
        # 整理数据
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        
        # 归一化到0-360度
        all_angles = all_angles % 360.0
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        
        return all_angles, all_values
    
    def iterative_sine_decomposition(self, angles, values, n_cycles=10, freq_range=None):
        """
        迭代正弦波分解
        """
        angles_rad = np.radians(angles)
        residual = values.copy()
        
        if freq_range is None:
            min_order = 1
            max_order = 5 * self.teeth_count
        else:
            min_order, max_order = freq_range
        
        components = []
        
        for cycle in range(n_cycles):
            best_order = 0
            best_amplitude = 0
            best_phase = 0
            best_fitted = None
            
            for order in range(min_order, max_order + 1):
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
                    best_phase = np.arctan2(a, b)
                    best_fitted = a * cos_term + b * sin_term
            
            if best_amplitude < 0.001 or best_order == 0:
                break
            
            components.append({
                'order': best_order,
                'amplitude': best_amplitude,
                'phase': np.degrees(best_phase),
                'cycle': cycle + 1
            })
            
            residual = residual - best_fitted
        
        components.sort(key=lambda x: x['amplitude'], reverse=True)
        return components, residual
    
    def analyze_direction(self, profile_data, flank_data, direction, gear_data, 
                         n_cycles=10, freq_range=None, preprocess_method='poly', 
                         preprocess_order=2):
        """分析指定方向"""
        
        if direction == 'left_profile':
            side_data = profile_data.get('left', {})
            data_type = 'profile'
            side = 'left'
            eval_start = gear_data.get('profile_eval_start', 0)
            eval_end = gear_data.get('profile_eval_end', 0)
            meas_start = gear_data.get('profile_meas_start', 0)
            meas_end = gear_data.get('profile_meas_end', 0)
        elif direction == 'right_profile':
            side_data = profile_data.get('right', {})
            data_type = 'profile'
            side = 'right'
            eval_start = gear_data.get('profile_eval_start', 0)
            eval_end = gear_data.get('profile_eval_end', 0)
            meas_start = gear_data.get('profile_meas_start', 0)
            meas_end = gear_data.get('profile_meas_end', 0)
        elif direction == 'left_helix':
            side_data = flank_data.get('left', {})
            data_type = 'helix'
            side = 'left'
            eval_start = gear_data.get('helix_eval_start', 0)
            eval_end = gear_data.get('helix_eval_end', 0)
            meas_start = gear_data.get('helix_meas_start', 0)
            meas_end = gear_data.get('helix_meas_end', 0)
        elif direction == 'right_helix':
            side_data = flank_data.get('right', {})
            data_type = 'helix'
            side = 'right'
            eval_start = gear_data.get('helix_eval_start', 0)
            eval_end = gear_data.get('helix_eval_end', 0)
            meas_start = gear_data.get('helix_meas_start', 0)
            meas_end = gear_data.get('helix_meas_end', 0)
        else:
            return [], None, None
        
        # 构建合并曲线（预处理在内部进行）
        angles, values = self.build_merged_curve_corrected(
            side_data, data_type, side, eval_start, eval_end, meas_start, meas_end,
            preprocess_method=preprocess_method, preprocess_order=preprocess_order
        )
        
        if angles is None or len(angles) < 100:
            return [], None, None
        
        # 重采样到等间隔
        unique_angles, unique_indices = np.unique(np.round(angles, 3), return_index=True)
        unique_values = values[unique_indices]
        
        num_points = max(1024, 2 * 5 * self.teeth_count + 10)
        interp_angles = np.linspace(0, 360, num_points, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        # 迭代正弦波分解
        components, residual = self.iterative_sine_decomposition(
            interp_angles, interp_values, n_cycles=n_cycles, freq_range=freq_range
        )
        
        return components, interp_angles, interp_values

def calculate_error(our_result, klingelnberg_ref):
    """计算误差"""
    errors = []
    for order, ref_amp in klingelnberg_ref.items():
        our_amp = next((c['amplitude'] for c in our_result if abs(c['order'] - order) < 0.5), 0)
        if our_amp > 0:
            error = abs(our_amp - ref_amp) / ref_amp * 100
            errors.append(error)
    return np.mean(errors) if errors else 100

def main():
    mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    print("=" * 90)
    print("修正后的Klingelnberg波纹度分析 (预处理方法修正)")
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
    
    analyzer = CorrectedKlingelnbergAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    print(f"\n齿轮参数:")
    print(f"  齿数 ZE = {teeth_count}")
    print(f"  模数 m = {module}")
    print(f"  压力角 α = {pressure_angle}°")
    print(f"  螺旋角 β = {helix_angle}°")
    
    # 测试不同预处理方法和参数
    print("\n" + "=" * 90)
    print("测试不同预处理方法 (预处理在合并曲线之前进行)")
    print("=" * 90)
    
    test_configs = [
        ('poly_order_1', 'poly', 1, 10),
        ('poly_order_2', 'poly', 2, 10),
        ('poly_order_3', 'poly', 3, 10),
        ('weighted_poly_order_2', 'weighted_poly', 2, 10),
        ('linear_only', 'linear', 1, 10),
        ('poly_order_2_15cycles', 'poly', 2, 15),
        ('poly_order_2_20cycles', 'poly', 2, 20),
    ]
    
    directions = ['left_profile', 'right_profile', 'left_helix', 'right_helix']
    direction_names = {
        'left_profile': 'Left Profile (左齿形)',
        'right_profile': 'Right Profile (右齿形)',
        'left_helix': 'Left Helix (左齿向)',
        'right_helix': 'Right Helix (右齿向)'
    }
    
    best_config = None
    best_error = float('inf')
    all_results = []
    
    for config_name, method, order, n_cycles in test_configs:
        print(f"\n测试配置: {config_name}")
        
        total_errors = []
        config_results = {}
        
        for direction in directions:
            components, angles, values = analyzer.analyze_direction(
                profile_data, flank_data, direction, gear_data,
                n_cycles=n_cycles, preprocess_method=method, preprocess_order=order
            )
            
            ref = Klingelnberg_REFERENCE[direction]
            error = calculate_error(components, ref)
            
            total_errors.append(error)
            config_results[direction] = {
                'components': components,
                'error': error
            }
        
        avg_error = np.mean(total_errors)
        all_results.append({
            'config': config_name,
            'method': method,
            'order': order,
            'n_cycles': n_cycles,
            'avg_error': avg_error,
            'results': config_results
        })
        
        print(f"  平均误差: {avg_error:.1f}%")
        
        if avg_error < best_error:
            best_error = avg_error
            best_config = {
                'name': config_name,
                'method': method,
                'order': order,
                'n_cycles': n_cycles,
                'results': config_results
            }
    
    # 输出最佳结果
    print("\n" + "=" * 90)
    print(f"最佳配置: {best_config['name']}")
    print(f"  预处理方法: {best_config['method']}, 阶数: {best_config['order']}")
    print(f"  迭代次数: {best_config['n_cycles']}")
    print(f"  平均误差: {best_error:.1f}%")
    print("=" * 90)
    
    for direction in directions:
        components = best_config['results'][direction]['components']
        ref = Klingelnberg_REFERENCE[direction]
        
        print(f"\n{direction_names[direction]}:")
        print(f"  {'阶次':<8} {'我们的结果':<12} {'Klingelnberg':<12} {'误差':<10} {'状态':<8}")
        print(f"  {'-'*55}")
        
        for order in sorted(ref.keys()):
            ref_amp = ref[order]
            our_amp = next((c['amplitude'] for c in components if abs(c['order'] - order) < 0.5), 0)
            
            if our_amp > 0:
                error = abs(our_amp - ref_amp) / ref_amp * 100
                status = "✅ 优秀" if error < 10 else "✓ 良好" if error < 25 else "⚠ 偏差" if error < 50 else "✗ 较大偏差"
                print(f"  {order:<8.0f} {our_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}% {status}")
        
        # 显示前10个主要分量
        print(f"\n  前10个主要频率分量:")
        for i, c in enumerate(components[:10]):
            in_ref = "★" if c['order'] in ref else ""
            print(f"    #{i+1}: 阶次={c['order']:<4.0f}, 振幅={c['amplitude']:.4f} {in_ref}")
    
    # 生成对比图
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    for idx, direction in enumerate(directions):
        row = idx // 2
        col = idx % 2
        ax = axes[row, col]
        
        components = best_config['results'][direction]['components']
        ref = Klingelnberg_REFERENCE[direction]
        
        ref_orders = sorted(ref.keys())
        our_amps = []
        ref_amps = []
        
        for order in ref_orders:
            our_amp = next((c['amplitude'] for c in components if abs(c['order'] - order) < 0.5), 0)
            our_amps.append(our_amp)
            ref_amps.append(ref[order])
        
        x = np.arange(len(ref_orders))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, our_amps, width, label='我们的结果', color='steelblue', alpha=0.8)
        bars2 = ax.bar(x + width/2, ref_amps, width, label='Klingelnberg', color='coral', alpha=0.8)
        
        ax.set_xlabel('阶次', fontsize=11)
        ax.set_ylabel('振幅 (μm)', fontsize=11)
        ax.set_title(direction_names[direction], fontsize=13, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([str(int(o)) for o in ref_orders])
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
        
        for i, (our, ref_val) in enumerate(zip(our_amps, ref_amps)):
            if our > 0:
                error = abs(our - ref_val) / ref_val * 100
                color = 'green' if error < 10 else 'orange' if error < 25 else 'red'
                ax.annotate(f'{error:.0f}%', 
                           xy=(i, max(our, ref_val) + 0.005),
                           ha='center', fontsize=8, color=color, fontweight='bold')
    
    plt.tight_layout()
    output_path = os.path.join(current_dir, "corrected_analysis_result.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n分析结果图已保存: {output_path}")
    
    # 保存详细结果到CSV
    csv_path = os.path.join(current_dir, "corrected_analysis_results.csv")
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write("配置,方向,阶次,我们的振幅,Klingelnberg振幅,误差(%),预处理方法,预处理阶数,迭代次数\n")
        
        for result in all_results:
            for direction in directions:
                components = result['results'][direction]['components']
                ref = Klingelnberg_REFERENCE[direction]
                
                for order in sorted(ref.keys()):
                    our_amp = next((c['amplitude'] for c in components if abs(c['order'] - order) < 0.5), 0)
                    ref_amp = ref[order]
                    error = abs(our_amp - ref_amp) / ref_amp * 100 if our_amp > 0 else 100
                    f.write(f"{result['config']},{direction},{order},{our_amp:.4f},{ref_amp:.4f},{error:.1f},{result['method']},{result['order']},{result['n_cycles']}\n")
    
    print(f"详细结果已保存: {csv_path}")

if __name__ == "__main__":
    main()
