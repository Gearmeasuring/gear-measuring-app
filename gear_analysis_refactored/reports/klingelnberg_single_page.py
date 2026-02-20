"""
克林贝格单页报告生成器 - 完全模仿参考图片布局
Single-page Klingelnberg report generator - exact replica of reference layout
"""
import os
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import math
from types import SimpleNamespace

from config.logging_config import logger
from .klingelnberg_spacing_page import KlingelnbergSpacingPageReport


class KlingelnbergSinglePageReport:
    """克林贝格单页报告 - 精确复制参考图片布局"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def _calculate_quality_grade(self, measured_value, param_type, param_code):
        """Calculate quality grade based on measured value and tolerance tables.
        
        Args:
            measured_value: The measured deviation value (absolute value)
            param_type: 'profile', 'lead', or 'spacing'
            param_code: Parameter code (e.g., 'fHa', 'fHb', 'fp', etc.)
            
        Returns:
            int: Quality grade (1-12), or None if cannot determine
        """
        if measured_value is None:
            return None
            
        # Take absolute value for comparison
        abs_value = abs(measured_value)
        
        # Tolerance lookup tables (from tolerance_dialog.py)
        if param_type == 'profile':
            # Quality level: (fHa, ffa, Fa)
            tolerance_table = {
                1: (3.0, 4.0, 5.0),
                2: (4.0, 6.0, 7.0),
                3: (5.5, 8.0, 10.0),
                4: (8.0, 12.0, 14.0),
                5: (11.0, 16.0, 20.0),
                6: (16.0, 22.0, 28.0),
                7: (22.0, 32.0, 40.0),
                8: (28.0, 45.0, 56.0),
                9: (40.0, 63.0, 80.0),
                10: (71.0, 110.0, 125.0),
                11: (110.0, 160.0, 200.0),
                12: (180.0, 250.0, 320.0)
            }
            # Map param_code to index
            code_map = {'fHa': 0, 'ffa': 1, 'Fa': 2}
            
        elif param_type == 'lead':
            # Quality level: (fHb, ffb, Fb)
            tolerance_table = {
                1: (2.5, 2.0, 3.0),
                2: (3.5, 5.0, 6.0),
                3: (4.5, 7.0, 8.0),
                4: (6.0, 8.0, 10.0),
                5: (8.0, 9.0, 12.0),
                6: (11.0, 12.0, 16.0),
                7: (16.0, 16.0, 22.0),
                8: (22.0, 25.0, 32.0),
                9: (32.0, 40.0, 50.0),
                10: (50.0, 63.0, 80.0),
                11: (80.0, 100.0, 125.0),
                12: (125.0, 160.0, 200.0)
            }
            code_map = {'fHb': 0, 'ffb': 1, 'Fb': 2}
            
        else:
            return None
            
        if param_code not in code_map:
            return None
            
        idx = code_map[param_code]
        
        # Find the quality grade where measured value <= tolerance
        for quality in range(1, 13):
            if quality in tolerance_table:
                tolerance = tolerance_table[quality][idx]
                if abs_value <= tolerance:
                    return quality
                    
        # If exceeds all tolerances, return 12+ (worst)
        return 12
        
    def generate_report(self, measurement_data, deviation_results, output_path: str, settings=None) -> bool:
        """生成单页Klingelnberg报告"""
        try:
            logger.info(f"开始生成单页Klingelnberg报告: {output_path}")
            
            # 创建PDF
            # 修复字体错误: TrueType font is missing table
            plt.rcParams['pdf.fonttype'] = 42
            plt.rcParams['ps.fonttype'] = 42
            plt.rcParams['font.sans-serif'] = ['Arial', 'Microsoft YaHei', 'SimHei', 'DejaVu Sans']
            
            # 收集所有齿号
            all_teeth = set()
            if measurement_data.profile_data.left:
                all_teeth.update(measurement_data.profile_data.left.keys())
            if measurement_data.profile_data.right:
                all_teeth.update(measurement_data.profile_data.right.keys())
            if measurement_data.flank_data.left:
                all_teeth.update(measurement_data.flank_data.left.keys())
            if measurement_data.flank_data.right:
                all_teeth.update(measurement_data.flank_data.right.keys())
            
            sorted_teeth = sorted(list(all_teeth))
            if not sorted_teeth:
                sorted_teeth = [1, 2, 3, 4, 5, 6] # Default
            
            # 分页：每页6个齿
            chunk_size = 6
            tooth_chunks = [sorted_teeth[i:i + chunk_size] for i in range(0, len(sorted_teeth), chunk_size)]
            
            # Handle PermissionError by trying alternative filenames
            actual_output_path = output_path
            max_retries = 5
            for retry in range(max_retries):
                try:
                    with PdfPages(actual_output_path) as pdf:
                        for page_idx, chunk in enumerate(tooth_chunks):
                            # 创建当前页面的数据视图 (Filtered Measurement Data)
                            class FilteredMeasurementData:
                                def __init__(self, original, teeth):
                                    self.basic_info = original.basic_info
                                    self.file_path = getattr(original, 'file_path', '')
                                    self.pitch_data = getattr(original, 'pitch_data', None)
                                    self.deviation_result = getattr(original, 'deviation_result', None)
                                    
                                    self.profile_data = SimpleNamespace()
                                    self.profile_data.left = {k: v for k, v in original.profile_data.left.items() if k in teeth}
                                    self.profile_data.right = {k: v for k, v in original.profile_data.right.items() if k in teeth}
                                    
                                    self.flank_data = SimpleNamespace()
                                    self.flank_data.left = {k: v for k, v in original.flank_data.left.items() if k in teeth}
                                    self.flank_data.right = {k: v for k, v in original.flank_data.right.items() if k in teeth}

                            chunk_data = FilteredMeasurementData(measurement_data, chunk)
                            
                            # 创建整页figure (A4尺寸)
                            fig = plt.figure(figsize=(8.27, 11.69), dpi=150)  # A4: 210mm x 297mm
                            
                            # 使用GridSpec进行精确布局
                            gs = gridspec.GridSpec(
                                4, 1,  # 4行1列: header, profile_charts, profile_table, lead section
                                figure=fig,
                                height_ratios=[0.14, 0.33, 0.08, 0.45],  # 精确控制各部分高度
                                hspace=0.03,
                                left=0.08,
                                right=0.95,
                                top=0.96,
                                bottom=0.04
                            )
                            
                            # 1. 创建Header区域
                            header_ax = fig.add_subplot(gs[0, 0])
                            self._create_header(header_ax, chunk_data)
                            
                            # 2. 创建Profile Chart区域
                            profile_gs = gridspec.GridSpecFromSubplotSpec(
                                1, 2, subplot_spec=gs[1, 0], wspace=0.1
                            )
                            profile_left_ax = fig.add_subplot(profile_gs[0, 0])
                            profile_right_ax = fig.add_subplot(profile_gs[0, 1])
                            self._create_profile_charts(profile_left_ax, profile_right_ax, 
                                                        chunk_data, deviation_results)
                            
                            # 3. 创建Profile Data Table区域  
                            profile_table_ax = fig.add_subplot(gs[2, 0])
                            self._create_profile_table(profile_table_ax, deviation_results, chunk_data, visible_teeth=chunk)
                            
                            # 4. 创建Lead Chart和Table区域
                            lead_gs = gridspec.GridSpecFromSubplotSpec(
                                2, 2, subplot_spec=gs[3, 0], 
                                height_ratios=[0.8, 0.2], wspace=0.1, hspace=0.05
                            )
                            lead_left_ax = fig.add_subplot(lead_gs[0, 0])
                            lead_right_ax = fig.add_subplot(lead_gs[0, 1])
                            lead_table_ax = fig.add_subplot(lead_gs[1, :])
                            
                            self._create_lead_section(lead_left_ax, lead_right_ax, lead_table_ax,
                                                     chunk_data, deviation_results, visible_teeth=chunk)
                            
                            # 保存页面
                            pdf.savefig(fig, bbox_inches='tight', pad_inches=0.1)
                            plt.close(fig)
                        
                        # Add Spacing Page
                        try:
                            spacing_reporter = KlingelnbergSpacingPageReport()
                            spacing_reporter.create_page(pdf, measurement_data, deviation_results)
                            logger.info("Added Spacing Page to report")
                        except Exception as e:
                            logger.error(f"Failed to add spacing page: {e}")
                    
                    # If we get here, file was saved successfully
                    logger.info(f"单页Klingelnberg报告生成成功: {actual_output_path}")
                    return True
                    
                except PermissionError as pe:
                    # File is locked, try with a new filename
                    if retry < max_retries - 1:
                        import datetime
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        base, ext = os.path.splitext(output_path)
                        actual_output_path = f"{base}_{timestamp}{ext}"
                        logger.warning(f"文件被占用，尝试保存到: {actual_output_path}")
                    else:
                        # Last retry failed
                        raise pe
            
        except PermissionError as e:
            logger.error(f"无法保存文件（文件被占用）: {e}")
            print(f"ERROR: 文件被占用，请关闭PDF文件后重试: {e}")
            return False
            
        except Exception as e:
            logger.exception(f"生成单页报告失败: {e}")
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_order_no(self, info):
        """获取Order No.，尝试多种方式"""
        # 方法1: 直接获取order_no
        order_no = getattr(info, 'order_no', None)
        if order_no:
            order_no = str(order_no).strip()
            if order_no and order_no.upper() not in ['N/A', 'NA', '']:
                return order_no
        
        # 方法2: 尝试从serial获取
        serial = getattr(info, 'serial', None)
        if serial:
            serial = str(serial).strip()
            if serial and serial.upper() not in ['N/A', 'NA', '']:
                return serial
        
        # 方法3: 尝试从order_no的其他变体获取
        for attr_name in ['order_number', 'serial_no', 'serial_number', 'order']:
            value = getattr(info, attr_name, None)
            if value:
                value = str(value).strip()
                if value and value.upper() not in ['N/A', 'NA', '']:
                    return value
        
        # 如果都没有，返回N/A
        return 'N/A'
    
    def _create_header(self, ax, measurement_data):
        """创建页面头部 - Header with metadata"""
        ax.axis('off')
        
        # 标题
        ax.text(0.5, 1.1, 'Gear Profile/Lead', 
                ha='center', va='bottom', fontsize=14, fontweight='bold',
                transform=ax.transAxes)
        
        info = measurement_data.basic_info
        
        # 辅助函数
        def fmt(val, format_str="{}", default=""):
            if val is None or val == "": return default
            try:
                # 如果是字符串，先去除首尾空白
                if isinstance(val, str):
                    val = val.strip()
                    if val == "" or val.upper() == "N/A" or val.upper() == "NA":
                        return default
                if isinstance(val, (float, int)):
                    return format_str.format(val)
                return str(val)
            except:
                return str(val) if val else default

        # 计算基本参数
        db_str = ""
        beta_b_str = ""
        try:
            mn = info.module
            z = info.teeth
            alpha_n_deg = info.pressure_angle
            beta_deg = info.helix_angle
            
            if mn and z and alpha_n_deg:
                alpha_n = math.radians(alpha_n_deg)
                beta = math.radians(beta_deg)
                
                # 端面压力角
                alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta))
                # 分度圆直径
                d = z * mn / math.cos(beta)
                # 基圆直径 db = d * cos(alpha_t)
                db = d * math.cos(alpha_t)
                
                # 基圆螺旋角 beta_b = asin(sin(beta) * cos(alpha_n))
                beta_b_deg = math.degrees(math.asin(math.sin(beta) * math.cos(alpha_n)))
                
                db_str = f"{db:.4f}mm"
                beta_b_str = f"{beta_b_deg:.3f}°"
        except Exception as e:
            logger.warning(f"计算基圆参数失败: {e}")

        # 计算评估长度和Approach Length
        l_alpha_str = ""
        l_beta_str = ""
        appr_length_str = ""
        
        try:
            # Profile Evaluation Length (L_alpha) = |d2 - d1|
            # Profile Approach Length = |d1 - da|
            if hasattr(info, 'profile_markers_left') and info.profile_markers_left and len(info.profile_markers_left) >= 3:
                da, d1, d2, _ = info.profile_markers_left
                l_alpha = abs(d2 - d1)
                appr_len = abs(d1 - da)
                if l_alpha > 0: l_alpha_str = f"{l_alpha:.2f}mm"
                if appr_len > 0: appr_length_str = f"{appr_len:.2f}mm"
                
            # Lead Evaluation Length (L_beta) = |b2 - b1|
            if hasattr(info, 'lead_markers_left') and info.lead_markers_left and len(info.lead_markers_left) >= 3:
                ba, b1, b2, _ = info.lead_markers_left
                l_beta = abs(b2 - b1)
                if l_beta > 0: l_beta_str = f"{l_beta:.2f}mm"
                
        except Exception as e:
            logger.warning(f"计算评估长度失败: {e}")

        # 构建表格数据
        # 格式: [Label, Value, Label, Value, Label, Value]
        data = [
            ['Prog.No.:', fmt(getattr(info, 'program', '')), 'Operator:', fmt(getattr(info, 'operator', '')), 'Date:', fmt(getattr(info, 'date', ''))],
            ['Type:', fmt(getattr(info, 'type_', 'gear'), default='gear'), 'No. of teeth:', fmt(getattr(info, 'teeth', '')), 'Face Width:', fmt(getattr(info, 'width', ''), "{:.2f}mm")],
            ['Drawing No.:', fmt(getattr(info, 'drawing_no', '')), 'Module m:', fmt(getattr(info, 'module', ''), "{:.3f}mm"), 'Length Ev. Lα:', l_alpha_str],
            ['Order No.:', self._get_order_no(info), 'Pressure angle:', fmt(getattr(info, 'pressure_angle', ''), "{:.0f}°"), 'Length Ev. Lβ:', l_beta_str],
            ['Cust./Mach. N:', fmt(getattr(info, 'customer', '')), 'Helix angle:', fmt(getattr(info, 'helix_angle', ''), "{:.2f}°"), 'Appr. Length:', appr_length_str],
            ['Loc. of check:', fmt(getattr(info, 'location', '')), 'Base Cir.-Ø db:', db_str, 'Stylus-Ø:', fmt(getattr(info, 'ball_diameter', ''), "{:.3f}mm")],
            ['Condition:', fmt(getattr(info, 'condition', '')), 'Base Helix ang:', beta_b_str, 'Add.Mod.Coe:', fmt(getattr(info, 'modification_coeff', ''), "{:.3f}")]
        ]
        
        # 创建表格
        # 调整bbox，给表格更多空间
        table = ax.table(cellText=data, loc='center', cellLoc='left', bbox=[0.02, 0, 0.98, 1])
        
        # 设置样式
        table.auto_set_font_size(False)
        table.set_fontsize(7)
        
        # 自动调整所有列的宽度，确保内容不溢出
        table.auto_set_column_width(range(len(data[0])))
        
        cells = table.get_celld()
        for (row, col), cell in cells.items():
            cell.set_edgecolor('black')
            cell.set_linewidth(0.5)
            
            # 根据列类型设置不同的样式
            if col in [0, 2, 4]:  # 标签列
                # 标签列：左对齐、加粗
                cell.set_text_props(verticalalignment='center', horizontalalignment='left', weight='bold')
            else:  # 数值列
                # 数值列：右对齐，确保内容不会溢出右侧边框
                cell.set_text_props(verticalalignment='center', horizontalalignment='right')
                # cell.set_facecolor('#f5f5f5') # 可选：添加浅灰色背景
            
            # 调整单元格高度
            cell.set_height(1.0/7)
            
    def _calculate_crowning(self, data, markers):
        """Calculate crowning (Ca/Cb) from measurement data and markers.
        
        Args:
            data: List/Array of measurement values
            markers: Tuple of (start_meas, start_eval, end_eval, end_meas)
            
        Returns:
            float: Crowning value, or None if calculation fails
        """
        # 正确处理numpy数组
        if data is None or (hasattr(data, '__len__') and len(data) == 0) or not markers or len(markers) < 4:
            return None
            
        try:
            # markers: da, d1, d2, de (or ba, b1, b2, be)
            # Assuming data corresponds linearly to the range [start_meas, end_meas]
            start_meas, start_eval, end_eval, end_meas = markers
            
            total_len = abs(end_meas - start_meas)
            if total_len == 0:
                return None
                
            # Calculate indices for evaluation range
            n_points = len(data)
            
            # Calculate relative positions (0 to 1)
            # Note: We use absolute differences to handle both increasing and decreasing coordinates
            dist_to_start = abs(start_eval - start_meas)
            dist_to_end = abs(end_eval - start_meas)
            
            idx_start = int(n_points * (dist_to_start / total_len))
            idx_end = int(n_points * (dist_to_end / total_len))
            
            # Ensure indices are within bounds and valid
            idx_start = max(0, min(idx_start, n_points - 1))
            idx_end = max(0, min(idx_end, n_points - 1))
            
            if idx_end <= idx_start + 2: # Need at least 3 points
                return None
                
            # Extract data in evaluation range
            y_eval = np.array(data[idx_start:idx_end])
            
            # Create x coordinates (physical units, e.g., mm)
            # We map indices to the physical range [start_eval, end_eval]
            eval_len = abs(end_eval - start_eval)
            x_eval = np.linspace(-eval_len/2, eval_len/2, len(y_eval))
            
            # Fit parabola: y = ax^2 + bx + c
            # We use a centered coordinate system for x to simplify
            coeffs = np.polyfit(x_eval, y_eval, 2)
            a = coeffs[0]
            
            # Crowning Ca = |a| * (L^2) / 4
            # Sign convention: usually crowning is positive for convex ("hill")
            # In gear profile deviation, "material plus" is usually positive.
            # A convex profile (hill) corresponds to a < 0 in y = ax^2 (concave down parabola).
            # So if a < 0, we report positive crowning.
            # If a > 0, it's "hollow", we might report negative crowning or just the value.
            # ISO 1328 usually defines C_alpha as the distance, so it's a magnitude?
            # But "hollow" is different from "crowned".
            # Let's use the standard definition: C = -a * (L^2) / 4
            # This gives positive C for convex (a<0) and negative C for concave (a>0).
            
            crowning = -a * (eval_len ** 2) / 4
            return crowning
            
        except Exception as e:
            logger.warning(f"Crowning calculation failed: {e}")
            return None
    
    def _create_profile_charts(self, ax_left, ax_right, measurement_data, deviation_results):
        """创建Profile图表 - 左右齿面"""
        # 左齿面
        self._draw_single_profile_chart(ax_left, 'Left Flank', measurement_data.profile_data.left, measurement_data, deviation_results)
        
        # 右齿面
        self._draw_single_profile_chart(ax_right, 'Right Flank', measurement_data.profile_data.right, measurement_data, deviation_results)
    
    def _draw_scale_box(self, ax, y_range_mm):
        """绘制10um比例尺标示框
        
        Args:
            ax: matplotlib axes对象
            y_range_mm: Y轴范围（mm），用于计算比例尺的位置
        """
        # 10um 对应的X轴宽度
        # 绘图比例: x = x_center + (values / 50.0)
        # 所以 10um = 10/50 = 0.2 单位
        scale_width = 0.2
        
        # 框的位置 (左上角)
        # X: 0.8 (第一个齿中心是1，左边是0.5，0.8在左侧空白处)
        # Y: 基于Y轴范围计算位置（在Y轴的上方，大约90%的位置）
        x_center = 0.8
        y_lim = ax.get_ylim()
        y_center = y_lim[0] + (y_lim[1] - y_lim[0]) * 0.9
        
        # 框的高度 (根据Y轴范围自适应，大约占8%)
        box_height = (y_lim[1] - y_lim[0]) * 0.08
        
        # 绘制矩形框
        rect = patches.Rectangle(
            (x_center - scale_width/2, y_center - box_height/2),
            scale_width, box_height,
            linewidth=0.8, edgecolor='black', facecolor='white',
            zorder=20
        )
        ax.add_patch(rect)
        
        # 文字
        ax.text(x_center, y_center, '10\nµm', 
                ha='center', va='center', fontsize=5, zorder=21)
        
        # 绘制左右箭头 (指向框的垂直边)
        # 左箭头 (在左边框外，指向右)
        ax.plot(x_center - scale_width/2 - 0.05, y_center, 'k>', markersize=2, zorder=22, clip_on=False)
        # 右箭头 (在右边框外，指向左)
        ax.plot(x_center + scale_width/2 + 0.05, y_center, 'k<', markersize=2, zorder=22, clip_on=False)

    def _draw_single_profile_chart(self, ax, title, tooth_data, measurement_data, deviation_results=None):
        """绘制单个Profile图表 - 每个齿独立X轴"""
        ax.set_facecolor('white')
        for spine in ax.spines.values():
            spine.set_linewidth(1.0)
            spine.set_edgecolor('black')
        
        # 标题放在图表内部顶部
        ax.text(0.5, 0.98, title, transform=ax.transAxes,
               fontsize=9, ha='center', va='top', fontweight='bold')
        
        # 获取标准名称
        standard_name = "DIN 3962"  # 默认值
        if measurement_data and hasattr(measurement_data, 'basic_info'):
            standard_attr = getattr(measurement_data.basic_info, 'tolerance_standard', None)
            if standard_attr:
                standard_name = standard_attr
        elif deviation_results and 'tolerance_standard' in deviation_results:
            standard_name = deviation_results['tolerance_standard']
        elif deviation_results and 'tolerance_settings' in deviation_results:
            tol_settings = deviation_results.get('tolerance_settings', {})
            if isinstance(tol_settings, dict):
                for key in tol_settings.keys():
                    if 'Profile' in key or 'profile' in key.lower():
                        if '_' in key:
                            parts = key.split('_', 1)
                            if len(parts) > 0:
                                standard_name = parts[0]
                            break
        
        # 左侧标注信息 - 仅在Left Flank图表上显示，放在图表兤部
        if 'Left' in title:
            # 1. 标准信息框 (动态标准名称)
            ax.text(0.02, 0.98, standard_name, transform=ax.transAxes,
                   fontsize=7, ha='left', va='top', 
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black', linewidth=0.8))
            
            # 2. Tip标记
            ax.text(0.02, 0.78, 'Tip', transform=ax.transAxes,
                   fontsize=6, ha='left', va='center',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.5))
            
            # 3. Root标记
            ax.text(0.02, 0.12, 'Root', transform=ax.transAxes,
                   fontsize=6, ha='left', va='center',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.5))


        
        # Y轴标签 - 已移除
        # ax.set_ylabel('10\nμm', fontsize=7, rotation=0, ha='right', va='center', labelpad=10)
        # ax.yaxis.set_label_coords(-0.08, 0.5)
        
        # Top/Bottom标注 - 已移除
        # ax.text(-0.12, 0.95, 'Top', transform=ax.transAxes, 
        #        fontsize=7, ha='center', va='top', rotation=90)
        # ax.text(-0.12, 0.05, 'Bottom', transform=ax.transAxes, 
        #        fontsize=7, ha='center', va='bottom', rotation=90)
        
        # Va标注 - 已移除
        # ax.text(-0.08, 0.8, 'Va100025', transform=ax.transAxes,
        #        fontsize=6, ha='center', va='center', rotation=90)
        # ax.text(-0.08, 0.2, 'Vb213', transform=ax.transAxes,
        #        fontsize=6, ha='center', va='center', rotation=90)
        
        
        tooth_width_mm = 15.0  # Default
        
        # 先获取markers并设置Y轴范围（在绘制曲线之前）
        profile_markers = None
        if hasattr(measurement_data, 'basic_info'):
            info = measurement_data.basic_info
            if 'Left' in title:
                profile_markers = getattr(info, 'profile_markers_left', None)
            else:
                profile_markers = getattr(info, 'profile_markers_right', None)
            
            # 调试日志
            logger.info(f"Profile chart '{title}': markers = {profile_markers}")
            
            if profile_markers and len(profile_markers) >= 4:
                tooth_width_mm = profile_markers[3] # de
        
        # 提前设置Y轴范围（基于markers）
        if profile_markers and len(profile_markers) >= 4:
            y_da, y_d1, y_d2, y_de = profile_markers
            y_min = min(y_da, y_de)
            y_max = max(y_da, y_de)
            y_range = y_max - y_min
            if y_range > 0:
                ax.set_ylim(y_min - y_range * 0.05, y_max + y_range * 0.05)
            else:
                ax.set_ylim(y_min - 0.1, y_max + 0.1)
        
        # 获取实际测量的齿数并按顺序排列
        # 根据标题判断是左侧还是右侧
        teeth_to_show = []
        if tooth_data:
            available_teeth = sorted(list(tooth_data.keys()))
            
            # 根据图表标题确定齿数排列顺序
            if 'Left' in title:
                # 左侧：从大到小
                teeth_to_show = sorted(available_teeth, reverse=True)
            else:  # Right
                # 右侧：从小到大
                teeth_to_show = sorted(available_teeth)
            
            for i, tooth_num in enumerate(teeth_to_show):
                # tooth_num is guaranteed to be in tooth_data
                values = tooth_data[tooth_num]
                
                if isinstance(values, (list, np.ndarray)) and len(values) > 0:
                    if len(values) > 10:
                        try:
                            from scipy.ndimage import gaussian_filter1d
                            values = gaussian_filter1d(values, sigma=2)
                        except ImportError:
                            pass
                    
                    # Use index + 1 as x_center to ensure equal spacing
                    x_center = i + 1
                    
                    # Calculate y_positions based on actual markers if available (PROFILE)
                    if profile_markers and len(profile_markers) >= 4:
                        # markers: da, d1, d2, de
                        da, d1, d2, de = profile_markers
                        # Map data points linearly from da to de
                        y_positions = np.linspace(da, de, len(values))
                    else:
                        # Fallback to default
                        y_positions = np.linspace(0, tooth_width_mm, len(values))
                    
                    x_positions = x_center + (values / 50.0)
                    
                    # 4个标记点 - 基于实际markers计算索引 (PROFILE)
                    n = len(values)
                    idx_start = 0
                    idx_end = n - 1
                    
                    # 计算起评点和终评点的索引
                    if profile_markers and len(profile_markers) >= 4:
                        da, d1, d2, de = profile_markers
                        total_len = abs(de - da)
                        if total_len > 0:
                            dist_to_d1 = abs(d1 - da)
                            dist_to_d2 = abs(d2 - da)
                            idx_eval_start = int(n * (dist_to_d1 / total_len))
                            idx_eval_end = int(n * (dist_to_d2 / total_len))
                            idx_eval_start = max(0, min(idx_eval_start, n - 1))
                            idx_eval_end = max(0, min(idx_eval_end, n - 1))
                        else:
                            idx_eval_start = int(n * 0.15)
                            idx_eval_end = int(n * 0.85)
                    else:
                        idx_eval_start = int(n * 0.15)
                        idx_eval_end = int(n * 0.85)
                    
                    # 绘制曲线 - 修改为红色
                    ax.plot(x_positions, y_positions, 'r-', linewidth=0.8)
                    
                    # 绘制零点垂直线（使用实际的Y轴范围）
                    y_min, y_max = ax.get_ylim() if hasattr(ax, 'get_ylim') else (0, 1)
                    ax.axvline(x=x_center, color='black', linestyle='-', linewidth=0.5, 
                              ymin=0, ymax=1, zorder=3)
                    
                    # 在零点垂直线上标记起评点和终评点（三角形）
                    # 起评点：绿色向下三角
                    ax.plot(x_center, y_positions[idx_eval_start], 'v', 
                           markersize=5, color='green', markerfacecolor='green',
                           markeredgewidth=0, zorder=6)
                    # 终评点：黄色向上三角
                    ax.plot(x_center, y_positions[idx_eval_end], '^', 
                           markersize=5, color='orange', markerfacecolor='orange',
                           markeredgewidth=0, zorder=6)
                    
                    # 在曲线上标记所有4个点（短横线）
                    ax.plot(x_positions[idx_start], y_positions[idx_start], '_', 
                           markersize=6, color='blue', markeredgewidth=1.5, zorder=5)
                    ax.plot(x_positions[idx_eval_start], y_positions[idx_eval_start], '_', 
                           markersize=6, color='green', markeredgewidth=1.5, zorder=5)
                    ax.plot(x_positions[idx_eval_end], y_positions[idx_eval_end], '_', 
                           markersize=6, color='orange', markeredgewidth=1.5, zorder=5)
                    ax.plot(x_positions[idx_end], y_positions[idx_end], '_', 
                           markersize=6, color='blue', markeredgewidth=1.5, zorder=5)
        
        
        # 坐标轴范围 - X轴
        num_teeth = len(teeth_to_show) if teeth_to_show else 6
        if num_teeth > 0:
            ax.set_xlim(0.5, num_teeth + 0.5)
        else:
            ax.set_xlim(0.5, 6.5)
        
        # 已删除紫色参考线和标注
        
        # Y轴刻度设置 - 基于实际markers (PROFILE)
        if profile_markers and len(profile_markers) == 4:
            # markers格式: (da, d1, d2, de)
            y_da, y_d1, y_d2, y_de = profile_markers
            
            # 设置Y轴刻度为这4个标记点，显示所有标识和数值
            ax.set_yticks([y_da, y_d1, y_d2, y_de])
            ax.set_yticklabels([
                f'{y_da:.1f}mm da',   # 起测点
                f'{y_d1:.1f}mm d1',   # 起评点
                f'{y_d2:.1f}mm d2',   # 终评点
                f'{y_de:.1f}mm de'    # 终测点
            ], fontsize=6)
            
            # 设置Y轴的次要刻度，用于显示更密集的水平网格
            y_range = max(y_de, y_da) - min(y_de, y_da)
            if y_range > 0:
                minor_step = y_range / 20  # 在主要标记之间添加约20个次要刻度
                y_minor_ticks = np.arange(min(y_da, y_de), max(y_da, y_de) + minor_step, minor_step)
                ax.set_yticks(y_minor_ticks, minor=True)
        else:
            # 如果没有标记数据，使用默认刻度（Y轴范围可能已在绘制前设置，这里只设置刻度）
            if tooth_width_mm > 0:
                # 只有在Y轴范围还没有设置时才设置
                current_ylim = ax.get_ylim()
                if current_ylim[0] == 0 and current_ylim[1] == 1:
                    ax.set_ylim(0, tooth_width_mm)
                step = max(3, tooth_width_mm / 10)
                ax.set_yticks(np.arange(0, tooth_width_mm + 0.1, step))
                ax.minorticks_on()
            else:
                # 只有在Y轴范围还没有设置时才设置
                current_ylim = ax.get_ylim()
                if current_ylim[0] == 0 and current_ylim[1] == 1:
                    ax.set_ylim(0, 1)
                ax.set_yticks([])
        
        # 绘制垂直分隔线 - 实线黑色，分隔每个齿号
        for i in range(1, num_teeth):
            ax.axvline(x=i + 0.5, color='black', linestyle='-', linewidth=0.8, zorder=2)
        
        # 启用次要刻度（仅用于水平网格）
        ax.minorticks_on()
        
        # 设置水平网格 - 灰色点线
        # 只显示水平网格（axis='y'），垂直网格由上面的axvline提供
        # Major grid: 灰色点线（水平）
        ax.grid(True, which='major', axis='y', linestyle=':', linewidth=1.0, color='gray', alpha=1.0)
        # Minor grid: 灰色点线（水平）
        ax.grid(True, which='minor', axis='y', linestyle=':', linewidth=1.0, color='gray', alpha=1.0)
        
        # 绘制10um比例尺（基于实际的Y轴范围）
        self._draw_scale_box(ax, None)
        
        # 已删除NOK标识
        
        # 添加参数信息（图2样式）
        # 获取Y轴范围用于定位参数信息
        y_min = ax.get_ylim()[0] - 0.3
        
        # A1参数
        ax.text(0.8, y_min, 'A1', fontsize=7, ha='right', va='center', 
               color='black', fontweight='bold', transform=ax.transData)
        ax.text(0.85, y_min, '0.10', fontsize=7, ha='left', va='center', 
               color='black', transform=ax.transData)
        
        # O(1)参数
        ax.text(1.2, y_min, 'O(1)', fontsize=7, ha='right', va='center', 
               color='black', fontweight='bold', transform=ax.transData)
        ax.text(1.25, y_min, '267', fontsize=7, ha='left', va='center', 
               color='black', transform=ax.transData)
        
        # 方向信息
        ax.text(2.0, y_min, 'Direction βw=-0.1° βb=-0.8°', fontsize=7, ha='center', va='center', 
               color='black', fontweight='bold', transform=ax.transData)
        
        ax.tick_params(axis='y', labelsize=7)
    
    def _create_profile_table(self, ax, deviation_results, measurement_data=None, visible_teeth=None):
        """创建Profile数据表格 - 匹配参考图格式"""
        ax.axis('off')
        
        # 获取实际测量的齿号
        left_teeth = []
        right_teeth = []
        
        if deviation_results and 'profile' in deviation_results:
            for key in deviation_results['profile'].keys():
                if key.startswith('L'):
                    tooth_num = int(key[1:])
                    if visible_teeth is None or tooth_num in visible_teeth:
                        if tooth_num not in left_teeth:
                            left_teeth.append(tooth_num)
                elif key.startswith('R'):
                    tooth_num = int(key[1:])
                    if visible_teeth is None or tooth_num in visible_teeth:
                        if tooth_num not in right_teeth:
                            right_teeth.append(tooth_num)
        
        # 排序：左侧降序，右侧升序
        left_teeth.sort(reverse=True)
        right_teeth.sort()
        
        # 如果没有数据，使用默认值
        if not left_teeth:
            left_teeth = [6, 5, 4, 3, 2, 1]
        if not right_teeth:
            right_teeth = [1, 2, 3, 4, 5, 6]
        
        # 获取标准名称
        standard_name = "DIN 3962"  # 默认值
        # 优先从measurement_data.basic_info获取
        if measurement_data and hasattr(measurement_data, 'basic_info'):
            standard_attr = getattr(measurement_data.basic_info, 'tolerance_standard', None)
            if standard_attr:
                standard_name = standard_attr
        # 如果basic_info中没有，尝试从deviation_results的tolerance_settings中获取
        elif deviation_results and 'tolerance_settings' in deviation_results:
            tol_settings = deviation_results.get('tolerance_settings', {})
            if isinstance(tol_settings, dict):
                # 查找第一个包含标准信息的键（Profile相关）
                for key in tol_settings.keys():
                    if 'Profile' in key or 'profile' in key.lower():
                        if '_' in key:
                            # 处理 "ISO 1328 : 1997_Profile" 这种格式
                            parts = key.split('_', 1)
                            if len(parts) > 0:
                                standard_name = parts[0]
                            break
        # 如果deviation_results中有tolerance_standard字段，也尝试获取
        if deviation_results and 'tolerance_standard' in deviation_results:
            standard_name = deviation_results['tolerance_standard']
        
        # 构建表头 - 恢复 "Lim.value Qual." 标签
        left_headers = [str(t) for t in left_teeth]
        right_headers = [str(t) for t in right_teeth]
        headers = ([''] + left_headers + 
                  ['Lim.value Qual.'] + 
                  ['Lim.value Qual.'] + 
                  right_headers)
        
        # 数据行
        # Params: fHam, fHa, fa, ffa, Ca
        params = [
            ('fHam', 'fH_alpha', 'fHa'),
            ('fHa', 'fH_alpha', 'fHa'), 
            ('fa', 'F_alpha', 'Fa'), 
            ('ffa', 'ff_alpha', 'ffa'), 
            ('Ca', 'C_alpha', None)  # Ca doesn't have quality calculation
        ]
        
        rows_data = []
        bold_cells = []
        for param_label, param_key, tol_key in params:
            row = [param_label]
            
            # Helper to get value
            def get_val(side, tooth_idx, key):
                if not deviation_results or 'profile' not in deviation_results:
                    return ''
                res_key = f"{'L' if side == 'left' else 'R'}{tooth_idx}"
                item = deviation_results['profile'].get(res_key, {})
                val = item.get(key, '')
                if isinstance(val, (int, float)):
                    return f"{val:.1f}"
                return ''

            # Left Data (按left_teeth顺序)
            left_values = []
            left_numeric_values = []  # For calculating max
            
            if param_label == 'fHam':
                # Calculate average of fHa
                vals = []
                for t in left_teeth:
                    v = get_val('left', t, 'fH_alpha')
                    if v:
                        try: 
                            vals.append(float(v))
                        except ValueError: 
                            pass
                avg = f"{sum(vals)/len(vals):.1f}" if vals else ""
                v_range = f"V {max(vals) - min(vals):.1f}" if vals else ""
                for i, t in enumerate(left_teeth):
                    if i == 0: 
                        left_values.append(avg)
                        left_numeric_values.append(float(avg) if avg else None)
                    elif i == 1: 
                        left_values.append(v_range)
                        left_numeric_values.append(None)
                    else: 
                        left_values.append("")
                        left_numeric_values.append(None)
            else:
                for t in left_teeth:
                    if param_label == 'Ca':
                        # Calculate Ca
                        val = None
                        if measurement_data and hasattr(measurement_data, 'profile_data'):
                            tooth_data = measurement_data.profile_data.left.get(t)
                            markers = getattr(measurement_data.basic_info, 'profile_markers_left', None)
                            val = self._calculate_crowning(tooth_data, markers)
                        
                        if val is not None:
                            left_values.append(f"{val:.1f}")
                            left_numeric_values.append(val)
                        else:
                            left_values.append('')
                            left_numeric_values.append(None)
                    else:
                        val_str = get_val('left', t, param_key)
                        left_values.append(val_str)
                        num_val = None
                        if val_str:
                            try:
                                num_val = float(val_str)
                            except ValueError:
                                pass
                        left_numeric_values.append(num_val)
            
            # Calculate left side quality info
            left_act_value = ''
            left_quality = ''
            left_lim_qual = ''
            
            # 获取精度等级（默认5级）
            accuracy_grade = 5
            if measurement_data and hasattr(measurement_data, 'basic_info'):
                grade_str = getattr(measurement_data.basic_info, 'accuracy_grade', '5')
                try:
                    accuracy_grade = int(grade_str)
                except:
                    accuracy_grade = 5
            
            # 固定公差查找表（ISO 1328标准）
            profile_tolerance_table = {
                1: (3.0, 4.0, 5.0),   # (fHa, ffa, Fa)
                2: (4.0, 6.0, 7.0),
                3: (5.5, 8.0, 10.0),
                4: (8.0, 12.0, 14.0),
                5: (11.0, 16.0, 20.0),
                6: (16.0, 22.0, 28.0),
                7: (22.0, 32.0, 40.0),
                8: (28.0, 45.0, 56.0),
                9: (40.0, 63.0, 80.0),
                10: (71.0, 110.0, 125.0),
                11: (110.0, 160.0, 200.0),
                12: (180.0, 250.0, 320.0)
            }
            default_fHa, default_ffa, default_Fa = profile_tolerance_table.get(accuracy_grade, profile_tolerance_table[5])
            
            # Get tolerance settings
            deviation_results = deviation_results or {}
            tol_settings = deviation_results.get('tolerance_settings', {})
            profile_tol = tol_settings.get('profile', {})
            
            # 初始化left_lim_qual
            left_lim_qual = ""
            left_tol_val = 0
            left_qual_setting = accuracy_grade
            
            # 如果有tol_key，总是设置一个值（要么从settings，要么用默认值）
            if tol_key:
                # 尝试从tolerance_settings获取公差值
                if profile_tol and tol_key in profile_tol and 'left' in profile_tol[tol_key]:
                    left_tol_val = profile_tol[tol_key]['left'].get('upp', 0)
                    left_qual_setting = profile_tol[tol_key]['left'].get('qual', accuracy_grade)
                
                # 如果没有有效的公差值，使用默认值
                if left_tol_val <= 0:
                    if tol_key == 'fHa':
                        left_tol_val = default_fHa
                    elif tol_key == 'ffa':
                        left_tol_val = default_ffa
                    elif tol_key == 'Fa':
                        left_tol_val = default_Fa
                    left_qual_setting = accuracy_grade
                
                # 格式化显示（确保总是有值）
                if left_tol_val > 0:
                    if param_label in ['fHa', 'fHam']:
                        left_lim_qual = f"±{int(left_tol_val)} {left_qual_setting}"
                    else:
                        left_lim_qual = f"{int(left_tol_val)} {left_qual_setting}"
                    
                    # Calculate max value
                    valid_nums = [v for v in left_numeric_values if v is not None]
                    max_val = 0
                    if valid_nums:
                        max_val = max([abs(v) for v in valid_nums])
                        left_act_value = f"{max_val:.1f}"
                        
                        # Calculate actual quality grade
                        calc_quality = self._calculate_quality_grade(max_val, 'profile', tol_key)
                        if calc_quality:
                            left_quality = str(calc_quality)
                            
                            # Append quality to max value in tooth columns
                            for i, val in enumerate(left_numeric_values):
                                if val is not None and abs(val) == max_val:
                                    left_values[i] = f"{left_values[i]}     {left_quality}"
                    
                    # Check for out of tolerance values (Left)
                    for i, val in enumerate(left_numeric_values):
                        if val is not None and abs(val) > left_tol_val:
                            # row index is len(rows_data) + 1 (header is 0)
                            # col index is 1 + i (0 is param label)
                            bold_cells.append((len(rows_data) + 1, 1 + i))
            
            # Right Data (按right_teeth顺序)
            right_values = []
            right_numeric_values = []
            
            if param_label == 'fHam':
                # Calculate average of fHa
                vals = []
                for t in right_teeth:
                    v = get_val('right', t, 'fH_alpha')
                    if v:
                        try: 
                            vals.append(float(v))
                        except ValueError: 
                            pass
                avg = f"{sum(vals)/len(vals):.1f}" if vals else ""
                v_range = f"V {max(vals) - min(vals):.1f}" if vals else ""
                for i, t in enumerate(right_teeth):
                    if i == 0: 
                        right_values.append(avg)
                        right_numeric_values.append(float(avg) if avg else None)
                    elif i == 1: 
                        right_values.append(v_range)
                        right_numeric_values.append(None)
                    else: 
                        right_values.append("")
                        right_numeric_values.append(None)
            else:
                for t in right_teeth:
                    if param_label == 'Ca':
                        # Calculate Ca
                        val = None
                        if measurement_data and hasattr(measurement_data, 'profile_data'):
                            tooth_data = measurement_data.profile_data.right.get(t)
                            markers = getattr(measurement_data.basic_info, 'profile_markers_right', None)
                            val = self._calculate_crowning(tooth_data, markers)
                        
                        if val is not None:
                            right_values.append(f"{val:.1f}")
                            right_numeric_values.append(val)
                        else:
                            right_values.append('')
                            right_numeric_values.append(None)
                    else:
                        val_str = get_val('right', t, param_key)
                        right_values.append(val_str)
                        num_val = None
                        if val_str:
                            try:
                                num_val = float(val_str)
                            except ValueError:
                                pass
                        right_numeric_values.append(num_val)

            # Calculate right side quality info
            right_act_value = ''
            right_quality = ''
            right_lim_qual = ""
            right_tol_val = 0
            right_qual_setting = accuracy_grade
            
            # 如果有tol_key，总是设置一个值（要么从settings，要么用默认值）
            if tol_key:
                # 尝试从tolerance_settings获取公差值
                if profile_tol and tol_key in profile_tol and 'right' in profile_tol[tol_key]:
                    right_tol_val = profile_tol[tol_key]['right'].get('upp', 0)
                    right_qual_setting = profile_tol[tol_key]['right'].get('qual', accuracy_grade)
                
                # 如果没有有效的公差值，使用默认值
                if right_tol_val <= 0:
                    if tol_key == 'fHa':
                        right_tol_val = default_fHa
                    elif tol_key == 'ffa':
                        right_tol_val = default_ffa
                    elif tol_key == 'Fa':
                        right_tol_val = default_Fa
                    right_qual_setting = accuracy_grade
                
                # 格式化显示（确保总是有值）
                if right_tol_val > 0:
                    if param_label in ['fHa', 'fHam']:
                        right_lim_qual = f"±{int(right_tol_val)} {right_qual_setting}"
                    else:
                        right_lim_qual = f"{int(right_tol_val)} {right_qual_setting}"
                    
                    # Calculate max value
                    valid_nums = [v for v in right_numeric_values if v is not None]
                    max_val = 0
                    if valid_nums:
                        max_val = max([abs(v) for v in valid_nums])
                        right_act_value = f"{max_val:.1f}"
                        
                        # Calculate actual quality grade
                        calc_quality = self._calculate_quality_grade(max_val, 'profile', tol_key)
                        if calc_quality:
                            right_quality = str(calc_quality)
                            
                            # Append quality to max value in tooth columns
                            for i, val in enumerate(right_numeric_values):
                                if val is not None and abs(val) == max_val:
                                    right_values[i] = f"{right_values[i]}     {right_quality}"
                    
                    # Check for out of tolerance values (Right)
                    for i, val in enumerate(right_numeric_values):
                        if val is not None and abs(val) > right_tol_val:
                            # col index: 1 + len(left_teeth) + 1 (left lim) + 1 (tooth) + 1 (right lim) + i
                            bold_cells.append((len(rows_data) + 1, len(left_teeth) + 3 + i))
            
            # Assemble row
            row.extend(left_values)
            row.append(left_lim_qual)
            row.append(right_lim_qual)
            row.extend(right_values)
            
            rows_data.append(row)
            
        # 创建表格
        table_data = [headers] + rows_data
        
        table = ax.table(
            cellText=table_data,
            cellLoc='center',
            bbox=[0, 0, 1, 1],
            edges='closed'
        )
        
        # 设置样式
        table.auto_set_font_size(False)
        table.set_fontsize(6)
        
        # 自动调整列宽，确保内容完整显示
        table.auto_set_column_width(range(len(table_data[0])))
        
        # 设置单元格样式
        num_left_teeth = len(left_teeth)
        num_right_teeth = len(right_teeth)
        
        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor('black')
            cell.set_linewidth(0.5)
            cell.set_height(0.15)
            
            # 表头样式
            if row == 0:
                cell.set_text_props(weight='bold', fontsize=6)
            
            # 参数列
            if col == 0:
                cell.set_text_props(weight='bold')
            
            # Apply bold to out-of-tolerance cells
            if (row, col) in bold_cells:
                cell.set_text_props(weight='bold')


    def _create_lead_section(self, ax_left, ax_right, ax_table, measurement_data, deviation_results, visible_teeth=None):
        """创建Lead图表和表格区域"""
        # 左齿面Lead图表
        self._draw_single_lead_chart(ax_left, 'Left Lead', measurement_data.flank_data.left, measurement_data, deviation_results)
        # 右齿面Lead图表
        self._draw_single_lead_chart(ax_right, 'Right Lead', measurement_data.flank_data.right, measurement_data, deviation_results)
        
        # 创建Lead表格
        self._create_lead_table(ax_table, deviation_results, measurement_data, visible_teeth=visible_teeth)
    
    def _create_lead_table(self, ax, deviation_results, measurement_data=None, visible_teeth=None):
        ax.axis('off')
        
        # 获取实际测量的齿号
        left_teeth = []
        right_teeth = []
        if deviation_results and 'flank' in deviation_results:
            for key in deviation_results['flank'].keys():
                if key.startswith('L'):
                    tooth_num = int(key[1:])
                    if visible_teeth is None or tooth_num in visible_teeth:
                        if tooth_num not in left_teeth:
                            left_teeth.append(tooth_num)
                elif key.startswith('R'):
                    tooth_num = int(key[1:])
                    if visible_teeth is None or tooth_num in visible_teeth:
                        if tooth_num not in right_teeth:
                            right_teeth.append(tooth_num)
        
        # 排序：左侧降序，右侧升序
        left_teeth.sort(reverse=True)
        right_teeth.sort()
        
        # 如果没有数据，使用默认值
        if not left_teeth:
            left_teeth = [6, 5, 4, 3, 2, 1]
        if not right_teeth:
            right_teeth = [1, 2, 3, 4, 5, 6]
        
        # 获取标准名称
        standard_name = "DIN 3962"  # 默认值
        # 优先从measurement_data.basic_info获取
        if measurement_data and hasattr(measurement_data, 'basic_info'):
            standard_attr = getattr(measurement_data.basic_info, 'tolerance_standard', None)
            if standard_attr:
                standard_name = standard_attr
        # 如果basic_info中没有，尝试从deviation_results的tolerance_settings中获取
        elif deviation_results and 'tolerance_settings' in deviation_results:
            tol_settings = deviation_results.get('tolerance_settings', {})
            if isinstance(tol_settings, dict):
                # 查找第一个包含标准信息的键（Lead相关）
                for key in tol_settings.keys():
                    if 'Lead' in key or 'lead' in key.lower() or 'Line of action' in key:
                        if '_' in key:
                            # 处理 "ISO 1328 : 1997_Lead / Line of action" 这种格式
                            parts = key.split('_', 1)
                            if len(parts) > 0:
                                standard_name = parts[0]
                            break
        # 如果deviation_results中有tolerance_standard字段，也尝试获取
        if deviation_results and 'tolerance_standard' in deviation_results:
            standard_name = deviation_results['tolerance_standard']
        
        # 构建表头 - 恢复 "Lim.value Qual." 标签
        left_headers = [str(t) for t in left_teeth]
        right_headers = [str(t) for t in right_teeth]
        headers = ([''] + left_headers + 
                  ['Lim.value Qual.'] + 
                  ['Lim.value Qual.'] + 
                  right_headers)
        
        # 数据行
        # Params: fHbm, fHb, fb, ffb, Cb
        params = [
            ('fHbm', 'fH_beta', 'fHb'), 
            ('fHb', 'fH_beta', 'fHb'), 
            ('fb', 'F_beta', 'Fb'), 
            ('ffb', 'ff_beta', 'ffb'), 
            ('Cb', 'C_beta', None)  # Cb doesn't have quality calculation
        ]
        
        rows_data = []
        bold_cells = []
        for param_label, param_key, tol_key in params:
            row = [param_label]
            
            # Helper to get value
            def get_val(side, tooth_idx, key):
                if not deviation_results or 'flank' not in deviation_results:
                    return ''
                res_key = f"{'L' if side == 'left' else 'R'}{tooth_idx}"
                item = deviation_results['flank'].get(res_key, {})
                val = item.get(key, '')
                if isinstance(val, (int, float)):
                    return f"{val:.1f}"
                return ''

            # Left Data (按left_teeth顺序)
            left_values = []
            left_numeric_values = []  # For calculating max
            
            if param_label == 'fHbm':
                # Calculate average of fHb
                vals = []
                for t in left_teeth:
                    v = get_val('left', t, 'fH_beta')
                    if v:
                        try: 
                            vals.append(float(v))
                        except ValueError: 
                            pass
                avg = f"{sum(vals)/len(vals):.1f}" if vals else ""
                v_range = f"V {max(vals) - min(vals):.1f}" if vals else ""
                for i, t in enumerate(left_teeth):
                    if i == 0: 
                        left_values.append(avg)
                        left_numeric_values.append(float(avg) if avg else None)
                    elif i == 1: 
                        left_values.append(v_range)
                        left_numeric_values.append(None)
                    else: 
                        left_values.append("")
                        left_numeric_values.append(None)
            else:
                for t in left_teeth:
                    if param_label == 'Cb':
                        # Calculate Cb
                        val = None
                        if measurement_data and hasattr(measurement_data, 'flank_data'):
                            tooth_data = measurement_data.flank_data.left.get(t)
                            markers = getattr(measurement_data.basic_info, 'lead_markers_left', None)
                            val = self._calculate_crowning(tooth_data, markers)
                        
                        if val is not None:
                            left_values.append(f"{val:.1f}")
                            left_numeric_values.append(val)
                        else:
                            left_values.append('')
                            left_numeric_values.append(None)
                    else:
                        val_str = get_val('left', t, param_key)
                        left_values.append(val_str)
                        num_val = None
                        if val_str:
                            try:
                                num_val = float(val_str)
                            except ValueError:
                                pass
                        left_numeric_values.append(num_val)
            
            # Calculate left side quality info
            left_act_value = ''
            left_quality = ''
            left_lim_qual = ''
            
            # 获取精度等级（默认5级）
            accuracy_grade = 5
            if measurement_data and hasattr(measurement_data, 'basic_info'):
                grade_str = getattr(measurement_data.basic_info, 'accuracy_grade', '5')
                try:
                    accuracy_grade = int(grade_str)
                except:
                    accuracy_grade = 5
            
            # 固定公差查找表（ISO 1328标准）
            lead_tolerance_table = {
                1: (2.5, 2.0, 3.0),   # (fHb, ffb, Fb)
                2: (3.5, 5.0, 6.0),
                3: (4.5, 7.0, 8.0),
                4: (6.0, 8.0, 10.0),
                5: (8.0, 9.0, 12.0),
                6: (11.0, 12.0, 16.0),
                7: (16.0, 16.0, 22.0),
                8: (22.0, 25.0, 32.0),
                9: (32.0, 40.0, 50.0),
                10: (50.0, 63.0, 80.0),
                11: (80.0, 100.0, 125.0),
                12: (125.0, 160.0, 200.0)
            }
            default_fHb, default_ffb, default_Fb = lead_tolerance_table.get(accuracy_grade, lead_tolerance_table[5])
            
            # Get tolerance settings
            deviation_results = deviation_results or {}
            tol_settings = deviation_results.get('tolerance_settings', {})
            lead_tol = tol_settings.get('lead', {})
            
            # 初始化left_lim_qual
            left_lim_qual = ""
            left_tol_val = 0
            left_qual_setting = accuracy_grade
            
            # 如果有tol_key，总是设置一个值（要么从settings，要么用默认值）
            if tol_key:
                # 尝试从tolerance_settings获取公差值
                if lead_tol and tol_key in lead_tol and 'left' in lead_tol[tol_key]:
                    left_tol_val = lead_tol[tol_key]['left'].get('upp', 0)
                    left_qual_setting = lead_tol[tol_key]['left'].get('qual', accuracy_grade)
                
                # 如果没有有效的公差值，使用默认值
                if left_tol_val <= 0:
                    if tol_key == 'fHb':
                        left_tol_val = default_fHb
                    elif tol_key == 'ffb':
                        left_tol_val = default_ffb
                    elif tol_key == 'Fb':
                        left_tol_val = default_Fb
                    left_qual_setting = accuracy_grade
                
                # 格式化显示（确保总是有值）
                if left_tol_val > 0:
                    if param_label in ['fHb', 'fHbm']:
                        left_lim_qual = f"±{int(left_tol_val)} {left_qual_setting}"
                    else:
                        left_lim_qual = f"{int(left_tol_val)} {left_qual_setting}"
                    
                    # Calculate max value
                    valid_nums = [v for v in left_numeric_values if v is not None]
                    max_val = 0
                    if valid_nums:
                        max_val = max([abs(v) for v in valid_nums])
                        left_act_value = f"{max_val:.1f}"
                        
                        # Calculate actual quality grade
                        calc_quality = self._calculate_quality_grade(max_val, 'lead', tol_key)
                        if calc_quality:
                            left_quality = str(calc_quality)
                            
                            # Append quality to max value in tooth columns
                            for i, val in enumerate(left_numeric_values):
                                if val is not None and abs(val) == max_val:
                                    left_values[i] = f"{left_values[i]}     {left_quality}"
                    
                    # Check for out of tolerance values (Left)
                    for i, val in enumerate(left_numeric_values):
                        if val is not None and abs(val) > left_tol_val:
                            bold_cells.append((len(rows_data) + 1, 1 + i))

            # Right Data (按right_teeth顺序)
            right_values = []
            right_numeric_values = []
            
            if param_label == 'fHbm':
                # Calculate average of fHb
                vals = []
                for t in right_teeth:
                    v = get_val('right', t, 'fH_beta')
                    if v:
                        try: 
                            vals.append(float(v))
                        except ValueError: 
                            pass
                avg = f"{sum(vals)/len(vals):.1f}" if vals else ""
                v_range = f"V {max(vals) - min(vals):.1f}" if vals else ""
                for i, t in enumerate(right_teeth):
                    if i == 0: 
                        right_values.append(avg)
                        right_numeric_values.append(float(avg) if avg else None)
                    elif i == 1: 
                        right_values.append(v_range)
                        right_numeric_values.append(None)
                    else: 
                        right_values.append("")
                        right_numeric_values.append(None)
            else:
                for t in right_teeth:
                    if param_label == 'Cb':
                        # Calculate Cb
                        val = None
                        if measurement_data and hasattr(measurement_data, 'flank_data'):
                            tooth_data = measurement_data.flank_data.right.get(t)
                            markers = getattr(measurement_data.basic_info, 'lead_markers_right', None)
                            val = self._calculate_crowning(tooth_data, markers)
                        
                        if val is not None:
                            right_values.append(f"{val:.1f}")
                            right_numeric_values.append(val)
                        else:
                            right_values.append('')
                            right_numeric_values.append(None)
                    else:
                        val_str = get_val('right', t, param_key)
                        right_values.append(val_str)
                        num_val = None
                        if val_str:
                            try:
                                num_val = float(val_str)
                            except ValueError:
                                pass
                        right_numeric_values.append(num_val)

            # Calculate right side quality info
            right_act_value = ''
            right_quality = ''
            right_lim_qual = ""
            right_tol_val = 0
            right_qual_setting = accuracy_grade
            
            # 如果有tol_key，总是设置一个值（要么从settings，要么用默认值）
            if tol_key:
                # 尝试从tolerance_settings获取公差值
                if lead_tol and tol_key in lead_tol and 'right' in lead_tol[tol_key]:
                    right_tol_val = lead_tol[tol_key]['right'].get('upp', 0)
                    right_qual_setting = lead_tol[tol_key]['right'].get('qual', accuracy_grade)
                
                # 如果没有有效的公差值，使用默认值
                if right_tol_val <= 0:
                    if tol_key == 'fHb':
                        right_tol_val = default_fHb
                    elif tol_key == 'ffb':
                        right_tol_val = default_ffb
                    elif tol_key == 'Fb':
                        right_tol_val = default_Fb
                    right_qual_setting = accuracy_grade
                
                # 格式化显示（确保总是有值）
                if right_tol_val > 0:
                    if param_label in ['fHb', 'fHbm']:
                        right_lim_qual = f"±{int(right_tol_val)} {right_qual_setting}"
                    else:
                        right_lim_qual = f"{int(right_tol_val)} {right_qual_setting}"
                    
                    # Calculate max value
                    valid_nums = [v for v in right_numeric_values if v is not None]
                    max_val = 0
                    if valid_nums:
                        max_val = max([abs(v) for v in valid_nums])
                        right_act_value = f"{max_val:.1f}"
                        
                        # Calculate actual quality grade
                        calc_quality = self._calculate_quality_grade(max_val, 'lead', tol_key)
                        if calc_quality:
                            right_quality = str(calc_quality)
                            
                            # Append quality to max value in tooth columns
                            for i, val in enumerate(right_numeric_values):
                                if val is not None and abs(val) == max_val:
                                    right_values[i] = f"{right_values[i]}     {right_quality}"
                    
                    # Check for out of tolerance values (Right)
                    for i, val in enumerate(right_numeric_values):
                        if val is not None and abs(val) > right_tol_val:
                            bold_cells.append((len(rows_data) + 1, len(left_teeth) + 3 + i))
            
            # Assemble row
            row.extend(left_values)
            row.append(left_lim_qual)
            row.append(right_lim_qual)
            row.extend(right_values)
            
            rows_data.append(row)
            
        # 创建表格
        table_data = [headers] + rows_data
        
        table = ax.table(
            cellText=table_data,
            cellLoc='center',
            bbox=[0, 0, 1, 1],
            edges='closed'
        )
        
        # 设置样式
        table.auto_set_font_size(False)
        table.set_fontsize(6)
        
        # 自动调整列宽，确保内容完整显示
        table.auto_set_column_width(range(len(table_data[0])))
        
        # 设置单元格样式
        num_left_teeth = len(left_teeth)
        num_right_teeth = len(right_teeth)
        
        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor('black')
            cell.set_linewidth(0.5)
            cell.set_height(0.15)
            
            # 表头样式
            if row == 0:
                cell.set_text_props(weight='bold', fontsize=6)
            
            # 参数列
            if col == 0:
                cell.set_text_props(weight='bold')
            
            # Apply bold to out-of-tolerance cells
            if (row, col) in bold_cells:
                cell.set_text_props(weight='bold')
    
    def _draw_single_lead_chart(self, ax, title, tooth_data, measurement_data, deviation_results=None):
        """绘制单个Lead图表 - 每个齿独立X轴"""
        ax.set_facecolor('white')
        for spine in ax.spines.values():
            spine.set_linewidth(1.0)
            spine.set_edgecolor('black')
        
        # 标题放在图表内部顶部
        ax.text(0.5, 0.98, title, transform=ax.transAxes,
               fontsize=9, ha='center', va='top', fontweight='bold')
        
        # 获取标准名称
        standard_name = "DIN 3962"  # 默认值
        if measurement_data and hasattr(measurement_data, 'basic_info'):
            standard_attr = getattr(measurement_data.basic_info, 'tolerance_standard', None)
            if standard_attr:
                standard_name = standard_attr
        elif deviation_results and 'tolerance_standard' in deviation_results:
            standard_name = deviation_results['tolerance_standard']
        elif deviation_results and 'tolerance_settings' in deviation_results:
            tol_settings = deviation_results.get('tolerance_settings', {})
            if isinstance(tol_settings, dict):
                for key in tol_settings.keys():
                    if 'Lead' in key or 'lead' in key.lower() or 'Line of action' in key:
                        if '_' in key:
                            parts = key.split('_', 1)
                            if len(parts) > 0:
                                standard_name = parts[0]
                            break
        
        # 左侧标注信息 - 仅在Left Lead图表上显示，放在图表内部
        if 'Left' in title:
            # 1. 标准信息框 (动态标准名称)
            ax.text(0.02, 0.98, standard_name, transform=ax.transAxes,
                   fontsize=7, ha='left', va='top', 
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black', linewidth=0.8))
            
            # 2. Top标记
            ax.text(0.02, 0.78, 'Top', transform=ax.transAxes,
                   fontsize=6, ha='left', va='center',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.5))
            
            # 3. Bottom标记
            ax.text(0.02, 0.12, 'Bottom', transform=ax.transAxes,
                   fontsize=6, ha='left', va='center',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.5))
        
        # Y轴标签 - 已移除
        # ax.set_ylabel('10\nμm', fontsize=7, rotation=0, ha='right', va='center', labelpad=10)
        # ax.yaxis.set_label_coords(-0.08, 0.5)
        
        # Top/Bottom标注 - 已移除
        # ax.text(-0.12, 0.95, 'Top', transform=ax.transAxes, 
        #        fontsize=7, ha='center', va='top', rotation=90)
        # ax.text(-0.12, 0.05, 'Bottom', transform=ax.transAxes, 
        #        fontsize=7, ha='center', va='bottom', rotation=90)
        
        # Va标注 - 已移除
        # ax.text(-0.08, 0.8, 'Va100025', transform=ax.transAxes,
        #        fontsize=6, ha='center', va='center', rotation=90)
        # ax.text(-0.08, 0.2, 'Vb213', transform=ax.transAxes,
        #        fontsize=6, ha='center', va='center', rotation=90)
        
        tooth_width_mm = 15.0  # Default
        
        # 先获取markers并设置Y轴范围（在绘制曲线之前）
        lead_markers = None
        if hasattr(measurement_data, 'basic_info'):
            info = measurement_data.basic_info
            if getattr(info, 'width', None):
                try:
                    tooth_width_mm = float(info.width)
                except (ValueError, TypeError):
                    pass
            
            # Get lead markers
            if 'Left' in title:
                lead_markers = getattr(info, 'lead_markers_left', None)
            else:
                lead_markers = getattr(info, 'lead_markers_right', None)
            
            # 调试日志
            logger.info(f"Lead chart '{title}': markers = {lead_markers}")
            
            # If width not found, try to infer from markers
            if lead_markers and len(lead_markers) >= 4:
                if tooth_width_mm == 15.0:  # Still default
                    tooth_width_mm = lead_markers[3] # be
        
        # 提前设置Y轴范围（基于markers）
        if lead_markers and len(lead_markers) >= 4:
            y_ba, y_b1, y_b2, y_be = lead_markers
            y_min = min(y_ba, y_be)
            y_max = max(y_ba, y_be)
            y_range = y_max - y_min
            if y_range > 0:
                ax.set_ylim(y_min - y_range * 0.05, y_max + y_range * 0.05)
            else:
                ax.set_ylim(y_min - 0.1, y_max + 0.1)
        
        teeth_to_show = []
        if tooth_data:
            available_teeth = sorted(list(tooth_data.keys()))
            
            # 根据图表标题确定齿数排列顺序
            if 'Left' in title:
                # 左侧：从大到小
                teeth_to_show = sorted(available_teeth, reverse=True)
            else:  # Right
                # 右侧：从小到大
                teeth_to_show = sorted(available_teeth)
            
            for i, tooth_num in enumerate(teeth_to_show):
                # tooth_num is guaranteed to be in tooth_data
                values = tooth_data[tooth_num]
                
                if isinstance(values, (list, np.ndarray)) and len(values) > 0:
                    if len(values) > 10:
                        try:
                            from scipy.ndimage import gaussian_filter1d
                            values = gaussian_filter1d(values, sigma=2)
                        except ImportError:
                            pass
                    
                    # Use index + 1 as x_center to ensure equal spacing
                    x_center = i + 1
                    
                    # Calculate y_positions based on actual markers if available (LEAD)
                    if lead_markers and len(lead_markers) >= 4:
                        # markers: ba, b1, b2, be
                        ba, b1, b2, be = lead_markers
                        # Map data points linearly from ba to be
                        y_positions = np.linspace(ba, be, len(values))
                    else:
                        # Fallback to default
                        y_positions = np.linspace(0, tooth_width_mm, len(values))
                    
                    x_positions = x_center + (values / 50.0)
                    
                    ax.plot(x_positions, y_positions, 'k-', linewidth=0.8)
                    
                    # 4个标记点 - 基于实际markers计算索引 (LEAD)
                    n = len(values)
                    idx_start = 0
                    idx_end = n - 1
                    
                    if lead_markers and len(lead_markers) >= 4:
                        ba, b1, b2, be = lead_markers
                        total_len = abs(be - ba)
                        if total_len > 0:
                            dist_to_b1 = abs(b1 - ba)
                            dist_to_b2 = abs(b2 - ba)
                            idx_eval_start = int(n * (dist_to_b1 / total_len))
                            idx_eval_end = int(n * (dist_to_b2 / total_len))
                            idx_eval_start = max(0, min(idx_eval_start, n - 1))
                            idx_eval_end = max(0, min(idx_eval_end, n - 1))
                        else:
                            idx_eval_start = int(n * 0.15)
                            idx_eval_end = int(n * 0.85)
                    else:
                        idx_eval_start = int(n * 0.15)
                        idx_eval_end = int(n * 0.85)
                    
                    # 绘制零点垂直线
                    ax.axvline(x=x_center, color='black', linestyle='-', linewidth=0.5, 
                              ymin=0, ymax=1, zorder=3)
                    
                    # 在零点垂直线上标记起评点和终评点（三角形）
                    # 起评点：绿色向下三角
                    ax.plot(x_center, y_positions[idx_eval_start], 'v', 
                           markersize=5, color='green', markerfacecolor='green',
                           markeredgewidth=0, zorder=6)
                    # 终评点：黄色向上三角
                    ax.plot(x_center, y_positions[idx_eval_end], '^', 
                           markersize=5, color='orange', markerfacecolor='orange',
                           markeredgewidth=0, zorder=6)
                    
                    # 在曲线上标记所有4个点（短横线）
                    ax.plot(x_positions[idx_start], y_positions[idx_start], '_', 
                           markersize=6, color='blue', markeredgewidth=1.5, zorder=5)
                    ax.plot(x_positions[idx_eval_start], y_positions[idx_eval_start], '_', 
                           markersize=6, color='green', markeredgewidth=1.5, zorder=5)
                    ax.plot(x_positions[idx_eval_end], y_positions[idx_eval_end], '_', 
                           markersize=6, color='orange', markeredgewidth=1.5, zorder=5)
                    ax.plot(x_positions[idx_end], y_positions[idx_end], '_', 
                           markersize=6, color='blue', markeredgewidth=1.5, zorder=5)
        
        
        # 坐标轴范围 - X轴
        num_teeth = len(teeth_to_show) if teeth_to_show else 6
        if num_teeth > 0:
            ax.set_xlim(0.5, num_teeth + 0.5)
        else:
            ax.set_xlim(0.5, 6.5)
        
        # Y轴刻度设置 - 基于实际markers (LEAD)
        if lead_markers and len(lead_markers) == 4:
            # markers格式: (ba, b1, b2, be)
            y_ba, y_b1, y_b2, y_be = lead_markers
            
            # 设置Y轴刻度为这4个标记点，显示所有标识和数值
            ax.set_yticks([y_ba, y_b1, y_b2, y_be])
            ax.set_yticklabels([
                f'{y_ba:.1f}mm ba',   # 起测点
                f'{y_b1:.1f}mm b1',   # 起评点
                f'{y_b2:.1f}mm b2',   # 终评点
                f'{y_be:.1f}mm be'    # 终测点
            ], fontsize=6)
            
            # 设置Y轴的次要刻度，用于显示更密集的水平网格
            y_range = max(y_be, y_ba) - min(y_be, y_ba)
            if y_range > 0:
                minor_step = y_range / 20  # 在主要标记之间添加约20个次要刻度
                y_minor_ticks = np.arange(min(y_ba, y_be), max(y_ba, y_be) + minor_step, minor_step)
                ax.set_yticks(y_minor_ticks, minor=True)
        else:
            # 如果没有标记数据，使用默认刻度（Y轴范围可能已在绘制前设置，这里只设置刻度）
            if tooth_width_mm > 0:
                # 只有在Y轴范围还没有设置时才设置
                current_ylim = ax.get_ylim()
                if current_ylim[0] == 0 and current_ylim[1] == 1:
                    ax.set_ylim(0, tooth_width_mm)
                step = max(3, tooth_width_mm / 10)
                ax.set_yticks(np.arange(0, tooth_width_mm + 0.1, step))
                ax.minorticks_on()
            else:
                # 只有在Y轴范围还没有设置时才设置
                current_ylim = ax.get_ylim()
                if current_ylim[0] == 0 and current_ylim[1] == 1:
                    ax.set_ylim(0, 1)
                ax.set_yticks([])
        
        # 绘制垂直分隔线 - 实线黑色，分隔每个齿号
        for i in range(1, num_teeth):
            ax.axvline(x=i + 0.5, color='black', linestyle='-', linewidth=0.8, zorder=2)
        
        # 启用次要刻度（仅用于水平网格）
        ax.minorticks_on()
        
        # 设置水平网格 - 灰色点线（与Profile一致）
        # 只显示水平网格（axis='y'），垂直网格由上面的axvline提供
        # Major grid: 灰色点线（水平）
        ax.grid(True, which='major', axis='y', linestyle=':', linewidth=1.0, color='gray', alpha=1.0)
        # Minor grid: 灰色点线（水平）
        ax.grid(True, which='minor', axis='y', linestyle=':', linewidth=1.0, color='gray', alpha=1.0)
        
        # 绘制10um比例尺（基于实际的Y轴范围）
        self._draw_scale_box(ax, None)
        
        ax.tick_params(axis='y', labelsize=7)

