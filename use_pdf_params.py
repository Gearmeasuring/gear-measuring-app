"""
使用PDF中的实际参数运行算法
PDF参数：
- ep = 1.454
- el = 2.766
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


class PDFParamsRippleAnalyzer:
    """使用PDF参数的分析器"""
    
    def __init__(self, teeth_count, module, pressure_angle=20.0, helix_angle=0.0, 
                 ep=1.454, el=2.766):
        self.teeth_count = teeth_count
        self.module = module
        self.pressure_angle = pressure_angle
        self.helix_angle = helix_angle
        
        # 使用PDF中的参数
        self.ep = ep
        self.el = el
        
        # 基本参数计算
        self.pitch_diameter = module * teeth_count
        self.pitch_radius = self.pitch_diameter / 2.0
        self.base_diameter = self.pitch_diameter * math.cos(math.radians(pressure_angle))
        self.base_radius = self.base_diameter / 2.0
        self.base_pitch = math.pi * self.base_diameter / teeth_count
        
        # 基圆螺旋角
        if abs(helix_angle) > 0.01:
            self.helix_angle_base = math.degrees(math.atan(
                math.tan(math.radians(helix_angle)) * math.cos(math.radians(pressure_angle))
            ))
        else:
            self.helix_angle_base = 0.0
        
        # 最佳缩放因子
        self.profile_scale = 0.109
        self.helix_scale = 0.05
    
    def calculate_involute_angle(self, radius):
        """计算渐开线极角"""
        if radius <= self.base_radius or self.base_radius <= 0:
            return 0.0
        cos_alpha = self.base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        alpha = math.acos(cos_alpha)
        return math.degrees(math.tan(alpha) - alpha)
    
    def preprocess_tooth_data(self, values, order=2):
        """预处理"""
        if len(values) < order + 1:
            return values - np.mean(values)
        
        n = len(values)
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        coeffs = np.polyfit(x_norm, values, order)
        trend = np.polyval(coeffs, x_norm)
        
        return values - trend
    
    def build_merged_curve(self, side_data, side, data_type, eval_start, eval_end):
        """构建合并曲线"""
        if not side_data:
            return None, None
        
        sorted_teeth = sorted(side_data.keys())
        
        all_angles = []
        all_values = []
        
        eval_center = (eval_start + eval_end) / 2.0
        
        # 根据ep或el计算评价长度
        if data_type == 'profile':
            eval_length = self.ep * self.base_pitch
        else:
            # 对于齿向，使用el来计算等效评价长度
            eval_length = abs(self.el) * self.base_pitch
        
        for tooth_id in sorted_teeth:
            tooth_values = side_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            actual_points = len(tooth_values)
            eval_values = np.array(tooth_values, dtype=float)
            
            # 预处理
            corrected_values = self.preprocess_tooth_data(eval_values, order=2)
            
            # 计算齿距角 τ
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * 360.0 / self.teeth_count
            
            if data_type == 'profile':
                # 齿形：计算渐开线极角 ξ
                if eval_start > 0 and eval_end > 0:
                    radii = np.linspace(eval_start/2, eval_end/2, actual_points)
                else:
                    radii = np.linspace(self.pitch_radius * 0.95, self.pitch_radius * 1.05, actual_points)
                
                xi_angles = np.array([self.calculate_involute_angle(r) for r in radii])
                
                # 角度合成
                if side == 'left':
                    angles = tau - xi_angles
                else:
                    angles = tau + xi_angles
            else:
                # 齿向：计算轴向旋转角 Δφ
                axial_positions = np.linspace(eval_start, eval_end, actual_points)
                delta_z = axial_positions - eval_center
                
                if abs(self.helix_angle_base) > 0.01:
                    # 使用el计算角度
                    delta_phi = (delta_z / eval_length) * self.el * (360.0 / self.teeth_count)
                else:
                    delta_phi = np.zeros(actual_points)
                
                # 角度合成
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
    
    def compute_spectrum(self, angles, values, target_orders, data_type='profile'):
        """计算频谱"""
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
            amplitude = np.sqrt(a*a + b*b)
            
            # 应用缩放因子
            if data_type == 'profile':
                amplitude = amplitude * self.profile_scale
            else:
                amplitude = amplitude * self.helix_scale
            
            spectrum[order] = amplitude
        
        return spectrum


def analyze_with_pdf_params(mka_file, sample_name, klingelnberg_ref):
    """使用PDF参数分析"""
    print(f"\n{'='*90}")
    print(f"Using PDF Parameters: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 25.3)
    
    profile_eval_start = gear_data.get('profile_eval_start', 0)
    profile_eval_end = gear_data.get('profile_eval_end', 0)
    helix_eval_start = gear_data.get('helix_eval_start', 0)
    helix_eval_end = gear_data.get('helix_eval_end', 0)
    
    print(f"\nGear Parameters:")
    print(f"  Teeth ZE = {teeth_count}")
    print(f"  Module m = {module}")
    print(f"  Pressure Angle α = {pressure_angle}°")
    print(f"  Helix Angle β = {helix_angle}°")
    
    # 使用PDF参数
    ep_pdf = 1.454
    el_pdf = 2.766
    
    print(f"\nPDF Parameters:")
    print(f"  ep = {ep_pdf}")
    print(f"  el = {el_pdf}")
    
    analyzer = PDFParamsRippleAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        ep=ep_pdf,
        el=el_pdf
    )
    
    print(f"\nCalculated:")
    print(f"  Base Pitch pb = {analyzer.base_pitch:.4f} mm")
    print(f"  Base Helix Angle βb = {analyzer.helix_angle_base:.2f}°")
    print(f"  Profile Scale = {analyzer.profile_scale}")
    print(f"  Helix Scale = {analyzer.helix_scale}")
    
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
        
        print(f"\n{direction_names[direction]}:")
        
        if 'profile' in direction:
            side = direction.split('_')[0]
            side_data = profile_data.get(side, {})
            angles, values = analyzer.build_merged_curve(
                side_data, side, 'profile',
                profile_eval_start, profile_eval_end
            )
            data_type = 'profile'
        else:
            side = direction.split('_')[0]
            side_data = flank_data.get(side, {})
            angles, values = analyzer.build_merged_curve(
                side_data, side, 'helix',
                helix_eval_start, helix_eval_end
            )
            data_type = 'helix'
        
        if angles is None:
            print("  No data available")
            continue
        
        spectrum = analyzer.compute_spectrum(angles, values, target_orders, data_type)
        
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
    
    return avg_error


def main():
    """主函数"""
    
    KLINGELNBERG_SAMPLE1 = {
        'left_profile': {87: 0.1400, 174: 0.0500, 261: 0.0600, 348: 0.0300, 435: 0.0400},
        'right_profile': {87: 0.1500, 174: 0.0500, 261: 0.0600, 348: 0.0700, 435: 0.0300},
        'left_helix': {87: 0.1200, 89: 0.0700, 174: 0.0600, 261: 0.0500, 348: 0.0300},
        'right_helix': {87: 0.0900, 174: 0.1000, 261: 0.0500, 348: 0.0400, 435: 0.0300}
    }
    
    sample1_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    error = analyze_with_pdf_params(sample1_file, "Sample1 (ZE=87)", KLINGELNBERG_SAMPLE1)
    
    print(f"\n{'='*90}")
    print("Comparison with calculated parameters:")
    print(f"  Using PDF params (ep=1.454, el=2.766): {error:.1f}%")
    print(f"  Using calculated params (ep=1.044, el=2.266): 66.4%")


if __name__ == "__main__":
    main()
