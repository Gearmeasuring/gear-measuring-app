"""
优化后的齿轮波纹度分析算法
针对大螺旋角齿轮和不同齿数的自适应处理
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


class OptimizedRippleAnalyzer:
    """优化后的波纹度分析器"""
    
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
        
        self.delta_phi_range = self._calculate_delta_phi_range()
        
        self.preprocess_order = self._get_adaptive_preprocess_order()
        
        self.interp_points = self._get_adaptive_interp_points()
    
    def _calculate_delta_phi_range(self):
        """计算单齿的Delta_phi范围"""
        if abs(self.helix_angle) > 0.01:
            tan_beta0 = math.tan(math.radians(abs(self.helix_angle)))
            eval_width = 28.0
            delta_phi = math.degrees(eval_width * tan_beta0 / self.pitch_diameter)
            return delta_phi
        return 0.0
    
    def _get_adaptive_preprocess_order(self):
        """根据Delta_phi范围自适应选择预处理阶数"""
        if self.delta_phi_range < 5:
            return 2
        elif self.delta_phi_range < 10:
            return 3
        elif self.delta_phi_range < 15:
            return 4
        else:
            return 5
    
    def _get_adaptive_interp_points(self):
        """根据齿数和Delta_phi范围自适应选择插值点数"""
        base_points = max(1024, 10 * self.teeth_count)
        if self.delta_phi_range > 10:
            base_points = int(base_points * 1.5)
        if self.delta_phi_range > 15:
            base_points = int(base_points * 2)
        return base_points
    
    def calculate_involute_angle(self, radius):
        """计算渐开线极角"""
        if radius <= self.base_radius or self.base_radius <= 0:
            return 0.0
        cos_alpha = self.base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        alpha = math.acos(cos_alpha)
        return math.tan(alpha) - alpha
    
    def preprocess_tooth_data(self, values, order=None):
        """预处理齿数据 - 自适应多项式阶数"""
        if order is None:
            order = self.preprocess_order
        
        if len(values) < order + 1:
            return values
        
        n = len(values)
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        coeffs = np.polyfit(x_norm, values, order)
        trend = np.polyval(coeffs, x_norm)
        
        return values - trend
    
    def build_profile_merged_curve(self, side_data, side, eval_start, eval_end, meas_start, meas_end):
        """构建齿形合并曲线"""
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
            
            corrected_values = self.preprocess_tooth_data(eval_values)
            
            tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
            tau = tooth_index * self.pitch_angle
            
            if eval_start > 0 and eval_end > 0:
                radii = np.linspace(eval_start/2, eval_end/2, eval_points)
            else:
                radii = np.linspace(self.pitch_radius * 0.95, self.pitch_radius * 1.05, eval_points)
            
            xi_angles = np.array([math.degrees(self.calculate_involute_angle(r)) for r in radii])
            
            if side == 'left':
                angles = tau - xi_angles
            else:
                angles = tau + xi_angles
            
            all_angles.extend(angles.tolist())
            all_values.extend(corrected_values.tolist())
        
        if not all_angles:
            return None, None
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        
        all_angles = all_angles % 360.0
        sort_idx = np.argsort(all_angles)
        
        return all_angles[sort_idx], all_values[sort_idx]
    
    def build_helix_merged_curve(self, side_data, side, eval_start, eval_end):
        """构建齿向合并曲线 - 优化版"""
        if not side_data:
            return None, None
        
        sorted_teeth = sorted(side_data.keys())
        
        all_angles = []
        all_values = []
        
        eval_width = eval_end - eval_start
        eval_center = (eval_start + eval_end) / 2.0
        
        tan_beta0 = math.tan(math.radians(abs(self.helix_angle))) if abs(self.helix_angle) > 0.01 else 0
        
        for tooth_id in sorted_teeth:
            tooth_values = side_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            actual_points = len(tooth_values)
            eval_values = np.array(tooth_values, dtype=float)
            
            corrected_values = self.preprocess_tooth_data(eval_values)
            
            axial_positions = np.linspace(eval_start, eval_end, actual_points)
            delta_z = axial_positions - eval_center
            
            if abs(self.helix_angle) > 0.01 and self.pitch_diameter > 0:
                delta_phi = np.degrees(2 * delta_z * tan_beta0 / self.pitch_diameter)
            else:
                delta_phi = np.zeros(actual_points)
            
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * self.pitch_angle
            
            if side == 'left':
                angles = tau - delta_phi
            else:
                angles = tau + delta_phi
            
            all_angles.extend(angles.tolist())
            all_values.extend(corrected_values.tolist())
        
        if not all_angles:
            return None, None
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        
        all_angles = all_angles % 360.0
        sort_idx = np.argsort(all_angles)
        
        return all_angles[sort_idx], all_values[sort_idx]
    
    def uniform_resample(self, angles, values, num_points=None):
        """角度域均匀重采样"""
        if num_points is None:
            num_points = self.interp_points
        
        unique_angles, unique_indices = np.unique(np.round(angles, 4), return_index=True)
        unique_values = values[unique_indices]
        
        interp_angles = np.linspace(0, 360, num_points, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        return interp_angles, interp_values
    
    def compute_spectrum(self, angles, values, max_order=None):
        """计算频谱 - 优化版"""
        if max_order is None:
            max_order = 5 * self.teeth_count
        
        interp_angles, interp_values = self.uniform_resample(angles, values)
        
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
    
    def iterative_decomposition(self, angles, values, num_components=10, max_order=None):
        """迭代正弦波分解"""
        if max_order is None:
            max_order = 5 * self.teeth_count
        
        interp_angles, interp_values = self.uniform_resample(angles, values)
        angles_rad = np.radians(interp_angles)
        
        residual = interp_values.copy()
        components = []
        
        for _ in range(num_components):
            best_order = 0
            best_amplitude = 0
            best_coeffs = (0, 0)
            
            for order in range(1, max_order + 1):
                cos_term = np.cos(order * angles_rad)
                sin_term = np.sin(order * angles_rad)
                
                A = np.column_stack([cos_term, sin_term])
                coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
                
                a, b = coeffs[0], coeffs[1]
                amplitude = np.sqrt(a**2 + b**2)
                
                if amplitude > best_amplitude:
                    best_amplitude = amplitude
                    best_order = order
                    best_coeffs = (a, b)
            
            if best_order > 0:
                a, b = best_coeffs
                component_signal = a * np.cos(best_order * angles_rad) + b * np.sin(best_order * angles_rad)
                residual = residual - component_signal
                
                phase = math.degrees(math.atan2(a, b))
                components.append({
                    'order': best_order,
                    'amplitude': best_amplitude,
                    'phase': phase,
                    'coeffs': (a, b)
                })
        
        return components, interp_angles, interp_values


def analyze_with_optimization(mka_file, sample_name, klingelnberg_ref):
    """使用优化算法分析样本"""
    print(f"\n{'='*90}")
    print(f"优化算法分析: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 0.0)
    base_diameter = gear_data.get('base_diameter', 0.0)
    
    print(f"\n齿轮参数:")
    print(f"  齿数 ZE = {teeth_count}")
    print(f"  模数 m = {module}")
    print(f"  螺旋角 beta = {helix_angle}")
    
    analyzer = OptimizedRippleAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    print(f"\n自适应参数:")
    print(f"  Delta_phi范围 = {analyzer.delta_phi_range:.2f}")
    print(f"  预处理阶数 = {analyzer.preprocess_order}")
    print(f"  插值点数 = {analyzer.interp_points}")
    
    directions = [
        ('right_profile', profile_data.get('right', {}), 'profile', 'right'),
        ('left_profile', profile_data.get('left', {}), 'profile', 'left'),
        ('right_helix', flank_data.get('right', {}), 'helix', 'right'),
        ('left_helix', flank_data.get('left', {}), 'helix', 'left'),
    ]
    
    direction_names = {
        'right_profile': 'Right Profile',
        'left_profile': 'Left Profile',
        'right_helix': 'Right Helix',
        'left_helix': 'Left Helix'
    }
    
    total_errors = []
    
    for direction, side_data, data_type, side in directions:
        if direction not in klingelnberg_ref:
            continue
        
        ref = klingelnberg_ref[direction]
        
        if data_type == 'profile':
            eval_start = gear_data.get('profile_eval_start', 0)
            eval_end = gear_data.get('profile_eval_end', 0)
            meas_start = gear_data.get('profile_meas_start', 0)
            meas_end = gear_data.get('profile_meas_end', 0)
            angles, values = analyzer.build_profile_merged_curve(
                side_data, side, eval_start, eval_end, meas_start, meas_end
            )
        else:
            eval_start = gear_data.get('helix_eval_start', 0)
            eval_end = gear_data.get('helix_eval_end', 0)
            angles, values = analyzer.build_helix_merged_curve(
                side_data, side, eval_start, eval_end
            )
        
        if angles is None:
            continue
        
        spectrum, _, _ = analyzer.compute_spectrum(angles, values)
        
        print(f"\n{direction_names[direction]}:")
        print(f"  {'Order':<8} {'Ours':<12} {'Klingelnberg':<12} {'Error':<10} {'Status':<8}")
        print(f"  {'-'*55}")
        
        for order in sorted(ref.keys()):
            our_amp = spectrum.get(order, 0)
            ref_amp = ref[order]
            error = abs(our_amp - ref_amp) / ref_amp * 100 if our_amp > 0 else 100
            total_errors.append(error)
            status = "OK" if error < 10 else "~" if error < 25 else "!" if error < 50 else "X"
            print(f"  {order:<8.0f} {our_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}% {status}")
    
    avg_error = np.mean(total_errors) if total_errors else 100
    print(f"\nAverage Error: {avg_error:.1f}%")
    
    return {
        'teeth_count': teeth_count,
        'avg_error': avg_error,
        'errors': total_errors,
        'analyzer': analyzer
    }


def main():
    """主函数 - 对比优化前后效果"""
    
    KLINGELNBERG_SAMPLE1 = {
        'left_profile': {87: 0.1400, 174: 0.0500, 261: 0.0600, 348: 0.0300, 435: 0.0400},
        'right_profile': {87: 0.1500, 174: 0.0500, 261: 0.0600, 348: 0.0700, 435: 0.0300},
        'left_helix': {87: 0.1200, 89: 0.0700, 174: 0.0600, 261: 0.0500, 348: 0.0300},
        'right_helix': {87: 0.0900, 174: 0.1000, 261: 0.0500, 348: 0.0400, 435: 0.0300}
    }
    
    KLINGELNBERG_SAMPLE2 = {
        'right_profile': {26: 0.19, 52: 0.07, 78: 0.10, 104: 0.05, 130: 0.05, 156: 0.06, 182: 0.08},
        'left_profile': {22: 0.03, 26: 0.24, 44: 0.04, 52: 0.19, 78: 0.09, 104: 0.16, 130: 0.09, 156: 0.06, 182: 0.08},
        'right_helix': {26: 0.03, 52: 0.06, 78: 0.03, 141: 0.03, 156: 0.02},
        'left_helix': {26: 0.07, 48: 0.03, 52: 0.08, 78: 0.04, 104: 0.03, 130: 0.02, 141: 0.04, 182: 0.02}
    }
    
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    sample2_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\004-xiaoxiao1.mka"
    
    result1 = analyze_with_optimization(sample1_file, "Sample1 (ZE=87)", KLINGELNBERG_SAMPLE1)
    result2 = analyze_with_optimization(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)
    
    print(f"\n{'='*90}")
    print("Optimization Summary")
    print(f"{'='*90}")
    
    print(f"\nSample1 (ZE=87, small Delta_phi):")
    print(f"  Average Error: {result1['avg_error']:.1f}%")
    
    print(f"\nSample2 (ZE=26, large Delta_phi):")
    print(f"  Average Error: {result2['avg_error']:.1f}%")
    
    print(f"\nImprovement Analysis:")
    print(f"  The algorithm now uses adaptive parameters based on gear characteristics:")
    print(f"  - Preprocessing order: 2-5 (based on Delta_phi range)")
    print(f"  - Interpolation points: 1024-20000 (based on teeth count and Delta_phi)")
    print(f"  - Uniform resampling in angle domain")


if __name__ == "__main__":
    main()
