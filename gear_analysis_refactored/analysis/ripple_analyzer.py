"""
齿轮波纹度分析算法模块

按照《波纹度算法说明.md》文档实现完整算法流程

算法流程：
1. 数据预处理（去除鼓形、斜率偏差）
2. 角度合成（齿形/齿向）
3. 曲线合并（构建0-360度闭合曲线）
4. 频谱分析（最小二乘法正弦波分解）
5. 高阶波纹度评价（阶次≥ZE的分量）

作者：Gear Analysis Team
版本：2.0.0
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional, NamedTuple
from dataclasses import dataclass, field
from enum import Enum


class DataType(Enum):
    PROFILE = "profile"
    HELIX = "helix"


class Side(Enum):
    LEFT = "left"
    RIGHT = "right"


@dataclass
class GearParameters:
    teeth_count: int
    module: float
    pressure_angle: float = 20.0
    helix_angle: float = 0.0
    base_diameter: float = 0.0
    
    def __post_init__(self):
        self.pitch_diameter = self.module * self.teeth_count
        self.pitch_angle = 360.0 / self.teeth_count
        
        if self.base_diameter <= 0:
            beta = math.radians(self.helix_angle)
            alpha_n = math.radians(self.pressure_angle)
            alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta)) if abs(beta) > 1e-6 else alpha_n
            self.base_diameter = self.pitch_diameter * math.cos(alpha_t)
        
        self.base_radius = self.base_diameter / 2.0
        self.pitch_radius = self.pitch_diameter / 2.0


@dataclass
class EvaluationRange:
    eval_start: float
    eval_end: float
    meas_start: float
    meas_end: float


@dataclass
class SpectrumComponent:
    order: int
    amplitude: float
    phase: float
    coefficient_a: float
    coefficient_b: float


@dataclass
class SpectrumResult:
    components: List[SpectrumComponent]
    orders: np.ndarray
    amplitudes: np.ndarray
    phases: np.ndarray
    reconstructed: np.ndarray
    residual: np.ndarray
    original: np.ndarray


@dataclass
class HighOrderResult:
    high_order_indices: np.ndarray
    high_order_waves: np.ndarray
    high_order_amplitudes: np.ndarray
    total_amplitude: float
    rms: float
    reconstructed: np.ndarray


@dataclass
class RippleAnalysisResult:
    angles: np.ndarray
    values: np.ndarray
    interp_angles: np.ndarray
    interp_values: np.ndarray
    spectrum: SpectrumResult
    high_order: HighOrderResult
    data_type: DataType
    side: Side


class DataPreprocessor:
    """数据预处理器：去除鼓形和斜率偏差"""
    
    @staticmethod
    def remove_crown_and_slope(data: np.ndarray) -> np.ndarray:
        """
        剔除鼓形和斜率偏差
        
        步骤：
        1. 用二元二次多项式（抛物线）去除鼓形
        2. 用一元一次多项式（线性）去除斜率偏差
        
        Args:
            data: 原始测量数据
            
        Returns:
            修正后的数据
        """
        if len(data) < 3:
            return np.array(data, dtype=float)
        
        data = np.array(data, dtype=float)
        n = len(data)
        x = np.linspace(-1, 1, n)
        
        A_crown = np.column_stack((x**2, x, np.ones(n)))
        coeffs_crown, _, _, _ = np.linalg.lstsq(A_crown, data, rcond=None)
        a, b, c = coeffs_crown
        crown = a * x**2 + b * x + c
        data_no_crown = data - crown
        
        A_slope = np.column_stack((x, np.ones(n)))
        coeffs_slope, _, _, _ = np.linalg.lstsq(A_slope, data_no_crown, rcond=None)
        k, d = coeffs_slope
        slope = k * x + d
        data_corrected = data_no_crown - slope
        
        return data_corrected


class AngleSynthesizer:
    """角度合成器：计算旋转角度"""
    
    def __init__(self, gear_params: GearParameters):
        self.params = gear_params
    
    def calculate_involute_polar_angle(self, radius: float) -> float:
        """
        计算渐开线极角
        
        公式: inv(α) = tan(α) - α
        其中: α = arccos(rb/r)
        
        Args:
            radius: 测量点半径
            
        Returns:
            极角（弧度）
        """
        if radius <= self.params.base_radius or self.params.base_radius <= 0:
            return 0.0
        
        cos_alpha = self.params.base_radius / radius
        if cos_alpha >= 1.0:
            return 0.0
        
        alpha = math.acos(cos_alpha)
        polar_angle = math.tan(alpha) - alpha
        
        return polar_angle
    
    def calculate_roll_angle(self, diameter: float) -> float:
        """
        计算展长对应的角度
        
        展长 s(d) = sqrt((d/2)^2 - (db/2)^2)
        旋转角 ξ = s/(π×db)×360°
        
        Args:
            diameter: 测量点直径
            
        Returns:
            旋转角度（度）
        """
        radius = diameter / 2.0
        if radius <= self.params.base_radius:
            return 0.0
        
        roll_length = math.sqrt(radius**2 - self.params.base_radius**2)
        base_circumference = math.pi * self.params.base_diameter
        
        if base_circumference <= 0:
            return 0.0
        
        roll_angle = (roll_length / base_circumference) * 360.0
        return roll_angle
    
    def calculate_axial_rotation_angle(self, axial_position: float, center_position: float) -> float:
        """
        计算轴向位置产生的旋转角度
        
        公式: Δφ = 2 × Δz × tan(β₀) / D₀
        
        Args:
            axial_position: 轴向位置
            center_position: 评价范围中心位置
            
        Returns:
            旋转角度（度）
        """
        if abs(self.params.helix_angle) < 0.01 or self.params.pitch_diameter <= 0:
            return 0.0
        
        delta_z = axial_position - center_position
        tan_beta = math.tan(math.radians(abs(self.params.helix_angle)))
        
        delta_phi_rad = 2.0 * delta_z * tan_beta / self.params.pitch_diameter
        delta_phi_deg = math.degrees(delta_phi_rad)
        
        return delta_phi_deg
    
    def synthesize_profile_angles(self, diameters: np.ndarray, tooth_index: int, side: Side) -> np.ndarray:
        """
        合成齿形旋转角度
        
        公式: φ = -ξ + τ
        其中:
        - ξ: 渐开线极角（展长对应的角度）
        - τ: 节距角 = 齿序号 × 360° / 齿数
        
        Args:
            diameters: 测量点直径数组
            tooth_index: 齿序号（从0开始）
            side: 左/右齿面
            
        Returns:
            旋转角度数组（度）
        """
        roll_angles = np.array([self.calculate_roll_angle(d) for d in diameters])
        roll_angles = roll_angles - np.mean(roll_angles)
        
        tau = tooth_index * self.params.pitch_angle
        
        if side == Side.LEFT:
            final_angles = tau - roll_angles
        else:
            final_angles = tau + roll_angles
        
        return final_angles
    
    def synthesize_profile_angles_from_roll(self, roll_lengths: np.ndarray, tooth_index: int, side: Side) -> np.ndarray:
        """
        从展长合成齿形旋转角度
        
        公式: φ = -ξ + τ
        其中:
        - ξ: 展长对应的角度 = s/(π×db)×360°
        - τ: 节距角 = 齿序号 × 360° / 齿数
        
        Args:
            roll_lengths: 展长数组 (mm)
            tooth_index: 齿序号（从0开始）
            side: 左/右齿面
            
        Returns:
            旋转角度数组（度）
        """
        base_circumference = math.pi * self.params.base_diameter
        
        if base_circumference <= 0:
            return np.zeros_like(roll_lengths)
        
        roll_angles = (roll_lengths / base_circumference) * 360.0
        roll_angles = roll_angles - np.mean(roll_angles)
        
        tau = tooth_index * self.params.pitch_angle
        
        if side == Side.LEFT:
            final_angles = tau - roll_angles
        else:
            final_angles = tau + roll_angles
        
        return final_angles
    
    def synthesize_helix_angles(self, axial_positions: np.ndarray, tooth_index: int, 
                                 eval_range: EvaluationRange, side: Side) -> np.ndarray:
        """
        合成齿向旋转角度
        
        公式: φ = -Δφ + τ
        其中:
        - Δφ: 轴向位置旋转 = 2 × Δz × tan(β₀) / D₀
        - τ: 节距角 = 齿序号 × 360° / 齿数
        
        Args:
            axial_positions: 轴向位置数组
            tooth_index: 齿序号（从0开始）
            eval_range: 评价范围
            side: 左/右齿面
            
        Returns:
            旋转角度数组（度）
        """
        center = (eval_range.eval_start + eval_range.eval_end) / 2.0
        delta_phis = np.array([self.calculate_axial_rotation_angle(z, center) for z in axial_positions])
        
        tau = tooth_index * self.params.pitch_angle
        
        if side == Side.LEFT:
            final_angles = tau - delta_phis
        else:
            final_angles = tau + delta_phis
        
        return final_angles


class CurveMerger:
    """曲线合并器：构建0-360度闭合曲线"""
    
    def __init__(self, gear_params: GearParameters, preprocessor: DataPreprocessor, 
                 synthesizer: AngleSynthesizer):
        self.params = gear_params
        self.preprocessor = preprocessor
        self.synthesizer = synthesizer
    
    def calc_roll_length(self, diameter: float) -> float:
        """计算展长 s(d) = sqrt((d/2)² - (db/2)²)"""
        radius = diameter / 2.0
        if radius <= self.params.base_radius:
            return 0.0
        return math.sqrt(radius**2 - self.params.base_radius**2)
    
    def process_tooth_data(self, tooth_values: np.ndarray, eval_range: EvaluationRange,
                           data_type: DataType = DataType.PROFILE) -> Tuple[np.ndarray, np.ndarray]:
        """
        处理单个齿的数据，提取评价范围内的数据并预处理
        
        对于齿形数据，评价范围是按展长计算的：
        - eval_start/eval_end 是直径 d1/d2
        - 需要转换为展长 s(d) = sqrt((d/2)² - (db/2)²)
        - 然后按展长比例提取数据
        
        Args:
            tooth_values: 齿的测量数据
            eval_range: 评价范围
            data_type: 数据类型
            
        Returns:
            (评价范围内的数据, 评价范围内的位置数组)
        """
        n = len(tooth_values)
        
        if data_type == DataType.PROFILE:
            s_eval_start = self.calc_roll_length(eval_range.eval_start)
            s_eval_end = self.calc_roll_length(eval_range.eval_end)
            s_meas_start = self.calc_roll_length(eval_range.meas_start)
            s_meas_end = self.calc_roll_length(eval_range.meas_end)
            
            if s_meas_end > s_meas_start and s_eval_end > s_eval_start:
                start_ratio = (s_eval_start - s_meas_start) / (s_meas_end - s_meas_start)
                end_ratio = (s_eval_end - s_meas_start) / (s_meas_end - s_meas_start)
                
                start_idx = int(n * max(0.0, min(1.0, start_ratio)))
                end_idx = int(n * max(0.0, min(1.0, end_ratio)))
            else:
                start_idx = 0
                end_idx = n
            
            eval_values = np.array(tooth_values[start_idx:end_idx], dtype=float)
            corrected_values = self.preprocessor.remove_crown_and_slope(eval_values)
            
            s_range = np.linspace(s_eval_start, s_eval_end, len(corrected_values))
            
            return corrected_values, s_range
        else:
            if eval_range.meas_end > eval_range.meas_start and eval_range.eval_end > eval_range.eval_start:
                start_ratio = (eval_range.eval_start - eval_range.meas_start) / (eval_range.meas_end - eval_range.meas_start)
                end_ratio = (eval_range.eval_end - eval_range.meas_start) / (eval_range.meas_end - eval_range.meas_start)
                
                start_idx = int(n * max(0.0, min(1.0, start_ratio)))
                end_idx = int(n * max(0.0, min(1.0, end_ratio)))
            else:
                start_idx = 0
                end_idx = n
            
            eval_values = np.array(tooth_values[start_idx:end_idx], dtype=float)
            corrected_values = self.preprocessor.remove_crown_and_slope(eval_values)
            
            positions = np.linspace(eval_range.eval_start, eval_range.eval_end, len(corrected_values))
            
            return corrected_values, positions
    
    def build_closed_curve(self, tooth_data_dict: Dict[int, np.ndarray], 
                           data_type: DataType, side: Side,
                           eval_range: EvaluationRange) -> Tuple[np.ndarray, np.ndarray]:
        """
        构建闭合曲线
        
        将所有齿的数据合并，归一化到0-360度范围
        
        Args:
            tooth_data_dict: 齿数据字典 {齿序号: 测量数据}
            data_type: 数据类型（齿形/齿向）
            side: 左/右齿面
            eval_range: 评价范围
            
        Returns:
            (角度数组, 值数组)
        """
        if not tooth_data_dict:
            return None, None
        
        all_angles = []
        all_values = []
        
        for tooth_id, tooth_values in tooth_data_dict.items():
            if tooth_values is None or len(tooth_values) < 3:
                continue
            
            corrected_values, positions = self.process_tooth_data(tooth_values, eval_range, data_type)
            
            if len(corrected_values) < 3:
                continue
            
            tooth_index = int(tooth_id) if isinstance(tooth_id, (int, str)) and str(tooth_id).isdigit() else 0
            
            if data_type == DataType.PROFILE:
                roll_lengths = positions
                angles = self.synthesizer.synthesize_profile_angles_from_roll(roll_lengths, tooth_index, side)
            else:
                axial_positions = positions
                angles = self.synthesizer.synthesize_helix_angles(axial_positions, tooth_index, eval_range, side)
            
            all_angles.extend(angles.tolist())
            all_values.extend(corrected_values.tolist())
        
        if not all_angles:
            return None, None
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        
        all_angles = all_angles % 360.0
        all_angles[all_angles < 0] += 360.0
        
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        
        unique_angles, unique_indices = np.unique(np.round(all_angles, 3), return_index=True)
        unique_values = all_values[unique_indices]
        
        return unique_angles, unique_values
    
    def interpolate_curve(self, angles: np.ndarray, values: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        数据插值
        
        1. 去除重复角度点
        2. 在0-360度范围内均匀插值
        3. 满足奈奎斯特采样定理
        
        Args:
            angles: 角度数组
            values: 值数组
            
        Returns:
            (插值后的角度数组, 插值后的值数组)
        """
        num_points = max(360, 2 * 5 * self.params.teeth_count + 10)
        
        interp_angles = np.linspace(0, 360, num_points)
        interp_values = np.interp(interp_angles, angles, values, period=360)
        
        return interp_angles, interp_values


class SpectrumAnalyzer:
    """频谱分析器：最小二乘法正弦波分解"""
    
    def __init__(self, gear_params: GearParameters):
        self.params = gear_params
    
    def fit_sine_wave(self, angles_rad: np.ndarray, values: np.ndarray, 
                       order: int) -> SpectrumComponent:
        """
        使用最小二乘法拟合指定阶次的正弦波
        
        y = A×cos(order×θ) + B×sin(order×θ)
        
        Args:
            angles_rad: 角度数组（弧度）
            values: 值数组
            order: 阶次
            
        Returns:
            频谱分量
        """
        cos_term = np.cos(order * angles_rad)
        sin_term = np.sin(order * angles_rad)
        
        A = np.column_stack([cos_term, sin_term])
        coeffs, _, _, _ = np.linalg.lstsq(A, values, rcond=None)
        
        a, b = coeffs[0], coeffs[1]
        amplitude = np.sqrt(a**2 + b**2)
        phase = np.arctan2(a, b)
        
        return SpectrumComponent(
            order=order,
            amplitude=amplitude,
            phase=phase,
            coefficient_a=a,
            coefficient_b=b
        )
    
    def find_max_amplitude_order(self, angles_rad: np.ndarray, values: np.ndarray,
                                  max_order: int, min_order: int = 1,
                                  excluded_orders: set = None) -> Tuple[int, float, SpectrumComponent]:
        """
        寻找振幅最大的阶次
        
        Args:
            angles_rad: 角度数组（弧度）
            values: 值数组
            max_order: 最大搜索阶次
            min_order: 最小搜索阶次
            excluded_orders: 已排除的阶次集合
            
        Returns:
            (阶次, 振幅, 频谱分量)
        """
        if excluded_orders is None:
            excluded_orders = set()
        
        best_order = min_order
        best_amplitude = 0
        best_component = None
        
        for order in range(min_order, max_order + 1):
            if order in excluded_orders:
                continue
            
            component = self.fit_sine_wave(angles_rad, values, order)
            
            if component.amplitude > best_amplitude:
                best_amplitude = component.amplitude
                best_order = order
                best_component = component
        
        return best_order, best_amplitude, best_component
    
    def iterative_decomposition(self, angles: np.ndarray, values: np.ndarray,
                                 num_components: int = 10, verbose: bool = False) -> SpectrumResult:
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
            频谱分析结果
        """
        max_order = 5 * self.params.teeth_count
        
        angles_rad = np.radians(angles)
        residual = np.array(values, dtype=float)
        residual = residual - np.mean(residual)
        
        components = []
        extracted_orders = set()
        
        if verbose:
            print(f"\n迭代正弦波分解算法:")
            print(f"  最大搜索阶次: {max_order}")
            print(f"  提取分量数: {num_components}")
            print(f"  初始信号范围: [{residual.min():.4f}, {residual.max():.4f}] um")
            print("-" * 60)
        
        for i in range(num_components):
            order, amplitude, component = self.find_max_amplitude_order(
                angles_rad, residual, max_order, min_order=1,
                excluded_orders=extracted_orders
            )
            
            extracted_orders.add(order)
            components.append(component)
            
            fitted = component.coefficient_a * np.cos(order * angles_rad) + \
                     component.coefficient_b * np.sin(order * angles_rad)
            residual = residual - fitted
            
            if verbose:
                print(f"  周期 {i+1}: 阶次={order}, 振幅={amplitude:.4f} um, "
                      f"相位={np.degrees(component.phase):.1f}°, "
                      f"残差RMS={np.sqrt(np.mean(residual**2)):.4f} um")
        
        orders = np.array([c.order for c in components])
        amplitudes = np.array([c.amplitude for c in components])
        phases = np.array([c.phase for c in components])
        
        reconstructed = np.zeros_like(values)
        for c in components:
            reconstructed += c.coefficient_a * np.cos(c.order * angles_rad) + \
                            c.coefficient_b * np.sin(c.order * angles_rad)
        
        if verbose:
            print("-" * 60)
            print(f"  重构信号范围: [{reconstructed.min():.4f}, {reconstructed.max():.4f}] um")
            print(f"  最终残差RMS: {np.sqrt(np.mean(residual**2)):.4f} um")
        
        return SpectrumResult(
            components=components,
            orders=orders,
            amplitudes=amplitudes,
            phases=phases,
            reconstructed=reconstructed,
            residual=residual,
            original=np.array(values)
        )


class HighOrderEvaluator:
    """高阶波纹度评价器"""
    
    DEFAULT_AMPLITUDE_SCALE = 0.1
    
    def __init__(self, gear_params: GearParameters, amplitude_scale: float = None):
        self.params = gear_params
        self.amplitude_scale = amplitude_scale if amplitude_scale is not None else self.DEFAULT_AMPLITUDE_SCALE
    
    def evaluate(self, spectrum: SpectrumResult, angles: np.ndarray) -> HighOrderResult:
        """
        计算高阶波纹度（波数≥ZE的分量）
        
        W值（高阶总振幅）= Σ(高阶分量振幅) × 缩放因子
        RMS值 = √(mean(高阶重构信号²)) × 缩放因子
        
        Args:
            spectrum: 频谱分析结果
            angles: 角度数组（度）
            
        Returns:
            高阶波纹度评价结果
        """
        orders = spectrum.orders
        amplitudes = spectrum.amplitudes * self.amplitude_scale
        
        high_order_mask = orders >= self.params.teeth_count
        high_order_indices = np.where(high_order_mask)[0]
        high_order_waves = orders[high_order_mask]
        high_order_amplitudes = amplitudes[high_order_mask]
        
        angles_rad = np.radians(angles)
        high_order_reconstructed = np.zeros_like(angles, dtype=float)
        
        for idx in high_order_indices:
            if idx < len(spectrum.components):
                c = spectrum.components[idx]
                high_order_reconstructed += c.coefficient_a * np.cos(c.order * angles_rad) + \
                                            c.coefficient_b * np.sin(c.order * angles_rad)
        
        high_order_reconstructed *= self.amplitude_scale
        
        total_amplitude = np.sum(high_order_amplitudes)
        rms = np.sqrt(np.mean(high_order_reconstructed ** 2))
        
        return HighOrderResult(
            high_order_indices=high_order_indices,
            high_order_waves=high_order_waves,
            high_order_amplitudes=high_order_amplitudes,
            total_amplitude=total_amplitude,
            rms=rms,
            reconstructed=high_order_reconstructed
        )


class RippleAnalyzer:
    """波纹度分析器主类"""
    
    def __init__(self, gear_params: GearParameters, amplitude_scale: float = 0.1):
        self.params = gear_params
        self.amplitude_scale = amplitude_scale
        self.preprocessor = DataPreprocessor()
        self.synthesizer = AngleSynthesizer(gear_params)
        self.merger = CurveMerger(gear_params, self.preprocessor, self.synthesizer)
        self.spectrum_analyzer = SpectrumAnalyzer(gear_params)
        self.high_order_evaluator = HighOrderEvaluator(gear_params, amplitude_scale)
    
    def analyze(self, tooth_data_dict: Dict[int, np.ndarray], 
                data_type: DataType, side: Side,
                eval_range: EvaluationRange,
                verbose: bool = False) -> Optional[RippleAnalysisResult]:
        """
        执行完整的波纹度分析
        
        Args:
            tooth_data_dict: 齿数据字典
            data_type: 数据类型（齿形/齿向）
            side: 左/右齿面
            eval_range: 评价范围
            verbose: 是否输出详细日志
            
        Returns:
            波纹度分析结果
        """
        angles, values = self.merger.build_closed_curve(
            tooth_data_dict, data_type, side, eval_range
        )
        
        if angles is None or len(angles) < 10:
            return None
        
        interp_angles, interp_values = self.merger.interpolate_curve(angles, values)
        
        spectrum = self.spectrum_analyzer.iterative_decomposition(
            interp_angles, interp_values, num_components=10, verbose=verbose
        )
        
        high_order = self.high_order_evaluator.evaluate(spectrum, interp_angles)
        
        return RippleAnalysisResult(
            angles=angles,
            values=values,
            interp_angles=interp_angles,
            interp_values=interp_values,
            spectrum=spectrum,
            high_order=high_order,
            data_type=data_type,
            side=side
        )
    
    def analyze_all_directions(self, profile_data: Dict, flank_data: Dict,
                                profile_eval_range: EvaluationRange,
                                helix_eval_range: EvaluationRange,
                                verbose: bool = False) -> Dict[str, RippleAnalysisResult]:
        """
        分析所有方向的波纹度
        
        Args:
            profile_data: 齿形数据 {'left': {齿序号: 数据}, 'right': {齿序号: 数据}}
            flank_data: 齿向数据 {'left': {齿序号: 数据}, 'right': {齿序号: 数据}}
            profile_eval_range: 齿形评价范围
            helix_eval_range: 齿向评价范围
            verbose: 是否输出详细日志
            
        Returns:
            所有方向的分析结果
        """
        results = {}
        
        for side in [Side.LEFT, Side.RIGHT]:
            side_key = side.value
            
            if side_key in profile_data and profile_data[side_key]:
                result = self.analyze(
                    profile_data[side_key], DataType.PROFILE, side,
                    profile_eval_range, verbose
                )
                if result:
                    results[f"{side_key}_profile"] = result
            
            if side_key in flank_data and flank_data[side_key]:
                result = self.analyze(
                    flank_data[side_key], DataType.HELIX, side,
                    helix_eval_range, verbose
                )
                if result:
                    results[f"{side_key}_helix"] = result
        
        return results
    
    def print_results(self, results: Dict[str, RippleAnalysisResult]) -> None:
        """打印分析结果"""
        print("\n" + "=" * 70)
        print("波纹度分析结果汇总")
        print("=" * 70)
        
        print(f"\n齿轮参数:")
        print(f"  齿数 ZE = {self.params.teeth_count}")
        print(f"  模数 m = {self.params.module} mm")
        print(f"  压力角 α = {self.params.pressure_angle}°")
        print(f"  螺旋角 β = {self.params.helix_angle}°")
        print(f"  节圆直径 D₀ = {self.params.pitch_diameter:.3f} mm")
        print(f"  基圆直径 db = {self.params.base_diameter:.3f} mm")
        
        for name, result in results.items():
            print(f"\n{'='*70}")
            print(f"【{name}】")
            print('='*70)
            
            spectrum = result.spectrum
            high_order = result.high_order
            
            print(f"  数据点数: {len(result.interp_angles)}")
            print(f"\n  前10个较大阶次:")
            for i, (order, amp, phase) in enumerate(zip(
                spectrum.orders, spectrum.amplitudes, spectrum.phases
            )):
                marker = " ★" if order >= self.params.teeth_count else ""
                print(f"    {i+1}. 阶次 {order:3d}: 幅值 = {amp:.4f} μm, 相位 = {np.degrees(phase):.1f}°{marker}")
            
            print(f"\n  高阶波纹度 (阶次≥{self.params.teeth_count}):")
            print(f"    高阶波数: {list(high_order.high_order_waves)}")
            print(f"    高阶振幅: {[f'{a:.4f}' for a in high_order.high_order_amplitudes]}")
            print(f"    总振幅 W = {high_order.total_amplitude:.4f} μm")
            print(f"    RMS = {high_order.rms:.4f} μm")
