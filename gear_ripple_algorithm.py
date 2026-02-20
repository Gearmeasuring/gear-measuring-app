"""
齿轮波纹度分析算法实现
按照《波纹度算法说明.md》文档实现完整算法流程

算法流程：
1. 数据预处理（去除鼓形、斜率偏差）
2. 角度合成（齿形/齿向）
3. 频谱分析（迭代正弦波分解）
4. 高阶波纹度计算
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import math
from typing import Dict, List, Tuple, Optional

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from utils.file_parser import parse_mka_file


class GearRippleAnalyzer:
    """齿轮波纹度分析器"""
    
    def __init__(self, teeth_count: int, module: float, pressure_angle: float = 20.0,
                 helix_angle: float = 0.0, base_diameter: float = 0.0):
        """
        初始化分析器
        
        Args:
            teeth_count: 齿数 (ZE)
            module: 模数 (m)
            pressure_angle: 压力角 (α)
            helix_angle: 螺旋角 (β₀)
            base_diameter: 基圆直径
        """
        self.teeth_count = teeth_count
        self.module = module
        self.pressure_angle = pressure_angle
        self.helix_angle = helix_angle
        
        self.pitch_diameter = module * teeth_count  # 节圆直径 D₀
        self.pitch_angle = 360.0 / teeth_count  # 节距角 τ
        
        if base_diameter > 0:
            self.base_diameter = base_diameter
        else:
            self.base_diameter = self.pitch_diameter * math.cos(math.radians(pressure_angle))
        
        self.base_radius = self.base_diameter / 2.0
        self.pitch_radius = self.pitch_diameter / 2.0
        
        print(f"齿轮参数:")
        print(f"  齿数 ZE = {teeth_count}")
        print(f"  模数 m = {module} mm")
        print(f"  压力角 α = {pressure_angle}°")
        print(f"  螺旋角 β₀ = {helix_angle}°")
        print(f"  节圆直径 D₀ = {self.pitch_diameter:.3f} mm")
        print(f"  基圆直径 db = {self.base_diameter:.3f} mm")
        print(f"  节距角 τ = {self.pitch_angle:.4f}°")
    
    def remove_slope_and_crowning(self, data: np.ndarray) -> np.ndarray:
        """
        去除斜率偏差和鼓形
        
        步骤：
        1. 用二元二次多项式（抛物线）去除鼓形
        2. 用一元一次多项式（线性）去除斜率偏差
        """
        if len(data) < 3:
            return data
        
        data = np.array(data, dtype=float)
        n = len(data)
        x = np.arange(n, dtype=float)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        # 步骤1：去除鼓形（二元二次多项式拟合）
        crowning_coeffs = np.polyfit(x_norm, data, 2)
        crowning_curve = np.polyval(crowning_coeffs, x_norm)
        data_after_crowning = data - crowning_curve
        
        # 步骤2：去除斜率偏差（一元一次多项式拟合）
        slope_coeffs = np.polyfit(x_norm, data_after_crowning, 1)
        slope_curve = np.polyval(slope_coeffs, x_norm)
        corrected_data = data_after_crowning - slope_curve
        
        return corrected_data
    
    def calculate_involute_polar_angle(self, radius: float) -> float:
        """
        计算渐开线极角
        
        公式: inv(α) = tan(α) - α
        其中: α = arccos(rb/r)
        """
        if radius <= self.base_radius or self.base_radius <= 0:
            return 0.0
        
        cos_alpha = self.base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        
        alpha = math.acos(cos_alpha)
        polar_angle = math.tan(alpha) - alpha
        
        return polar_angle
    
    def process_profile_tooth(self, tooth_values: np.ndarray, tooth_id: int,
                              eval_start: float, eval_end: float,
                              meas_start: float, meas_end: float,
                              side: str = 'left') -> Tuple[np.ndarray, np.ndarray]:
        """
        处理单个齿的齿形数据
        
        角度合成公式: φ = -ξ + τ
        其中:
        - ξ: 渐开线极角
        - τ: 节距角 = 齿序号 × 360° / 齿数
        """
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
        
        # 只使用评价范围内的数据
        eval_values = np.array(tooth_values[start_idx:end_idx], dtype=float)
        eval_points = len(eval_values)
        
        if eval_points < 3:
            return None, None
        
        # 数据预处理：去除鼓形和斜率偏差
        corrected_values = self.remove_slope_and_crowning(eval_values)
        
        # 计算渐开线极角
        if eval_start > 0 and eval_end > 0:
            radii = np.linspace(eval_start/2, eval_end/2, eval_points)
        else:
            radii = np.linspace(self.pitch_radius * 0.95, self.pitch_radius * 1.05, eval_points)
        
        polar_angles = np.array([self.calculate_involute_polar_angle(r) for r in radii])
        polar_angles_deg = np.degrees(polar_angles)
        
        # 计算齿序号和节距角
        tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
        tau_angle = tooth_index * self.pitch_angle
        
        # 角度合成: φ = -ξ + τ
        if side == 'left':
            final_angles = tau_angle - polar_angles_deg
        else:
            final_angles = tau_angle + polar_angles_deg
        
        return final_angles, corrected_values
    
    def process_helix_tooth(self, tooth_values: np.ndarray, tooth_id: int,
                            eval_start: float, eval_end: float,
                            meas_start: float, meas_end: float,
                            side: str = 'left') -> Tuple[np.ndarray, np.ndarray]:
        """
        处理单个齿的齿向数据
        
        角度合成公式: φ = -Δφ + τ
        其中:
        - Δφ: 轴向位置旋转 = 2 × Δz × tan(β₀) / D₀
        - τ: 节距角 = 齿序号 × 360° / 齿数
        """
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
        
        # 只使用评价范围内的数据
        eval_values = np.array(tooth_values[start_idx:end_idx], dtype=float)
        eval_points = len(eval_values)
        
        if eval_points < 3:
            return None, None
        
        # 数据预处理：去除鼓形和斜率偏差
        corrected_values = self.remove_slope_and_crowning(eval_values)
        
        # 计算轴向旋转角度 Δφ = 2 × Δz × tan(β₀) / D₀
        if abs(self.helix_angle) > 0.01 and self.pitch_diameter > 0:
            # 生成轴向位置数组
            axial_positions = np.linspace(eval_start, eval_end, eval_points)
            # 计算评价范围中心
            eval_center = (eval_start + eval_end) / 2.0
            # 计算相对于中心的轴向距离 Δz
            delta_z = axial_positions - eval_center
            # 使用标准公式计算轴向旋转角度
            tan_beta0 = math.tan(math.radians(self.helix_angle))
            delta_phi_rad = 2 * delta_z * tan_beta0 / self.pitch_diameter
            delta_phi_deg = np.degrees(delta_phi_rad)
        else:
            delta_phi_deg = np.linspace(0, 1, eval_points)
        
        # 计算齿序号和节距角
        tooth_index = int(tooth_id) - 1 if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
        tau_angle = tooth_index * self.pitch_angle
        
        # 角度合成: φ = -Δφ + τ
        if side == 'left':
            final_angles = tau_angle - delta_phi_deg
        else:
            final_angles = tau_angle + delta_phi_deg
        
        return final_angles, corrected_values
    
    def build_merged_curve(self, data_dict: Dict, data_type: str, side: str,
                           eval_start: float, eval_end: float,
                           meas_start: float, meas_end: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        构建合并后的旋转角曲线
        
        将所有齿的数据合并，归一化到0-360度范围
        """
        if side not in data_dict or not data_dict[side]:
            return None, None
        
        side_data = data_dict[side]
        sorted_teeth = sorted(side_data.keys())
        
        all_angles = []
        all_values = []
        
        for tooth_id in sorted_teeth:
            tooth_values = side_data[tooth_id]
            if tooth_values is None or len(tooth_values) == 0:
                continue
            
            if data_type == 'profile':
                angles, values = self.process_profile_tooth(
                    tooth_values, tooth_id,
                    eval_start, eval_end, meas_start, meas_end, side
                )
            else:  # helix
                angles, values = self.process_helix_tooth(
                    tooth_values, tooth_id,
                    eval_start, eval_end, meas_start, meas_end, side
                )
            
            if angles is not None and values is not None:
                all_angles.extend(angles.tolist())
                all_values.extend(values.tolist())
        
        if not all_angles:
            return None, None
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        
        # 归一化到 0-360 度范围
        all_angles = all_angles % 360.0
        all_angles[all_angles < 0] += 360.0
        
        # 按角度排序
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        
        return all_angles, all_values
    
    def interpolate_curve(self, angles: np.ndarray, values: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        数据插值
        
        1. 去除重复角度点
        2. 在0-360度范围内均匀插值
        3. 满足奈奎斯特采样定理
        """
        # 去除重复角度点
        unique_angles, unique_indices = np.unique(np.round(angles, 3), return_index=True)
        unique_values = values[unique_indices]
        
        # 计算插值点数 = max(360, 2×5×ZE+10)
        num_interp_points = max(360, 2 * 5 * self.teeth_count + 10)
        
        # 均匀插值
        interp_angles = np.linspace(0, 360, num_interp_points)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        return interp_angles, interp_values
    
    def fit_sine_wave_least_squares(self, angles_rad: np.ndarray, values: np.ndarray, 
                                     order: int) -> Dict:
        """
        使用最小二乘法拟合指定阶次的正弦波
        
        y = A×sin(order×θ) + B×cos(order×θ)
        """
        cos_term = np.cos(order * angles_rad)
        sin_term = np.sin(order * angles_rad)
        
        A = np.column_stack([cos_term, sin_term])
        coeffs, residuals, rank, s = np.linalg.lstsq(A, values, rcond=None)
        
        a, b = coeffs[0], coeffs[1]
        amplitude = np.sqrt(a**2 + b**2)
        phase = np.arctan2(a, b)
        
        fitted = a * cos_term + b * sin_term
        residual = values - fitted
        
        return {
            'amplitude': amplitude,
            'phase': phase,
            'fitted': fitted,
            'residual': residual,
            'coefficients': (a, b)
        }
    
    def find_max_amplitude_order(self, angles_rad: np.ndarray, values: np.ndarray,
                                  max_order: int, min_order: int = 1,
                                  excluded_orders: set = None) -> Dict:
        """寻找振幅最大的阶次"""
        if excluded_orders is None:
            excluded_orders = set()
        
        best_order = min_order
        best_amplitude = 0
        best_result = None
        
        for order in range(min_order, max_order + 1):
            if order in excluded_orders:
                continue
            
            result = self.fit_sine_wave_least_squares(angles_rad, values, order)
            
            if result['amplitude'] > best_amplitude:
                best_amplitude = result['amplitude']
                best_order = order
                best_result = result
        
        return {
            'order': best_order,
            'amplitude': best_amplitude,
            'fit_result': best_result
        }
    
    def iterative_sine_decomposition(self, angles: np.ndarray, values: np.ndarray,
                                      num_components: int = 10, verbose: bool = True) -> Dict:
        """
        迭代正弦波分解算法
        
        核心流程：
        1. 计算选定频率范围内补偿正弦波函数的振幅
        2. 振幅最大的补偿正弦波被视为第一主导频率
        3. 将该主导正弦波函数从偏差曲线中剔除
        4. 对剩余偏差进行重新分析
        5. 经过10个周期后，得到包含10个最大振幅的频谱
        
        Args:
            angles: 角度数组（度）
            values: 偏差值数组
            num_components: 提取的分量数（默认10）
            verbose: 是否输出详细日志
            
        Returns:
            包含阶次、振幅、相位等信息的字典
        """
        max_order = 5 * self.teeth_count
        
        angles_rad = np.radians(angles)
        residual = np.array(values, dtype=float)
        
        orders = []
        amplitudes = []
        phases = []
        components = []
        extracted_orders = set()
        
        if verbose:
            print(f"\n迭代正弦波分解算法:")
            print(f"  最大搜索阶次: {max_order}")
            print(f"  提取分量数: {num_components}")
            print(f"  初始信号范围: [{residual.min():.4f}, {residual.max():.4f}] um")
            print("-" * 60)
        
        for i in range(num_components):
            # 步骤1: 在当前信号中寻找振幅最大的阶次
            result = self.find_max_amplitude_order(
                angles_rad, residual, max_order, min_order=1,
                excluded_orders=extracted_orders
            )
            
            order = result['order']
            extracted_orders.add(order)
            
            # 步骤2: 使用最小二乘法拟合该阶次的正弦波
            fit_result = self.fit_sine_wave_least_squares(angles_rad, residual, order)
            
            orders.append(order)
            amplitudes.append(fit_result['amplitude'])
            phases.append(fit_result['phase'])
            components.append(fit_result['fitted'])
            
            # 步骤3: 从信号中减去已提取的分量（剔除主导正弦波）
            residual = fit_result['residual']
            
            # 步骤4: 输出迭代信息
            if verbose:
                print(f"  周期 {i+1}: 阶次={order}, 振幅={fit_result['amplitude']:.4f} um, "
                      f"相位={np.degrees(fit_result['phase']):.1f}°, "
                      f"残差RMS={np.sqrt(np.mean(residual**2)):.4f} um")
        
        # 重构信号
        reconstructed = np.zeros_like(values)
        for comp in components:
            reconstructed += comp
        
        if verbose:
            print("-" * 60)
            print(f"  重构信号范围: [{reconstructed.min():.4f}, {reconstructed.max():.4f}] um")
            print(f"  最终残差RMS: {np.sqrt(np.mean(residual**2)):.4f} um")
        
        return {
            'orders': np.array(orders),
            'amplitudes': np.array(amplitudes),
            'phases': np.array(phases),
            'components': components,
            'residual': residual,
            'original': np.array(values),
            'reconstructed': reconstructed
        }
    
    def calculate_high_order_undulation(self, spectrum_result: Dict) -> Dict:
        """
        计算高阶波纹度（波数≥ZE的分量）
        
        W值（高阶总振幅）= Σ(高阶分量振幅)
        RMS值 = √(mean(高阶重构信号²))
        """
        orders = spectrum_result['orders']
        amplitudes = spectrum_result['amplitudes']
        phases = spectrum_result['phases']
        components = spectrum_result['components']
        
        # 高阶分量筛选：波数 ≥ ZE
        high_order_mask = orders >= self.teeth_count
        
        high_order_indices = np.where(high_order_mask)[0]
        high_order_waves = orders[high_order_mask]
        high_order_amplitudes = amplitudes[high_order_mask]
        high_order_phases = phases[high_order_mask]
        
        # 高阶重构信号
        high_order_reconstructed = np.zeros_like(spectrum_result['original'])
        for idx in high_order_indices:
            if idx < len(components):
                high_order_reconstructed += components[idx]
        
        # 评价指标
        total_amplitude = np.sum(high_order_amplitudes)
        rms = np.sqrt(np.mean(high_order_reconstructed ** 2))
        
        return {
            'high_order_indices': high_order_indices,
            'high_order_waves': high_order_waves,
            'high_order_amplitudes': high_order_amplitudes,
            'high_order_phases': high_order_phases,
            'total_high_order_amplitude': total_amplitude,
            'high_order_rms': rms,
            'high_order_reconstructed': high_order_reconstructed,
            'ze': self.teeth_count
        }
    
    def analyze_spectrum(self, curve_data: Tuple[np.ndarray, np.ndarray]) -> Dict:
        """
        分析频谱
        
        完整流程：
        1. 数据插值
        2. 迭代正弦波分解
        3. 高阶波纹度计算
        """
        if curve_data is None or len(curve_data[0]) == 0:
            return None
        
        angles, values = curve_data
        
        # 数据插值
        interp_angles, interp_values = self.interpolate_curve(angles, values)
        
        # 迭代正弦波分解
        spectrum = self.iterative_sine_decomposition(interp_angles, interp_values, num_components=10)
        
        # 高阶波纹度计算
        high_order = self.calculate_high_order_undulation(spectrum)
        
        return {
            'spectrum': spectrum,
            'high_order': high_order,
            'interp_angles': interp_angles,
            'interp_values': interp_values
        }
    
    def plot_results(self, curve_data: Tuple[np.ndarray, np.ndarray], 
                     spectrum_data: Dict, title: str, output_file: str):
        """
        绘制分析结果图表
        
        包含：
        1. 前10波数振幅柱状图
        2. 原始信号vs重构信号
        3. 残差信号
        4. 高阶分量合成
        """
        if curve_data is None or spectrum_data is None:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(title, fontsize=14, fontweight='bold')
        
        angles = curve_data[0]
        values = curve_data[1]
        spectrum = spectrum_data['spectrum']
        high_order = spectrum_data['high_order']
        
        # 图1: 前10波数振幅柱状图
        ax1 = axes[0, 0]
        orders = spectrum['orders']
        amplitudes = spectrum['amplitudes']
        
        bar_colors = ['red' if o >= self.teeth_count else 'steelblue' for o in orders]
        bars = ax1.bar(range(len(orders)), amplitudes, color=bar_colors, alpha=0.8)
        ax1.set_xlabel('Component Index')
        ax1.set_ylabel('Amplitude (um)')
        ax1.set_title(f'Top 10 Waves per Revolution\n(Red: High Order >= {self.teeth_count})')
        ax1.set_xticks(range(len(orders)))
        ax1.set_xticklabels([f'{o}' for o in orders])
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 图2: 原始信号vs重构信号
        ax2 = axes[0, 1]
        interp_angles = spectrum_data['interp_angles']
        interp_values = spectrum_data['interp_values']
        ax2.plot(interp_angles, interp_values, 'b-', alpha=0.5, label='Original', linewidth=1)
        ax2.plot(interp_angles, spectrum['reconstructed'], 'r-', alpha=0.8, 
                label='Reconstructed', linewidth=1.5)
        ax2.set_xlabel('Rotation Angle (deg)')
        ax2.set_ylabel('Deviation (um)')
        ax2.set_title('Original vs Reconstructed')
        ax2.set_xlim(0, 360)
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper right', fontsize=8)
        
        # 图3: 残差信号
        ax3 = axes[1, 0]
        ax3.plot(interp_angles, spectrum['residual'], 'g-', alpha=0.7, linewidth=1)
        ax3.set_xlabel('Rotation Angle (deg)')
        ax3.set_ylabel('Residual (um)')
        ax3.set_title('Residual Signal')
        ax3.set_xlim(0, 360)
        ax3.grid(True, alpha=0.3)
        
        # 图4: 高阶分量合成
        ax4 = axes[1, 1]
        ax4.plot(interp_angles, high_order['high_order_reconstructed'], 'm-', alpha=0.8, linewidth=1.5)
        ax4.set_xlabel('Rotation Angle (deg)')
        ax4.set_ylabel('High Order (um)')
        ax4.set_title(f'High Order Components (>= {self.teeth_count})')
        ax4.set_xlim(0, 360)
        ax4.grid(True, alpha=0.3)
        
        # 添加统计信息
        info_text = f"""Spectrum Analysis Results:

Top 10 Waves:
"""
        for i, (order, amp, phase) in enumerate(zip(orders, amplitudes, spectrum['phases'])):
            info_text += f"  {order} waves/rev: {amp:.4f} um, {np.degrees(phase):.1f} deg\n"
        
        info_text += f"""
High Order Undulation (>={self.teeth_count}):
  Waves: {list(high_order['high_order_waves'])}
  Total Amplitude (W): {high_order['total_high_order_amplitude']:.4f} um
  RMS: {high_order['high_order_rms']:.4f} um
"""
        
        fig.text(0.02, 0.02, info_text, fontsize=8, verticalalignment='bottom',
                fontfamily='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Saved: {output_file}")
        plt.close()


def main():
    """主函数：按照波纹度算法说明文档执行完整分析"""
    
    # 读取MKA文件
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    if not os.path.exists(mka_file):
        mka_file = os.path.join(current_dir, '004-xiaoxiao1.mka')
    
    print(f"读取文件: {mka_file}")
    print("="*60)
    
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    # 提取齿轮参数
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 20.0)
    helix_angle = gear_data.get('helix_angle', 0.0)
    base_diameter = gear_data.get('base_diameter', 0.0)
    
    # 创建分析器
    analyzer = GearRippleAnalyzer(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle,
        base_diameter=base_diameter
    )
    
    # 获取评价范围参数
    profile_eval_start = gear_data.get('profile_eval_start', 0)
    profile_eval_end = gear_data.get('profile_eval_end', 0)
    profile_meas_start = gear_data.get('profile_meas_start', 0)
    profile_meas_end = gear_data.get('profile_meas_end', 0)
    
    helix_eval_start = gear_data.get('helix_eval_start', 0)
    helix_eval_end = gear_data.get('helix_eval_end', 0)
    helix_meas_start = gear_data.get('helix_meas_start', 0)
    helix_meas_end = gear_data.get('helix_meas_end', 0)
    
    print(f"\n评价范围参数:")
    print(f"  齿形评价范围: {profile_eval_start} ~ {profile_eval_end} mm")
    print(f"  齿形测量范围: {profile_meas_start} ~ {profile_meas_end} mm")
    print(f"  齿向评价范围: {helix_eval_start} ~ {helix_eval_end} mm")
    print(f"  齿向测量范围: {helix_meas_start} ~ {helix_meas_end} mm")
    
    print(f"\n数据概况:")
    print(f"  左齿形: {len(profile_data.get('left', {}))} 齿")
    print(f"  右齿形: {len(profile_data.get('right', {}))} 齿")
    print(f"  左齿向: {len(flank_data.get('left', {}))} 齿")
    print(f"  右齿向: {len(flank_data.get('right', {}))} 齿")
    
    results = {}
    
    # 分析左齿形
    print("\n" + "="*60)
    print("分析左齿形...")
    left_profile_curve = analyzer.build_merged_curve(
        profile_data, 'profile', 'left',
        profile_eval_start, profile_eval_end,
        profile_meas_start, profile_meas_end
    )
    if left_profile_curve:
        results['left_profile'] = {
            'curve': left_profile_curve,
            'spectrum': analyzer.analyze_spectrum(left_profile_curve)
        }
        print(f"  左齿形: {len(left_profile_curve[0])} 个数据点")
        if results['left_profile']['spectrum']:
            ho = results['left_profile']['spectrum']['high_order']
            print(f"  高阶总振幅 W = {ho['total_high_order_amplitude']:.4f} um")
            print(f"  高阶RMS = {ho['high_order_rms']:.4f} um")
    
    # 分析右齿形
    print("\n" + "="*60)
    print("分析右齿形...")
    right_profile_curve = analyzer.build_merged_curve(
        profile_data, 'profile', 'right',
        profile_eval_start, profile_eval_end,
        profile_meas_start, profile_meas_end
    )
    if right_profile_curve:
        results['right_profile'] = {
            'curve': right_profile_curve,
            'spectrum': analyzer.analyze_spectrum(right_profile_curve)
        }
        print(f"  右齿形: {len(right_profile_curve[0])} 个数据点")
        if results['right_profile']['spectrum']:
            ho = results['right_profile']['spectrum']['high_order']
            print(f"  高阶总振幅 W = {ho['total_high_order_amplitude']:.4f} um")
            print(f"  高阶RMS = {ho['high_order_rms']:.4f} um")
    
    # 分析左齿向
    print("\n" + "="*60)
    print("分析左齿向...")
    left_helix_curve = analyzer.build_merged_curve(
        flank_data, 'helix', 'left',
        helix_eval_start, helix_eval_end,
        helix_meas_start, helix_meas_end
    )
    if left_helix_curve:
        results['left_helix'] = {
            'curve': left_helix_curve,
            'spectrum': analyzer.analyze_spectrum(left_helix_curve)
        }
        print(f"  左齿向: {len(left_helix_curve[0])} 个数据点")
        if results['left_helix']['spectrum']:
            ho = results['left_helix']['spectrum']['high_order']
            print(f"  高阶总振幅 W = {ho['total_high_order_amplitude']:.4f} um")
            print(f"  高阶RMS = {ho['high_order_rms']:.4f} um")
    
    # 分析右齿向
    print("\n" + "="*60)
    print("分析右齿向...")
    right_helix_curve = analyzer.build_merged_curve(
        flank_data, 'helix', 'right',
        helix_eval_start, helix_eval_end,
        helix_meas_start, helix_meas_end
    )
    if right_helix_curve:
        results['right_helix'] = {
            'curve': right_helix_curve,
            'spectrum': analyzer.analyze_spectrum(right_helix_curve)
        }
        print(f"  右齿向: {len(right_helix_curve[0])} 个数据点")
        if results['right_helix']['spectrum']:
            ho = results['right_helix']['spectrum']['high_order']
            print(f"  高阶总振幅 W = {ho['total_high_order_amplitude']:.4f} um")
            print(f"  高阶RMS = {ho['high_order_rms']:.4f} um")
    
    # 生成图表
    print("\n" + "="*60)
    print("生成分析图表...")
    
    if 'left_profile' in results and results['left_profile']['spectrum']:
        analyzer.plot_results(
            results['left_profile']['curve'],
            results['left_profile']['spectrum'],
            f'Left Profile (Involute) - z={teeth_count}, m={module}',
            os.path.join(current_dir, 'ripple_analysis_left_profile.png')
        )
    
    if 'right_profile' in results and results['right_profile']['spectrum']:
        analyzer.plot_results(
            results['right_profile']['curve'],
            results['right_profile']['spectrum'],
            f'Right Profile (Involute) - z={teeth_count}, m={module}',
            os.path.join(current_dir, 'ripple_analysis_right_profile.png')
        )
    
    if 'left_helix' in results and results['left_helix']['spectrum']:
        analyzer.plot_results(
            results['left_helix']['curve'],
            results['left_helix']['spectrum'],
            f'Left Helix - z={teeth_count}, m={module}, beta={helix_angle} deg',
            os.path.join(current_dir, 'ripple_analysis_left_helix.png')
        )
    
    if 'right_helix' in results and results['right_helix']['spectrum']:
        analyzer.plot_results(
            results['right_helix']['curve'],
            results['right_helix']['spectrum'],
            f'Right Helix - z={teeth_count}, m={module}, beta={helix_angle} deg',
            os.path.join(current_dir, 'ripple_analysis_right_helix.png')
        )
    
    # 输出最终结果汇总
    print("\n" + "="*60)
    print("波纹度分析结果汇总")
    print("="*60)
    
    for name, data in results.items():
        if data and data.get('spectrum'):
            spectrum = data['spectrum']['spectrum']
            high_order = data['spectrum']['high_order']
            print(f"\n{name}:")
            print(f"  前3波数: {list(spectrum['orders'][:3])}")
            print(f"  前3振幅: {[f'{a:.4f}' for a in spectrum['amplitudes'][:3]]}")
            print(f"  高阶总振幅 W: {high_order['total_high_order_amplitude']:.4f} um")
            print(f"  高阶RMS: {high_order['high_order_rms']:.4f} um")
    
    print("\n" + "="*60)
    print("分析完成!")


if __name__ == '__main__':
    main()
