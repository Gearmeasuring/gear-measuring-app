"""
根据Klingelnberg论文实现的波纹度分析算法

关键公式：
- ep = lp / pb  (评价长度与基节的比值)
- el = (Ib × tan(βb)) / pb  (螺旋线相关)
- 角度合成使用论文中的标准公式
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


class KlingelnbergPaperRippleAnalyzer:
    """基于Klingelnberg论文的波纹度分析器"""
    
    def __init__(self, teeth_count, module, pressure_angle=20.0, helix_angle=0.0, 
                 face_width=0.0, eval_length_profile=0.0, eval_length_helix=0.0):
        self.teeth_count = teeth_count
        self.module = module
        self.pressure_angle = pressure_angle
        self.helix_angle = helix_angle
        self.face_width = face_width
        self.eval_length_profile = eval_length_profile
        self.eval_length_helix = eval_length_helix
        
        # 基本参数计算
        self.pitch_diameter = module * teeth_count
        self.pitch_radius = self.pitch_diameter / 2.0
        self.base_diameter = self.pitch_diameter * math.cos(math.radians(pressure_angle))
        self.base_radius = self.base_diameter / 2.0
        
        # 基节计算
        self.base_pitch = math.pi * self.base_diameter / teeth_count
        
        # 节圆处螺旋角
        if abs(helix_angle) > 0.01:
            # tan(βb) = tan(β) * cos(α)
            self.helix_angle_base = math.degrees(math.atan(
                math.tan(math.radians(helix_angle)) * math.cos(math.radians(pressure_angle))
            ))
        else:
            self.helix_angle_base = 0.0
        
        # ep和el计算
        if eval_length_profile > 0 and self.base_pitch > 0:
            self.ep = eval_length_profile / self.base_pitch
        else:
            self.ep = 1.0  # 默认值
        
        if face_width > 0 and self.base_pitch > 0 and abs(self.helix_angle_base) > 0.01:
            self.el = (face_width * math.tan(math.radians(self.helix_angle_base))) / self.base_pitch
        else:
            self.el = 0.0
        
        print(f"  Base Pitch pb = {self.base_pitch:.4f} mm")
        print(f"  Helix Angle at Base βb = {self.helix_angle_base:.2f}°")
        print(f"  ep (Profile) = {self.ep:.4f}")
        print(f"  el (Helix) = {self.el:.4f}")
    
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
        """预处理：去除趋势"""
        if len(values) < order + 1:
            return values - np.mean(values)
        
        n = len(values)
        x = np.arange(n)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        coeffs = np.polyfit(x_norm, values, order)
        trend = np.polyval(coeffs, x_norm)
        
        return values - trend
    
    def build_profile_merged_curve(self, side_data, side, eval_start, eval_end):
        """
        构建齿形合并曲线
        使用论文中的角度合成公式
        """
        if not side_data:
            return None, None
        
        sorted_teeth = sorted(side_data.keys())
        
        all_angles = []
        all_values = []
        
        # 计算评价长度范围内的角度跨度
        # 根据论文，使用ep来计算
        angle_span_per_tooth = 360.0 / self.teeth_count * self.ep
        
        for tooth_id in sorted_teeth:
            tooth_values = side_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            actual_points = len(tooth_values)
            eval_values = np.array(tooth_values, dtype=float)
            
            # 预处理 - 根据论文去除鼓形和斜率
            corrected_values = self.preprocess_tooth_data(eval_values, order=2)
            
            # 计算齿距角 τ
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * 360.0 / self.teeth_count
            
            # 计算渐开线极角 ξ
            if eval_start > 0 and eval_end > 0:
                radii = np.linspace(eval_start/2, eval_end/2, actual_points)
            else:
                radii = np.linspace(self.pitch_radius * 0.95, self.pitch_radius * 1.05, actual_points)
            
            xi_angles = np.array([self.calculate_involute_angle(r) for r in radii])
            
            # 根据论文的角度合成公式
            # φ = -ξ + τ (右齿面) 或 φ = +ξ + τ (左齿面)
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
        
        # 归一化到0-360度
        all_angles = all_angles % 360.0
        sort_idx = np.argsort(all_angles)
        
        return all_angles[sort_idx], all_values[sort_idx]
    
    def build_helix_merged_curve(self, side_data, side, eval_start, eval_end):
        """
        构建齿向合并曲线
        使用论文中的角度合成公式，考虑el
        """
        if not side_data:
            return None, None
        
        sorted_teeth = sorted(side_data.keys())
        
        all_angles = []
        all_values = []
        
        eval_center = (eval_start + eval_end) / 2.0
        
        # 根据el计算轴向角度跨度
        if abs(self.helix_angle_base) > 0.01 and self.el > 0:
            # 使用el来计算角度跨度
            delta_phi_max = 180.0 * self.el / self.teeth_count  # 简化的角度计算
        else:
            delta_phi_max = 0.0
        
        for tooth_id in sorted_teeth:
            tooth_values = side_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            actual_points = len(tooth_values)
            eval_values = np.array(tooth_values, dtype=float)
            
            # 预处理
            corrected_values = self.preprocess_tooth_data(eval_values, order=2)
            
            # 计算轴向位置
            axial_positions = np.linspace(eval_start, eval_end, actual_points)
            delta_z = axial_positions - eval_center
            
            # 计算轴向旋转角 Δφ
            # 根据论文，使用el来计算
            if abs(self.helix_angle_base) > 0.01 and self.face_width > 0:
                # Δφ = (Δz / face_width) * el * (360° / ZE)
                delta_phi = (delta_z / self.face_width) * self.el * (360.0 / self.teeth_count)
            else:
                delta_phi = np.zeros(actual_points)
            
            # 计算齿距角 τ
            tooth_index = int(tooth_id) - 1
            tau = tooth_index * 360.0 / self.teeth_count
            
            # 根据论文的角度合成公式
            # φ = -Δφ + τ (右齿面) 或 φ = +Δφ + τ (左齿面)
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
        
        # 归一化到0-360度
        all_angles = all_angles % 360.0
        sort_idx = np.argsort(all_angles)
        
        return all_angles[sort_idx], all_values[sort_idx]
    
    def compute_spectrum(self, angles, values, target_orders, data_type='profile'):
        """计算频谱 - 使用论文中的方法"""
        if angles is None or values is None:
            return {}
        
        # 去除重复角度点
        unique_angles, unique_indices = np.unique(np.round(angles, 4), return_index=True)
        unique_values = values[unique_indices]
        
        # 在0-360度范围内均匀插值
        num_points = max(360, 2 * 5 * self.teeth_count + 10)
        interp_angles = np.linspace(0, 360, num_points, endpoint=False)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        # 转换为弧度
        theta = np.radians(interp_angles)
        
        spectrum = {}
        for order in target_orders:
            # 最小二乘法拟合
            cos_x = np.cos(order * theta)
            sin_x = np.sin(order * theta)
            A = np.column_stack((cos_x, sin_x))
            coeffs, _, _, _ = np.linalg.lstsq(A, interp_values, rcond=None)
            a, b = coeffs
            
            # 振幅计算
            amplitude = np.sqrt(a*a + b*b)
            
            # 根据论文，振幅可能需要根据ep或el调整
            # 对于齿形数据，使用ep
            # 对于齿向数据，使用el
            if data_type == 'profile' and self.ep > 0:
                # 齿形：可能需要除以sqrt(ep)或ep
                amplitude = amplitude / np.sqrt(self.ep)
            elif data_type == 'helix' and abs(self.el) > 0:
                # 齿向：可能需要除以sqrt(|el|)或|el|
                amplitude = amplitude / np.sqrt(abs(self.el))
            
            spectrum[order] = amplitude
        
        return spectrum


def analyze_sample_paper(mka_file, sample_name, klingelnberg_ref):
    """使用Klingelnberg论文算法分析样本"""
    print(f"\n{'='*90}")
    print(f"Klingelnberg Paper Algorithm: {sample_name}")
    print(f"{'='*90}")
    
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 0.0)
    face_width = gear_data.get('face_width', 28.0)
    
    # 计算评价长度
    profile_eval_start = gear_data.get('profile_eval_start', 0)
    profile_eval_end = gear_data.get('profile_eval_end', 0)
    eval_length_profile = profile_eval_end - profile_eval_start if profile_eval_end > profile_eval_start else 0
    
    helix_eval_start = gear_data.get('helix_eval_start', 0)
    helix_eval_end = gear_data.get('helix_eval_end', 0)
    eval_length_helix = helix_eval_end - helix_eval_start if helix_eval_end > helix_eval_start else 0
    
    print(f"\nGear Parameters:")
    print(f"  Teeth ZE = {teeth_count}")
    print(f"  Module m = {module}")
    print(f"  Pressure Angle α = {pressure_angle}°")
    print(f"  Helix Angle β = {helix_angle}°")
    print(f"  Face Width = {face_width} mm")
    print(f"  Profile Eval Length = {eval_length_profile:.3f} mm")
    print(f"  Helix Eval Length = {eval_length_helix:.3f} mm")
    
    analyzer = KlingelnbergPaperRippleAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        face_width=face_width,
        eval_length_profile=eval_length_profile,
        eval_length_helix=eval_length_helix
    )
    
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
            angles, values = analyzer.build_profile_merged_curve(
                side_data, side,
                profile_eval_start, profile_eval_end
            )
        else:
            side = direction.split('_')[0]
            side_data = flank_data.get(side, {})
            angles, values = analyzer.build_helix_merged_curve(
                side_data, side,
                helix_eval_start, helix_eval_end
            )
        
        if angles is None:
            print("  No data available")
            continue
        
        data_type = 'profile' if 'profile' in direction else 'helix'
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
    
    result1 = analyze_sample_paper(sample1_file, "Sample1 (ZE=87)", KLINGELNBERG_SAMPLE1)
    result2 = analyze_sample_paper(sample2_file, "Sample2 (ZE=26)", KLINGELNBERG_SAMPLE2)
    
    print(f"\n{'='*90}")
    print("SUMMARY")
    print(f"{'='*90}")
    
    print(f"\nSample1 (ZE=87): Average Error = {result1['avg_error']:.1f}%")
    print(f"Sample2 (ZE=26): Average Error = {result2['avg_error']:.1f}%")


if __name__ == "__main__":
    main()
