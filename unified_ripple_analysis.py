"""
统一标准波纹度分析算法
根据分析结果：
1. 使用合并曲线法
2. 缩放因子 = 1/√ZE
3. 直接最小二乘法计算所有目标阶次
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


class UnifiedRippleAnalyzer:
    """统一标准波纹度分析器"""
    
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
        
        self.amplitude_scale = 1.0 / math.sqrt(teeth_count)
    
    def calculate_involute_angle(self, radius):
        """计算渐开线极角 ξ = inv(α) = tan(α) - α"""
        if radius <= self.base_radius or self.base_radius <= 0:
            return 0.0
        cos_alpha = self.base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        alpha = math.acos(cos_alpha)
        return math.degrees(math.tan(alpha) - alpha)
    
    def preprocess_tooth_data(self, values):
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
            
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * self.pitch_angle
            
            if eval_start > 0 and eval_end > 0:
                radii = np.linspace(eval_start/2, eval_end/2, eval_points)
            else:
                radii = np.linspace(self.pitch_radius * 0.95, self.pitch_radius * 1.05, eval_points)
            
            xi_angles = np.array([self.calculate_involute_angle(r) for r in radii])
            
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
        """构建齿向合并曲线"""
        if not side_data:
            return None, None
        
        sorted_teeth = sorted(side_data.keys())
        
        all_angles = []
        all_values = []
        
        eval_center = (eval_start + eval_end) / 2.0
        tan_beta0 = math.tan(math.radians(self.helix_angle)) if abs(self.helix_angle) > 0.01 else 0
        
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
    
    def compute_spectrum(self, angles, values, target_orders):
        """计算频谱 - 直接最小二乘法"""
        if angles is None or values is None:
            return {}
        
        unique_angles, unique_indices = np.unique(np.round(angles, 4), return_index=True)
        unique_values = values[unique_indices]
        
        num_points = max(360, 2 * 5 * self.teeth_count + 10)
        interp_angles = np.linspace(0, 360, num_points, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        theta = np.radians(interp_angles)
        
        spectrum = {}
        for order in target_orders:
            cos_x = np.cos(order * theta)
            sin_x = np.sin(order * theta)
            A = np.column_stack((cos_x, sin_x))
            coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
            a, b = coeffs
            amplitude = np.sqrt(a*a + b*b) * self.amplitude_scale
            spectrum[order] = amplitude
        
        return spectrum
    
    def analyze_profile(self, side_data, side, eval_start, eval_end, meas_start, meas_end, target_orders):
        """分析齿形波纹度"""
        angles, values = self.build_profile_merged_curve(side_data, side, eval_start, eval_end, meas_start, meas_end)
        return self.compute_spectrum(angles, values, target_orders)
    
    def analyze_helix(self, side_data, side, eval_start, eval_end, target_orders):
        """分析齿向波纹度"""
        angles, values = self.build_helix_merged_curve(side_data, side, eval_start, eval_end)
        return self.compute_spectrum(angles, values, target_orders)


def analyze_sample_unified(mka_file, sample_name, klingelnberg_ref):
    """使用统一标准算法分析样本"""
    print(f"\n{'='*90}")
    print(f"Unified Standard Analysis: {sample_name}")
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
    
    print(f"\nGear Parameters:")
    print(f"  Teeth ZE = {teeth_count}")
    print(f"  Module m = {module}")
    print(f"  Pressure Angle alpha = {pressure_angle}")
    print(f"  Helix Angle beta = {helix_angle}")
    
    analyzer = UnifiedRippleAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    print(f"\nAlgorithm Parameters:")
    print(f"  Amplitude Scale = 1/sqrt(ZE) = {analyzer.amplitude_scale:.4f}")
    
    profile_eval_start = gear_data.get('profile_eval_start', 0)
    profile_eval_end = gear_data.get('profile_eval_end', 0)
    profile_meas_start = gear_data.get('profile_meas_start', 0)
    profile_meas_end = gear_data.get('profile_meas_end', 0)
    helix_eval_start = gear_data.get('helix_eval_start', 0)
    helix_eval_end = gear_data.get('helix_eval_end', 0)
    
    direction_names = {
        'right_profile': 'Right Profile',
        'left_profile': 'Left Profile',
        'right_helix': 'Right Helix',
        'left_helix': 'Left Helix'
    }
    
    total_errors = []
    
    for direction in ['right_profile', 'left_profile', 'right_helix', 'left_helix']:
        if direction not in klingelnberg_ref:
            continue
        
        ref = klingelnberg_ref[direction]
        target_orders = list(ref.keys())
        
        if 'profile' in direction:
            side = direction.split('_')[0]
            side_data = profile_data.get(side, {})
            spectrum = analyzer.analyze_profile(
                side_data, side,
                profile_eval_start, profile_eval_end,
                profile_meas_start, profile_meas_end,
                target_orders
            )
        else:
            side = direction.split('_')[0]
            side_data = flank_data.get(side, {})
            spectrum = analyzer.analyze_helix(
                side_data, side,
                helix_eval_start, helix_eval_end,
                target_orders
            )
        
        print(f"\n{direction_names[direction]}:")
        print(f"  {'Order':<8} {'Ours':<12} {'Klingelnberg':<12} {'Error':<10} {'Status':<8}")
        print(f"  {'-'*55}")
        
        errors = []
        for order in sorted(ref.keys()):
            our_amp = spectrum.get(order, 0)
            ref_amp = ref[order]
            error = abs(our_amp - ref_amp) / ref_amp * 100 if ref_amp > 0 else 100
            errors.append(error)
            total_errors.append(error)
            status = "OK" if error < 10 else "~" if error < 25 else "!" if error < 50 else "X"
            print(f"  {order:<8.0f} {our_amp:<12.4f} {ref_amp:<12.4f} {error:<10.1f}% {status}")
        
        print(f"  Average Error: {np.mean(errors):.1f}%")
    
    avg_error = np.mean(total_errors) if total_errors else 100
    print(f"\n{'='*55}")
    print(f"Overall Average Error: {avg_error:.1f}%")
    
    return {
        'teeth_count': teeth_count,
        'avg_error': avg_error,
        'analyzer': analyzer
    }


def main():
    """主函数"""
    
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
    
    result1 = analyze_sample_unified(sample1_file, "Sample1 (ZE=87)", KLINGELNBERG_SAMPLE1)
    result2 = analyze_sample_unified(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)
    
    print(f"\n{'='*90}")
    print("SUMMARY")
    print(f"{'='*90}")
    
    print(f"\nSample1 (ZE=87): Average Error = {result1['avg_error']:.1f}%")
    print(f"Sample2 (ZE=26): Average Error = {result2['avg_error']:.1f}%")
    
    print(f"""
Unified Standard Algorithm:
  1. Merged Curve Method for angle synthesis
  2. Preprocessing: Remove crowning (order-2) and slope (order-1)
  3. Amplitude Scale = 1/sqrt(ZE)
  4. Direct Least Squares for all target orders
""")


if __name__ == "__main__":
    main()
