"""
齿轮波纹度分析模块 - 完全重构版

算法说明：
对于齿形：
- 测量点沿着渐开线分布，根据渐开线理论计算每个点的极角
- 找出起评点，算出起始极角，以此类推，把每一个测量点的极角都算出来，直到终评点极角
- 从齿顶开始排列：
  - 右齿形：齿1=0°，齿2=节距角，齿3=2*节距角，按齿数节距角加每一个测量点的极角排列起来
  - 左齿形：齿1=0°，齿2=节距角，齿3=2*节距角，按齿数节距角减每一个测量点的极角排列起来
- y轴为测量值，组成0到360度的一周曲线
- 合并单个曲线前自动剔除鼓形（二元多项式方式）和斜率偏差（一元多项式方式）

对于齿向：
- 从起评点到终评点，每一个测量点的极角 = 2*(测量点-起评点)*tan(螺旋角)/节圆直径
- 右齿向：齿1=0°，齿2=节距角，齿3=2*节距角，按齿数节距角加每一个测量点的极角排列起来
- 左齿向：齿1=0°，齿2=节距角，齿3=2*节距角，按齿数节距角减每一个测量点的极角排列起来

频谱分析：
- 通过最小二乘法分解阶次最大的正弦波
- 从0度到360度合并的曲线中移除已提取的最大阶次正弦波
- 对剩余信号重复上述过程，直到提取出第十个较大的阶次
- 高阶评价：阶次 >= ZE（总齿数）为高阶波纹度

作者：Gear Analysis Team
版本：3.0.0
"""

import re
import os
import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


@dataclass
class GearParameters:
    """齿轮参数"""
    module: float
    teeth_count: int
    pressure_angle: float = 20.0
    helix_angle: float = 0.0
    tip_diameter: float = 0.0
    root_diameter: float = 0.0
    width: float = 0.0
    
    def __post_init__(self):
        self.pitch_diameter = self.module * self.teeth_count
        self.pitch_angle = 360.0 / self.teeth_count
        self.pitch_radius = self.pitch_diameter / 2.0
        
        beta = math.radians(self.helix_angle)
        alpha_n = math.radians(self.pressure_angle)
        if abs(beta) > 1e-6:
            alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta))
        else:
            alpha_t = alpha_n
        self.transverse_pressure_angle = math.degrees(alpha_t)
        self.base_diameter = self.pitch_diameter * math.cos(alpha_t)
        self.base_radius = self.base_diameter / 2.0


@dataclass
class EvaluationRange:
    """评价范围"""
    eval_start: float
    eval_end: float
    meas_start: float
    meas_end: float


@dataclass
class SpectrumComponent:
    """频谱分量"""
    order: int
    amplitude: float
    phase: float
    coefficient_a: float
    coefficient_b: float


@dataclass
class WavinessResult:
    """波纹度分析结果"""
    angles: np.ndarray
    values: np.ndarray
    spectrum_components: List[SpectrumComponent]
    high_order_amplitude: float
    high_order_rms: float
    high_order_waves: List[int]
    reconstructed_signal: np.ndarray


@dataclass
class PitchData:
    """周节数据"""
    tooth_num: int
    fp: float  # 单齿周节偏差
    Fp: float  # 累积周节偏差
    Fr: float  # 径向跳动


@dataclass
class PitchAnalysisResult:
    """周节分析结果"""
    teeth: List[int]
    fp_values: List[float]  # 单齿周节偏差
    Fp_values: List[float]  # 累积周节偏差
    Fr: float  # 径向跳动
    fp_max: float
    fp_min: float
    fp_avg: float
    Fp_max: float
    Fp_min: float
    Fp_avg: float
    side: str


class MKAFileReader:
    """MKA文件读取器"""

    UNDEFINED_VALUE = -2147483.648

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = ""
        self.gear_params: Optional[GearParameters] = None
        self.profile_eval_range: Optional[EvaluationRange] = None
        self.helix_eval_range: Optional[EvaluationRange] = None
        self.profile_data: Dict[str, Dict[int, np.ndarray]] = {'left': {}, 'right': {}}
        self.helix_data: Dict[str, Dict[int, np.ndarray]] = {'left': {}, 'right': {}}
        self.topography_data: Dict = {}
        self.pitch_data: Dict[str, Dict[int, Dict[str, float]]] = {'left': {}, 'right': {}}
        
    def read(self) -> bool:
        """读取并解析MKA文件"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"文件不存在: {self.file_path}")
        
        encodings = ['utf-8', 'gbk', 'latin-1']
        for encoding in encodings:
            try:
                with open(self.file_path, 'r', encoding=encoding, errors='ignore') as f:
                    self.content = f.read()
                break
            except:
                continue
        
        self._parse_gear_parameters()
        self._parse_evaluation_ranges()
        self._parse_measurement_data()
        
        return True
    
    def _parse_gear_parameters(self):
        """解析齿轮参数"""
        params = {}
        
        patterns = {
            'module': [r'Normalmodul[^:]*:\s*([\d.]+)', r'mn[^:]*:\s*([\d.]+)'],
            'teeth_count': [r'Zähnezahl[^:]*:\s*(\d+)', r'Z.*hnezahl[^:]*:\s*(\d+)', r'No\. of teeth[^:]*:\s*(\d+)'],
            'pressure_angle': [r'Eingriffswinkel[^:]*:\s*([\d.]+)', r'alpha[^:]*:\s*([\d.]+)'],
            'helix_angle': [r'Schrägungswinkel[^:]*:\s*(-?[\d.]+)', r'Schr.*gungswinkel[^:]*:\s*(-?[\d.]+)'],
            'tip_diameter': [r'Kopfkreisdurchmesser[^:]*:\s*([\d.]+)'],
            'root_diameter': [r'Fußkreisdurchmesser[^:]*:\s*([\d.]+)', r'Fu.*kreisdurchmesser[^:]*:\s*([\d.]+)'],
            'width': [r'Zahnbreite[^:]*:\s*([\d.]+)'],
        }
        
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, self.content, re.IGNORECASE)
                if match:
                    try:
                        value = match.group(1).strip()
                        if key == 'teeth_count':
                            params[key] = int(float(value))
                        else:
                            params[key] = float(value)
                        break
                    except ValueError:
                        continue
        
        if 'module' in params and 'teeth_count' in params:
            self.gear_params = GearParameters(
                module=params.get('module', 1.0),
                teeth_count=params.get('teeth_count', 20),
                pressure_angle=params.get('pressure_angle', 20.0),
                helix_angle=params.get('helix_angle', 0.0),
                tip_diameter=params.get('tip_diameter', 0.0),
                root_diameter=params.get('root_diameter', 0.0),
                width=params.get('width', 0.0)
            )
    
    def _parse_evaluation_ranges(self):
        """解析评价范围"""
        profile_patterns = {
            'meas_start': [r'da\s*\[?mm\]?\.*:?\s*([\d.]+)'],
            'eval_start': [r'd1\s*\[?mm\]?\.*:?\s*([\d.]+)'],
            'eval_end': [r'd2\s*\[?mm\]?\.*:?\s*([\d.]+)'],
            'meas_end': [r'de\s*\[?mm\]?\.*:?\s*([\d.]+)'],
        }
        
        helix_patterns = {
            'meas_start': [r'ba\s*\[?mm\]?\.*:?\s*([\d.]+)'],
            'eval_start': [r'b1\s*\[?mm\]?\.*:?\s*([\d.]+)'],
            'eval_end': [r'b2\s*\[?mm\]?\.*:?\s*([\d.]+)'],
            'meas_end': [r'be\s*\[?mm\]?\.*:?\s*([\d.]+)'],
        }
        
        profile_values = {}
        for key, pattern_list in profile_patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, self.content, re.IGNORECASE)
                if match:
                    try:
                        profile_values[key] = float(match.group(1))
                        break
                    except ValueError:
                        continue
        
        helix_values = {}
        for key, pattern_list in helix_patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, self.content, re.IGNORECASE)
                if match:
                    try:
                        helix_values[key] = float(match.group(1))
                        break
                    except ValueError:
                        continue
        
        if len(profile_values) == 4:
            self.profile_eval_range = EvaluationRange(
                eval_start=profile_values['eval_start'],
                eval_end=profile_values['eval_end'],
                meas_start=profile_values['meas_start'],
                meas_end=profile_values['meas_end']
            )
        
        if len(helix_values) == 4:
            self.helix_eval_range = EvaluationRange(
                eval_start=helix_values['eval_start'],
                eval_end=helix_values['eval_end'],
                meas_start=helix_values['meas_start'],
                meas_end=helix_values['meas_end']
            )
    
    def _parse_measurement_data(self):
        """解析测量数据"""
        self._parse_profile_data()
        self._parse_helix_data()
        self._parse_topography_data()
        self._parse_pitch_data()
    
    def _parse_profile_data(self):
        """解析齿形数据 (Profil)"""
        pattern = re.compile(
            r'Profil:\s*Zahn-Nr\.:\s*(\d+[a-z]?)\s*(links|rechts)\s*/\s*(\d+)\s*Werte\s*/\s*z=\s*([-\d.]+)',
            re.IGNORECASE
        )
        
        matches = list(pattern.finditer(self.content))
        
        for i, match in enumerate(matches):
            tooth_id_str = match.group(1)
            side_str = match.group(2).lower()
            num_points = int(match.group(3))
            z_value = float(match.group(4))
            
            tooth_id = int(re.match(r'(\d+)', tooth_id_str).group(1))
            side = 'left' if side_str == 'links' else 'right'
            
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(self.content)
            data_section = self.content[start_pos:end_pos]
            
            values = self._extract_values(data_section, num_points)
            
            if side not in self.profile_data:
                self.profile_data[side] = {}
            if tooth_id not in self.profile_data[side]:
                self.profile_data[side][tooth_id] = {}
            self.profile_data[side][tooth_id][z_value] = values
    
    def _parse_helix_data(self):
        """解析齿向数据 (Flankenlinie)"""
        pattern = re.compile(
            r'Flankenlinie:\s*Zahn-Nr\.:\s*(\d+[a-z]?)\s*(links|rechts)\s*/\s*(\d+)\s*Werte\s*/\s*d=\s*([-\d.]+)',
            re.IGNORECASE
        )
        
        matches = list(pattern.finditer(self.content))
        
        for i, match in enumerate(matches):
            tooth_id_str = match.group(1)
            side_str = match.group(2).lower()
            num_points = int(match.group(3))
            d_value = float(match.group(4))
            
            tooth_id = int(re.match(r'(\d+)', tooth_id_str).group(1))
            side = 'left' if side_str == 'links' else 'right'
            
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(self.content)
            data_section = self.content[start_pos:end_pos]
            
            values = self._extract_values(data_section, num_points)
            
            if side not in self.helix_data:
                self.helix_data[side] = {}
            if tooth_id not in self.helix_data[side]:
                self.helix_data[side][tooth_id] = {}
            self.helix_data[side][tooth_id][d_value] = values
    
    def _parse_topography_data(self):
        """解析形貌数据"""
        self.topography_data = {
            'profile': self.profile_data,
            'helix': self.helix_data
        }

    def _parse_pitch_data(self):
        """解析周节数据"""
        # 方法1: 查找 "linke Zahnflanke" 和 "rechte Zahnflanke" 格式的数据
        left_pattern = r'linke Zahnflanke\s*\n\s*Zahn-Nr\.\s+fp\s+Fp\s+Fr\s*\n((?:\s*\d+\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s*\n?)+)'
        right_pattern = r'rechte Zahnflanke\s*\n\s*Zahn-Nr\.\s+fp\s+Fp\s+Fr\s*\n((?:\s*\d+\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s*\n?)+)'

        # 提取左侧周节数据
        left_match = re.search(left_pattern, self.content, re.IGNORECASE)
        if left_match:
            left_data_text = left_match.group(1)
            left_data_lines = left_data_text.strip().split('\n')

            for line in left_data_lines:
                line = line.strip()
                if line and re.match(r'^\d+', line):
                    parts = line.split()
                    if len(parts) >= 4:
                        tooth_num = int(parts[0])
                        fp = float(parts[1])
                        Fp = float(parts[2])
                        Fr = float(parts[3])

                        self.pitch_data['left'][tooth_num] = {
                            'fp': fp,
                            'Fp': Fp,
                            'Fr': Fr
                        }

        # 提取右侧周节数据
        right_match = re.search(right_pattern, self.content, re.IGNORECASE)
        if right_match:
            right_data_text = right_match.group(1)
            right_data_lines = right_data_text.strip().split('\n')

            for line in right_data_lines:
                line = line.strip()
                if line and re.match(r'^\d+', line):
                    parts = line.split()
                    if len(parts) >= 4:
                        tooth_num = int(parts[0])
                        fp = float(parts[1])
                        Fp = float(parts[2])
                        Fr = float(parts[3])

                        self.pitch_data['right'][tooth_num] = {
                            'fp': fp,
                            'Fp': Fp,
                            'Fr': Fr
                        }

    def _extract_values(self, data_section: str, expected_points: int) -> np.ndarray:
        """从数据段提取数值"""
        next_block_patterns = [
            r'Flankenlinie:\s*Zahn-Nr',
            r'Profil:\s*Zahn-Nr',
            r'TOPOGRAFIE:',
        ]
        
        lines = data_section.split('\n')
        clean_lines = []
        for line in lines:
            stop = False
            for pattern in next_block_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    stop = True
                    break
            if stop:
                break
            if re.search(r'\s+[LR]\s+', line) or re.search(r'^\s*\d+\s+[LR]\s+', line):
                break
            number_pattern = re.compile(r'[-+]?\d*\.?\d+')
            nums = number_pattern.findall(line)
            if len(nums) < 6 and len(clean_lines) > 0:
                break
            clean_lines.append(line)
        
        clean_section = '\n'.join(clean_lines)
        
        number_pattern = re.compile(r'[-+]?\d*\.?\d+')
        numbers = number_pattern.findall(clean_section)
        
        values = []
        for num in numbers:
            try:
                if num.startswith('.'):
                    num = '0' + num
                elif num.startswith('-.'):
                    num = '-0.' + num[2:]
                val = float(num)
                if abs(val - self.UNDEFINED_VALUE) < 1:
                    continue
                values.append(val)
            except ValueError:
                continue
        
        return np.array(values, dtype=float)


class DataPreprocessor:
    """数据预处理器：剔除鼓形和斜率偏差"""
    
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


class InvoluteCalculator:
    """渐开线计算器"""
    
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
    
    def calculate_roll_angle_degrees(self, diameter: float) -> float:
        """
        计算展长对应的角度（度）
        
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
    
    def calculate_roll_length(self, diameter: float) -> float:
        """计算展长 s(d) = sqrt((d/2)² - (db/2)²)"""
        radius = diameter / 2.0
        if radius <= self.params.base_radius:
            return 0.0
        return math.sqrt(radius**2 - self.params.base_radius**2)
    
    def diameter_from_roll_length(self, roll_length: float) -> float:
        """从展长反算直径"""
        if roll_length < 0:
            return 0.0
        radius = math.sqrt(roll_length**2 + self.params.base_radius**2)
        return 2.0 * radius


class ProfileAngleCalculator:
    """齿形角度计算器"""
    
    def __init__(self, gear_params: GearParameters, involute_calc: InvoluteCalculator):
        self.params = gear_params
        self.involute_calc = involute_calc
    
    def calculate_profile_polar_angles(self, eval_range: EvaluationRange, 
                                        num_points: int, side: str = 'right') -> np.ndarray:
        """
        计算齿形测量点的极角
        
        右齿形: 从齿顶开始，齿顶极角为0°
        左齿形: 从齿根开始，齿根极角为0°
        
        Args:
            eval_range: 评价范围
            num_points: 数据点数
            side: 'left' 或 'right'
            
        Returns:
            极角数组（度）
        """
        d_start = eval_range.eval_start  # 齿根
        d_end = eval_range.eval_end      # 齿顶
        
        s_start = self.involute_calc.calculate_roll_length(d_start)
        s_end = self.involute_calc.calculate_roll_length(d_end)
        
        roll_lengths = np.linspace(s_start, s_end, num_points)
        
        base_circumference = math.pi * self.params.base_diameter
        if base_circumference <= 0:
            return np.zeros(num_points)
        
        roll_angles = (roll_lengths / base_circumference) * 360.0
        
        if side == 'right':
            roll_angle_ref = (s_end / base_circumference) * 360.0
        else:
            roll_angle_ref = (s_start / base_circumference) * 360.0
        
        relative_angles = roll_angles - roll_angle_ref
        
        return relative_angles
    
    def build_rotation_curve(self, profile_data: Dict[int, Dict[float, np.ndarray]],
                             eval_range: EvaluationRange, side: str,
                             meas_range: EvaluationRange = None,
                             helix_eval_range: EvaluationRange = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        构建0-360度旋转曲线
        
        从齿顶开始排列：
        - 右齿形：齿1=0°，齿2=节距角，齿3=2*节距角，按齿数节距角加每一个测量点的极角排列起来
        - 左齿形：齿1=0°，齿2=节距角，齿3=2*节距角，按齿数节距角减每一个测量点的极角排列起来
        
        Args:
            profile_data: 齿形数据 {齿号: {z位置: 数据}}
            eval_range: 评价范围
            side: 'left' 或 'right'
            meas_range: 测量范围，用于筛选数据点
            helix_eval_range: 齿向评价范围，用于选择最合适的z位置
            
        Returns:
            (角度数组, 值数组)
        """
        all_angles = []
        all_values = []
        
        preprocessor = DataPreprocessor()
        
        # 计算评价范围和测量范围的展长
        s_eval_start = self.involute_calc.calculate_roll_length(eval_range.eval_start)
        s_eval_end = self.involute_calc.calculate_roll_length(eval_range.eval_end)
        
        if meas_range is not None:
            s_meas_start = self.involute_calc.calculate_roll_length(meas_range.meas_start)
            s_meas_end = self.involute_calc.calculate_roll_length(meas_range.meas_end)
        else:
            s_meas_start = s_eval_start
            s_meas_end = s_eval_end
        
        sorted_teeth = sorted(profile_data.keys())
        
        # 获取齿向评价范围中间点（用于选择最合适的z位置）
        if helix_eval_range is not None:
            helix_mid = (helix_eval_range.eval_start + helix_eval_range.eval_end) / 2
        else:
            helix_mid = None
        
        for tooth_id in sorted_teeth:
            tooth_profiles = profile_data[tooth_id]
            
            # 如果有多条曲线（不同z位置），选择最接近齿向评价范围中间位置的
            if helix_mid is not None and len(tooth_profiles) > 1:
                # 找到最接近中间点的z位置
                best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                tooth_profiles = {best_z: tooth_profiles[best_z]}
            
            for z_pos, values in tooth_profiles.items():
                if len(values) < 3:
                    continue
                
                # 预处理
                corrected_values = preprocessor.remove_crown_and_slope(values)
                
                # 如果提供了测量范围，筛选评价范围内的数据点
                if meas_range is not None and s_meas_end > s_meas_start:
                    num_points_total = len(corrected_values)
                    
                    # 计算评价范围在数据点中的索引
                    idx_start = max(0, int((s_eval_start - s_meas_start) / (s_meas_end - s_meas_start) * num_points_total))
                    idx_end = min(num_points_total, int((s_eval_end - s_meas_start) / (s_meas_end - s_meas_start) * num_points_total))
                    
                    # 筛选数据点
                    if idx_end > idx_start:
                        corrected_values = corrected_values[idx_start:idx_end]
                    else:
                        continue
                
                num_points = len(corrected_values)
                if num_points < 3:
                    continue
                
                polar_angles = self.calculate_profile_polar_angles(eval_range, num_points, side)
                
                tooth_index = tooth_id - 1
                tau = tooth_index * self.params.pitch_angle
                
                if side == 'right':
                    final_angles = tau + polar_angles
                else:
                    final_angles = tau - polar_angles
                
                # 对按角度排列的曲线再次进行预处理，去除趋势
                final_angles_arr = np.array(final_angles)
                corrected_values_arr = np.array(corrected_values)
                
                # 按角度排序
                sort_idx = np.argsort(final_angles_arr)
                final_angles_sorted = final_angles_arr[sort_idx]
                corrected_values_sorted = corrected_values_arr[sort_idx]
                
                # 去除趋势
                corrected_values_detrended = preprocessor.remove_crown_and_slope(corrected_values_sorted)
                
                all_angles.extend(final_angles_sorted.tolist())
                all_values.extend(corrected_values_detrended.tolist())
        
        if not all_angles:
            return None, None
        
        return np.array(all_angles), np.array(all_values)


class HelixAngleCalculator:
    """齿向角度计算器"""
    
    def __init__(self, gear_params: GearParameters):
        self.params = gear_params
    
    def calculate_helix_polar_angle(self, axial_position: float, 
                                     eval_start: float) -> float:
        """
        计算齿向测量点的极角
        
        公式: 极角 = 2 * (测量点 - 起评点) * tan(螺旋角) / 节圆直径
        
        Args:
            axial_position: 轴向位置
            eval_start: 起评点位置
            
        Returns:
            极角（度）
        """
        if abs(self.params.helix_angle) < 0.01:
            return 0.0
        
        delta_z = axial_position - eval_start
        tan_beta = math.tan(math.radians(abs(self.params.helix_angle)))
        
        polar_angle = 2.0 * delta_z * tan_beta / self.params.pitch_diameter
        polar_angle_deg = math.degrees(polar_angle)
        
        return polar_angle_deg
    
    def build_rotation_curve(self, helix_data: Dict[int, Dict[float, np.ndarray]],
                             eval_range: EvaluationRange, side: str,
                             profile_eval_range: EvaluationRange = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        构建0-360度旋转曲线
        
        从起评点到终评点：
        - 右齿向：齿1=0°，齿2=节距角，齿3=2*节距角，按齿数节距角加每一个测量点的极角排列起来
        - 左齿向：齿1=0°，齿2=节距角，齿3=2*节距角，按齿数节距角减每一个测量点的极角排列起来
        
        Args:
            helix_data: 齿向数据 {齿号: {d位置: 数据}}
            eval_range: 齿向评价范围
            side: 'left' 或 'right'
            profile_eval_range: 齿形评价范围，用于筛选d位置
            
        Returns:
            (角度数组, 值数组)
        """
        all_angles = []
        all_values = []
        
        preprocessor = DataPreprocessor()
        
        sorted_teeth = sorted(helix_data.keys())
        
        for tooth_id in sorted_teeth:
            tooth_helices = helix_data[tooth_id]
            
            for d_pos, values in tooth_helices.items():
                if profile_eval_range is not None:
                    if d_pos < profile_eval_range.eval_start or d_pos > profile_eval_range.eval_end:
                        continue
                
                if len(values) < 3:
                    continue
                
                corrected_values = preprocessor.remove_crown_and_slope(values)
                
                num_points = len(corrected_values)
                
                axial_positions = np.linspace(eval_range.eval_start, eval_range.eval_end, num_points)
                
                polar_angles = np.array([
                    self.calculate_helix_polar_angle(z, eval_range.eval_start) 
                    for z in axial_positions
                ])
                
                tooth_index = tooth_id - 1
                tau = tooth_index * self.params.pitch_angle
                
                if side == 'right':
                    final_angles = tau + polar_angles
                else:
                    final_angles = tau - polar_angles
                
                # 对按角度排列的曲线再次进行预处理，去除趋势
                final_angles_arr = np.array(final_angles)
                corrected_values_arr = np.array(corrected_values)
                
                # 按角度排序
                sort_idx = np.argsort(final_angles_arr)
                final_angles_sorted = final_angles_arr[sort_idx]
                corrected_values_sorted = corrected_values_arr[sort_idx]
                
                # 去除趋势
                corrected_values_detrended = preprocessor.remove_crown_and_slope(corrected_values_sorted)
                
                all_angles.extend(final_angles_sorted.tolist())
                all_values.extend(corrected_values_detrended.tolist())
        
        if not all_angles:
            return None, None
        
        return np.array(all_angles), np.array(all_values)


class CurveBuilder:
    """闭合曲线构建器"""
    
    def __init__(self, gear_params: GearParameters):
        self.params = gear_params
    
    def build_closed_curve(self, angles: np.ndarray, values: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        构建0-360度闭合曲线
        
        1. 将角度归一化到0-360度范围
        2. 按角度排序
        3. 去除重复点
        4. 插值到均匀网格
        
        Args:
            angles: 角度数组
            values: 值数组
            
        Returns:
            (插值角度数组, 插值值数组)
        """
        if angles is None or len(angles) < 10:
            return None, None
        
        angles = angles % 360.0
        angles[angles < 0] += 360.0
        
        sort_idx = np.argsort(angles)
        angles = angles[sort_idx]
        values = values[sort_idx]
        
        unique_angles, unique_indices = np.unique(np.round(angles, 3), return_index=True)
        unique_values = values[unique_indices]
        
        num_interp = max(720, 4 * self.params.teeth_count)
        interp_angles = np.linspace(0, 360, num_interp)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        return interp_angles, interp_values


class SpectrumAnalyzer:
    """频谱分析器：最小二乘法正弦波迭代分解"""
    
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
                                 num_components: int = 10, 
                                 max_order_factor: int = 5,
                                 verbose: bool = False) -> List[SpectrumComponent]:
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
            max_order_factor: 最大阶次因子（最大阶次 = 因子 * 齿数）
            verbose: 是否输出详细日志
            
        Returns:
            频谱分量列表
        """
        max_order = max_order_factor * self.params.teeth_count
        
        angles_rad = np.radians(angles)
        residual = np.array(values, dtype=float)
        residual = residual - np.mean(residual)
        
        components = []
        extracted_orders = set()
        
        if verbose:
            print(f"\n迭代正弦波分解算法:")
            print(f"  齿数 ZE = {self.params.teeth_count}")
            print(f"  最大搜索阶次: {max_order}")
            print(f"  提取分量数: {num_components}")
            print(f"  初始信号范围: [{residual.min():.4f}, {residual.max():.4f}]")
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
                high_order_marker = " ★ 高阶" if order >= self.params.teeth_count else ""
                print(f"  周期 {i+1}: 阶次={order:3d}, 振幅={amplitude:.4f} μm, "
                      f"相位={np.degrees(component.phase):.1f}°, "
                      f"残差RMS={np.sqrt(np.mean(residual**2)):.4f} μm{high_order_marker}")
        
        if verbose:
            print("-" * 60)
        
        return components


class HighOrderEvaluator:
    """高阶波纹度评价器"""
    
    def __init__(self, gear_params: GearParameters):
        self.params = gear_params
    
    def evaluate(self, components: List[SpectrumComponent], 
                 angles: np.ndarray) -> Tuple[float, float, List[int], np.ndarray]:
        """
        计算高阶波纹度（波数≥ZE的分量）
        
        评价方式的高阶大于等于ZE=波数，ZE为总齿数。
        0到360度之间有多少个波，0到360为一周，一周中有多少个波。
        如有87个波，阶次，频率为87。
        
        Args:
            components: 频谱分量列表
            angles: 角度数组（度）
            
        Returns:
            (总振幅, RMS值, 高阶波数列表, 重构信号)
        """
        ze = self.params.teeth_count
        
        high_order_components = [c for c in components if c.order >= ze]
        
        if not high_order_components:
            return 0.0, 0.0, [], np.zeros_like(angles)
        
        high_order_waves = [c.order for c in high_order_components]
        high_order_amplitudes = [c.amplitude for c in high_order_components]
        
        total_amplitude = sum(high_order_amplitudes)
        
        angles_rad = np.radians(angles)
        reconstructed = np.zeros_like(angles, dtype=float)
        
        for c in high_order_components:
            reconstructed += c.coefficient_a * np.cos(c.order * angles_rad) + \
                            c.coefficient_b * np.sin(c.order * angles_rad)
        
        rms = np.sqrt(np.mean(reconstructed ** 2))
        
        return total_amplitude, rms, high_order_waves, reconstructed


class PitchAnalyzer:
    """周节分析器"""

    def __init__(self, gear_params: GearParameters):
        self.params = gear_params

    def analyze(self, pitch_data: Dict[int, Dict[str, float]], side: str) -> Optional[PitchAnalysisResult]:
        """
        分析周节数据

        Args:
            pitch_data: 周节数据 {齿号: {fp, Fp, Fr}}
            side: 'left' 或 'right'

        Returns:
            周节分析结果
        """
        if not pitch_data:
            return None

        # 提取数据
        teeth = []
        fp_values = []

        for tooth_num in sorted(pitch_data.keys()):
            data = pitch_data[tooth_num]
            if isinstance(data, dict):
                teeth.append(tooth_num)
                fp_values.append(float(data.get('fp', 0)))

        if not teeth or not fp_values:
            return None

        # 计算累积周节偏差 Fp
        Fp_values = []
        cumulative_sum = 0
        for fp in fp_values:
            cumulative_sum += fp
            Fp_values.append(cumulative_sum)

        # 计算径向跳动 Fr (峰峰值)
        Fr = max(Fp_values) - min(Fp_values) if Fp_values else 0

        # 计算统计信息
        fp_max = max(fp_values) if fp_values else 0
        fp_min = min(fp_values) if fp_values else 0
        fp_avg = sum(fp_values) / len(fp_values) if fp_values else 0

        Fp_max = max(Fp_values) if Fp_values else 0
        Fp_min = min(Fp_values) if Fp_values else 0
        Fp_avg = sum(Fp_values) / len(Fp_values) if Fp_values else 0

        return PitchAnalysisResult(
            teeth=teeth,
            fp_values=fp_values,
            Fp_values=Fp_values,
            Fr=Fr,
            fp_max=fp_max,
            fp_min=fp_min,
            fp_avg=fp_avg,
            Fp_max=Fp_max,
            Fp_min=Fp_min,
            Fp_avg=Fp_avg,
            side=side
        )


class RippleWavinessAnalyzer:
    """波纹度分析器主类"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.reader: Optional[MKAFileReader] = None
        self.gear_params: Optional[GearParameters] = None
        self.results: Dict[str, WavinessResult] = {}
        self.pitch_results: Dict[str, PitchAnalysisResult] = {}
        
    def load_file(self) -> bool:
        """加载MKA文件"""
        self.reader = MKAFileReader(self.file_path)
        self.reader.read()
        self.gear_params = self.reader.gear_params
        return True
    
    def analyze_profile(self, side: str = 'right', verbose: bool = False) -> Optional[WavinessResult]:
        """
        分析齿形波纹度
        
        Args:
            side: 'left' 或 'right'
            verbose: 是否输出详细日志
            
        Returns:
            波纹度分析结果
        """
        if not self.reader or not self.reader.profile_eval_range:
            if verbose:
                print("缺少齿形评价范围数据")
            return None
        
        profile_data = self.reader.profile_data.get(side, {})
        if not profile_data:
            if verbose:
                print(f"缺少{side}侧齿形数据")
            return None
        
        involute_calc = InvoluteCalculator(self.gear_params)
        profile_calc = ProfileAngleCalculator(self.gear_params, involute_calc)
        
        angles, values = profile_calc.build_rotation_curve(
            profile_data, self.reader.profile_eval_range, side,
            meas_range=self.reader.profile_eval_range,
            helix_eval_range=self.reader.helix_eval_range
        )
        
        if angles is None:
            return None
        
        curve_builder = CurveBuilder(self.gear_params)
        interp_angles, interp_values = curve_builder.build_closed_curve(angles, values)
        
        if interp_angles is None:
            return None
        
        # 在合并后的曲线上再进行一次预处理，去除整体趋势
        interp_values = DataPreprocessor.remove_crown_and_slope(interp_values)
        
        spectrum_analyzer = SpectrumAnalyzer(self.gear_params)
        components = spectrum_analyzer.iterative_decomposition(
            interp_angles, interp_values, num_components=10, verbose=verbose
        )
        
        high_order_eval = HighOrderEvaluator(self.gear_params)
        total_amp, rms, high_waves, reconstructed = high_order_eval.evaluate(
            components, interp_angles
        )
        
        result = WavinessResult(
            angles=interp_angles,
            values=interp_values,
            spectrum_components=components,
            high_order_amplitude=total_amp,
            high_order_rms=rms,
            high_order_waves=high_waves,
            reconstructed_signal=reconstructed
        )
        
        self.results[f'profile_{side}'] = result
        return result
    
    def analyze_helix(self, side: str = 'right', verbose: bool = False) -> Optional[WavinessResult]:
        """
        分析齿向波纹度
        
        Args:
            side: 'left' 或 'right'
            verbose: 是否输出详细日志
            
        Returns:
            波纹度分析结果
        """
        if not self.reader or not self.reader.helix_eval_range:
            if verbose:
                print("缺少齿向评价范围数据")
            return None
        
        helix_data = self.reader.helix_data.get(side, {})
        if not helix_data:
            if verbose:
                print(f"缺少{side}侧齿向数据")
            return None
        
        helix_calc = HelixAngleCalculator(self.gear_params)
        
        angles, values = helix_calc.build_rotation_curve(
            helix_data, self.reader.helix_eval_range, side,
            profile_eval_range=self.reader.profile_eval_range
        )
        
        if angles is None:
            return None
        
        curve_builder = CurveBuilder(self.gear_params)
        interp_angles, interp_values = curve_builder.build_closed_curve(angles, values)
        
        if interp_angles is None:
            return None
        
        # 在合并后的曲线上再进行一次预处理，去除整体趋势
        interp_values = DataPreprocessor.remove_crown_and_slope(interp_values)
        
        spectrum_analyzer = SpectrumAnalyzer(self.gear_params)
        components = spectrum_analyzer.iterative_decomposition(
            interp_angles, interp_values, num_components=10, verbose=verbose
        )
        
        high_order_eval = HighOrderEvaluator(self.gear_params)
        total_amp, rms, high_waves, reconstructed = high_order_eval.evaluate(
            components, interp_angles
        )
        
        result = WavinessResult(
            angles=interp_angles,
            values=interp_values,
            spectrum_components=components,
            high_order_amplitude=total_amp,
            high_order_rms=rms,
            high_order_waves=high_waves,
            reconstructed_signal=reconstructed
        )
        
        self.results[f'helix_{side}'] = result
        return result
    
    def analyze_pitch(self, side: str = 'right') -> Optional[PitchAnalysisResult]:
        """
        分析周节偏差

        Args:
            side: 'left' 或 'right'

        Returns:
            周节分析结果
        """
        if not self.reader:
            return None

        pitch_data = self.reader.pitch_data.get(side, {})
        if not pitch_data:
            return None

        pitch_analyzer = PitchAnalyzer(self.gear_params)
        result = pitch_analyzer.analyze(pitch_data, side)

        if result:
            self.pitch_results[side] = result

        return result

    def analyze_all(self, verbose: bool = False) -> Dict[str, WavinessResult]:
        """分析所有方向的波纹度"""
        for side in ['left', 'right']:
            self.analyze_profile(side, verbose)
            self.analyze_helix(side, verbose)
            self.analyze_pitch(side)

        return self.results
    
    def print_results(self):
        """打印分析结果"""
        print("\n" + "=" * 70)
        print("齿轮波纹度分析结果")
        print("=" * 70)
        
        if self.gear_params:
            print(f"\n齿轮参数:")
            print(f"  齿数 ZE = {self.gear_params.teeth_count}")
            print(f"  模数 m = {self.gear_params.module} mm")
            print(f"  压力角 α = {self.gear_params.pressure_angle}°")
            print(f"  螺旋角 β = {self.gear_params.helix_angle}°")
            print(f"  节圆直径 D₀ = {self.gear_params.pitch_diameter:.3f} mm")
            print(f"  基圆直径 db = {self.gear_params.base_diameter:.3f} mm")
            print(f"  节距角 = {self.gear_params.pitch_angle:.4f}°")
        
        for name, result in self.results.items():
            print(f"\n{'='*70}")
            print(f"【{name}】")
            print('='*70)
            
            print(f"  数据点数: {len(result.angles)}")
            print(f"\n  前10个较大阶次:")
            
            for i, comp in enumerate(result.spectrum_components):
                high_order_marker = " ★ 高阶" if comp.order >= self.gear_params.teeth_count else ""
                print(f"    {i+1}. 阶次 {comp.order:3d}: 幅值 = {comp.amplitude:.4f} μm, "
                      f"相位 = {np.degrees(comp.phase):.1f}°{high_order_marker}")
            
            print(f"\n  高阶波纹度 (阶次≥{self.gear_params.teeth_count}):")
            print(f"    高阶波数: {result.high_order_waves}")
            print(f"    总振幅 W = {result.high_order_amplitude:.4f} μm")
            print(f"    RMS = {result.high_order_rms:.4f} μm")
    
    def plot_results(self, save_path: str = None):
        """绘制分析结果图表"""
        if not self.results:
            print("没有可绘制的结果")
            return
        
        num_results = len(self.results)
        fig, axes = plt.subplots(num_results, 2, figsize=(16, 5*num_results))
        
        if num_results == 1:
            axes = axes.reshape(1, -1)
        
        for idx, (name, result) in enumerate(self.results.items()):
            ax1 = axes[idx, 0]
            ax2 = axes[idx, 1]
            
            ax1.plot(result.angles, result.values, 'b-', linewidth=0.8, label='Original Curve')
            ax1.plot(result.angles, result.reconstructed_signal, 'r-', linewidth=1.5, 
                    label=f'High-Order Reconstructed (order>={self.gear_params.teeth_count})')
            ax1.set_xlabel('Rotation Angle (deg)')
            ax1.set_ylabel('Deviation (um)')
            ax1.set_title(f'{name} - Rotation Curve')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.set_xlim(0, 360)
            
            orders = [c.order for c in result.spectrum_components]
            amplitudes = [c.amplitude for c in result.spectrum_components]
            
            colors = ['red' if o >= self.gear_params.teeth_count else 'blue' for o in orders]
            ax2.bar(range(len(orders)), amplitudes, color=colors, alpha=0.7)
            ax2.axvline(x=self.gear_params.teeth_count - 0.5, color='green', 
                       linestyle='--', label=f'ZE={self.gear_params.teeth_count}')
            ax2.set_xlabel('Order Rank')
            ax2.set_ylabel('Amplitude (um)')
            ax2.set_title(f'{name} - Spectrum (Red:High-Order, Blue:Low-Order)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图表已保存到: {save_path}")
        
        plt.show()


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = r"e:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka"
    
    print(f"正在分析文件: {file_path}")
    
    analyzer = RippleWavinessAnalyzer(file_path)
    analyzer.load_file()
    
    print("\n" + "=" * 70)
    print("分析齿形波纹度")
    print("=" * 70)
    
    analyzer.analyze_profile('right', verbose=True)
    analyzer.analyze_profile('left', verbose=True)
    
    print("\n" + "=" * 70)
    print("分析齿向波纹度")
    print("=" * 70)
    
    analyzer.analyze_helix('right', verbose=True)
    analyzer.analyze_helix('left', verbose=True)
    
    analyzer.print_results()
    
    output_dir = os.path.dirname(file_path)
    save_path = os.path.join(output_dir, "waviness_analysis_result.png")
    analyzer.plot_results(save_path)


if __name__ == "__main__":
    main()
