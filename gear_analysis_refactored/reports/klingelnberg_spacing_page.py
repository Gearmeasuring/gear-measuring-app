"""
Klingelnberg Spacing Report Generator
Generates the "Gear Spacing" page with fp, Fp, and Fr charts and data table.
"""
import os
import tempfile
from typing import Dict, List, Any, Optional
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import math

from config.logging_config import logger

class KlingelnbergSpacingPageReport:
    """Klingelnberg Spacing Report Page"""
    
    def __init__(self):
        pass
        
    def generate_report(self, measurement_data, output_path: str) -> bool:
        """Generate the spacing report page"""
        try:
            logger.info(f"Generating Klingelnberg Spacing Report: {output_path}")
            
            # Font settings
            plt.rcParams['pdf.fonttype'] = 42
            plt.rcParams['ps.fonttype'] = 42
            plt.rcParams['font.sans-serif'] = ['Arial', 'Microsoft YaHei', 'SimHei', 'DejaVu Sans']
            
            # Create PDF
            with PdfPages(output_path) as pdf:
                self.create_page(pdf, measurement_data)
                
            logger.info(f"Spacing report generated successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to generate spacing report: {e}")
            return False

    def create_page(self, pdf, measurement_data, deviation_results=None):
        """Create a single page in the PDF"""
        # A4 size
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
        
        # Grid Layout
        # Rows: Header, Left Charts (fp, Fp), Right Charts (fp, Fp), Table, Runout Chart, Footer
        # Ratios approx: 0.12, 0.22, 0.22, 0.15, 0.15, 0.04
        gs = gridspec.GridSpec(
            6, 1,
            figure=fig,
            height_ratios=[0.12, 0.22, 0.22, 0.15, 0.20, 0.05],
            hspace=0.4,
            left=0.08, right=0.95, top=0.95, bottom=0.05
        )
        
        # 1. Header
        header_ax = fig.add_subplot(gs[0, 0])
        self._create_header(header_ax, measurement_data)
        
        # 2. Left Flank Charts
        left_gs = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gs[1, 0], hspace=0.1)
        ax_fp_left = fig.add_subplot(left_gs[0, 0])
        ax_Fp_left = fig.add_subplot(left_gs[1, 0])
        self._create_spacing_charts(ax_fp_left, ax_Fp_left, measurement_data, 'left')
        
        # 3. Right Flank Charts
        right_gs = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gs[2, 0], hspace=0.1)
        ax_fp_right = fig.add_subplot(right_gs[0, 0])
        ax_Fp_right = fig.add_subplot(right_gs[1, 0])
        self._create_spacing_charts(ax_fp_right, ax_Fp_right, measurement_data, 'right')
        
        # 4. Data Table
        table_ax = fig.add_subplot(gs[3, 0])
        self._create_data_table(table_ax, measurement_data, deviation_results)
        
        # 5. Runout Chart
        runout_ax = fig.add_subplot(gs[4, 0])
        self._create_runout_chart(runout_ax, measurement_data)
        
        # 6. Footer (包含MdK信息显示)
        footer_ax = fig.add_subplot(gs[5, 0])
        self._create_footer(footer_ax, measurement_data)
        
        pdf.savefig(fig, bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)

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
        """Create header similar to profile report"""
        ax.axis('off')
        
        # Title
        ax.text(0.5, 1.1, 'Gear Spacing', 
                ha='center', va='bottom', fontsize=16, fontweight='bold',
                transform=ax.transAxes)
        
        info = measurement_data.basic_info
        
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

        # Data for header table
        data = [
            ['Prog.No.:', fmt(getattr(info, 'program', '')), 'Operator:', fmt(getattr(info, 'operator', '')), 'Date:', fmt(getattr(info, 'date', ''))],
            ['Type:', fmt(getattr(info, 'type_', 'gear'), default='gear'), 'No. of teeth:', fmt(getattr(info, 'teeth', '')), 'Pressure angle:', fmt(getattr(info, 'pressure_angle', ''), "{:.0f}°")],
            ['Drawing No.:', fmt(getattr(info, 'drawing_no', '')), 'Module m:', fmt(getattr(info, 'module', ''), "{:.2f}mm"), 'Helix angle:', fmt(getattr(info, 'helix_angle', ''), "{:.0f}°")],
            ['Order No.:', self._get_order_no(info), 'Loc. of check:', fmt(getattr(info, 'location', '')), '', ''],
            ['Cust./Mach. No.:', fmt(getattr(info, 'customer', '')), 'Condition:', fmt(getattr(info, 'condition', '')), '', '']
        ]
        
        table = ax.table(cellText=data, loc='center', cellLoc='left', bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        
        cells = table.get_celld()
        for (row, col), cell in cells.items():
            cell.set_edgecolor('black')
            cell.set_linewidth(0.5)
            cell.set_text_props(verticalalignment='center')
            if col in [0, 2, 4]:
                cell.set_text_props(weight='bold')
                
    def _create_spacing_charts(self, ax_fp, ax_Fp, measurement_data, side):
        """Create fp and Fp charts for one side"""
        pitch_data = getattr(measurement_data, 'pitch_data', None)
        if not pitch_data:
            side_data = {}
        else:
            side_data = getattr(pitch_data, side, {})
        
        if not side_data:
            ax_fp.text(0.5, 0.5, 'No Data', ha='center', va='center')
            ax_Fp.text(0.5, 0.5, 'No Data', ha='center', va='center')
            return

        teeth = sorted(side_data.keys())
        fp_values = [side_data[t]['fp'] for t in teeth]
        Fp_values = [side_data[t]['Fp'] for t in teeth]
        
        # 调整Fp值，使其从0开始（减去第一个值以消除初始偏移）
        if Fp_values:
            first_value = Fp_values[0]
            Fp_values = [fp - first_value for fp in Fp_values]
        
        # fp Chart (Bar)
        ax_fp.bar(teeth, fp_values, color='white', edgecolor='black', width=1.0, linewidth=0.5)
        ax_fp.set_title(f'Tooth to tooth spacing fp {"left" if side=="left" else "right"} flank', fontsize=9, fontweight='bold', pad=2)
        ax_fp.grid(True, linestyle=':', alpha=0.5)
        ax_fp.set_xlim(0, len(teeth)+1)
        # Add scale indicator (10um)
        self._draw_scale_indicator(ax_fp, 10, "10µm")
        
        # Fp Chart (Line)
        ax_Fp.plot(teeth, Fp_values, 'k-', linewidth=0.8)
        ax_Fp.set_title(f'Index Fp {"left" if side=="left" else "right"} flank', fontsize=9, fontweight='bold', pad=2)
        ax_Fp.grid(True, linestyle=':', alpha=0.5)
        ax_Fp.set_xlim(0, len(teeth)+1)
        self._draw_scale_indicator(ax_Fp, 10, "10µm")
        
        # Hide x labels for top chart
        ax_fp.set_xticklabels([])
        
    def _draw_scale_indicator(self, ax, value, label):
        """Draw a scale indicator (vertical bar)"""
        # Draw a vertical line or bar on the left
        ylim = ax.get_ylim()
        y_range = ylim[1] - ylim[0]
        if y_range == 0: y_range = 1
        
        # Let's just add text for now
        ax.text(0.02, 0.8, label, transform=ax.transAxes, fontsize=7)
        
    def _create_data_table(self, ax, measurement_data, deviation_results=None):
        """Create the data table"""
        ax.axis('off')
        
        # 获取精度等级（默认5级）
        accuracy_grade = 5
        if measurement_data and hasattr(measurement_data, 'basic_info'):
            grade_str = getattr(measurement_data.basic_info, 'accuracy_grade', '5')
            try:
                accuracy_grade = int(grade_str)
            except:
                accuracy_grade = 5
        
        # 固定公差查找表（ISO 1328标准）- 周节公差 (fp, Fp, Fr)
        spacing_tolerance_table = {
            1: (3.0, 9.0, 7.0),
            2: (4.5, 14.0, 10.0),
            3: (6.0, 18.0, 14.0),
            4: (8.0, 25.0, 20.0),
            5: (12.0, 36.0, 28.0),
            6: (16.0, 45.0, 40.0),
            7: (22.0, 71.0, 56.0),
            8: (32.0, 90.0, 80.0),
            9: (45.0, 125.0, 110.0),
            10: (71.0, 200.0, 160.0),
            11: (110.0, 320.0, 220.0),
            12: (180.0, 560.0, 320.0)
        }
        default_fp, default_Fp, default_Fr = spacing_tolerance_table.get(accuracy_grade, spacing_tolerance_table[5])
        
        # Get tolerance settings
        deviation_results = deviation_results or {}
        tol_settings = deviation_results.get('tolerance_settings', {})
        spacing_tol = tol_settings.get('spacing', {})
        
        # Calculate statistics
        def calc_stats(side):
            pitch_data = getattr(measurement_data, 'pitch_data', None)
            if not pitch_data: return {}
            data = getattr(pitch_data, side, {})
            if not data: return {}
            
            teeth = sorted(data.keys())
            fp_vals = [data[t]['fp'] for t in teeth]
            Fp_vals = [data[t]['Fp'] for t in teeth]
            
            # fp max: Max absolute single pitch deviation
            fp_max = max([abs(x) for x in fp_vals]) if fp_vals else 0
            
            # fu max: Max absolute adjacent pitch difference
            fu_vals = []
            for i in range(len(fp_vals)):
                prev = fp_vals[i-1] # Wrap around? usually yes for gears
                curr = fp_vals[i]
                fu_vals.append(abs(curr - prev))
            fu_max = max(fu_vals) if fu_vals else 0
            
            # Rp: Range of Pitch Error Rp
            Rp = max(fp_vals) - min(fp_vals) if fp_vals else 0
            
            # Fp: Total cum. pitch dev. Fp
            Fp = max(Fp_vals) - min(Fp_vals) if Fp_vals else 0
            
            # Fp10 (or Fpk): Cumulative over k pitches.
            k = 10
            Fpk_max = 0
            if len(Fp_vals) > k:
                extended_fp = fp_vals + fp_vals[:k]
                window_sums = []
                for i in range(len(fp_vals)):
                    window_sum = sum(extended_fp[i:i+k])
                    window_sums.append(window_sum)
                Fpk_max = max([abs(x) for x in window_sums])
            
            return {
                'fp_max': fp_max,
                'fu_max': fu_max,
                'Rp': Rp,
                'Fp': Fp,
                'Fpk': Fpk_max
            }

        left_stats = calc_stats('left')
        right_stats = calc_stats('right')
        
        # Helper function to get tolerance value and quality
        def get_tolerance_value(param_key, side):
            """Get tolerance value and quality grade for a parameter"""
            tol_val = 0
            qual_setting = accuracy_grade
            
            # Try to get from tolerance settings
            if spacing_tol and param_key in spacing_tol:
                side_data = spacing_tol[param_key].get(side, {})
                tol_val = side_data.get('upp', 0)
                qual_setting = side_data.get('qual', accuracy_grade)
            
            # Use default if no valid tolerance value
            if tol_val <= 0:
                if param_key == 'fp':
                    tol_val = default_fp
                elif param_key == 'Fp':
                    tol_val = default_Fp
                elif param_key == 'Fr':
                    tol_val = default_Fr
                qual_setting = accuracy_grade
            
            # Format limit and quality
            if tol_val > 0:
                return f"{int(tol_val)} {qual_setting}"
            return ""
        
        # Table Data
        col_labels = ['', 'Act.value', 'Qual.', 'Lim.value Qual.', 'Act.value', 'Qual.', 'Lim.value Qual.']
        
        # Build rows with tolerance values
        rows = []
        
        # Row 1: fp max
        left_fp_lim = get_tolerance_value('fp', 'left')
        right_fp_lim = get_tolerance_value('fp', 'right')
        rows.append([
            'Worst single pitch deviation fp max',
            left_stats.get('fp_max', ''),
            '',
            left_fp_lim,
            right_stats.get('fp_max', ''),
            '',
            right_fp_lim
        ])
        
        # Row 2: fu max (no standard tolerance, use empty)
        rows.append([
            'Worst spacing deviation fu max',
            left_stats.get('fu_max', ''),
            '',
            '',
            right_stats.get('fu_max', ''),
            '',
            ''
        ])
        
        # Row 3: Rp (no standard tolerance, use empty)
        rows.append([
            'Range of Pitch Error Rp',
            left_stats.get('Rp', ''),
            '',
            '',
            right_stats.get('Rp', ''),
            '',
            ''
        ])
        
        # Row 4: Fp
        left_Fp_lim = get_tolerance_value('Fp', 'left')
        right_Fp_lim = get_tolerance_value('Fp', 'right')
        rows.append([
            'Total cum. pitch dev. Fp',
            left_stats.get('Fp', ''),
            '',
            left_Fp_lim,
            right_stats.get('Fp', ''),
            '',
            right_Fp_lim
        ])
        
        # Row 5: Fp10 (no standard tolerance, use empty)
        rows.append([
            'Cum. pitch deviation Fp10',
            left_stats.get('Fpk', ''),
            '',
            '',
            right_stats.get('Fpk', ''),
            '',
            ''
        ])
        
        # Format numbers
        for row in rows:
            for i in [1, 4]: # Act values
                if isinstance(row[i], (int, float)):
                    row[i] = f"{row[i]:.1f}"
        
        # Create table
        # Add headers manually
        # Main header
        ax.text(0.0, 1.05, f"Pitch measuring circle:{getattr(measurement_data.basic_info, 'pitch_diameter', '')}", fontsize=8)
        ax.text(0.5, 1.05, "left flank", ha='center', fontsize=8, transform=ax.transAxes) # Adjust pos
        ax.text(0.8, 1.05, "right flank", ha='center', fontsize=8, transform=ax.transAxes)
        
        # Set column widths: First column wider for labels
        col_widths = [0.28] + [0.10] * 6
        
        table = ax.table(cellText=rows, colLabels=col_labels, loc='center', bbox=[0, 0, 1, 1], colWidths=col_widths)
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        
        # Align first column to left
        cells = table.get_celld()
        for i in range(len(rows) + 1): # +1 for header
            if (i, 0) in cells:
                cells[(i, 0)].set_text_props(ha='left')
                # Add some padding if possible, or just rely on left alignment
        
    def _create_runout_chart(self, ax, measurement_data):
        """Create Runout Fr chart"""
        pitch_data = getattr(measurement_data, 'pitch_data', None)
        if not pitch_data:
            return
            
        side_data = getattr(pitch_data, 'left', {}) or getattr(pitch_data, 'right', {})
        
        if not side_data:
            return
            
        teeth = sorted(side_data.keys())
        Fr_values = [side_data[t]['Fr'] for t in teeth]
        
        ax.bar(teeth, Fr_values, color='white', edgecolor='black', width=1.0, linewidth=0.5)
        
        # Add sine wave overlay?
        x = np.array(teeth)
        y = np.array(Fr_values)
        if len(x) > 4:
            Z = len(teeth)
            w = 2 * np.pi / Z
            X = np.column_stack([np.sin(w*x), np.cos(w*x), np.ones(len(x))])
            try:
                beta = np.linalg.lstsq(X, y, rcond=None)[0]
                y_fit = X @ beta
                ax.plot(x, y_fit, 'k-', linewidth=1.0)
            except:
                pass
        
        ax.set_title('Runout Fr (Ball-Ø =3mm)', fontsize=9, fontweight='bold', pad=2)
        ax.grid(True, linestyle=':', alpha=0.5)
        ax.set_xlim(0, len(teeth)+1)
        self._draw_scale_indicator(ax, 10, "10µm")

    def _create_footer(self, ax, measurement_data):
        """Create footer - 模仿图2的格式"""
        ax.axis('off')
        
        pitch_data = getattr(measurement_data, 'pitch_data', None)
        side_data = getattr(pitch_data, 'left', {}) if pitch_data else {}
        
        Fr_val = 0
        if side_data:
            Fr_vals = [side_data[t]['Fr'] for t in side_data]
            Fr_val = max(Fr_vals) - min(Fr_vals)
        
        # 从measurement_data中获取MDK数据
        info = measurement_data.basic_info
        mdk_value = getattr(info, 'mdk_value', 0.0)
        mdk_tolerance = getattr(info, 'mdk_tolerance', 0.0)
        ball_diameter = getattr(info, 'ball_diameter', 0.0)
        
        # 调试日志
        logger.info(f"MDK数据提取: mdk_value={mdk_value}, mdk_tolerance={mdk_tolerance}, ball_diameter={ball_diameter}")
        
        # 如果mdk_value为0，尝试从gear_data字典中直接获取
        if mdk_value == 0.0:
            # 尝试从原始数据中获取
            if hasattr(measurement_data, 'file_path') and measurement_data.file_path:
                try:
                    from gear_analysis_refactored.utils.file_parser import parse_mka_file
                    data_dict = parse_mka_file(measurement_data.file_path)
                    gear_data = data_dict.get('gear_data', {})
                    mdk_value = gear_data.get('mdk_value', 0.0)
                    mdk_tolerance = gear_data.get('mdk_tolerance', 0.0)
                    logger.info(f"从文件重新提取MDK: mdk_value={mdk_value}, mdk_tolerance={mdk_tolerance}")
                except Exception as e:
                    logger.warning(f"重新提取MDK数据失败: {e}")
        
        # 根据用户说明：
        # 1. MdK后面的值：用球径4毫米测量跨棒距时的理论距离（名义值）- 这就是mdk_value
        # 2. Lim.value：要求的上下限公差 - 上限和下限
        # 3. Act.后面的三个值：跨棒距平均值、实际测量的最大值、实际测量的最小值
        
        # 计算MDK的上下限值（Lim.value）
        mdk_upper = mdk_value + abs(mdk_tolerance) if mdk_tolerance != 0 else mdk_value
        mdk_lower = mdk_value - abs(mdk_tolerance) if mdk_tolerance != 0 else mdk_value
        
        # 格式化MDK显示值（保留3位小数）
        mdk_display = f"{mdk_value:.3f}" if mdk_value > 0 else ""
        mdk_upper_str = f"{mdk_upper:.3f}" if mdk_upper > 0 else ""
        mdk_lower_str = f"{mdk_lower:.3f}" if mdk_lower > 0 else ""
        
        # 格式化球直径显示（取整数）
        ball_display = f"{int(ball_diameter)}" if ball_diameter > 0 else "4"
        
        # 从周节数据中计算MDK的实际测量值
        # MDK（跨棒距）与周节偏差相关，可以通过累积周节偏差（Fp）来估算实际测量值
        # 跨棒距的实际值 = 理论MDK值 + 周节偏差的影响
        mdk_avg = mdk_value  # 默认使用理论值
        mdk_max = mdk_value  # 默认使用理论值
        mdk_min = mdk_value  # 默认使用理论值
        
        if pitch_data and mdk_value > 0:
            # 收集所有齿的Fp值（累积周节偏差）
            all_Fp_values = []
            
            # 从左侧和右侧收集Fp值
            for side in ['left', 'right']:
                side_data = getattr(pitch_data, side, {})
                if side_data:
                    for tooth_num, tooth_data in side_data.items():
                        if isinstance(tooth_data, dict):
                            Fp_val = tooth_data.get('Fp', 0.0)
                            if Fp_val != 0.0:  # 只收集非零值
                                all_Fp_values.append(Fp_val)
            
            if all_Fp_values:
                # Fp值是微米单位的偏差，需要转换为毫米
                # 跨棒距的实际值 = 理论MDK值 + Fp偏差（转换为毫米）
                # Fp是微米，需要除以1000转换为毫米
                Fp_values_mm = [fp / 1000.0 for fp in all_Fp_values]
                
                # 计算平均值、最大值、最小值
                Fp_avg = sum(Fp_values_mm) / len(Fp_values_mm) if Fp_values_mm else 0.0
                Fp_max = max(Fp_values_mm) if Fp_values_mm else 0.0
                Fp_min = min(Fp_values_mm) if Fp_values_mm else 0.0
                
                # MDK实际测量值 = 理论MDK值 + Fp偏差
                mdk_avg = mdk_value + Fp_avg
                mdk_max = mdk_value + Fp_max
                mdk_min = mdk_value + Fp_min
                
                logger.info(f"从周节数据计算MDK: 理论值={mdk_value:.3f}, Fp_avg={Fp_avg:.3f}, Fp_max={Fp_max:.3f}, Fp_min={Fp_min:.3f}")
                logger.info(f"MDK实际值: 平均值={mdk_avg:.3f}, 最大值={mdk_max:.3f}, 最小值={mdk_min:.3f}")
            else:
                logger.warning("周节数据中没有有效的Fp值，使用理论MDK值")
        
        # 格式化Act.的三个值（平均值、最大值、最小值）
        mdk_avg_str = f"{mdk_avg:.3f}" if mdk_avg > 0 else ""
        mdk_max_str = f"{mdk_max:.3f}" if mdk_max > 0 else ""
        mdk_min_str = f"{mdk_min:.3f}" if mdk_min > 0 else ""
        
        # 根据图1，表格格式应该是：10列（扩展以容纳Act.的3个值）
        # Row 1: Pitch Line Runout | Fr | 值 | (空) | (空) | (空) | Lim.value | 上限 | 下限
        # Row 2: Variation of tooth thickness | Rs | (空) | (空) | (空) | (空) | Act. | 平均值 | 最大值 | 最小值
        
        # 表格结构：10列
        # 列1：参数名
        # 列2：缩写（Fr, Rs）
        # 列3：数值（Fr的值，或为空）
        # 列4-6：空列
        # 列7：Lim.value或Act.标签（作为单元格内容）
        # 列8-10：Lim.value对应上限和下限（2个值），Act.对应平均值、最大值、最小值（3个值）
        
        data = [
            ['Pitch Line Runout', 'Fr', f'{Fr_val:.1f}', '', '', '', 'Lim.value', '', '', ''],
            ['Variation of tooth thickness', 'Rs', '', '', '', '', 'Act.', '', '', '']
        ]
        
        # 如果有MDK数据，添加到表格中
        if mdk_value > 0:
            # 在Pitch Line Runout行的Lim.value列显示MDK的上下限
            data[0][7] = mdk_upper_str  # 上限
            data[0][8] = mdk_lower_str  # 下限
            
            # 在Variation of tooth thickness行的Act.列显示MDK的实际测量值
            data[1][7] = mdk_avg_str  # 平均值
            data[1][8] = mdk_max_str  # 最大值
            data[1][9] = mdk_min_str  # 最小值
        
        # Set column widths: 第一列较宽用于参数名，其他列均匀分布（10列）
        col_widths = [0.20, 0.06, 0.08, 0.08, 0.08, 0.08, 0.12, 0.12, 0.12, 0.12]
        
        # 调整表格位置：居中偏下，留出空间给MdK信息
        table = ax.table(cellText=data, loc='center', bbox=[0, 0.1, 0.95, 0.7], colWidths=col_widths)
        
        # 在表格上方右上角显示MdK信息（模仿图1）
        # 位置与表格右边缘对齐，在表格上方
        if mdk_value > 0:
            mdk_text = f'MdK {mdk_display}[mm]/Ball-Ø {ball_display}'
        else:
            mdk_text = 'MdK [mm]/Ball-Ø 4'
        # 计算表格右上角的位置（表格bbox的右边缘和顶部）
        table_top = 0.1 + 0.7  # bbox的y + height
        ax.text(0.95, table_top + 0.02, mdk_text, transform=ax.transAxes, 
                ha='right', va='bottom', fontsize=9, fontweight='bold')
        
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        
        # 设置单元格样式
        cells = table.get_celld()
        for i in range(len(data)):
            # 第一列和第二列左对齐
            for j in [0, 1]:
                if (i, j) in cells:
                    cells[(i, j)].set_text_props(ha='left')
            # 数值列（列3, 列7, 列8, 列9）右对齐
            for j in [2, 7, 8, 9]:
                if (i, j) in cells:
                    cells[(i, j)].set_text_props(ha='right')
            # 标签列（Lim.value, Act.）左对齐（根据图1）
            if (i, 6) in cells:
                cells[(i, 6)].set_text_props(ha='left')
