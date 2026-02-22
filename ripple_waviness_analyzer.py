"""
齿轮波纹度分析模块 - 完整版
正确解析MKA文件格式
"""

import re
import os
import sys
import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass


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
        if self.module > 0 and self.teeth_count > 0:
            beta = math.radians(abs(self.helix_angle))
            alpha_n = math.radians(self.pressure_angle)
            alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta)) if abs(beta) > 1e-6 else alpha_n
            
            self.pitch_diameter = self.teeth_count * self.module / math.cos(beta)
            self.base_diameter = self.pitch_diameter * math.cos(alpha_t)
            self.pitch_angle = 360.0 / self.teeth_count
        else:
            self.pitch_diameter = 0.0
            self.base_diameter = 0.0
            self.pitch_angle = 0.0


@dataclass
class SpectrumComponent:
    """频谱分量"""
    order: float
    amplitude: float
    phase: float


@dataclass
class AnalysisResult:
    """分析结果"""
    angles: np.ndarray
    values: np.ndarray
    reconstructed_signal: np.ndarray
    high_order_waves: List[Dict]
    spectrum_components: List[Any]
    high_order_amplitude: float
    high_order_rms: float


@dataclass
class PitchResult:
    """周节分析结果"""
    teeth: List[int]
    fp_values: List[float]
    Fp_values: List[float]
    fp_max: float
    Fp_max: float
    Fp_min: float
    Fr: float


class MKAReader:
    """MKA文件读取器 - 正确解析Klingelnberg格式"""
    
    UNDEFINED = -2147483.648
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.raw_content = None
        self.lines = []
        self.profile_data = {'left': {}, 'right': {}}
        self.helix_data = {'left': {}, 'right': {}}
        self.pitch_data = {'left': {}, 'right': {}}
        self.gear_params = None
        self.d1 = 174.822
        self.d2 = 180.603
        self.b1 = 2.1
        self.b2 = 39.9
        self.profile_eval_range = None
        self.helix_eval_range = None
        
    def load_file(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                self.raw_content = f.read()
                self.lines = self.raw_content.split('\n')
            
            self._parse_header()
            self._parse_data_sections()
            self._parse_pitch_data()
            return True
        except Exception as e:
            print(f"加载文件失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _parse_teeth_count(self, content: str) -> int:
        """解析齿数，尝试多种模式"""
        import re

        # 首先尝试从文件头部（前100行）解析
        header_lines = '\n'.join(content.split('\n')[:100])

        # 模式列表 - 按优先级排序，更具体的模式在前
        # 使用原始字节匹配来避免编码问题
        patterns = [
            # 匹配 Z�hnezahl 或 Zähnezahl (使用 . 匹配任意字符)
            r'Z.hnezahl\s*z\s*\.+:\s*(\d+)',
            r'Z.hnezahl\s*z\s*[^:\n]*:\s*(\d+)',
            # 备选：直接匹配行模式
            r':Z[^:]*hnezahl[^:]*:\s*(\d+)',
            # 英语格式
            r'Number\s+of\s+teeth[^:\n]*:\s*(\d+)',
            r'No\.\s*of\s+teeth[^:\n]*:\s*(\d+)',
            r'Teeth\s+count[^:\n]*:\s*(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, header_lines, re.IGNORECASE)
            if match:
                try:
                    teeth_count = int(match.group(1))
                    # 验证齿数合理性（通常在5-500之间）
                    if 5 <= teeth_count <= 500:
                        print(f"解析到齿数: {teeth_count} (模式: {pattern[:40]}...)")
                        return teeth_count
                except:
                    continue

        # 如果都没匹配到，尝试从数据部分推断
        try:
            # 尝试从齿形数据或齿向数据中推断齿数
            if hasattr(self, 'profile_data') and self.profile_data:
                for side in ['left', 'right']:
                    if side in self.profile_data and self.profile_data[side]:
                        teeth = list(self.profile_data[side].keys())
                        if teeth:
                            max_tooth = max(teeth)
                            if 5 <= max_tooth <= 500:
                                print(f"从齿形数据推断齿数: {max_tooth}")
                                return max_tooth

            if hasattr(self, 'helix_data') and self.helix_data:
                for side in ['left', 'right']:
                    if side in self.helix_data and self.helix_data[side]:
                        teeth = list(self.helix_data[side].keys())
                        if teeth:
                            max_tooth = max(teeth)
                            if 5 <= max_tooth <= 500:
                                print(f"从齿向数据推断齿数: {max_tooth}")
                                return max_tooth
        except Exception as e:
            print(f"从数据推断齿数失败: {e}")

        print("警告: 无法解析齿数，使用默认值 87")
        return 87

    def _parse_header(self):
        content = self.raw_content or ""

        module = 1.0
        teeth_count = 87
        pressure_angle = 20.0
        helix_angle = 0.0

        mn_match = re.search(r'Normalmodul\s*mn\s*.*?:\s*([\d.]+)', content, re.IGNORECASE)
        if mn_match:
            module = float(mn_match.group(1))

        # 齿数解析 - 尝试多种模式
        teeth_count = self._parse_teeth_count(content)

        alpha_match = re.search(r'Eingriffswinkel\s*alpha\s*.*?:\s*([\d.]+)', content, re.IGNORECASE)
        if alpha_match:
            pressure_angle = float(alpha_match.group(1))

        beta_match = re.search(r'Schr.gungswinkel[^:]*:\s*([\d.-]+)', content, re.IGNORECASE)
        if not beta_match:
            beta_match = re.search(r'Helix\s*angle[^:]*:\s*([\d.-]+)', content, re.IGNORECASE)
        if not beta_match:
            beta_match = re.search(r'\[\s*Grad\s*\]\.\.:\s*([\d.]+)\s+rechts', content, re.IGNORECASE)
        if beta_match:
            helix_angle = float(beta_match.group(1))

        d1_match = re.search(r'Auswertestrecke\s*.*?d1.*?:\s*([\d.]+)', content, re.IGNORECASE)
        if d1_match:
            self.d1 = float(d1_match.group(1))

        d2_match = re.search(r'Auswertestrecke\s*.*?d2.*?:\s*([\d.]+)', content, re.IGNORECASE)
        if d2_match:
            self.d2 = float(d2_match.group(1))

        b1_match = re.search(r'Auswerteanfang\s*.*?b1.*?:\s*([\d.]+)', content, re.IGNORECASE)
        if b1_match:
            self.b1 = float(b1_match.group(1))

        b2_match = re.search(r'Auswerteende\s*.*?b2.*?:\s*([\d.]+)', content, re.IGNORECASE)
        if b2_match:
            self.b2 = float(b2_match.group(1))

        # 解析其他信息
        self.info = {}

        # 操作者
        operator_match = re.search(r'Bedieners\s*:\s*(.+)', content, re.IGNORECASE)
        if operator_match:
            self.info['operator'] = operator_match.group(1).strip()
        else:
            operator_match = re.search(r'Operator\s*:\s*(.+)', content, re.IGNORECASE)
            if operator_match:
                self.info['operator'] = operator_match.group(1).strip()

        # 日期
        date_match = re.search(r'Datum\s*:\s*(\d{2}\.\d{2}\.\d{2,4})', content, re.IGNORECASE)
        if date_match:
            self.info['date'] = date_match.group(1)
        else:
            date_match = re.search(r'Date\s*:\s*(\d{2}\.\d{2}\.\d{2,4})', content, re.IGNORECASE)
            if date_match:
                self.info['date'] = date_match.group(1)

        # 订单号
        order_match = re.search(r'Auftrags-Nr\.\s*:\s*(.+)', content, re.IGNORECASE)
        if order_match:
            self.info['order_no'] = order_match.group(1).strip()
        else:
            order_match = re.search(r'Order\s*No\.\s*:\s*(.+)', content, re.IGNORECASE)
            if order_match:
                self.info['order_no'] = order_match.group(1).strip()

        # 客户/机器号
        customer_match = re.search(r'Kunde/Masch-Nr\.\s*:\s*(.+)', content, re.IGNORECASE)
        if customer_match:
            self.info['customer'] = customer_match.group(1).strip()
        else:
            customer_match = re.search(r'Cust\./Mach\.\s*No\.\s*:\s*(.+)', content, re.IGNORECASE)
            if customer_match:
                self.info['customer'] = customer_match.group(1).strip()

        # 检查位置
        location_match = re.search(r'Prüfort\s*:\s*(.+)', content, re.IGNORECASE)
        if location_match:
            self.info['location'] = location_match.group(1).strip()
        else:
            location_match = re.search(r'Loc\.\s*of\s*check\s*:\s*(.+)', content, re.IGNORECASE)
            if location_match:
                self.info['location'] = location_match.group(1).strip()

        # 图号
        drawing_match = re.search(r'Zeichnungs-Nr\.\s*:\s*(.+)', content, re.IGNORECASE)
        if drawing_match:
            self.info['drawing_no'] = drawing_match.group(1).strip()
        else:
            drawing_match = re.search(r'Drawing\s*No\.\s*:\s*(.+)', content, re.IGNORECASE)
            if drawing_match:
                self.info['drawing_no'] = drawing_match.group(1).strip()

        # 类型
        type_match = re.search(r'Type\s*:\s*(.+)', content, re.IGNORECASE)
        if type_match:
            self.info['type_'] = type_match.group(1).strip()
        else:
            self.info['type_'] = 'gear'

        self.gear_params = GearParameters(
            module=module,
            teeth_count=teeth_count,
            pressure_angle=pressure_angle,
            helix_angle=helix_angle
        )
        
        self.profile_eval_range = type('EvaluationRange', (), {
            'meas_start': 0.0,
            'meas_end': 8.0,
            'eval_start': min(self.d1, self.d2),
            'eval_end': max(self.d1, self.d2)
        })()
        
        self.helix_eval_range = type('EvaluationRange', (), {
            'meas_start': 0.0,
            'meas_end': max(self.b1, self.b2) + 5,
            'eval_start': min(self.b1, self.b2),
            'eval_end': max(self.b1, self.b2)
        })()
    
    def _parse_data_sections(self):
        content = self.raw_content or ""
        lines = self.lines
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            helix_match = re.match(r'Flankenlinie:\s*Zahn-Nr\.?:\s*(\d+)([a-z]?)\s+(links|rechts|left|right)', line, re.IGNORECASE)
            if helix_match:
                tooth_num = int(helix_match.group(1))
                side_str = helix_match.group(3).lower()
                side = 'left' if side_str in ['links', 'left'] else 'right'
                
                d_match = re.search(r'd=\s*([\d.]+)', line)
                d_pos = float(d_match.group(1)) if d_match else 0
                
                values = self._parse_data_values(lines, i + 1)
                if values is not None and len(values) > 0:
                    if tooth_num not in self.helix_data[side]:
                        self.helix_data[side][tooth_num] = {}
                    self.helix_data[side][tooth_num][d_pos] = values
                i += 1
                continue
            
            profile_match = re.match(r'Profil:\s*Zahn-Nr\.?:\s*(\d+)([a-z]?)\s+(links|rechts|left|right)', line, re.IGNORECASE)
            if profile_match:
                tooth_num = int(profile_match.group(1))
                side_str = profile_match.group(3).lower()
                side = 'left' if side_str in ['links', 'left'] else 'right'
                
                z_match = re.search(r'z=\s*([\d.]+)', line)
                z_pos = float(z_match.group(1)) if z_match else 0
                
                values = self._parse_data_values(lines, i + 1)
                if values is not None and len(values) > 0:
                    if tooth_num not in self.profile_data[side]:
                        self.profile_data[side][tooth_num] = {}
                    self.profile_data[side][tooth_num][z_pos] = values
                i += 1
                continue
            
            i += 1
    
    def _parse_data_values(self, lines, start_idx):
        values = []
        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            if re.match(r'(Flankenlinie|Profil|Teilung):', line, re.IGNORECASE):
                break
            if re.match(r'^[A-Za-z]', line):
                break
            
            nums = re.findall(r'[-\d.]+', line)
            for n in nums:
                try:
                    v = float(n)
                    if abs(v - self.UNDEFINED) > 0.001:
                        values.append(v)
                except:
                    pass
        
        return np.array(values) if values else None

    def _parse_pitch_data(self):
        content = self.raw_content or ""
        
        for side in ['left', 'right']:
            side_pattern = r'linke Zahnflanke' if side == 'left' else r'rechte Zahnflanke'
            pattern = rf'{side_pattern}\s*\n\s*Zahn-Nr\.\s+fp\s+Fp\s+Fr\s*\n((?:\s*\d+\s+[-\d.]+\s+[-\d.]+\s+[-\d.]+\s*\n?)+)'
            
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                data_text = match.group(1)
                lines = data_text.strip().split('\n')
                
                teeth = []
                fp_values = []
                Fp_values_raw = []
                
                for line in lines:
                    line = line.strip()
                    if line and re.match(r'^\s*\d+', line):
                        parts = line.split()
                        if len(parts) >= 4:
                            teeth.append(int(parts[0]))
                            fp_values.append(float(parts[1]))
                            Fp_values_raw.append(float(parts[2]))
                
                if teeth:
                    Fp_values = list(np.cumsum(fp_values))
                    
                    self.pitch_data[side] = {
                        'teeth': teeth,
                        'fp_values': fp_values,
                        'Fp_values': Fp_values,
                        'angles': np.array([(t-1) * 360.0 / len(teeth) for t in teeth]),
                        'deviations': np.array(fp_values)
                    }
        
        if not self.pitch_data['left'] and not self.pitch_data['right']:
            teeth_count = self.gear_params.teeth_count if self.gear_params else 87
            for side in ['left', 'right']:
                self.pitch_data[side] = {
                    'teeth': list(range(1, teeth_count + 1)),
                    'fp_values': [0.0] * teeth_count,
                    'Fp_values': [0.0] * teeth_count,
                    'angles': np.array([i * 360.0 / teeth_count for i in range(teeth_count)]),
                    'deviations': np.array([0.0] * teeth_count)
                }


class RippleWavinessAnalyzer:
    """波纹度分析器"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.reader = MKAReader(file_path)
        self.gear_params = None
        
    def load_file(self):
        success = self.reader.load_file()
        if success:
            self.gear_params = self.reader.gear_params
        return success
    
    def _remove_crown_and_slope(self, data: np.ndarray) -> np.ndarray:
        n = len(data)
        if n < 5:
            return data
        
        y = np.array(data, dtype=float)
        x = np.arange(n, dtype=float)
        x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
        
        crowning_coeffs = np.polyfit(x_norm, y, 2)
        crowning_curve = np.polyval(crowning_coeffs, x_norm)
        y_no_crown = y - crowning_curve
        
        slope_coeffs = np.polyfit(x_norm, y_no_crown, 1)
        slope_curve = np.polyval(slope_coeffs, x_norm)
        y_corrected = y_no_crown - slope_curve
        
        return y_corrected
    
    def _calculate_involute_polar_angle(self, radius: float, base_radius: float) -> float:
        if radius <= base_radius or base_radius <= 0:
            return 0.0
        cos_alpha = base_radius / radius
        cos_alpha = max(-1.0, min(1.0, cos_alpha))
        alpha = np.arccos(cos_alpha)
        return np.tan(alpha) - alpha
    
    def _build_closed_curve(self, data_dict: Dict, data_type: str = 'profile', 
                            side: str = 'left') -> Tuple[np.ndarray, np.ndarray]:
        if not data_dict:
            return np.array([]), np.array([])
        
        teeth_count = self.gear_params.teeth_count if self.gear_params else 87
        module = self.gear_params.module if self.gear_params else 1.859
        pressure_angle = self.gear_params.pressure_angle if self.gear_params else 18.6
        helix_angle = self.gear_params.helix_angle if self.gear_params else 25.3
        
        beta = math.radians(abs(helix_angle))
        alpha_n = math.radians(pressure_angle)
        alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta)) if abs(beta) > 1e-6 else alpha_n
        
        pitch_diameter = teeth_count * module / math.cos(beta)
        pitch_radius = pitch_diameter / 2.0
        base_diameter = pitch_diameter * math.cos(alpha_t)
        base_radius = base_diameter / 2.0
        pitch_angle_deg = 360.0 / teeth_count
        
        all_angles = []
        all_values = []
        
        sorted_teeth = sorted(data_dict.keys())
        
        for tooth_id in sorted_teeth:
            tooth_data = data_dict[tooth_id]
            
            if isinstance(tooth_data, dict):
                if data_type == 'profile':
                    target_z = 21.0
                    best_z = None
                    for z_pos in tooth_data.keys():
                        if best_z is None or abs(z_pos - target_z) < abs(best_z - target_z):
                            best_z = z_pos
                    
                    if best_z is None:
                        best_z = list(tooth_data.keys())[0]
                    
                    values = tooth_data[best_z]
                else:
                    target_d = 178.638
                    best_d = None
                    for d_pos in tooth_data.keys():
                        if best_d is None or abs(d_pos - target_d) < abs(best_d - target_d):
                            best_d = d_pos
                    
                    if best_d is None:
                        best_d = list(tooth_data.keys())[0]
                    
                    values = tooth_data[best_d]
                
                if values is not None and len(values) > 5:
                    raw_values = np.array(values)
                    
                    if data_type == 'profile':
                        d1 = self.reader.d1
                        d2 = self.reader.d2
                        da = 174.24
                        de = 182.775
                        
                        da_match = re.search(r'Start Messbereich[^:]*da[^:]*:\s*([\d.]+)', self.reader.raw_content or "", re.IGNORECASE)
                        if da_match:
                            da = float(da_match.group(1))
                        de_match = re.search(r'Ende der Messstrecke[^:]*de[^:]*:\s*([\d.]+)', self.reader.raw_content or "", re.IGNORECASE)
                        if de_match:
                            de = float(de_match.group(1))
                        
                        meas_start_radius = da / 2.0
                        meas_end_radius = de / 2.0
                        eval_start_radius = d1 / 2.0
                        eval_end_radius = d2 / 2.0
                        
                        meas_start_spread = np.sqrt(max(0, meas_start_radius**2 - base_radius**2))
                        meas_end_spread = np.sqrt(max(0, meas_end_radius**2 - base_radius**2))
                        eval_start_spread = np.sqrt(max(0, eval_start_radius**2 - base_radius**2))
                        eval_end_spread = np.sqrt(max(0, eval_end_radius**2 - base_radius**2))
                        
                        total_spread = meas_end_spread - meas_start_spread
                        if total_spread > 0:
                            start_ratio = (eval_start_spread - meas_start_spread) / total_spread
                            end_ratio = (eval_end_spread - meas_start_spread) / total_spread
                            
                            n_total = len(raw_values)
                            start_idx = max(0, int(start_ratio * n_total))
                            end_idx = min(n_total, int(end_ratio * n_total))
                            
                            if end_idx - start_idx > 10:
                                raw_values = raw_values[start_idx:end_idx]
                    
                    corrected = self._remove_crown_and_slope(raw_values)
                    n = len(corrected)
                    
                    tooth_index = int(tooth_id) - 1
                    tooth_base_angle = tooth_index * pitch_angle_deg
                    
                    if data_type == 'profile':
                        # 齿形数据：使用展长计算极角
                        # 使用MKA文件中的起评点和终评点直径
                        d1 = self.reader.d1  # 起评点直径 174.822mm
                        d2 = self.reader.d2  # 终评点直径 180.603mm
                        
                        # 计算起评点和终评点对应的展长
                        # L = sqrt(r^2 - rb^2), 其中 r = d/2
                        eval_start_radius = d1 / 2.0
                        eval_end_radius = d2 / 2.0
                        
                        # 计算展长范围
                        eval_start_spread = np.sqrt(max(0, eval_start_radius**2 - base_radius**2))
                        eval_end_spread = np.sqrt(max(0, eval_end_radius**2 - base_radius**2))
                        
                        # 展长从起评点到终评点
                        spread_lengths = np.linspace(eval_start_spread, eval_end_spread, n)
                        
                        # 根据展长计算半径: r = sqrt(L^2 + rb^2)
                        radii = np.sqrt(spread_lengths ** 2 + base_radius ** 2)
                        
                        # 计算极角
                        polar_angles = np.array([self._calculate_involute_polar_angle(r, base_radius) for r in radii])
                        
                        # 起评点的极角为0
                        start_polar_angle = polar_angles[0]
                        point_angles_deg = np.degrees(polar_angles - start_polar_angle)
                        
                        if side == 'right':
                            final_angles = tooth_base_angle + point_angles_deg
                        else:
                            # 左齿形：使用与右齿形相同的角度分配逻辑
                            final_angles = tooth_base_angle + point_angles_deg
                    else:
                        # 齿向(lead)数据处理
                        b1 = self.reader.b1  # 评估起始位置
                        b2 = self.reader.b2  # 评估结束位置
                        
                        # 从原始数据中获取测量范围
                        ba = 0.0  # 测量起始
                        be = 42.0  # 测量结束
                        
                        ba_match = re.search(r'Messanfang[^:]*ba[^:]*:\s*([\d.]+)', self.reader.raw_content or "", re.IGNORECASE)
                        if ba_match:
                            ba = float(ba_match.group(1))
                        be_match = re.search(r'Messende[^:]*be[^:]*:\s*([\d.]+)', self.reader.raw_content or "", re.IGNORECASE)
                        if be_match:
                            be = float(be_match.group(1))
                        
                        # 提取评估范围内的数据
                        meas_length = be - ba
                        if meas_length > 0:
                            start_ratio = (min(b1, b2) - ba) / meas_length
                            end_ratio = (max(b1, b2) - ba) / meas_length
                            
                            n_total = len(raw_values)
                            start_idx = max(0, int(start_ratio * n_total))
                            end_idx = min(n_total, int(end_ratio * n_total))
                            
                            if end_idx - start_idx > 10:
                                raw_values = raw_values[start_idx:end_idx]
                                corrected = self._remove_crown_and_slope(raw_values)
                                n = len(corrected)
                        
                        # 齿向数据的角度映射：
                        # 齿向偏差沿齿宽方向，需要映射到旋转角度
                        # 每个齿占据 360°/齿数 的角度范围
                        # 齿向数据在齿宽方向上的变化对应于这个角度范围内的小变化
                        
                        # 计算齿向数据在齿宽方向上的位置
                        eval_width = abs(b2 - b1)
                        z_positions = np.linspace(0, eval_width, n)
                        
                        # 齿向偏差对应的角度变化：
                        # 由于螺旋角的存在，齿宽方向的变化会导致旋转方向的变化
                        # 但齿向偏差本身是沿齿宽方向的直线测量，应该均匀分布在齿的角度范围内
                        pitch_angle = 360.0 / teeth_count
                        
                        # 齿向数据点均匀分布在齿的角度范围内（略小于一个齿距，避免重叠）
                        # 使用 0.9 * pitch_angle 确保数据点不会超出当前齿的角度范围
                        point_angles_within_tooth = np.linspace(0, pitch_angle * 0.9, n)
                        
                        final_angles = tooth_base_angle + point_angles_within_tooth
                    
                    all_angles.extend(final_angles.tolist())
                    all_values.extend(corrected.tolist())
            else:
                if tooth_data is not None and len(tooth_data) > 5:
                    raw_values = np.array(tooth_data)
                    
                    if data_type == 'profile':
                        d1 = self.reader.d1
                        d2 = self.reader.d2
                        da = 174.24
                        de = 182.775
                        
                        da_match = re.search(r'Start Messbereich[^:]*da[^:]*:\s*([\d.]+)', self.reader.raw_content or "", re.IGNORECASE)
                        if da_match:
                            da = float(da_match.group(1))
                        de_match = re.search(r'Ende der Messstrecke[^:]*de[^:]*:\s*([\d.]+)', self.reader.raw_content or "", re.IGNORECASE)
                        if de_match:
                            de = float(de_match.group(1))
                        
                        meas_start_radius = da / 2.0
                        meas_end_radius = de / 2.0
                        eval_start_radius = d1 / 2.0
                        eval_end_radius = d2 / 2.0
                        
                        meas_start_spread = np.sqrt(max(0, meas_start_radius**2 - base_radius**2))
                        meas_end_spread = np.sqrt(max(0, meas_end_radius**2 - base_radius**2))
                        eval_start_spread = np.sqrt(max(0, eval_start_radius**2 - base_radius**2))
                        eval_end_spread = np.sqrt(max(0, eval_end_radius**2 - base_radius**2))
                        
                        total_spread = meas_end_spread - meas_start_spread
                        if total_spread > 0:
                            start_ratio = (eval_start_spread - meas_start_spread) / total_spread
                            end_ratio = (eval_end_spread - meas_start_spread) / total_spread
                            
                            n_total = len(raw_values)
                            start_idx = max(0, int(start_ratio * n_total))
                            end_idx = min(n_total, int(end_ratio * n_total))
                            
                            if end_idx - start_idx > 10:
                                raw_values = raw_values[start_idx:end_idx]
                    
                    corrected = self._remove_crown_and_slope(raw_values)
                    n = len(corrected)
                    
                    tooth_index = int(tooth_id) - 1
                    tooth_base_angle = tooth_index * pitch_angle_deg
                    
                    if data_type == 'profile':
                        # 齿形数据：使用展长计算极角
                        # 使用MKA文件中的起评点和终评点直径
                        d1 = self.reader.d1  # 起评点直径 174.822mm
                        d2 = self.reader.d2  # 终评点直径 180.603mm
                        
                        # 计算起评点和终评点对应的展长
                        # L = sqrt(r^2 - rb^2), 其中 r = d/2
                        eval_start_radius = d1 / 2.0
                        eval_end_radius = d2 / 2.0
                        
                        # 计算展长范围
                        eval_start_spread = np.sqrt(max(0, eval_start_radius**2 - base_radius**2))
                        eval_end_spread = np.sqrt(max(0, eval_end_radius**2 - base_radius**2))
                        
                        # 展长从起评点到终评点
                        spread_lengths = np.linspace(eval_start_spread, eval_end_spread, n)
                        
                        # 根据展长计算半径: r = sqrt(L^2 + rb^2)
                        radii = np.sqrt(spread_lengths ** 2 + base_radius ** 2)
                        
                        # 计算极角
                        polar_angles = np.array([self._calculate_involute_polar_angle(r, base_radius) for r in radii])
                        
                        # 起评点的极角为0
                        start_polar_angle = polar_angles[0]
                        point_angles_deg = np.degrees(polar_angles - start_polar_angle)
                        
                        # 所有齿形都使用相同的角度计算方式
                        final_angles = tooth_base_angle + point_angles_deg
                    else:
                        b1 = self.reader.b1
                        b2 = self.reader.b2
                        ba = 0.0
                        be = 42.0
                        
                        ba_match = re.search(r'Messanfang[^:]*ba[^:]*:\s*([\d.]+)', self.reader.raw_content or "", re.IGNORECASE)
                        if ba_match:
                            ba = float(ba_match.group(1))
                        be_match = re.search(r'Messende[^:]*be[^:]*:\s*([\d.]+)', self.reader.raw_content or "", re.IGNORECASE)
                        if be_match:
                            be = float(be_match.group(1))
                        
                        meas_length = be - ba
                        if meas_length > 0:
                            start_ratio = (min(b1, b2) - ba) / meas_length
                            end_ratio = (max(b1, b2) - ba) / meas_length
                            
                            n_total = len(raw_values)
                            start_idx = max(0, int(start_ratio * n_total))
                            end_idx = min(n_total, int(end_ratio * n_total))
                            
                            if end_idx - start_idx > 10:
                                raw_values = raw_values[start_idx:end_idx]
                                corrected = self._remove_crown_and_slope(raw_values)
                                n = len(corrected)
                        
                        z_positions = np.linspace(min(b1, b2), max(b1, b2), n)
                        z_from_start = z_positions - min(b1, b2)
                        
                        rotation_angles = 2.0 * z_from_start * np.tan(np.radians(abs(helix_angle))) / pitch_diameter
                        point_angles_deg = np.degrees(rotation_angles)
                        
                        final_angles = tooth_base_angle + point_angles_deg
                    
                    all_angles.extend(final_angles.tolist())
                    all_values.extend(corrected.tolist())
        
        if not all_angles:
            return np.array([]), np.array([])
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        
        # 归一化角度到0-360度
        all_angles = all_angles % 360.0
        all_angles[all_angles < 0] += 360.0
        
        # 按角度排序，保持曲线的连续性
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        
        return all_angles, all_values
    
    def _iterative_sine_decomposition(self, angles: np.ndarray, values: np.ndarray,
                                       num_components: int = 10, max_order: int = None) -> List[SpectrumComponent]:
        n = len(angles)
        if n < 8:
            return []
        
        teeth_count = self.gear_params.teeth_count if self.gear_params else 87
        if max_order is None:
            max_order = 5 * teeth_count
        
        unique_angles, unique_indices = np.unique(np.round(angles, 3), return_index=True)
        unique_values = values[unique_indices]
        
        num_interp_points = max(360, 2 * max_order + 10)
        interp_angles = np.linspace(0, 360, num_interp_points)
        interp_values = np.interp(interp_angles, unique_angles, unique_values, period=360)
        
        angles_rad = np.radians(interp_angles)
        residual = np.array(interp_values, dtype=float)
        residual = residual - np.mean(residual)
        
        components = []
        extracted_orders = set()
        amplitude_threshold = 1e-6
        
        for _ in range(num_components):
            best_order = None
            best_amplitude = 0.0
            best_phase = 0.0
            best_coeffs = None
            
            for order in range(1, max_order + 1):
                if order in extracted_orders:
                    continue
                
                try:
                    cos_term = np.cos(order * angles_rad)
                    sin_term = np.sin(order * angles_rad)
                    A = np.column_stack([cos_term, sin_term])
                    
                    coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
                    a, b = coeffs[0], coeffs[1]
                    amplitude = np.sqrt(a**2 + b**2)
                    phase = np.arctan2(a, b)
                    
                    if amplitude > best_amplitude:
                        best_amplitude = amplitude
                        best_order = order
                        best_phase = phase
                        best_coeffs = (a, b)
                except:
                    continue
            
            if best_order is None or best_amplitude < amplitude_threshold:
                break
            
            components.append(SpectrumComponent(
                order=float(best_order),
                amplitude=best_amplitude,
                phase=best_phase
            ))
            extracted_orders.add(best_order)
            
            a, b = best_coeffs
            fitted_wave = a * np.cos(best_order * angles_rad) + b * np.sin(best_order * angles_rad)
            residual = residual - fitted_wave
        
        components.sort(key=lambda x: x.amplitude, reverse=True)
        return components
    
    def analyze_profile(self, side: str, verbose: bool = True):
        profile_data = self.reader.profile_data.get(side, {})
        
        angles, values = self._build_closed_curve(profile_data, 'profile', side)
        
        if len(angles) < 100:
            angles = np.linspace(0, 360, 1000)
            values = np.zeros(1000)
        
        spectrum_components = self._iterative_sine_decomposition(angles, values)
        
        teeth_count = self.gear_params.teeth_count if self.gear_params else 87
        
        high_order_comps = [c for c in spectrum_components if c.order >= teeth_count]
        high_order_amplitude = sum(c.amplitude for c in high_order_comps) if high_order_comps else 0.0
        high_order_rms = np.sqrt(sum(c.amplitude**2 for c in high_order_comps)) if high_order_comps else 0.0
        
        high_order_waves = [{'order': c.order, 'amplitude': c.amplitude} for c in high_order_comps]
        
        angles_rad = np.deg2rad(angles)
        reconstructed = np.zeros_like(values)
        for comp in high_order_comps:
            a = comp.amplitude * np.sin(comp.phase)
            b = comp.amplitude * np.cos(comp.phase)
            reconstructed += a * np.cos(comp.order * angles_rad) + b * np.sin(comp.order * angles_rad)
        
        return AnalysisResult(
            angles=angles,
            values=values,
            reconstructed_signal=reconstructed,
            high_order_waves=high_order_waves,
            spectrum_components=spectrum_components,
            high_order_amplitude=high_order_amplitude,
            high_order_rms=high_order_rms
        )
    
    def analyze_helix(self, side: str, verbose: bool = True):
        helix_data = self.reader.helix_data.get(side, {})
        
        angles, values = self._build_closed_curve(helix_data, 'helix', side)
        
        if len(angles) < 100:
            angles = np.linspace(0, 360, 1000)
            values = np.zeros(1000)
        
        spectrum_components = self._iterative_sine_decomposition(angles, values)
        
        teeth_count = self.gear_params.teeth_count if self.gear_params else 87
        
        high_order_comps = [c for c in spectrum_components if c.order >= teeth_count]
        high_order_amplitude = sum(c.amplitude for c in high_order_comps) if high_order_comps else 0.0
        high_order_rms = np.sqrt(sum(c.amplitude**2 for c in high_order_comps)) if high_order_comps else 0.0
        
        high_order_waves = [{'order': c.order, 'amplitude': c.amplitude} for c in high_order_comps]
        
        angles_rad = np.deg2rad(angles)
        reconstructed = np.zeros_like(values)
        for comp in high_order_comps:
            a = comp.amplitude * np.sin(comp.phase)
            b = comp.amplitude * np.cos(comp.phase)
            reconstructed += a * np.cos(comp.order * angles_rad) + b * np.sin(comp.order * angles_rad)
        
        return AnalysisResult(
            angles=angles,
            values=values,
            reconstructed_signal=reconstructed,
            high_order_waves=high_order_waves,
            spectrum_components=spectrum_components,
            high_order_amplitude=high_order_amplitude,
            high_order_rms=high_order_rms
        )
    
    def analyze_pitch(self, side: str):
        pitch_data = self.reader.pitch_data.get(side, {})
        
        if 'teeth' in pitch_data and len(pitch_data['teeth']) > 0:
            teeth = pitch_data['teeth']
            fp_values = pitch_data['fp_values']
            Fp_values = pitch_data['Fp_values']
        else:
            teeth_count = self.gear_params.teeth_count if self.gear_params else 87
            teeth = list(range(1, teeth_count + 1))
            fp_values = [0.0] * teeth_count
            Fp_values = [0.0] * teeth_count
        
        return PitchResult(
            teeth=teeth,
            fp_values=fp_values,
            Fp_values=Fp_values,
            fp_max=max(fp_values) if fp_values else 0.0,
            Fp_max=max(Fp_values) if Fp_values else 0.0,
            Fp_min=min(Fp_values) if Fp_values else 0.0,
            Fr=max(Fp_values) - min(Fp_values) if Fp_values else 0.0
        )
