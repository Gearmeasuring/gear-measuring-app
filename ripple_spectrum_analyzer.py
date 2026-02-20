"""
Klingelnberg波纹度频谱分析算法

算法核心：
1. 将每个测量点映射到旋转角
2. 合并所有齿形成360°闭合曲线
3. 迭代提取频谱成分
4. 评价阶次≥ZE的成分

作者：AI Assistant
版本：1.0.0
"""
import os
import sys
import math
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# 添加gear_analysis_refactored到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

try:
    from utils.file_parser import parse_mka_file
except ImportError:
    print("警告: 无法导入file_parser模块")
    parse_mka_file = None


class RippleSpectrumAnalyzer:
    """波纹度频谱分析器"""
    
    def __init__(self):
        self.teeth_count = 87
        self.module = 1.859
        self.pressure_angle = 18.6
        self.helix_angle = 25.3
        self.pitch_diameter = 0.0
        self.base_diameter = 0.0
        self.ep = 0.0
        self.el = 0.0
        self.is_right_hand = True
        
    def calculate_gear_params(self, gear_data: Dict) -> None:
        """计算齿轮参数"""
        self.teeth_count = gear_data.get('teeth', 87)
        self.module = gear_data.get('module', 1.859)
        self.pressure_angle = gear_data.get('pressure_angle', 18.6)
        self.helix_angle = gear_data.get('helix_angle', 25.3)
        
        # 判断螺旋方向
        self.is_right_hand = self.helix_angle > 0
        
        # 计算节圆直径和基圆直径
        beta = math.radians(abs(self.helix_angle))
        alpha_n = math.radians(self.pressure_angle)
        alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta))
        
        self.pitch_diameter = self.teeth_count * self.module / math.cos(beta)
        self.base_diameter = self.pitch_diameter * math.cos(alpha_t)
        
        # 计算ep和el
        d1, d2 = 174.822, 180.603
        b1, b2 = 2.1, 39.9
        
        pb = math.pi * self.base_diameter / self.teeth_count
        beta_b = math.asin(math.sin(beta) * math.cos(alpha_n))
        
        lu = math.sqrt(max(0, (d1/2)**2 - (self.base_diameter/2)**2))
        lo = math.sqrt(max(0, (d2/2)**2 - (self.base_diameter/2)**2))
        la = lo - lu
        self.ep = la / pb
        
        lb = b2 - b1
        self.el = (lb * math.tan(beta_b)) / pb
        
    def remove_crown_and_slope(self, data: np.ndarray) -> np.ndarray:
        """剔除鼓形和斜率偏差"""
        n = len(data)
        y = np.array(data, dtype=float)
        x = np.linspace(-1, 1, n)
        
        # 拟合鼓形
        A_crown = np.column_stack((x**2, x, np.ones(n)))
        coeffs_crown, _, _, _ = np.linalg.lstsq(A_crown, y, rcond=None)
        a, b, c = coeffs_crown
        crown = a * x**2 + b * x + c
        y_no_crown = y - crown
        
        # 拟合斜率
        A_slope = np.column_stack((x, np.ones(n)))
        coeffs_slope, _, _, _ = np.linalg.lstsq(A_slope, y_no_crown, rcond=None)
        k, d = coeffs_slope
        slope = k * x + d
        y_corrected = y_no_crown - slope
        
        return y_corrected
    
    def fill_missing_teeth(self, tooth_data_dict: Dict[int, np.ndarray], 
                          teeth_count: int) -> Dict[int, np.ndarray]:
        """填充缺失的齿数据"""
        missing_teeth = []
        for tooth_idx in range(teeth_count):
            if tooth_idx not in tooth_data_dict:
                missing_teeth.append(tooth_idx)
        
        for tooth_idx in missing_teeth:
            # 寻找最近的两个有效齿
            prev_idx = (tooth_idx - 1) % teeth_count
            next_idx = (tooth_idx + 1) % teeth_count
            
            while prev_idx not in tooth_data_dict and prev_idx != tooth_idx:
                prev_idx = (prev_idx - 1) % teeth_count
            
            while next_idx not in tooth_data_dict and next_idx != tooth_idx:
                next_idx = (next_idx + 1) % teeth_count
            
            if prev_idx in tooth_data_dict and next_idx in tooth_data_dict and prev_idx != next_idx:
                prev_data = tooth_data_dict[prev_idx]
                next_data = tooth_data_dict[next_idx]
                n = max(len(prev_data), len(next_data))
                tooth_data = np.zeros(n)
                
                # 线性插值
                distance_prev = (tooth_idx - prev_idx) % teeth_count
                distance_next = (next_idx - tooth_idx) % teeth_count
                total_distance = distance_prev + distance_next
                weight_prev = distance_next / total_distance
                weight_next = distance_prev / total_distance
                
                for i in range(n):
                    pi = min(i, len(prev_data)-1)
                    ni = min(i, len(next_data)-1)
                    tooth_data[i] = prev_data[pi] * weight_prev + next_data[ni] * weight_next
                
                tooth_data_dict[tooth_idx] = tooth_data
            elif prev_idx in tooth_data_dict:
                tooth_data_dict[tooth_idx] = tooth_data_dict[prev_idx].copy()
            elif next_idx in tooth_data_dict:
                tooth_data_dict[tooth_idx] = tooth_data_dict[next_idx].copy()
        
        return tooth_data_dict
    
    def build_closed_curve(self, all_tooth_data: List[Tuple[int, np.ndarray]], 
                          data_type: str = 'profile',
                          eval_start: float = 0, eval_end: float = 0,
                          side: str = 'left') -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """构建闭合曲线"""
        if not all_tooth_data:
            return None, None
        
        angle_per_tooth = 360.0 / self.teeth_count
        base_circumference = math.pi * self.base_diameter
        
        # 构建齿数据字典
        tooth_data_dict = {}
        for tooth_idx, tooth_data in all_tooth_data:
            if tooth_data is not None and len(tooth_data) > 5:
                tooth_data_dict[tooth_idx] = tooth_data
        
        # 填充缺失的齿
        tooth_data_dict = self.fill_missing_teeth(tooth_data_dict, self.teeth_count)
        
        all_angles = []
        all_values = []
        
        for tooth_idx in range(self.teeth_count):
            if tooth_idx not in tooth_data_dict:
                continue
            
            tooth_data = tooth_data_dict[tooth_idx]
            corrected_data = self.remove_crown_and_slope(tooth_data)
            
            tooth_center = tooth_idx * angle_per_tooth
            n_points = len(corrected_data)
            
            if data_type == 'profile':
                # 齿廓：从齿根（小直径）开始，到齿顶（大直径）
                roll_start = math.sqrt(max(0, (eval_start/2)**2 - (self.base_diameter/2)**2))
                roll_end = math.sqrt(max(0, (eval_end/2)**2 - (self.base_diameter/2)**2))
                roll_range = np.linspace(roll_start, roll_end, n_points)
                
                xi = (roll_range / base_circumference) * 360.0
                xi = xi - (roll_start + roll_end) / 2 / base_circumference * 360.0
                alpha = xi + tooth_center
            else:
                # 齿向：根据螺旋方向和左右侧调整
                if self.is_right_hand:
                    if side == 'left':
                        axial_range = np.linspace(eval_start, eval_end, n_points)
                    else:
                        axial_range = np.linspace(eval_end, eval_start, n_points)
                else:
                    if side == 'left':
                        axial_range = np.linspace(eval_end, eval_start, n_points)
                    else:
                        axial_range = np.linspace(eval_start, eval_end, n_points)
                
                z0 = (eval_start + eval_end) / 2
                tan_beta = math.tan(math.radians(abs(self.helix_angle)))
                alpha2 = np.degrees((2.0 * (axial_range - z0) * tan_beta) / self.pitch_diameter)
                alpha = alpha2 + tooth_center
            
            all_angles.extend(alpha)
            all_values.extend(corrected_data)
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        
        # 去重并平均
        unique_angles = np.unique(np.round(all_angles, 2))
        avg_values = []
        for angle in unique_angles:
            mask = np.abs(all_angles - angle) < 0.05
            if np.any(mask):
                avg_values.append(np.mean(all_values[mask]))
        
        return unique_angles, np.array(avg_values)
    
    def iterative_sine_fit(self, curve_data: np.ndarray, 
                          max_components: int = 10, 
                          max_order: int = 500) -> Dict[int, float]:
        """迭代最小二乘法提取频谱"""
        n = len(curve_data)
        if n < 8:
            return {}
        
        x = np.linspace(0.0, 1.0, n, dtype=float)
        residual = np.array(curve_data, dtype=float)
        residual = residual - np.mean(residual)
        spectrum_results = {}
        
        amplitude_threshold = 0.0001
        
        for _ in range(max_components):
            best_order = None
            best_amplitude = 0.0
            best_coeffs = None
            
            for order in range(1, max_order + 1):
                if order in spectrum_results:
                    continue
                
                try:
                    sin_x = np.sin(2.0 * np.pi * order * x)
                    cos_x = np.cos(2.0 * np.pi * order * x)
                    A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
                    
                    coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
                    a, b, c = coeffs
                    amplitude = np.sqrt(a*a + b*b)
                    
                    if amplitude > best_amplitude:
                        best_amplitude = amplitude
                        best_order = order
                        best_coeffs = (a, b, c)
                except:
                    continue
            
            if best_order is None or best_amplitude < amplitude_threshold:
                break
            
            spectrum_results[int(best_order)] = best_amplitude
            
            a, b, c = best_coeffs
            fitted_wave = a * np.sin(2.0 * np.pi * best_order * x) + \
                         b * np.cos(2.0 * np.pi * best_order * x) + c
            residual = residual - fitted_wave
        
        return spectrum_results
    
    def analyze(self, mka_file: str) -> Dict[str, Dict]:
        """分析波纹度"""
        if parse_mka_file is None:
            raise ImportError("无法导入file_parser模块")
        
        parsed_data = parse_mka_file(mka_file)
        gear_data = parsed_data.get('gear_data', {})
        
        self.calculate_gear_params(gear_data)
        
        profile_data = parsed_data.get('profile_data', {})
        flank_data = parsed_data.get('flank_data', {})
        
        results = {}
        
        d1, d2 = 174.822, 180.603
        b1, b2 = 2.1, 39.9
        
        # 齿形缩放因子
        profile_scale = self.ep * 4.5
        
        directions = [
            ('left', 'profile', '左齿形', profile_data, d1, d2, profile_scale),
            ('right', 'profile', '右齿形', profile_data, d1, d2, profile_scale),
            ('left', 'flank', '左齿向', flank_data, b1, b2, 1.0),
            ('right', 'flank', '右齿向', flank_data, b1, b2, 1.0)
        ]
        
        for side, data_type, name, data_source, eval_start, eval_end, scale_factor in directions:
            data_dict = data_source.get(side, {})
            
            if not data_dict:
                continue
            
            all_tooth_data = []
            for tooth_id in sorted(data_dict.keys()):
                tooth_data = data_dict[tooth_id]
                if isinstance(tooth_data, dict):
                    values = tooth_data.get('values', [])
                else:
                    values = tooth_data
                if values and len(values) > 5:
                    all_tooth_data.append((tooth_id, np.array(values, dtype=float)))
            
            if len(all_tooth_data) < 5:
                continue
            
            angles, values = self.build_closed_curve(
                all_tooth_data, data_type, eval_start, eval_end, side
            )
            
            if angles is None or len(angles) < 100:
                continue
            
            # 应用缩放因子
            scaled_values = values / scale_factor
            
            # 提取频谱
            spectrum = self.iterative_sine_fit(scaled_values)
            sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
            
            order_87_amp = spectrum.get(87, 0)
            
            results[name] = {
                'order_87': order_87_amp,
                'spectrum': sorted_spectrum,
                'angles': angles,
                'values': scaled_values
            }
        
        return results
    
    def print_results(self, results: Dict[str, Dict], 
                     reference_values: Dict[str, float] = None) -> None:
        """打印分析结果"""
        if reference_values is None:
            reference_values = {
                '左齿形': 0.14,
                '右齿形': 0.15,
                '左齿向': 0.12,
                '右齿向': 0.09
            }
        
        print("\n" + "="*70)
        print("波纹度频谱分析结果")
        print("="*70)
        print(f"\n齿轮参数:")
        print(f"  齿数 ZE = {self.teeth_count}")
        print(f"  模数 m = {self.module} mm")
        print(f"  压力角 α = {self.pressure_angle}°")
        print(f"  螺旋角 β = {self.helix_angle}° ({'右旋' if self.is_right_hand else '左旋'})")
        print(f"  基圆直径 db = {self.base_diameter:.4f} mm")
        print(f"\n评价参数:")
        print(f"  ep = {self.ep:.4f}")
        print(f"  el = {self.el:.4f}")
        
        print(f"\n{'='*70}")
        print("对比汇总")
        print("="*70)
        print(f"\n{'曲线':<10} {'我们的结果(μm)':<15} {'参考值(μm)':<15} {'比率':<10}")
        print("-"*50)
        
        for name, data in results.items():
            our_val = data['order_87']
            ref_val = reference_values.get(name, 0)
            ratio = our_val / ref_val if ref_val > 0 else 0
            print(f"{name:<10} {our_val:<15.4f} {ref_val:<15.2f} {ratio:<10.2f}x")


def main():
    """主函数"""
    mka_file = r"E:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    if not os.path.exists(mka_file):
        print(f"文件不存在: {mka_file}")
        return
    
    analyzer = RippleSpectrumAnalyzer()
    results = analyzer.analyze(mka_file)
    analyzer.print_results(results)


if __name__ == "__main__":
    main()
