"""
Klingelnberg 拟合正弦波报告 - 完美复刻图片样式
评估方法：正弦拟合
"""
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import matplotlib.table
import numpy as np
import logging
from typing import Any, Optional

# 尝试导入scipy用于插值，如果不可用则跳过
try:
    from scipy.interpolate import interp1d
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# 使用统一的logger配置
try:
    from config.logging_config import logger
except ImportError:
    logger = logging.getLogger('KlingelnbergSineFitPerfectReport')
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

class KlingelnbergSineFitPerfectReport:
    """Klingelnberg 拟合正弦波报告 - 完美复刻图片样式"""
    
    def __init__(self, settings=None):
        self.settings = settings
    
    def create_page(self, pdf, measurement_data):
        """
        创建拟合正弦波页面并添加到PDF
        
        Args:
            pdf: 打开的PdfPages对象
            measurement_data: 齿轮测量数据对象
        """
        logger.info("Starting to create Perfect Sine Fit Page...")
        try:
            # 创建A4纵向页面
            fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
            
            # 布局：Header, Profile部分（图表+表格）, Lead部分（图表+表格）
            gs = gridspec.GridSpec(3, 1, figure=fig, 
                                 height_ratios=[0.12, 0.44, 0.44],
                                 hspace=0.2, left=0.08, right=0.92, top=0.95, bottom=0.05)
            
            # 1. 创建Header区域
            header_ax = fig.add_subplot(gs[0, 0])
            self._create_header(header_ax, measurement_data)
            
            # 2. Profile部分：左右两个图表和表格
            profile_gs = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gs[1, 0], 
                                                         height_ratios=[0.7, 0.3], hspace=0.1)
            profile_charts_gs = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=profile_gs[0, 0], wspace=0.1)
            profile_left_ax = fig.add_subplot(profile_charts_gs[0, 0])
            profile_right_ax = fig.add_subplot(profile_charts_gs[0, 1])
            profile_table_ax = fig.add_subplot(profile_gs[1, 0])
            self._draw_charts_section(profile_left_ax, profile_right_ax, profile_table_ax, "Profile", measurement_data, 'profile')
            
            # 3. Lead部分：左右两个图表和表格
            lead_gs = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gs[2, 0],
                                                      height_ratios=[0.7, 0.3], hspace=0.1)
            lead_charts_gs = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=lead_gs[0, 0], wspace=0.1)
            lead_left_ax = fig.add_subplot(lead_charts_gs[0, 0])
            lead_right_ax = fig.add_subplot(lead_charts_gs[0, 1])
            lead_table_ax = fig.add_subplot(lead_gs[1, 0])
            self._draw_charts_section(lead_left_ax, lead_right_ax, lead_table_ax, "Lead", measurement_data, 'flank')
            
            pdf.savefig(fig)
            plt.close(fig)
            logger.info("Added Perfect Sine Fit Page to report")
        except Exception as e:
            logger.exception(f"Failed to create Perfect Sine Fit Page: {e}")
            raise
    
    def _create_header(self, ax, measurement_data):
        """创建页面头部"""
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        # 标题
        title = "Fit of sinusoids"
        ax.text(0.5, 0.6, title, transform=ax.transAxes,
               fontsize=16, ha='center', va='center', fontweight='bold')
        
        # 评估方法
        method = "Evaluation method: Sine fit"
        ax.text(0.5, 0.3, method, transform=ax.transAxes,
               fontsize=11, ha='center', va='center')
    
    def _draw_charts_section(self, left_ax, right_ax, table_ax, section_name, measurement_data, data_type):
        """
        绘制完整部分（左右两个图表+表格）
        
        Args:
            left_ax: 左侧图表坐标轴
            right_ax: 右侧图表坐标轴
            table_ax: 表格坐标轴
            section_name: 部分名称（"Profile"或"Lead"）
            measurement_data: 测量数据
            data_type: 数据类型（'profile'或'flank'）
        """
        # 绘制左侧图表
        left_result, left_avg = self._draw_perfect_chart(left_ax, f"{section_name} left", measurement_data, data_type, 'left')
        
        # 绘制右侧图表
        right_result, right_avg = self._draw_perfect_chart(right_ax, f"{section_name} right", measurement_data, data_type, 'right')
        
        # 绘制表格（使用左右两侧的数据）
        self._create_evaluation_table(table_ax, section_name, measurement_data, data_type, 
                                     left_result, left_avg, right_result, right_avg)
    
    def _draw_perfect_chart(self, ax, chart_type, measurement_data, data_type, side='left'):
        """
        绘制完美复刻图片样式的图表 - 使用真实的测量数据
        
        包含：
        - 左侧比例尺（绿色垂直线）
        - 红色原始数据曲线（每个齿的曲线都绘制）
        - 蓝色拟合正弦波曲线（基于平均数据）
        - 垂直刻度线
        - 水平标记线
        
        Args:
            ax: matplotlib坐标轴对象
            chart_type: 图表标题（如"Profile left"或"Lead right"）
            measurement_data: 测量数据
            data_type: 数据类型（'profile'或'flank'）
            side: 侧边（'left'或'right'）
        """
        ax.set_facecolor('white')
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        # 图表标题
        ax.text(0.5, 0.98, chart_type, transform=ax.transAxes,
               fontsize=10, ha='center', va='top', fontweight='bold')
        
        # 获取真实的测量数据
        data_dict = getattr(measurement_data, f"{data_type}_data", None)
        if not data_dict:
            ax.text(0.5, 0.5, f"No {data_type} data available", ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12, color='red')
            return None, None
        
        # 获取指定侧边的数据
        side_data = getattr(data_dict, side, {}) if hasattr(data_dict, side) else {}
        if not side_data:
            ax.text(0.5, 0.5, f"No {side} data available", ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12, color='red')
            return None, None
        
        # 获取markers
        if data_type == 'flank':
            markers_attr = f"lead_markers_{side}"
        else:
            markers_attr = f"{data_type}_markers_{side}"
        markers = getattr(measurement_data.basic_info, markers_attr, None)
        
        # 获取可用的齿号
        available_teeth = sorted(list(side_data.keys()))
        if not available_teeth:
            ax.text(0.5, 0.5, "No data available", ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12, color='red')
            return None, None
        
        # 选择要显示的齿（最多4个）
        if side == 'left':
            teeth_to_use = sorted(available_teeth, reverse=True)[:min(4, len(available_teeth))]
        else:
            teeth_to_use = sorted(available_teeth)[:min(4, len(available_teeth))]
        
        # 辅助函数：提取数据值（兼容不同格式）
        def extract_values(data_item):
            """从数据项中提取值列表，兼容不同格式"""
            if isinstance(data_item, dict):
                if 'values' in data_item:
                    return np.array(data_item['values'], dtype=float)
                return None
            elif isinstance(data_item, (list, tuple, np.ndarray)):
                return np.array(data_item, dtype=float)
            return None
        
        # 检查数据单位和格式
        first_tooth = teeth_to_use[0]
        sample_values = extract_values(side_data[first_tooth])
        if sample_values is None or len(sample_values) == 0:
            ax.text(0.5, 0.5, f"Invalid data format for tooth {first_tooth}", ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12, color='red')
            return None, None
        
        unit_scale = 1.0
        if len(sample_values) > 0 and np.max(np.abs(sample_values)) < 1.0:
            unit_scale = 1000.0
        
        # 计算平均数据（用于蓝色拟合曲线）
        avg_data = self._calculate_average_data(side_data, teeth_to_use, unit_scale)
        if avg_data is None or len(avg_data) == 0:
            ax.text(0.5, 0.5, "No data available", ha='center', va='center', 
                   transform=ax.transAxes, fontsize=12, color='red')
            return None, None
        
        # 计算评价范围
        evaluation_range = None
        n = len(avg_data)
        if markers and len(markers) >= 4:
            start_meas, eval_start, eval_end, end_meas = markers
            total_len = abs(end_meas - start_meas)
            if total_len > 0:
                dist_to_eval_start = abs(eval_start - start_meas)
                dist_to_eval_end = abs(eval_end - start_meas)
                idx_eval_start = int(n * (dist_to_eval_start / total_len))
                idx_eval_end = int(n * (dist_to_eval_end / total_len))
                idx_eval_start = max(0, min(idx_eval_start, n - 1))
                idx_eval_end = max(0, min(idx_eval_end, n - 1))
                if idx_eval_end > idx_eval_start + 4:
                    evaluation_range = (idx_eval_start, idx_eval_end)
        
        # 计算正弦拟合
        sine_result = self._calculate_dominant_sine(avg_data, evaluation_range)
        
        # 绘制区域定义
        chart_x_start = 0.15  # 左侧比例尺结束位置
        chart_x_end = 0.85    # 右侧刻度线开始位置
        chart_y_start = 0.15
        chart_y_end = 0.90
        
        # 确定要绘制的数据范围（只绘制评价范围内的数据）
        if evaluation_range:
            idx_eval_start, idx_eval_end = evaluation_range
            eval_indices = np.arange(idx_eval_start, idx_eval_end + 1)
            eval_n = len(eval_indices)
        else:
            eval_indices = np.arange(n)
            eval_n = n
        
        # 计算Y轴位置（基于markers，只使用评价范围）
        if markers and len(markers) >= 4:
            start_meas, eval_start, eval_end, end_meas = markers
            # 只使用评价范围的Y位置
            if evaluation_range:
                y_positions_eval = np.linspace(eval_start, eval_end, eval_n)
            else:
                y_positions_eval = np.linspace(start_meas, end_meas, n)
            y_min = min(eval_start, eval_end)
            y_max = max(eval_start, eval_end)
            y_range = y_max - y_min
            if y_range > 0:
                y_positions_norm = (y_positions_eval - y_min) / y_range * (chart_y_end - chart_y_start) + chart_y_start
            else:
                y_positions_norm = np.linspace(chart_y_start, chart_y_end, eval_n)
        else:
            y_positions_norm = np.linspace(chart_y_start, chart_y_end, eval_n)
        
        # 计算中心X位置（用于绘制曲线）
        x_center = (chart_x_start + chart_x_end) / 2
        chart_width = chart_x_end - chart_x_start
        
        # 缩放因子（10微米 = 0.2 * chart_width）
        scale_factor = chart_width / 50.0
        
        # 绘制每个齿的红色原始数据曲线（只绘制评价范围内的数据）
        for tooth in teeth_to_use:
            if tooth not in side_data:
                continue
            
            # 提取数据值（兼容不同格式）
            tooth_values = extract_values(side_data[tooth])
            if tooth_values is None or len(tooth_values) == 0:
                logger.warning(f"_draw_perfect_chart: tooth {tooth} has no valid data")
                continue
            
            # 单位转换（如果需要）
            if unit_scale != 1.0:
                tooth_values = tooth_values * unit_scale
            
            # 处理数据长度不匹配的情况
            if len(tooth_values) != n:
                logger.warning(f"_draw_perfect_chart: tooth {tooth} data length mismatch: {len(tooth_values)} != {n}")
                # 如果数据长度不同，尝试插值到目标长度
                if len(tooth_values) > 1 and HAS_SCIPY:
                    try:
                        orig_indices = np.linspace(0, len(tooth_values) - 1, len(tooth_values))
                        target_indices = np.linspace(0, len(tooth_values) - 1, n)
                        interp_func = interp1d(orig_indices, tooth_values, kind='linear', 
                                             bounds_error=False, fill_value='extrapolate')
                        tooth_values = interp_func(target_indices)
                    except Exception as e:
                        logger.warning(f"_draw_perfect_chart: interpolation failed for tooth {tooth}: {e}")
                        continue
                elif len(tooth_values) > n:
                    # 如果数据更长，截断到目标长度
                    tooth_values = tooth_values[:n]
                else:
                    # 如果数据更短且没有scipy，跳过这个齿
                    logger.warning(f"_draw_perfect_chart: tooth {tooth} data too short and scipy not available")
                    continue
            
            # 只取评价范围内的数据
            if len(tooth_values) == n:
                tooth_values_eval = tooth_values[eval_indices]
                x_tooth_norm = x_center + scale_factor * tooth_values_eval
                ax.plot(x_tooth_norm, y_positions_norm, color='red', linewidth=0.6,
                       transform=ax.transAxes, zorder=5, alpha=0.7)
        
        # 绘制平均数据的红色曲线（更粗，用于强调，只绘制评价范围内的数据）
        avg_values = np.array(avg_data, dtype=float)
        avg_values_eval = avg_values[eval_indices]
        x_avg_norm = x_center + scale_factor * avg_values_eval
        ax.plot(x_avg_norm, y_positions_norm, color='red', linewidth=0.8,
               transform=ax.transAxes, zorder=6, label='Raw Data', alpha=0.9)
        
        # 绘制蓝色拟合正弦波曲线（只绘制评价范围内的数据）
        if sine_result and 'sine_fit' in sine_result:
            sine_fit = sine_result['sine_fit']
            if len(sine_fit) == n:
                # 只取评价范围内的数据
                sine_fit_eval = sine_fit[eval_indices]
                sine_fit_mean = np.mean(sine_fit_eval)
                sine_fit_centered = sine_fit_eval - sine_fit_mean
                x_sine_norm = x_center + scale_factor * sine_fit_centered
                ax.plot(x_sine_norm, y_positions_norm, color='#0000FF', linewidth=1.0,
                       transform=ax.transAxes, zorder=6, label='Sine Fit', alpha=0.9)
            else:
                logger.warning(f"_draw_perfect_chart: sine_fit length mismatch: {len(sine_fit)} != {n}")
        
        # 绘制零线（黑色垂直线）
        ax.plot([x_center, x_center], [chart_y_start, chart_y_end],
               color='black', linewidth=0.5, transform=ax.transAxes, zorder=3)
        
        # 绘制左侧比例尺（绿色垂直线）
        scale_x = 0.08
        self._draw_scale_bar(ax, scale_x, chart_y_start, chart_y_end, markers, data_type)
        
        # 绘制右侧刻度线
        gray_line_x = 0.88
        ax.plot([gray_line_x, gray_line_x], [chart_y_start, chart_y_end],
               color='gray', linewidth=1.5, zorder=3, transform=ax.transAxes)
        
        black_line_x = 0.92
        ax.plot([black_line_x, black_line_x], [chart_y_start, chart_y_end],
               color='black', linewidth=1.5, zorder=3, transform=ax.transAxes)
        
        # 绘制数字标记（1, 2, 3, 4）
        num_labels = 4
        label_y_positions = np.linspace(chart_y_start + 0.05, chart_y_end - 0.05, num_labels)
        label_x_pos = (gray_line_x + black_line_x) / 2
        
        for i, y_pos in enumerate(label_y_positions):
            label_num = i + 1
            arrow_x = label_x_pos - 0.015
            ax.plot([arrow_x, arrow_x + 0.01], [y_pos, y_pos],
                   color='black', linewidth=0.8, zorder=6, transform=ax.transAxes)
            ax.plot([arrow_x, arrow_x + 0.005], [y_pos - 0.005, y_pos],
                   color='black', linewidth=0.8, zorder=6, transform=ax.transAxes)
            ax.plot([arrow_x, arrow_x + 0.005], [y_pos + 0.005, y_pos],
                   color='black', linewidth=0.8, zorder=6, transform=ax.transAxes)
            ax.text(arrow_x + 0.02, y_pos, str(label_num), transform=ax.transAxes,
                   fontsize=9, ha='left', va='center', color='black', fontweight='bold', zorder=7)
        
        # 返回计算结果供表格使用
        return sine_result, avg_data
    
    def _draw_scale_bar(self, ax, x, y_start, y_end, markers, data_type):
        """
        绘制左侧比例尺（绿色垂直线）
        
        Args:
            ax: matplotlib坐标轴对象
            x: X坐标（归一化）
            y_start, y_end: Y轴范围（归一化）
            markers: 评价范围标记点
            data_type: 数据类型
        """
        # 绘制绿色垂直线
        ax.plot([x, x], [y_start, y_end],
               color='green', linewidth=2.0, transform=ax.transAxes, zorder=4)
        
        # 绘制刻度标记（从下到上：<1, 1, 2, 3, 4）
        num_ticks = 5
        tick_labels = ['<1', '1', '2', '3', '4']
        tick_y_positions = np.linspace(y_start, y_end, num_ticks)
        
        bar_width = 0.012
        bar_height = 0.008
        tick_length = 0.008
        
        for i, (y_pos, label) in enumerate(zip(tick_y_positions, tick_labels)):
            # 绘制柱状标记（矩形块，在绿色线的左侧）
            bar_x = x - bar_width
            bar_y = y_pos - bar_height / 2
            rect = patches.Rectangle(
                (bar_x, bar_y), bar_width, bar_height,
                transform=ax.transAxes,
                facecolor='green', edgecolor='green', linewidth=0.5,
                zorder=5
            )
            ax.add_patch(rect)
            
            # 刻度线（水平短线，在绿色线上）
            ax.plot([x - tick_length, x + tick_length], [y_pos, y_pos],
                   color='green', linewidth=1.0, transform=ax.transAxes, zorder=6)
            
            # 标签（在柱状标记的左侧）
            ax.text(x - bar_width - 0.01, y_pos, label, transform=ax.transAxes,
                   fontsize=7, ha='right', va='center', color='black')
        
        # 计算评价范围长度（用于比例尺标注）
        if markers and len(markers) >= 4:
            start_meas, eval_start, eval_end, end_meas = markers
            eval_range_mm = abs(eval_end - eval_start)
        else:
            eval_range_mm = 3.0  # 默认值
        
        # 在比例尺下方标注长度和比例
        scale_text_y = y_start - 0.03
        ax.text(x, scale_text_y, f"{eval_range_mm:.3f} mm", transform=ax.transAxes,
               fontsize=7, ha='center', va='top', color='black')
        ax.text(x, scale_text_y - 0.02, "10.0 µm", transform=ax.transAxes,
               fontsize=7, ha='center', va='top', color='black')
        ratio = int(eval_range_mm * 1000 / 10.0) if eval_range_mm > 0 else 1000
        ax.text(x, scale_text_y - 0.04, f"{ratio}:1", transform=ax.transAxes,
               fontsize=7, ha='center', va='top', color='black')
    
    def _create_evaluation_table(self, ax, section_name, measurement_data, data_type, 
                                 left_result=None, left_avg=None, right_result=None, right_avg=None):
        """
        创建评估表格
        
        Args:
            ax: matplotlib坐标轴对象
            section_name: 部分名称（"Profile"或"Lead"）
            measurement_data: 测量数据
            data_type: 数据类型（'profile'或'flank'）
            left_result: 左侧正弦拟合结果（可选）
            left_avg: 左侧平均数据（可选）
            right_result: 右侧正弦拟合结果（可选）
            right_avg: 右侧平均数据（可选）
        """
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        # 辅助函数：计算单个侧面的表格数据
        def calculate_table_values(result, avg):
            if result is None or avg is None:
                return ["0.00", "1", "0.0", "0.00", "1", "0.0", "0.0"]
            
            A1 = result.get('A1', 0.0)
            O1 = result.get('O1', 1)
            phase_degrees = result.get('phase_degrees', 0.0)
            Pw1 = phase_degrees
            
            # 计算A2, O2, Pw2（简化处理，使用默认值）
            A2 = 0.0
            O2 = 1
            Pw2 = 0.0
            
            # 计算6xσ
            sigma = np.std(avg)
            six_sigma = 6 * sigma
            
            return [
                f"{A1:.2f}",
                f"{int(O1)}",
                f"{Pw1:.1f}",
                f"{A2:.2f}",
                f"{int(O2)}",
                f"{Pw2:.1f}",
                f"{six_sigma:.1f}"
            ]
        
        # 如果没有传入结果，尝试计算
        if left_result is None or left_avg is None:
            left_result, left_avg = self._calculate_side_results(measurement_data, data_type, 'left')
        if right_result is None or right_avg is None:
            right_result, right_avg = self._calculate_side_results(measurement_data, data_type, 'right')
        
        # 计算左右两列的数据
        left_col = calculate_table_values(left_result, left_avg)
        right_col = calculate_table_values(right_result, right_avg)
        
        # 中间列（参数名）
        middle_col = ["A1", "W(1)", "Pw(1)", "A2", "W(2)", "Pw(2)", "βxσ"]
        
        # 构建表格数据
        table_data = []
        for i in range(len(middle_col)):
            table_data.append([left_col[i], middle_col[i], right_col[i]])
        
        # 创建表格
        table = ax.table(
            cellText=table_data,
            cellLoc='center',
            bbox=[0.1, 0.1, 0.8, 0.8],
            edges='closed'
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        
        # 设置表格样式
        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor('black')
            cell.set_linewidth(0.5)
            
            # 中间列（参数名）加粗
            if col == 1:
                cell.set_text_props(weight='bold')
        
        # 添加标题
        ax.text(0.5, 0.95, "Evaluation method: Fit of sinusoids", transform=ax.transAxes,
               fontsize=9, ha='center', va='top', fontweight='bold')
        ax.text(0.5, 0.88, "Limiting curve parameters: R = 0.0039mm, n0 = 0.6, K = 2.8",
               transform=ax.transAxes, fontsize=8, ha='center', va='top')
    
    def _calculate_average_data(self, data_dict, teeth_list, unit_scale=1.0):
        """
        计算指定齿号的平均数据
        
        Args:
            data_dict: 齿面数据字典
            teeth_list: 要计算平均的齿号列表
            unit_scale: 单位缩放因子（1.0=微米，1000.0=毫米转微米）
        
        Returns:
            numpy.ndarray: 平均数据曲线（单位：微米）
        """
        if not data_dict or not teeth_list:
            return None
        
        # 辅助函数：提取数据值（兼容不同格式）
        def extract_values(data_item):
            """从数据项中提取值列表，兼容不同格式"""
            if isinstance(data_item, dict):
                if 'values' in data_item:
                    return np.array(data_item['values'], dtype=float)
                return None
            elif isinstance(data_item, (list, tuple, np.ndarray)):
                return np.array(data_item, dtype=float)
            return None
        
        sample_length = None
        for tooth in teeth_list:
            if tooth in data_dict:
                values = extract_values(data_dict[tooth])
                if values is not None and len(values) > 0:
                    sample_length = len(values)
                    break
        
        if sample_length is None:
            return None
        
        avg_data = np.zeros(sample_length)
        valid_count = 0
        
        for tooth in teeth_list:
            if tooth in data_dict:
                data = extract_values(data_dict[tooth])
                if data is not None and len(data) == sample_length:
                    if unit_scale != 1.0:
                        data = data * unit_scale
                    avg_data += data
                    valid_count += 1
        
        if valid_count == 0:
            return None
        
        return avg_data / valid_count
    
    def _calculate_side_results(self, measurement_data, data_type, side='left'):
        """
        计算指定侧面的正弦拟合结果
        
        Args:
            measurement_data: 测量数据
            data_type: 数据类型（'profile'或'flank'）
            side: 侧边（'left'或'right'）
        
        Returns:
            tuple: (sine_result, avg_data) 或 (None, None)
        """
        # 获取数据
        data_dict = getattr(measurement_data, f"{data_type}_data", None)
        if not data_dict:
            return None, None
        
        side_data = getattr(data_dict, side, {}) if hasattr(data_dict, side) else {}
        if not side_data:
            return None, None
        
        available_teeth = sorted(list(side_data.keys()))
        if not available_teeth:
            return None, None
        
        # 选择要使用的齿（最多4个）
        if side == 'left':
            teeth_to_use = sorted(available_teeth, reverse=True)[:min(4, len(available_teeth))]
        else:
            teeth_to_use = sorted(available_teeth)[:min(4, len(available_teeth))]
        
        # 辅助函数：提取数据值（兼容不同格式）
        def extract_values(data_item):
            """从数据项中提取值列表，兼容不同格式"""
            if isinstance(data_item, dict):
                if 'values' in data_item:
                    return np.array(data_item['values'], dtype=float)
                return None
            elif isinstance(data_item, (list, tuple, np.ndarray)):
                return np.array(data_item, dtype=float)
            return None
        
        # 检查数据单位和格式
        first_tooth = teeth_to_use[0]
        sample_values = extract_values(side_data[first_tooth])
        if sample_values is None or len(sample_values) == 0:
            return None, None
        
        unit_scale = 1.0
        if len(sample_values) > 0 and np.max(np.abs(sample_values)) < 1.0:
            unit_scale = 1000.0
        
        # 计算平均数据
        avg_data = self._calculate_average_data(side_data, teeth_to_use, unit_scale)
        if avg_data is None or len(avg_data) == 0:
            return None, None
        
        # 获取markers
        if data_type == 'flank':
            markers_attr = f"lead_markers_{side}"
        else:
            markers_attr = f"{data_type}_markers_{side}"
        markers = getattr(measurement_data.basic_info, markers_attr, None)
        
        # 计算评价范围
        evaluation_range = None
        n = len(avg_data)
        if markers and len(markers) >= 4:
            start_meas, eval_start, eval_end, end_meas = markers
            total_len = abs(end_meas - start_meas)
            if total_len > 0:
                dist_to_eval_start = abs(eval_start - start_meas)
                dist_to_eval_end = abs(eval_end - start_meas)
                idx_eval_start = int(n * (dist_to_eval_start / total_len))
                idx_eval_end = int(n * (dist_to_eval_end / total_len))
                idx_eval_start = max(0, min(idx_eval_start, n - 1))
                idx_eval_end = max(0, min(idx_eval_end, n - 1))
                if idx_eval_end > idx_eval_start + 4:
                    evaluation_range = (idx_eval_start, idx_eval_end)
        
        # 计算正弦拟合
        sine_result = self._calculate_dominant_sine(avg_data, evaluation_range)
        
        return sine_result, avg_data
    
    def _calculate_dominant_sine(self, data, evaluation_range=None):
        """
        使用FFT分析计算主导正弦分量（参考klingelnberg_sine_fit.py）
        
        Args:
            data: 原始测量数据（单位：微米）
            evaluation_range: 评价范围，格式为(idx_start, idx_end)
        
        Returns:
            dict: 包含O1（阶次）、A1（振幅，单位：微米）、phase（相位）、sine_fit（拟合正弦波）的字典
        """
        n = len(data)
        if n < 4:
            return {'O1': 1, 'A1': 0.0, 'phase': 0.0, 'phase_degrees': 0.0, 'sine_fit': np.zeros_like(data)}
        
        data_array = np.array(data, dtype=float)
        data_mean = np.mean(data_array)
        data_centered = data_array - data_mean
        
        # 确定评价范围
        if evaluation_range is None:
            eval_start, eval_end = 0, n
        else:
            eval_start, eval_end = evaluation_range
            eval_start = max(0, int(eval_start))
            eval_end = min(n, int(eval_end))
            if eval_end - eval_start < 4:
                eval_start, eval_end = 0, n
        
        # 在评价范围内执行FFT分析
        eval_data_centered = data_centered[eval_start:eval_end]
        eval_n = eval_end - eval_start
        
        if eval_n < 4:
            return {'O1': 1, 'A1': 0.0, 'phase': 0.0, 'phase_degrees': 0.0, 'sine_fit': np.zeros_like(data)}
        
        # 执行FFT分析
        fft_data = np.fft.rfft(eval_data_centered)
        n_freq = len(fft_data)
        
        # 计算振幅
        amplitudes = np.abs(fft_data) / eval_n
        
        # 找出振幅最大的频率分量（跳过直流分量）
        if n_freq > 1:
            max_amp_index = np.argmax(amplitudes[1:]) + 1
        else:
            max_amp_index = 0
        
        O1 = max_amp_index if max_amp_index > 0 else 1
        dominant_amp = amplitudes[max_amp_index] * 2
        phase = np.angle(fft_data[max_amp_index])
        
        if abs(dominant_amp) < 0.01:
            dominant_amp = 0.01 if dominant_amp >= 0 else -0.01
        
        # 计算频率
        if O1 > 0:
            eval_freq = float(O1) / eval_n
        else:
            eval_freq = 1.0 / eval_n
        
        # 创建拟合正弦波
        x = np.arange(n)
        if evaluation_range and eval_n < n:
            freq_scale = float(eval_n) / n
            freq = eval_freq * freq_scale
            phase_adjusted = phase - 2 * np.pi * eval_freq * eval_start
        else:
            freq = eval_freq
            phase_adjusted = phase
        
        sine_fit = dominant_amp * np.sin(2 * np.pi * freq * x + phase_adjusted) + data_mean
        
        # 计算相位值（度）
        phase_degrees = np.degrees(phase_adjusted) % 360
        
        return {
            'O1': O1,
            'A1': abs(dominant_amp),
            'phase': phase_adjusted,
            'phase_degrees': phase_degrees,
            'sine_fit': sine_fit
        }