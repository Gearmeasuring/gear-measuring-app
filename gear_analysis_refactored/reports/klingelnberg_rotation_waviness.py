"""
克林贝格旋转角范围内波纹度报表生成器
根据MKA文件生成旋转角范围内的波纹度分析图表（A4横排PDF）
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import font_manager
from scipy.signal import savgol_filter
from scipy.ndimage import gaussian_filter1d
from typing import Dict, List, Optional, Tuple, Any
import logging
import math

# 导入klingelnberg_ripple_spectrum模块的方法
from .klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings, SpectrumParams

# 配置matplotlib中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

logger = logging.getLogger(__name__)


class RotationWavinessReport:
    """旋转角范围内波纹度报表生成器"""
    
    def __init__(self, gear_data: Dict[str, Any], output_path: str = None):
        """
        初始化报表生成器
        
        Args:
            gear_data: 齿轮数据字典，包含profile_data, flank_data, gear_params等
            output_path: 输出PDF路径
        """
        self.gear_data = gear_data
        self.output_path = output_path or "Rotation_Waviness_Analysis.pdf"
        
        # 提取数据
        self.profile_data = gear_data.get('profile_data', {})
        self.flank_data = gear_data.get('flank_data', {})
        self.gear_params = gear_data.get('gear_params', {})
        self.evaluation_settings = gear_data.get('evaluation_settings', {}) or {}
        self.raw_gear_data = gear_data.get('gear_data', {}) or {}
        
        # 从gear_data中提取更多参数用于频谱页
        if 'gear_data' in gear_data:
            gd = gear_data['gear_data']
            self.gear_params.update({
                'drawing_no': gd.get('图号', 'N/A'),
                'customer': gd.get('客户', ''),
                'order_no': gd.get('订单号', 'N/A'),
                'date': gd.get('日期', 'N/A'),
                'file': gd.get('文件名', 'N/A'),
                'ep': gd.get('ep', 5.000),
                'b': gd.get('b', 76.438),
                'tu': gd.get('tu', 78.338)
            })
        
        # 齿轮参数
        self.teeth_count = self.gear_params.get('teeth', 87)
        self.module = self.gear_params.get('module', 1.859)
        self.helix_angle = self.gear_params.get('helix_angle', 25.3)
        self.pressure_angle = self.gear_params.get('pressure_angle', 20.0)
        self.base_diameter = self.gear_params.get('base_diameter', 0.0)
        self.pitch_diameter = self.gear_params.get('pitch_diameter', 0.0)
        
        # 计算基圆直径（如果未提供）
        if not self.base_diameter or self.base_diameter <= 0:
            if self.pitch_diameter and self.pitch_diameter > 0:
                self.base_diameter = self.pitch_diameter * math.cos(math.radians(self.pressure_angle))
            elif self.module and self.teeth_count:
                pitch_dia = self.module * self.teeth_count
                self.base_diameter = pitch_dia * math.cos(math.radians(self.pressure_angle))
        
        # 计算节圆直径（如果未提供）
        if not self.pitch_diameter or self.pitch_diameter <= 0:
            if self.module and self.teeth_count:
                self.pitch_diameter = self.module * self.teeth_count
    
    def _map_to_base_circle(self, data_type: str, tooth_data: np.ndarray, tooth_id: int, side: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        将齿形和齿向曲线映射到基圆上，计算旋转角
        
        算法流程：
        1. Profile: 计算渐开线展开角 ξ = (s / π×db) × 360°
        2. Helix: 计算轴向角度差 α₂ = (2×Δz×tan(βb)) / D₀
        3. 添加齿间偏移: tooth_offset = (tooth_id - 1) × (360° / ZE)
        4. 最终旋转角: α = ξ + α₂ + tooth_offset
        
        Args:
            data_type: 数据类型（'profile' 或 'flank'）
            tooth_data: 齿数据数组
            tooth_id: 齿号
            side: 齿面侧 ('left' or 'right')
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: (旋转角数组, 偏差值数组)
        """
        n_points = len(tooth_data)
        if n_points < 8:
            return None, None
        
        try:
            teeth_count = self.teeth_count
            if teeth_count <= 0:
                teeth_count = 87
            
            base_diameter = self.base_diameter
            if not base_diameter or base_diameter <= 0:
                base_diameter = 50.0
            
            pitch_diameter = self.pitch_diameter
            if not pitch_diameter or pitch_diameter <= 0:
                pitch_diameter = base_diameter / math.cos(math.radians(self.pressure_angle))
            
            helix_angle = self.helix_angle
            beta_0 = math.radians(helix_angle)
            
            # 齿间角度间隔
            tooth_angle_step = 360.0 / teeth_count
            tooth_offset = (tooth_id - 1) * tooth_angle_step
            
            if data_type == 'profile':
                # Profile: 基于渐开线展开长度计算旋转角
                # 获取评价范围
                start_idx, end_idx = self._get_evaluation_indices(n_points, data_type, side)
                if end_idx <= start_idx:
                    start_idx, end_idx = 0, n_points
                
                # 计算展开长度范围
                # 使用评价范围或默认值
                d1 = self.raw_gear_data.get('齿形起评点展长', {}).get(side, pitch_diameter * 0.95)
                d2 = self.raw_gear_data.get('齿形终评点展长', {}).get(side, pitch_diameter * 1.05)
                
                if isinstance(d1, dict):
                    d1 = d1.get('value', pitch_diameter * 0.95)
                if isinstance(d2, dict):
                    d2 = d2.get('value', pitch_diameter * 1.05)
                
                try:
                    d1 = float(d1)
                    d2 = float(d2)
                except:
                    d1 = pitch_diameter * 0.95
                    d2 = pitch_diameter * 1.05
                
                # 计算渐开线展开长度
                if d1 > 0 and d2 > 0:
                    lu = math.sqrt(max(0, d1**2 - base_diameter**2)) / 2.0
                    lo = math.sqrt(max(0, d2**2 - base_diameter**2)) / 2.0
                else:
                    lu = 0
                    lo = math.pi * base_diameter / 4
                
                # 生成展开长度数组
                roll_s_values = np.linspace(lu, lo, n_points)
                base_circumference = math.pi * base_diameter
                
                # 计算每个点的旋转角（不添加tau，因为xi已经包含了齿内角度信息）
                angles = []
                for i, s in enumerate(roll_s_values):
                    xi = (s / base_circumference) * 360.0  # 展开角
                    alpha2 = 0.0  # Profile无轴向分量
                    # 注意：不添加tau，因为xi已经包含了齿内的角度信息
                    alpha = xi + alpha2 + tooth_offset
                    angles.append(alpha)
                
                angles = np.array(angles)
                values = np.array(tooth_data)
                
                logger.info(f"Profile基圆映射: 齿{tooth_id}, 角度范围=[{np.min(angles):.1f}°, {np.max(angles):.1f}°]")
                return angles, values
            
            else:
                # Helix: 基于轴向位置计算旋转角 - 使用标准公式 Δφ = 2 × Δz × tan(β₀) / D₀
                # 获取评价范围
                b1 = self.raw_gear_data.get('齿向起评点', {}).get(side, 0.0)
                b2 = self.raw_gear_data.get('齿向终评点', {}).get(side, 0.0)
                
                if isinstance(b1, dict):
                    b1 = b1.get('value', 0.0)
                if isinstance(b2, dict):
                    b2 = b2.get('value', 0.0)
                
                try:
                    b1 = float(b1)
                    b2 = float(b2)
                except:
                    b1 = 0.0
                    b2 = 10.0
                
                if b2 <= b1:
                    b1 = 0.0
                    b2 = self.gear_params.get('face_width', 10.0)
                
                lb = abs(b2 - b1)
                # 使用评价范围中心作为参考点
                z0 = (b1 + b2) / 2.0
                
                # 使用节圆螺旋角 β₀（根据标准公式）
                # Δφ = 2 × Δz × tan(β₀) / D₀
                # 其中 β₀ 是节圆处的螺旋角，D₀ 是节圆直径
                tan_beta0 = math.tan(beta_0)
                
                # 生成轴向位置数组
                axial_positions = np.linspace(b1, b2, n_points)
                
                # 计算每个点的旋转角（使用标准公式）
                angles = []
                for i, z in enumerate(axial_positions):
                    # 计算相对于中心的轴向距离 Δz
                    delta_z = z - z0
                    # 使用标准公式计算轴向角度差 Δφ
                    # Δφ = 2 × Δz × tan(β₀) / D₀
                    alpha2_rad = (2.0 * delta_z * tan_beta0) / pitch_diameter
                    alpha2_deg = math.degrees(alpha2_rad)  # 转换为角度
                    xi = 0.0  # Helix无展开分量
                    # 注意：不添加tau，因为alpha2已经包含了齿内的角度信息
                    alpha = xi + alpha2_deg + tooth_offset
                    angles.append(alpha)
                
                angles = np.array(angles)
                values = np.array(tooth_data)
                
                logger.info(f"Helix基圆映射: 齿{tooth_id}, 角度范围=[{np.min(angles):.1f}°, {np.max(angles):.1f}°]")
                return angles, values
                
        except Exception as e:
            logger.warning(f"基圆映射失败: {e}")
            return None, None
    
    def _build_merged_curve(self, data_dict: Dict[int, List[float]], 
                            data_type: str, side: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        构建合并后的旋转角曲线
        
        Args:
            data_dict: 齿数据字典
            data_type: 数据类型 ('profile' or 'flank')
            side: 齿面侧 ('left' or 'right')
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: (合并后的旋转角数组, 合并后的偏差值数组)
        """
        if not data_dict:
            return None, None
        
        all_angles = []
        all_values = []
        
        tooth_ids = sorted(data_dict.keys())
        
        for tooth_id in tooth_ids:
            tooth_data = data_dict[tooth_id]
            
            if isinstance(tooth_data, dict) and 'values' in tooth_data:
                vals = np.array(tooth_data['values'], dtype=float)
            elif isinstance(tooth_data, (list, tuple, np.ndarray)):
                vals = np.array(tooth_data, dtype=float)
            else:
                continue
            
            if len(vals) < 8:
                continue
            
            # 过滤无效值
            valid_mask = vals > -1000000
            if np.sum(valid_mask) < len(vals) * 0.5:
                continue
            
            vals = vals[valid_mask]
            
            # 单位转换和去均值
            vals = vals - np.mean(vals)
            
            # 基圆映射
            angles, mapped_vals = self._map_to_base_circle(data_type, vals, tooth_id, side)
            
            if angles is not None and mapped_vals is not None:
                # 角度归一化到 [0, 360)
                angles = angles % 360.0
                all_angles.extend(angles)
                all_values.extend(mapped_vals)
        
        if not all_angles:
            return None, None
        
        all_angles = np.array(all_angles)
        all_values = np.array(all_values)
        
        # 按角度排序
        sort_idx = np.argsort(all_angles)
        all_angles = all_angles[sort_idx]
        all_values = all_values[sort_idx]
        
        logger.info(f"合并曲线: {len(all_angles)}个点, 角度范围=[{np.min(all_angles):.1f}°, {np.max(all_angles):.1f}°]")
        
        return all_angles, all_values
        
    def process_tooth_data(self, data_dict: Dict[int, List[float]],
                           data_type: Optional[str] = None,
                           side: Optional[str] = None) -> Tuple[List, List, List]:
        """
        处理齿数据，返回每个齿的独立数据用于分别绘制
        
        Args:
            data_dict: 齿数据字典 {tooth_id: [values]}
            data_type: 数据类型 ('profile' or 'flank')
            side: 齿面侧 ('left' or 'right')
            
        Returns:
            (tooth_ids_list, tooth_positions_list, tooth_values_list): 
            每个齿的ID列表、位置数组列表、值数组列表
        """
        if not data_dict:
            return None, None, None
        
        # 收集每个齿的数据
        tooth_ids_list = []
        tooth_positions_list = []
        tooth_values_list = []
        
        tooth_ids = sorted(data_dict.keys())
        
        for tooth_id in tooth_ids:
            tooth_values = data_dict[tooth_id]
            if isinstance(tooth_values, (list, np.ndarray)) and len(tooth_values) > 0:
                values = np.array(tooth_values)

                # 按评价范围裁剪数据
                if data_type and side:
                    start_idx, end_idx = self._get_evaluation_indices(len(values), data_type, side)
                    if end_idx > start_idx:
                        values = values[start_idx:end_idx]

                # 过滤掉未定义值（-2147483.648）
                valid_mask = values > -1000000
                if np.sum(valid_mask) > len(values) * 0.5:  # 至少50%的有效数据
                    valid_values = values[valid_mask]
                    
                    # 为这个齿创建横坐标（齿号范围）
                    tooth_positions = np.linspace(tooth_id, tooth_id + 1, 
                                                 len(valid_values), endpoint=False)
                    
                    tooth_ids_list.append(tooth_id)
                    tooth_positions_list.append(tooth_positions)
                    tooth_values_list.append(valid_values)
        
        if not tooth_ids_list:
            logger.warning("没有找到有效的齿数据")
            return None, None, None
        
        return tooth_ids_list, tooth_positions_list, tooth_values_list

    def _get_evaluation_range(self, data_type: Optional[str]) -> Tuple[float, float]:
        """获取评价范围设置（单位：mm）"""
        if data_type == 'profile':
            return self.evaluation_settings.get('profile_range', (0.0, 0.0))
        return self.evaluation_settings.get('lead_range', (0.0, 0.0))

    def _get_evaluation_indices(self, data_len: int, data_type: str, side: str) -> Tuple[int, int]:
        """获取评价范围索引（基于测量起止点和评价起止点）"""
        if data_len <= 0:
            return 0, 0

        eval_range = self._get_evaluation_range(data_type)
        start_eval, end_eval = eval_range if eval_range else (0.0, 0.0)

        prefix = '齿形' if data_type == 'profile' else '齿向'
        start_measure_key = f'{prefix}起测点展长' if data_type == 'profile' else f'{prefix}起测点'
        end_measure_key = f'{prefix}终测点展长' if data_type == 'profile' else f'{prefix}终测点'
        start_eval_key = f'{prefix}起评点展长' if data_type == 'profile' else f'{prefix}起评点'
        end_eval_key = f'{prefix}终评点展长' if data_type == 'profile' else f'{prefix}终评点'

        start_measure = self.raw_gear_data.get(start_measure_key, {}).get(side, 0.0)
        end_measure = self.raw_gear_data.get(end_measure_key, {}).get(side, 0.0)
        start_eval_point = self.raw_gear_data.get(start_eval_key, {}).get(side, 0.0)
        end_eval_point = self.raw_gear_data.get(end_eval_key, {}).get(side, 0.0)

        # 若用户设置了评价范围，优先使用用户设置
        if start_eval != 0.0 or end_eval != 0.0:
            start_eval_point = start_eval
            end_eval_point = end_eval

        # 如果测量起止点缺失，尝试用评价范围推断
        if end_measure <= start_measure:
            if end_eval_point > start_eval_point:
                start_measure = 0.0
                end_measure = end_eval_point
            else:
                return 0, data_len

        if end_eval_point <= start_eval_point:
            return 0, data_len

        if data_len <= 1:
            return 0, data_len

        point_spacing = (end_measure - start_measure) / (data_len - 1)
        if point_spacing <= 0:
            return 0, data_len

        start_idx = int((start_eval_point - start_measure) / point_spacing)
        end_idx = int((end_eval_point - start_measure) / point_spacing)

        start_idx = max(0, min(start_idx, data_len - 1))
        end_idx = max(start_idx + 1, min(end_idx, data_len))
        return start_idx, end_idx
    
    def fit_curve(self, angles: np.ndarray, values: np.ndarray, order: int = 1) -> np.ndarray:
        """
        拟合曲线
        
        Args:
            angles: 旋转角数组
            values: 测量值数组
            order: 主导阶次
            
        Returns:
            拟合后的曲线
        """
        if len(values) < 10:
            return values
        
        try:
            # 使用Savitzky-Golay滤波进行平滑
            window_length = min(51, len(values) // 4)
            if window_length % 2 == 0:
                window_length += 1
            if window_length < 5:
                window_length = 5
            
            fitted = savgol_filter(values, window_length, 3)
            
            # 或者使用高斯滤波
            # sigma = len(values) / 50
            # fitted = gaussian_filter1d(values, sigma)
            
            return fitted
        except Exception as e:
            logger.warning(f"拟合曲线失败: {e}, 返回原始数据")
            return values
    
    def plot_merged_rotation_waviness_chart(self, fig, ax, merged_angles: np.ndarray, 
                                             merged_values: np.ndarray, chart_number: str, 
                                             title: str, order: int = 1) -> None:
        """
        绘制基于基圆映射合并后的旋转角波纹度子图
        
        Args:
            fig: matplotlib图形对象
            ax: matplotlib坐标轴对象
            merged_angles: 合并后的旋转角数组（度）
            merged_values: 合并后的偏差值数组（μm）
            chart_number: 图表编号（1,2,3,4）
            title: 子图标题（Profile right等）
            order: 主导阶次
        """
        if merged_angles is None or merged_values is None or len(merged_angles) < 10:
            logger.warning(f"子图{chart_number}无有效合并数据")
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)
            ax.set_facecolor('white')
            return
        
        print(f"  绘制子图{chart_number}: {len(merged_angles)}个点")
        logger.info(f"绘制子图{chart_number}: {len(merged_angles)}个点, 角度范围=[{np.min(merged_angles):.1f}°, {np.max(merged_angles):.1f}°]")
        
        # 绘制合并后的曲线
        ax.plot(merged_angles, merged_values, '-', color='blue', linewidth=0.8, alpha=0.7)
        
        # 计算并绘制拟合曲线
        if len(merged_values) >= 10:
            fitted = self.fit_curve(merged_angles, merged_values, order)
            ax.plot(merged_angles, fitted, '-', color='red', linewidth=1.2, alpha=0.9)
        
        # 计算整体波纹度参数
        A1 = np.std(merged_values)
        O = order
        Pw = np.max(merged_values) - np.min(merged_values)
        
        print(f"  参数计算完成: A1={A1:.2f}, O={O}, Pw={Pw:.1f}")
        
        # 设置x轴范围（0-360度）
        ax.set_xlim(0, 360)
        
        # 设置y轴范围
        y_min = np.min(merged_values)
        y_max = np.max(merged_values)
        y_range = y_max - y_min
        ax.set_ylim(y_min - y_range*0.1, y_max + y_range*0.1)
        
        # 不添加网格线
        ax.grid(False)
        
        # 隐藏刻度标签（按照图片样式）
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        
        # 移除边框（只保留底部和左侧）
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # 在左上角显示标题
        ax.text(0.01, 0.95, title, transform=ax.transAxes,
               ha='left', va='top', fontsize=8, fontweight='bold')
        
        # 在左侧显示参数（按照图片格式）
        param_y = 0.70
        ax.text(0.01, param_y, f'A1', transform=ax.transAxes,
               ha='left', va='top', fontsize=7, fontweight='normal')
        ax.text(0.01, param_y-0.12, f'O', transform=ax.transAxes,
               ha='left', va='top', fontsize=7, fontweight='normal')
        ax.text(0.01, param_y-0.24, f'Pw', transform=ax.transAxes,
               ha='left', va='top', fontsize=7, fontweight='normal')
        
        # 显示参数值
        ax.text(0.055, param_y, f'{A1:.2f}', transform=ax.transAxes,
               ha='left', va='top', fontsize=7)
        ax.text(0.055, param_y-0.12, f'{O}', transform=ax.transAxes,
               ha='left', va='top', fontsize=7)
        ax.text(0.055, param_y-0.24, f'{Pw:.1f}', transform=ax.transAxes,
               ha='left', va='top', fontsize=7)
        
        # 设置刻度朝内
        ax.tick_params(direction='in', length=3, width=0.5)
    
    def plot_rotation_waviness_chart(self, fig, ax, tooth_ids_list: List, 
                                    tooth_positions_list: List, tooth_values_list: List,
                                    chart_number: str, title: str, order: int = 1) -> None:
        """
        绘制单个旋转角波纹度子图（每个齿用不同颜色独立绘制）
        
        Args:
            fig: matplotlib图形对象
            ax: matplotlib坐标轴对象
            tooth_ids_list: 齿ID列表
            tooth_positions_list: 每个齿的位置数组列表
            tooth_values_list: 每个齿的测量值数组列表
            chart_number: 图表编号（1,2,3,4）
            title: 子图标题（Profile right等）
            order: 主导阶次
        """
        if not tooth_ids_list or not tooth_positions_list or not tooth_values_list:
            logger.warning(f"子图{chart_number}无数据")
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)
            ax.set_facecolor('white')
            return
        
        print(f"  绘制子图{chart_number}: {len(tooth_ids_list)}个齿")
        logger.info(f"绘制子图{chart_number}: {len(tooth_ids_list)}个齿")
        
        # 生成颜色列表（用不同颜色区分每个齿）
        colors = plt.cm.tab10(np.linspace(0, 1, 10))  # 10种颜色循环使用
        
        # 收集所有数据用于计算整体参数
        all_values = []
        y_min_global = float('inf')
        y_max_global = float('-inf')
        max_tooth_id = 0
        
        # 为每个齿分别绘制
        for i, (tooth_id, positions, values) in enumerate(zip(tooth_ids_list, tooth_positions_list, tooth_values_list)):
            if len(positions) == 0 or len(values) == 0:
                continue
            
            color = colors[i % len(colors)]
            
            # 绘制测量曲线（原始数据）
            ax.plot(positions, values, '-', color=color, linewidth=0.8, alpha=0.7)
            
            # 计算并绘制拟合曲线
            if len(values) >= 10:
                fitted = self.fit_curve(positions, values, order)
                ax.plot(positions, fitted, '-', color=color, linewidth=1.2, alpha=0.9)
            
            all_values.extend(values)
            y_min_global = min(y_min_global, np.min(values))
            y_max_global = max(y_max_global, np.max(values))
            max_tooth_id = max(max_tooth_id, tooth_id)
        
        if not all_values:
            ax.text(0.5, 0.5, 'No Valid Data', ha='center', va='center',
                   transform=ax.transAxes, fontsize=10)
            return
        
        # 计算整体波纹度参数
        all_values_array = np.array(all_values)
        
        # 简单计算波纹度参数
        A1 = np.std(all_values_array)  # 使用标准差作为A1的近似值
        O = order  # 主导阶次
        Pw = np.max(all_values_array) - np.min(all_values_array)  # 峰峰值
        
        print(f"  参数计算完成: A1={A1:.2f}, O={O}, Pw={Pw:.1f}")
        
        # 设置x轴范围
        ax.set_xlim(min(tooth_ids_list), max_tooth_id + 1)
        
        # 设置y轴范围
        y_range = y_max_global - y_min_global
        ax.set_ylim(y_min_global - y_range*0.1, y_max_global + y_range*0.1)
        
        # 不添加网格线
        ax.grid(False)
        
        # 隐藏刻度标签（按照图片样式）
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        
        # 移除边框（只保留底部和左侧）
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # 在左上角显示齿号/标题
        ax.text(0.01, 0.95, title, transform=ax.transAxes,
               ha='left', va='top', fontsize=8, fontweight='bold')
        
        # 在左侧显示参数（按照图片格式）
        param_y = 0.70
        ax.text(0.01, param_y, f'A1', transform=ax.transAxes,
               ha='left', va='top', fontsize=7, fontweight='normal')
        ax.text(0.01, param_y-0.12, f'O', transform=ax.transAxes,
               ha='left', va='top', fontsize=7, fontweight='normal')
        ax.text(0.01, param_y-0.24, f'Pw', transform=ax.transAxes,
               ha='left', va='top', fontsize=7, fontweight='normal')
        
        # 显示参数值
        ax.text(0.055, param_y, f'{A1:.2f}', transform=ax.transAxes,
               ha='left', va='top', fontsize=7)
        ax.text(0.055, param_y-0.12, f'{O}', transform=ax.transAxes,
               ha='left', va='top', fontsize=7)
        ax.text(0.055, param_y-0.24, f'{Pw:.1f}', transform=ax.transAxes,
               ha='left', va='top', fontsize=7)
        
        # 设置刻度朝内
        ax.tick_params(direction='in', length=3, width=0.5)
    
    def generate_spectrum_page(self, pdf, order: int = 1):
        """
        生成第二页：频谱分析（Spectrum of the ripple）
        
        Args:
            pdf: PdfPages对象
            order: 主导阶次
        """
        logger.info("生成频谱分析页...")
        
        # 创建A4横排页面
        fig = plt.figure(figsize=(11.69, 8.27))
        fig.patch.set_facecolor('white')
        
        # 添加页面标题和信息
        self._add_spectrum_header(fig)
        
        # 创建4个频谱图
        gs = fig.add_gridspec(4, 1, hspace=0.25, top=0.88, bottom=0.12, 
                            left=0.08, right=0.92)
        
        # 数据映射
        data_map = [
            ('Profile right', self.profile_data.get('right', {}), 'profile', 'right'),
            ('Profile left', self.profile_data.get('left', {}), 'profile', 'left'),
            ('Helix right', self.flank_data.get('right', {}), 'flank', 'right'),
            ('Helix left', self.flank_data.get('left', {}), 'flank', 'left')
        ]
        
        spectrum_results = []
        
        for idx, (title, data, data_type, side) in enumerate(data_map):
            ax = fig.add_subplot(gs[idx])
            spectrum_data = self._plot_spectrum_chart(fig, ax, data, title, order, data_type, side)
            spectrum_results.append(spectrum_data)
        
        # 添加底部表格
        self._add_spectrum_tables(fig, spectrum_results)
        
        # 保存到PDF
        pdf.savefig(fig, dpi=150, bbox_inches='tight')
        plt.close(fig)
        logger.info("频谱分析页生成完成")
    
    def _add_spectrum_header(self, fig):
        """添加频谱分析页的头部信息"""
        # 左上角：Drawing no. 和 Customer
        fig.text(0.02, 0.96, f'Drawing no.: {self.gear_params.get("drawing_no", "N/A")}',
                fontsize=8, ha='left', va='top')
        fig.text(0.02, 0.93, f'Customer: {self.gear_params.get("customer", "")}',
                fontsize=8, ha='left', va='top')
        
        # 中央标题
        fig.text(0.5, 0.96, 'Analysis of ripple', fontsize=14, ha='center', 
                va='top', fontweight='bold')
        fig.text(0.5, 0.92, 'Spectrum of the ripple', fontsize=12, ha='center', va='top')
        
        # 右上角：Order no., Date, 参数
        fig.text(0.98, 0.96, f'Order no.: {self.gear_params.get("order_no", "N/A")}',
                fontsize=8, ha='right', va='top')
        fig.text(0.98, 0.93, f'Date: {self.gear_params.get("date", "N/A")}',
                fontsize=8, ha='right', va='top')
        fig.text(0.98, 0.90, 'Limiting curve parameters: R = 2.00, n0 = 1.00, K = 0.00',
                fontsize=7, ha='right', va='top')
        fig.text(0.98, 0.87, f'File: {self.gear_params.get("file", "N/A")}',
                fontsize=7, ha='right', va='top')
        fig.text(0.98, 0.84, f'z= {self.teeth_count}',
                fontsize=8, ha='right', va='top')
    
    def _plot_spectrum_chart(self, fig, ax, data_dict: Dict[int, List[float]], 
                           title: str, order: int, data_type: str, side: str) -> Dict:
        """
        绘制单个频谱图（使用klingelnberg_ripple_spectrum.py中的正弦拟合分析）
        
        Args:
            fig: matplotlib图形对象
            ax: matplotlib坐标轴对象
            data_dict: 齿数据字典
            title: 图表标题
            order: 主导阶次
            data_type: 数据类型 ('profile' or 'flank')
            side: 齿面侧 ('left' or 'right')
            
        Returns:
            频谱数据字典
        """
        # 处理数据
        print(f"\n=== 处理{title}数据 ===")
        print(f"  data_type={data_type}, side={side}")
        print(f"  data_dict包含{len(data_dict)}个齿")
        
        tooth_ids, tooth_positions_list, tooth_values_list = self.process_tooth_data(
            data_dict,
            data_type=data_type,
            side=side
        )
        
        if not tooth_ids or not tooth_values_list:
            print(f"  警告: {title}无数据")
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center',
                   transform=ax.transAxes)
            ax.set_title(title, loc='center', fontsize=9)
            return {}
        
        print(f"  处理后得到{len(tooth_ids)}个齿的数据")
        
        # 使用klingelnberg_ripple_spectrum.py中的方法进行频谱分析
        ze = self.teeth_count
        
        # 创建设置对象
        settings = RippleSpectrumSettings()
        # 禁用去趋势和滤波，使用原始数据
        settings.profile_helix_settings['detrend_settings']['enabled'] = False
        settings.profile_helix_settings['filter_params']['enabled'] = False
        
        # 创建报告对象
        report = KlingelnbergRippleSpectrumReport(settings)
        
        # 准备参数
        params = SpectrumParams(
            data_dict={side: data_dict},  # 只包含当前侧的数据
            teeth_count=ze,
            eval_markers=None,
            max_order=ze*7,  # 最大阶次为7倍齿数
            eval_length=None,
            base_diameter=None,
            max_components=50,
            side=side,
            data_type=data_type,
            info=None
        )
        
        # 计算频谱
        try:
            orders, amplitudes = report._calculate_spectrum(params, disable_detrend=True, disable_filter=True)
            print(f"  频谱分析完成，得到{len(orders)}个阶次")
        except Exception as e:
            print(f"  频谱分析失败: {e}")
            ax.text(0.5, 0.5, 'Spectrum Analysis Failed', ha='center', va='center',
                   transform=ax.transAxes)
            ax.set_title(title, loc='center', fontsize=9)
            return {}
        
        if not orders or not amplitudes:
            print(f"  警告: {title}频谱分析无结果")
            ax.text(0.5, 0.5, 'No Spectrum Data', ha='center', va='center',
                   transform=ax.transAxes)
            ax.set_title(title, loc='center', fontsize=9)
            return {}
        
        # 齿数和要分析的阶次
        teeth_multipliers = [1, 2, 3, 4, 5, 6, 7]  # 齿数的倍数（1Z, 2Z...）
        important_orders = [ze * mult for mult in teeth_multipliers]  # 实际阶次值：87, 174, 261...
        
        # 提取这些阶次的幅值
        amplitudes = []
        valid_orders = []
        valid_multipliers = []
        
        # 创建阶次到幅值的映射
        order_amp_map = dict(zip(orders, amplitudes))
        
        print(f"  {title} 拟合结果:")
        for mult in teeth_multipliers:
            order_val = ze * mult
            if order_val in order_amp_map:
                amp = order_amp_map[order_val]
                amplitudes.append(amp)
                valid_orders.append(order_val)
                valid_multipliers.append(mult)
                print(f"    阶次{order_val}({mult}Z): 幅值={amp:.4f}")
        
        if not amplitudes:
            ax.text(0.5, 0.5, 'No Valid Orders', ha='center', va='center',
                   transform=ax.transAxes)
            ax.set_title(title, loc='center', fontsize=9)
            return {}
        
        # 绘制柱状图
        x_positions = np.arange(len(valid_orders))
        bars = ax.bar(x_positions, amplitudes, width=0.6, color='blue', alpha=0.7)
        
        # 添加阶次标签和幅值标注（参考克林贝格格式）
        for i, (order_val, mult, amp) in enumerate(zip(valid_orders, valid_multipliers, amplitudes)):
            # 在柱子底部标注阶次值（如87, 174），黑色文字
            if amp > 0.02:  # 柱子足够高才标注
                ax.text(i, 0.001, f'{order_val}', ha='center', va='bottom', 
                       fontsize=6, fontweight='bold', color='black')
            
            # 在柱子顶部标注幅值（只标注较大的值）
            if amp > 0.04:  # 只标注超过0.04的值
                ax.text(i, amp + 0.003, f'{amp:.2f}', ha='center', 
                       va='bottom', fontsize=7, fontweight='normal', color='black')
        
        # 设置坐标轴（保持与原图一致）
        ax.set_xlim(-0.5, len(valid_orders) - 0.5)
        ax.set_ylim(0, 0.18)
        ax.set_yticks([0.04, 0.06, 0.08, 0.10, 0.15])
        ax.set_yticklabels(['0.04', '0.06', '0.08', '0.10', '0.15'], fontsize=7)
        ax.set_xticks([])
        
        # 添加x轴底部标注（ZE格式）- 参考克林贝格格式
        for i, mult in enumerate(valid_multipliers):
            if mult == 1:
                # 第一个位置标注"1"和"ZE"
                ax.text(i, -0.012, '1', ha='center', va='top', fontsize=7, 
                       transform=ax.transData, color='gray')
            else:
                # 其他位置显示"2ZE", "3ZE"等
                ax.text(i, -0.012, f'{mult}ZE', ha='center', va='top', fontsize=7, 
                       transform=ax.transData, color='gray')
        
        # x轴最右端标注最大阶次值
        max_order_approx = ze * 7
        ax.text(len(valid_orders) - 0.5, -0.012, f'{max_order_approx}', ha='right', 
               va='top', fontsize=6, transform=ax.transData, color='gray')
        
        # 设置标题
        ax.set_title(title, loc='center', fontsize=10, pad=5, fontweight='bold')
        
        # 添加右上角的滤波器和单位标注
        filter_text = 'Low-pass filter RC\n100000:1'
        ax.text(0.98, 0.98, filter_text, transform=ax.transAxes, 
               fontsize=6, ha='right', va='top', color='blue')
        
        # 添加网格
        ax.grid(True, axis='y', linestyle='-', linewidth=0.3, alpha=0.3)
        ax.set_axisbelow(True)
        
        # 添加右侧参数（根据数据类型显示不同参数）
        if data_type == 'profile':
            # 齿形参数
            ax.text(1.01, 0.85, f'ep={self.gear_params.get("ep", 1.454):.3f}',
                   transform=ax.transAxes, fontsize=7, va='top', ha='left')
            ax.text(1.01, 0.70, f'lo={self.gear_params.get("lo", 33.578):.3f}',
                   transform=ax.transAxes, fontsize=7, va='top', ha='left')
            ax.text(1.01, 0.55, f'lu={self.gear_params.get("lu", 24.775):.3f}',
                   transform=ax.transAxes, fontsize=7, va='top', ha='left')
        else:
            # 齿向参数
            ax.text(1.01, 0.85, f'el={self.gear_params.get("el", 2.766):.3f}',
                   transform=ax.transAxes, fontsize=7, va='top', ha='left')
            ax.text(1.01, 0.70, f'zo={self.gear_params.get("zo", 18.900):.3f}',
                   transform=ax.transAxes, fontsize=7, va='top', ha='left')
            ax.text(1.01, 0.55, f'zu={self.gear_params.get("zu", -18.900):.3f}',
                   transform=ax.transAxes, fontsize=7, va='top', ha='left')
        
        # 返回结果用于表格（包含所有显著阶次，按幅值降序）
        result_data = {}
        
        # 找出所有显著阶次（幅值 > 0.02）
        significant_threshold = 0.02
        significant_orders = []
        for order_val, amp in order_amp_map.items():
            if amp > significant_threshold:
                significant_orders.append((order_val, amp))  # (阶次, 幅值)
        
        # 按幅值降序排序
        significant_orders.sort(key=lambda x: x[1], reverse=True)
        
        # 取前10个显著阶次
        for order_val, amp in significant_orders[:10]:
            result_data[order_val] = {
                'A': amp,
                'O': order_val
            }
        
        print(f"  显著阶次（幅值>{significant_threshold}）: {[(o, f'{a:.3f}') for o, a in significant_orders[:10]]}")
        
        return result_data
    
    def _add_spectrum_tables(self, fig, spectrum_results):
        """添加底部表格（显示各阶次的幅值和阶次值）"""
        # 表格位置和尺寸
        table_y = 0.06
        cell_width = 0.040
        cell_height = 0.018
        
        # 左侧表格（Profile left & Helix left）
        if len(spectrum_results) >= 2:
            profile_left = spectrum_results[1] if len(spectrum_results) > 1 else {}
            helix_left = spectrum_results[3] if len(spectrum_results) > 3 else {}
            
            # Profile left 表格
            x_start = 0.06
            self._draw_table(fig, x_start, table_y, 'Profile\nleft', profile_left, 
                           cell_width, cell_height)
            
            # Helix left 表格（在Profile left下方）
            self._draw_table(fig, x_start, table_y - 0.042, 'Helix\nleft', helix_left, 
                           cell_width, cell_height)
        
        # 右侧表格（Profile right & Helix right）
        if len(spectrum_results) >= 3:
            profile_right = spectrum_results[0] if len(spectrum_results) > 0 else {}
            helix_right = spectrum_results[2] if len(spectrum_results) > 2 else {}
            
            # Profile right 表格
            x_start = 0.54
            self._draw_table(fig, x_start, table_y, 'Profile\nright', profile_right, 
                           cell_width, cell_height)
            
            # Helix right 表格（在Profile right下方）
            self._draw_table(fig, x_start, table_y - 0.042, 'Helix\nright', helix_right, 
                           cell_width, cell_height)
        
        # 添加右下角min:0.020标注
        fig.text(0.98, 0.01, 'min:0.020', fontsize=7, ha='right', va='bottom', color='gray')
    
    def _draw_table(self, fig, x_start, y_start, label, data_dict, cell_width, cell_height):
        """绘制单个数据表格（克林贝格格式）"""
        
        # 绘制标签列（带边框）
        rect = mpatches.Rectangle((x_start, y_start - cell_height*2), cell_width*0.7, cell_height*2,
                                 facecolor='lightgray', edgecolor='black', linewidth=0.5,
                                 transform=fig.transFigure)
        fig.patches.append(rect)
        fig.text(x_start + cell_width*0.35, y_start - cell_height, label, 
                fontsize=6, ha='center', va='center', fontweight='normal')
        
        # 在标签列内添加A/O标识
        fig.text(x_start + cell_width*0.15, y_start - cell_height/2, 'A', 
                fontsize=6, ha='center', va='center', fontweight='bold')
        fig.text(x_start + cell_width*0.15, y_start - cell_height*1.5, 'O', 
                fontsize=6, ha='center', va='center', fontweight='bold')
        
        # 绘制数据列
        col_x = x_start + cell_width*0.7
        for i, (order_key, data) in enumerate(list(data_dict.items())[:9]):  # 最多9列
            # A行（幅值）
            rect_a = mpatches.Rectangle((col_x, y_start - cell_height), cell_width, cell_height,
                                       facecolor='white', edgecolor='black', linewidth=0.5,
                                       transform=fig.transFigure)
            fig.patches.append(rect_a)
            fig.text(col_x + cell_width/2, y_start - cell_height/2, f'{data["A"]:.2f}', 
                    fontsize=6, ha='center', va='center')
            
            # O行（阶次）
            rect_o = mpatches.Rectangle((col_x, y_start - cell_height*2), cell_width, cell_height,
                                       facecolor='white', edgecolor='black', linewidth=0.5,
                                       transform=fig.transFigure)
            fig.patches.append(rect_o)
            fig.text(col_x + cell_width/2, y_start - cell_height*1.5, f'{data["O"]}', 
                    fontsize=6, ha='center', va='center')
            
            col_x += cell_width
    
    def create_waviness_curves_page(self, order: int = 1):
        """
        创建第一页：旋转角波纹度曲线（使用基圆映射合并曲线）
        
        Args:
            order: 主导阶次
            
        Returns:
            matplotlib figure对象
        """
        print("=== 创建旋转角波纹度曲线页（基圆映射版）===")
        logger.info("创建旋转角波纹度曲线页（基圆映射版）...")
        print(f"Profile数据: left={len(self.profile_data.get('left', {}))}个齿, right={len(self.profile_data.get('right', {}))}个齿")
        logger.info(f"Profile数据: left={len(self.profile_data.get('left', {}))}个齿, right={len(self.profile_data.get('right', {}))}个齿")
        print(f"Flank数据: left={len(self.flank_data.get('left', {}))}个齿, right={len(self.flank_data.get('right', {}))}个齿")
        logger.info(f"Flank数据: left={len(self.flank_data.get('left', {}))}个齿, right={len(self.flank_data.get('right', {}))}个齿")
        
        # 创建A4横排页面（297mm x 210mm）
        fig = plt.figure(figsize=(11.69, 8.27))  # A4横排尺寸（英寸）
        fig.patch.set_facecolor('white')
        
        # 添加页面标题（加大字体）
        fig.text(0.5, 0.975, 'Waviness in Rotation Angle Range', 
                ha='center', va='top', fontsize=16, fontweight='bold')
        
        # 创建4个子图（更紧凑的布局）
        gs = fig.add_gridspec(4, 1, hspace=0.08, top=0.92, bottom=0.08, 
                            left=0.12, right=0.98)
        
        # 1. 子图① (顶部) - Profile right（使用基圆映射合并曲线）
        ax1 = fig.add_subplot(gs[0])
        ax1.set_facecolor('white')
        angles1, values1 = self._build_merged_curve(
            self.profile_data.get('right', {}),
            data_type='profile',
            side='right'
        )
        print(f"子图1 Profile right: {len(angles1) if angles1 is not None else 0}个点")
        logger.info(f"子图1 Profile right: {len(angles1) if angles1 is not None else 0}个点")
        self.plot_merged_rotation_waviness_chart(fig, ax1, angles1, values1, '1', 'Profile right', order)
        
        # 2. 子图② - Profile left（使用基圆映射合并曲线）
        ax2 = fig.add_subplot(gs[1])
        ax2.set_facecolor('white')
        angles2, values2 = self._build_merged_curve(
            self.profile_data.get('left', {}),
            data_type='profile',
            side='left'
        )
        logger.info(f"子图2 Profile left: {len(angles2) if angles2 is not None else 0}个点")
        self.plot_merged_rotation_waviness_chart(fig, ax2, angles2, values2, '2', 'Profile left', order)
        
        # 3. 子图③ - Helix right（使用基圆映射合并曲线）
        ax3 = fig.add_subplot(gs[2])
        ax3.set_facecolor('white')
        angles3, values3 = self._build_merged_curve(
            self.flank_data.get('right', {}),
            data_type='flank',
            side='right'
        )
        logger.info(f"子图3 Helix right: {len(angles3) if angles3 is not None else 0}个点")
        self.plot_merged_rotation_waviness_chart(fig, ax3, angles3, values3, '3', 'Helix right', order)
        
        # 4. 子图④ (底部) - Helix left（使用基圆映射合并曲线）
        ax4 = fig.add_subplot(gs[3])
        ax4.set_facecolor('white')
        angles4, values4 = self._build_merged_curve(
            self.flank_data.get('left', {}),
            data_type='flank',
            side='left'
        )
        logger.info(f"子图4 Helix left: {len(angles4) if angles4 is not None else 0}个点")
        self.plot_merged_rotation_waviness_chart(fig, ax4, angles4, values4, '4', 'Helix left', order)
        
        print("=== 旋转角波纹度曲线页创建完成 ===")
        logger.info("旋转角波纹度曲线页创建完成")
        return fig
    
    def generate_report(self, order: int = 1) -> str:
        """
        生成完整的旋转角波纹度报表（独立PDF文件，仅包含曲线页）
        
        Args:
            order: 主导阶次
            
        Returns:
            生成的PDF文件路径
        """
        logger.info("开始生成旋转角波纹度报表...")
        
        # 保存PDF（仅包含曲线页）
        try:
            with PdfPages(self.output_path) as pdf:
                # 旋转角波纹度曲线页
                fig1 = self.create_waviness_curves_page(order)
                pdf.savefig(fig1, dpi=300, bbox_inches='tight')
                plt.close(fig1)
                
                # 添加元数据
                d = pdf.infodict()
                d['Title'] = 'Waviness in Rotation Angle Range'
                d['Author'] = 'Klingelnberg Gear Measurement System'
                d['Subject'] = 'Gear Waviness Analysis Report'
                d['Keywords'] = 'Rotation Angle, Waviness, Gear Measurement, Profile, Lead'
            
            logger.info(f"报表生成成功: {self.output_path}")
            return self.output_path
            
        except Exception as e:
            logger.error(f"保存PDF失败: {e}")
            raise


def generate_rotation_waviness_report(gear_data: Dict[str, Any], 
                                     output_path: str = None,
                                     order: int = 1) -> str:
    """
    生成旋转角波纹度报表的便捷函数
    
    Args:
        gear_data: 齿轮数据字典
        output_path: 输出PDF路径
        order: 主导阶次
        
    Returns:
        生成的PDF文件路径
    """
    report = RotationWavinessReport(gear_data, output_path)
    return report.generate_report(order)


if __name__ == "__main__":
    # 测试代码
    print("旋转角波纹度报表生成器")
    print("请从主程序调用此模块")
