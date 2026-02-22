"""
Klingelnberg 风格完整PDF报告生成器
整合齿形、齿向、周节报表
支持多页显示（每页6个齿）
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import io
from datetime import datetime
from types import SimpleNamespace

class KlingelnbergReportGenerator:
    """生成Klingenberg风格的完整PDF报告"""
    
    def __init__(self):
        plt.rcParams['pdf.fonttype'] = 42
        plt.rcParams['ps.fonttype'] = 42
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'SimHei']
    
    def _calculate_profile_deviations(self, values):
        """计算齿形偏差: F_alpha, fH_alpha, ff_alpha"""
        try:
            if values is None or len(values) == 0:
                return 0.0, 0.0, 0.0

            data = np.array(values)
            
            # 使用评价区间 (15% - 85%)
            n = len(data)
            start_idx = int(n * 0.15)
            end_idx = int(n * 0.85)
            eval_data = data[start_idx:end_idx]
            
            if len(eval_data) == 0:
                return 0.0, 0.0, 0.0
            
            # 总偏差 F_alpha（峰峰值）
            F_alpha = np.max(eval_data) - np.min(eval_data)
            
            # 斜率偏差 fH_alpha（最小二乘拟合趋势线的差值）
            x = np.arange(len(eval_data))
            coeffs = np.polyfit(x, eval_data, 1)
            trend_line = coeffs[0] * x + coeffs[1]
            fH_alpha = trend_line[-1] - trend_line[0]
            
            # 形状偏差 ff_alpha（去除趋势后的残余分量峰峰值）
            residuals = eval_data - trend_line
            ff_alpha = np.max(residuals) - np.min(residuals)
            
            return F_alpha, fH_alpha, ff_alpha
            
        except Exception as e:
            print(f"齿形偏差计算错误: {e}")
            return 0.0, 0.0, 0.0
    
    def _calculate_lead_deviations(self, values):
        """计算齿向偏差: F_beta, fH_beta, ff_beta"""
        try:
            if values is None or len(values) == 0:
                return 0.0, 0.0, 0.0

            data = np.array(values)
            
            # 使用评价区间 (15% - 85%)
            n = len(data)
            start_idx = int(n * 0.15)
            end_idx = int(n * 0.85)
            eval_data = data[start_idx:end_idx]
            
            if len(eval_data) == 0:
                return 0.0, 0.0, 0.0
            
            # 总偏差 F_beta（峰峰值）
            F_beta = np.max(eval_data) - np.min(eval_data)
            
            # 斜率偏差 fH_beta（最小二乘拟合趋势线的差值）
            x = np.arange(len(eval_data))
            coeffs = np.polyfit(x, eval_data, 1)
            trend_line = coeffs[0] * x + coeffs[1]
            fH_beta = trend_line[-1] - trend_line[0]
            
            # 形状偏差 ff_beta（去除趋势后的残余分量峰峰值）
            residuals = eval_data - trend_line
            ff_beta = np.max(residuals) - np.min(residuals)
            
            return F_beta, fH_beta, ff_beta
            
        except Exception as e:
            print(f"齿向偏差计算错误: {e}")
            return 0.0, 0.0, 0.0
    
    def _calculate_crowning(self, values):
        """计算鼓形量 C_alpha 或 C_beta"""
        try:
            if values is None or len(values) == 0:
                return 0.0

            data = np.array(values)
            
            # 使用评价区间 (15% - 85%)
            n = len(data)
            start_idx = int(n * 0.15)
            end_idx = int(n * 0.85)
            eval_data = data[start_idx:end_idx]
            
            if len(eval_data) < 3:
                return 0.0
            
            # 拟合抛物线 y = ax^2 + bx + c
            x = np.arange(len(eval_data))
            coeffs = np.polyfit(x, eval_data, 2)
            a = coeffs[0]
            
            # 计算鼓形量: C = -a * L^2 / 4
            L = len(eval_data)
            crowning = -a * (L ** 2) / 4
            
            return crowning
            
        except Exception as e:
            print(f"鼓形量计算错误: {e}")
            return 0.0
    
    def generate_full_report(self, analyzer, output_filename="gear_report.pdf"):
        """生成完整报告"""
        buffer = io.BytesIO()
        
        # 收集所有齿号
        all_teeth = set()
        profile_left = analyzer.reader.profile_data.get('left', {})
        profile_right = analyzer.reader.profile_data.get('right', {})
        helix_left = analyzer.reader.helix_data.get('left', {})
        helix_right = analyzer.reader.helix_data.get('right', {})
        
        all_teeth.update(profile_left.keys())
        all_teeth.update(profile_right.keys())
        all_teeth.update(helix_left.keys())
        all_teeth.update(helix_right.keys())
        
        sorted_teeth = sorted(list(all_teeth))
        if not sorted_teeth:
            sorted_teeth = [1, 2, 3, 4, 5, 6]  # 默认齿号
        
        # 分页：每页6个齿
        chunk_size = 6
        tooth_chunks = [sorted_teeth[i:i + chunk_size] for i in range(0, len(sorted_teeth), chunk_size)]
        
        with PdfPages(buffer) as pdf:
            # 为每6个齿生成一页Profile/Lead报告
            for chunk in tooth_chunks:
                self._create_profile_lead_page(pdf, analyzer, chunk)
            
            # 生成一页Spacing报告（显示所有齿的周节数据）
            self._create_spacing_page(pdf, analyzer)
        
        buffer.seek(0)
        return buffer
    
    def _create_profile_lead_page(self, pdf, analyzer, teeth_chunk):
        """创建齿形/齿向报告页面 - 显示指定齿号的数据"""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
        
        gear_params = analyzer.gear_params
        info = analyzer.reader.info if hasattr(analyzer.reader, 'info') else {}
        
        # 页面标题（显示当前页码范围）
        page_info = f"Teeth {min(teeth_chunk)}-{max(teeth_chunk)}"
        fig.suptitle(f'Gear Profile/Lead - {page_info}', fontsize=14, fontweight='bold', y=0.98)
        
        # 创建网格布局
        gs = gridspec.GridSpec(
            6, 1,
            figure=fig,
            height_ratios=[0.12, 0.28, 0.08, 0.28, 0.08, 0.04],
            hspace=0.15,
            left=0.06, right=0.96, top=0.94, bottom=0.04
        )
        
        # 1. Header区域
        header_ax = fig.add_subplot(gs[0, 0])
        self._create_header(header_ax, analyzer, gear_params, info)
        
        # 2. Profile图表区域（左右齿面）- 只显示当前页的齿
        profile_gs = gridspec.GridSpecFromSubplotSpec(
            1, 2, subplot_spec=gs[1, 0], wspace=0.08
        )
        profile_left_ax = fig.add_subplot(profile_gs[0, 0])
        profile_right_ax = fig.add_subplot(profile_gs[0, 1])
        self._create_profile_charts(profile_left_ax, profile_right_ax, analyzer, teeth_chunk)
        
        # 3. Profile数据表格
        profile_table_ax = fig.add_subplot(gs[2, 0])
        self._create_profile_table(profile_table_ax, analyzer, teeth_chunk)
        
        # 4. Lead图表区域（左右齿面）- 只显示当前页的齿
        lead_gs = gridspec.GridSpecFromSubplotSpec(
            1, 2, subplot_spec=gs[3, 0], wspace=0.08
        )
        lead_left_ax = fig.add_subplot(lead_gs[0, 0])
        lead_right_ax = fig.add_subplot(lead_gs[0, 1])
        self._create_lead_charts(lead_left_ax, lead_right_ax, analyzer, teeth_chunk)
        
        # 5. Lead数据表格
        lead_table_ax = fig.add_subplot(gs[4, 0])
        self._create_lead_table(lead_table_ax, analyzer, teeth_chunk)
        
        # 6. 底部信息
        footer_ax = fig.add_subplot(gs[5, 0])
        footer_ax.axis('off')
        
        pdf.savefig(fig, bbox_inches='tight', pad_inches=0.05)
        plt.close(fig)
    
    def _create_header(self, ax, analyzer, gear_params, info):
        """创建Header表格"""
        ax.axis('off')
        
        def fmt(val, default=""):
            if val is None or val == "":
                return default
            return str(val)
        
        # 计算基圆直径
        db_str = ""
        beta_b_str = ""
        if gear_params:
            try:
                import math
                mn = gear_params.module
                z = gear_params.teeth_count
                alpha_n = math.radians(gear_params.pressure_angle)
                beta = math.radians(gear_params.helix_angle)
                
                alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta))
                d = z * mn / math.cos(beta)
                db = d * math.cos(alpha_t)
                beta_b = math.degrees(math.asin(math.sin(beta) * math.cos(alpha_n)))
                
                db_str = f"{db:.4f}mm"
                beta_b_str = f"{beta_b:.3f}°"
            except:
                pass
        
        # Header表格数据
        data = [
            ['Prog.No.:', fmt(info.get('program', '')), 'Operator:', fmt(info.get('operator', '')), 'Date:', fmt(info.get('date', ''))],
            ['Type:', fmt(info.get('type_', 'gear')), 'No. of teeth:', fmt(gear_params.teeth_count if gear_params else ''), 'Face Width:', fmt(info.get('width', ''), "{:.2f}mm")],
            ['Drawing No.:', fmt(info.get('drawing_no', '')), 'Module m:', fmt(gear_params.module if gear_params else '', "{:.3f}mm"), 'Length Ev. Lα:', ''],
            ['Order No.:', fmt(info.get('order_no', '')), 'Pressure angle:', fmt(gear_params.pressure_angle if gear_params else '', "{:.0f}°"), 'Length Ev. Lβ:', ''],
            ['Cust./Mach. N:', fmt(info.get('customer', '')), 'Helix angle:', fmt(gear_params.helix_angle if gear_params else '', "{:.2f}°"), 'Appr. Length:', ''],
            ['Loc. of check:', fmt(info.get('location', '')), 'Base Cir.-Ø db:', db_str, 'Stylus-Ø:', fmt(info.get('ball_diameter', ''), "{:.3f}mm")],
            ['Condition:', fmt(info.get('condition', '')), 'Base Helix ang:', beta_b_str, 'Add.Mod.Coe:', fmt(info.get('modification_coeff', ''), "{:.3f}")]
        ]
        
        table = ax.table(cellText=data, loc='center', cellLoc='left', bbox=[0.02, 0, 0.98, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(7)
        table.auto_set_column_width(range(len(data[0])))
        
        cells = table.get_celld()
        for (row, col), cell in cells.items():
            cell.set_edgecolor('black')
            cell.set_linewidth(0.5)
            if col in [0, 2, 4]:  # 标签列
                cell.set_text_props(verticalalignment='center', horizontalalignment='left', weight='bold')
            else:
                cell.set_text_props(verticalalignment='center', horizontalalignment='right')
            cell.set_height(1.0/7)
    
    def _create_profile_charts(self, ax_left, ax_right, analyzer, teeth_chunk):
        """创建齿形图表 - 只显示指定齿号"""
        self._draw_single_profile_chart(ax_left, 'Left Flank', analyzer.reader.profile_data.get('left', {}), analyzer, teeth_chunk)
        self._draw_single_profile_chart(ax_right, 'Right Flank', analyzer.reader.profile_data.get('right', {}), analyzer, teeth_chunk)
    
    def _draw_single_profile_chart(self, ax, title, tooth_data, analyzer, teeth_chunk):
        """绘制单个齿形图表 - 只显示指定齿号"""
        ax.set_facecolor('white')
        for spine in ax.spines.values():
            spine.set_linewidth(1.0)
            spine.set_edgecolor('black')
        
        # 标题
        ax.text(0.5, 0.98, title, transform=ax.transAxes,
               fontsize=9, ha='center', va='top', fontweight='bold')
        
        # 标准信息框
        if 'Left' in title:
            ax.text(0.02, 0.98, 'DIN 3962', transform=ax.transAxes,
                   fontsize=7, ha='left', va='top',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black', linewidth=0.8))
            ax.text(0.02, 0.78, 'Tip', transform=ax.transAxes,
                   fontsize=6, ha='left', va='center',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.5))
            ax.text(0.02, 0.12, 'Root', transform=ax.transAxes,
                   fontsize=6, ha='left', va='center',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.5))
        
        if not tooth_data:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            return
        
        # 只显示当前页的齿号
        available_teeth = [t for t in teeth_chunk if t in tooth_data]
        
        # 根据左右齿面确定齿号排列顺序
        if 'Left' in title:
            teeth_to_show = sorted(available_teeth, reverse=True)  # 左侧：从大到小
        else:
            teeth_to_show = sorted(available_teeth)  # 右侧：从小到大
        
        if not teeth_to_show:
            ax.text(0.5, 0.5, 'No Data for this page', ha='center', va='center', transform=ax.transAxes)
            return
        
        for i, tooth_num in enumerate(teeth_to_show):
            x_center = i + 1
            values_dict = tooth_data[tooth_num]
            
            if isinstance(values_dict, dict):
                values = list(values_dict.values())[0] if values_dict else []
            else:
                values = values_dict
            
            if len(values) > 0:
                # Y轴位置（展长）
                y_positions = np.linspace(0, 8, len(values))
                # X轴位置（偏差值，缩放50倍）
                x_positions = x_center + (np.array(values) / 50.0)
                
                # 绘制曲线（红色）
                ax.plot(x_positions, y_positions, 'r-', linewidth=0.8)
                
                # 零点垂直线
                ax.axvline(x=x_center, color='black', linestyle='-', linewidth=0.5, ymin=0, ymax=1, zorder=3)
                
                # 标记起评点和终评点
                n = len(values)
                idx_eval_start = int(n * 0.15)
                idx_eval_end = int(n * 0.85)
                
                ax.plot(x_center, y_positions[idx_eval_start], 'v',
                       markersize=5, color='green', markerfacecolor='green', markeredgewidth=0, zorder=6)
                ax.plot(x_center, y_positions[idx_eval_end], '^',
                       markersize=5, color='orange', markerfacecolor='orange', markeredgewidth=0, zorder=6)
                
                # 在曲线上标记4个点
                ax.plot(x_positions[0], y_positions[0], '_', markersize=6, color='blue', markeredgewidth=1.5, zorder=5)
                ax.plot(x_positions[idx_eval_start], y_positions[idx_eval_start], '_', markersize=6, color='green', markeredgewidth=1.5, zorder=5)
                ax.plot(x_positions[idx_eval_end], y_positions[idx_eval_end], '_', markersize=6, color='orange', markeredgewidth=1.5, zorder=5)
                ax.plot(x_positions[-1], y_positions[-1], '_', markersize=6, color='blue', markeredgewidth=1.5, zorder=5)
        
        # 设置坐标轴
        num_teeth = len(teeth_to_show)
        ax.set_xlim(0.5, num_teeth + 0.5)
        ax.set_ylim(-1, 9)
        
        # Y轴刻度
        ax.set_yticks([0, 2, 4, 6, 8])
        ax.set_yticklabels(['0mm', '2mm', '4mm', '6mm', '8mm'], fontsize=6)
        
        # 垂直分隔线
        for i in range(1, num_teeth):
            ax.axvline(x=i + 0.5, color='black', linestyle='-', linewidth=0.8, zorder=2)
        
        # 网格
        ax.minorticks_on()
        ax.grid(True, which='major', axis='y', linestyle=':', linewidth=1.0, color='gray', alpha=1.0)
        ax.grid(True, which='minor', axis='y', linestyle=':', linewidth=1.0, color='gray', alpha=1.0)
        
        # 10um比例尺
        self._draw_scale_box(ax)
        
        ax.tick_params(axis='y', labelsize=7)
    
    def _draw_scale_box(self, ax):
        """绘制10um比例尺标示框"""
        scale_width = 0.2  # 10um = 10/50 = 0.2
        x_center = 0.8
        y_lim = ax.get_ylim()
        y_center = y_lim[0] + (y_lim[1] - y_lim[0]) * 0.9
        box_height = (y_lim[1] - y_lim[0]) * 0.08
        
        rect = patches.Rectangle(
            (x_center - scale_width/2, y_center - box_height/2),
            scale_width, box_height,
            linewidth=0.8, edgecolor='black', facecolor='white', zorder=20
        )
        ax.add_patch(rect)
        
        ax.text(x_center, y_center, '10\nµm', ha='center', va='center', fontsize=5, zorder=21)
        ax.plot(x_center - scale_width/2 - 0.05, y_center, 'k>', markersize=2, zorder=22, clip_on=False)
        ax.plot(x_center + scale_width/2 + 0.05, y_center, 'k<', markersize=2, zorder=22, clip_on=False)
    
    def _create_profile_table(self, ax, analyzer, teeth_chunk):
        """创建齿形数据表格 - 只显示指定齿号，包含实际计算数据"""
        ax.axis('off')

        # 获取当前页的齿号
        left_all = analyzer.reader.profile_data.get('left', {})
        right_all = analyzer.reader.profile_data.get('right', {})

        # 只使用实际存在的齿号
        left_teeth = [t for t in teeth_chunk if t in left_all]
        right_teeth = [t for t in teeth_chunk if t in right_all]

        # 根据左右齿面确定齿号排列顺序
        left_teeth = sorted(left_teeth, reverse=True)  # 左侧降序
        right_teeth = sorted(right_teeth)  # 右侧升序

        # 如果没有数据，直接返回空表格
        if not left_teeth and not right_teeth:
            ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center', transform=ax.transAxes)
            return
        
        # 表头
        left_headers = [str(t) for t in left_teeth]
        right_headers = [str(t) for t in right_teeth]
        headers = [''] + left_headers + ['Lim.value Qual.', 'Lim.value Qual.'] + right_headers
        
        # 计算每个齿的偏差值
        def get_tooth_values(tooth_data, tooth_num):
            """获取指定齿号的测量值"""
            if tooth_num not in tooth_data:
                return []
            values_dict = tooth_data[tooth_num]
            if isinstance(values_dict, dict):
                return list(values_dict.values())[0] if values_dict else []
            return values_dict
        
        # 为每个齿计算偏差
        left_deviations = {}
        for t in left_teeth:
            values = get_tooth_values(left_all, t)
            if values is not None and len(values) > 0:
                F_alpha, fH_alpha, ff_alpha = self._calculate_profile_deviations(values)
                Ca = self._calculate_crowning(values)
                left_deviations[t] = {
                    'fHa': fH_alpha,
                    'fa': F_alpha,
                    'ffa': ff_alpha,
                    'Ca': Ca
                }

        right_deviations = {}
        for t in right_teeth:
            values = get_tooth_values(right_all, t)
            if values is not None and len(values) > 0:
                F_alpha, fH_alpha, ff_alpha = self._calculate_profile_deviations(values)
                Ca = self._calculate_crowning(values)
                right_deviations[t] = {
                    'fHa': fH_alpha,
                    'fa': F_alpha,
                    'ffa': ff_alpha,
                    'Ca': Ca
                }
        
        # 计算平均值和变异
        def calc_avg_and_var(deviations, key, teeth):
            vals = [deviations[t][key] for t in teeth if t in deviations]
            if vals:
                avg = sum(vals) / len(vals)
                var = max(vals) - min(vals)
                return avg, var
            return 0, 0
        
        # 数据行
        rows_data = []
        
        # fHam - fHa的平均值和变异
        left_fHa_avg, left_fHa_var = calc_avg_and_var(left_deviations, 'fHa', left_teeth)
        right_fHa_avg, right_fHa_var = calc_avg_and_var(right_deviations, 'fHa', right_teeth)
        
        row = ['fHam']
        for i, t in enumerate(left_teeth):
            if i == 0:
                row.append(f"{left_fHa_avg:.1f}" if left_fHa_avg != 0 else "")
            elif i == 1:
                row.append(f"V {left_fHa_var:.1f}" if left_fHa_var != 0 else "")
            else:
                row.append("")
        row.append('±11 5')
        row.append('±11 5')
        for i, t in enumerate(right_teeth):
            if i == 0:
                row.append(f"{right_fHa_avg:.1f}" if right_fHa_avg != 0 else "")
            elif i == 1:
                row.append(f"V {right_fHa_var:.1f}" if right_fHa_var != 0 else "")
            else:
                row.append("")
        rows_data.append(row)
        
        # fHa - 每个齿的斜率偏差
        row = ['fHa']
        for t in left_teeth:
            val = left_deviations.get(t, {}).get('fHa', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        row.append('±11 5')
        row.append('±11 5')
        for t in right_teeth:
            val = right_deviations.get(t, {}).get('fHa', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        rows_data.append(row)
        
        # fa - 每个齿的总偏差
        row = ['fa']
        for t in left_teeth:
            val = left_deviations.get(t, {}).get('fa', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        row.append('11 5')
        row.append('11 5')
        for t in right_teeth:
            val = right_deviations.get(t, {}).get('fa', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        rows_data.append(row)
        
        # ffa - 每个齿的形状偏差
        row = ['ffa']
        for t in left_teeth:
            val = left_deviations.get(t, {}).get('ffa', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        row.append('5 5')
        row.append('5 5')
        for t in right_teeth:
            val = right_deviations.get(t, {}).get('ffa', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        rows_data.append(row)
        
        # Ca - 每个齿的鼓形量
        row = ['Ca']
        for t in left_teeth:
            val = left_deviations.get(t, {}).get('Ca', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        row.append('')
        row.append('')
        for t in right_teeth:
            val = right_deviations.get(t, {}).get('Ca', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        rows_data.append(row)
        
        # 创建表格
        table_data = [headers] + rows_data
        table = ax.table(cellText=table_data, cellLoc='center', bbox=[0, 0, 1, 1], edges='closed')
        table.auto_set_font_size(False)
        table.set_fontsize(6)
        table.auto_set_column_width(range(len(table_data[0])))
        
        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor('black')
            cell.set_linewidth(0.5)
            cell.set_height(0.15)
            if row == 0:
                cell.set_text_props(weight='bold', fontsize=6)
            if col == 0:
                cell.set_text_props(weight='bold')
    
    def _create_lead_charts(self, ax_left, ax_right, analyzer, teeth_chunk):
        """创建齿向图表 - 只显示指定齿号"""
        self._draw_single_lead_chart(ax_left, 'Left Lead', analyzer.reader.helix_data.get('left', {}), analyzer, teeth_chunk)
        self._draw_single_lead_chart(ax_right, 'Right Lead', analyzer.reader.helix_data.get('right', {}), analyzer, teeth_chunk)
    
    def _draw_single_lead_chart(self, ax, title, tooth_data, analyzer, teeth_chunk):
        """绘制单个齿向图表 - 只显示指定齿号"""
        ax.set_facecolor('white')
        for spine in ax.spines.values():
            spine.set_linewidth(1.0)
            spine.set_edgecolor('black')
        
        ax.text(0.5, 0.98, title, transform=ax.transAxes,
               fontsize=9, ha='center', va='top', fontweight='bold')
        
        if 'Left' in title:
            ax.text(0.02, 0.98, 'DIN 3962', transform=ax.transAxes,
                   fontsize=7, ha='left', va='top',
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='black', linewidth=0.8))
            ax.text(0.02, 0.78, 'Top', transform=ax.transAxes,
                   fontsize=6, ha='left', va='center',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.5))
            ax.text(0.02, 0.12, 'Bottom', transform=ax.transAxes,
                   fontsize=6, ha='left', va='center',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='black', linewidth=0.5))
        
        if not tooth_data:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            return
        
        # 只显示当前页的齿号
        available_teeth = [t for t in teeth_chunk if t in tooth_data]
        
        # 根据左右齿面确定齿号排列顺序
        if 'Left' in title:
            teeth_to_show = sorted(available_teeth, reverse=True)  # 左侧：从大到小
        else:
            teeth_to_show = sorted(available_teeth)  # 右侧：从小到大
        
        if not teeth_to_show:
            ax.text(0.5, 0.5, 'No Data for this page', ha='center', va='center', transform=ax.transAxes)
            return
        
        for i, tooth_num in enumerate(teeth_to_show):
            x_center = i + 1
            values_dict = tooth_data[tooth_num]
            
            if isinstance(values_dict, dict):
                values = list(values_dict.values())[0] if values_dict else []
            else:
                values = values_dict
            
            if len(values) > 0:
                y_positions = np.linspace(0, 40, len(values))
                x_positions = x_center + (np.array(values) / 50.0)
                
                ax.plot(x_positions, y_positions, 'k-', linewidth=0.8)
                ax.axvline(x=x_center, color='black', linestyle='-', linewidth=0.5, ymin=0, ymax=1, zorder=3)
                
                n = len(values)
                idx_eval_start = int(n * 0.15)
                idx_eval_end = int(n * 0.85)
                
                ax.plot(x_center, y_positions[idx_eval_start], 'v',
                       markersize=5, color='green', markerfacecolor='green', markeredgewidth=0, zorder=6)
                ax.plot(x_center, y_positions[idx_eval_end], '^',
                       markersize=5, color='orange', markerfacecolor='orange', markeredgewidth=0, zorder=6)
                
                ax.plot(x_positions[0], y_positions[0], '_', markersize=6, color='blue', markeredgewidth=1.5, zorder=5)
                ax.plot(x_positions[idx_eval_start], y_positions[idx_eval_start], '_', markersize=6, color='green', markeredgewidth=1.5, zorder=5)
                ax.plot(x_positions[idx_eval_end], y_positions[idx_eval_end], '_', markersize=6, color='orange', markeredgewidth=1.5, zorder=5)
                ax.plot(x_positions[-1], y_positions[-1], '_', markersize=6, color='blue', markeredgewidth=1.5, zorder=5)
        
        num_teeth = len(teeth_to_show)
        ax.set_xlim(0.5, num_teeth + 0.5)
        ax.set_ylim(-5, 45)
        ax.set_yticks([0, 10, 20, 30, 40])
        ax.set_yticklabels(['0mm', '10mm', '20mm', '30mm', '40mm'], fontsize=6)
        
        for i in range(1, num_teeth):
            ax.axvline(x=i + 0.5, color='black', linestyle='-', linewidth=0.8, zorder=2)
        
        ax.minorticks_on()
        ax.grid(True, which='major', axis='y', linestyle=':', linewidth=1.0, color='gray', alpha=1.0)
        ax.grid(True, which='minor', axis='y', linestyle=':', linewidth=1.0, color='gray', alpha=1.0)
        
        self._draw_scale_box(ax)
        ax.tick_params(axis='y', labelsize=7)
    
    def _create_lead_table(self, ax, analyzer, teeth_chunk):
        """创建齿向数据表格 - 只显示指定齿号，包含实际计算数据"""
        ax.axis('off')

        left_all = analyzer.reader.helix_data.get('left', {})
        right_all = analyzer.reader.helix_data.get('right', {})

        # 只使用实际存在的齿号
        left_teeth = [t for t in teeth_chunk if t in left_all]
        right_teeth = [t for t in teeth_chunk if t in right_all]

        # 根据左右齿面确定齿号排列顺序
        left_teeth = sorted(left_teeth, reverse=True)  # 左侧降序
        right_teeth = sorted(right_teeth)  # 右侧升序

        # 如果没有数据，直接返回空表格
        if not left_teeth and not right_teeth:
            ax.text(0.5, 0.5, 'No Data Available', ha='center', va='center', transform=ax.transAxes)
            return

        left_headers = [str(t) for t in left_teeth]
        right_headers = [str(t) for t in right_teeth]
        headers = [''] + left_headers + ['Lim.value Qual.', 'Lim.value Qual.'] + right_headers

        # 计算每个齿的偏差值
        def get_tooth_values(tooth_data, tooth_num):
            """获取指定齿号的测量值"""
            if tooth_num not in tooth_data:
                return []
            values_dict = tooth_data[tooth_num]
            if isinstance(values_dict, dict):
                return list(values_dict.values())[0] if values_dict else []
            return values_dict

        # 为每个齿计算偏差
        left_deviations = {}
        for t in left_teeth:
            values = get_tooth_values(left_all, t)
            if values is not None and len(values) > 0:
                F_beta, fH_beta, ff_beta = self._calculate_lead_deviations(values)
                Cb = self._calculate_crowning(values)
                left_deviations[t] = {
                    'fHb': fH_beta,
                    'fb': F_beta,
                    'ffb': ff_beta,
                    'Cb': Cb
                }

        right_deviations = {}
        for t in right_teeth:
            values = get_tooth_values(right_all, t)
            if values is not None and len(values) > 0:
                F_beta, fH_beta, ff_beta = self._calculate_lead_deviations(values)
                Cb = self._calculate_crowning(values)
                right_deviations[t] = {
                    'fHb': fH_beta,
                    'fb': F_beta,
                    'ffb': ff_beta,
                    'Cb': Cb
                }

        # 计算平均值和变异
        def calc_avg_and_var(deviations, key, teeth):
            vals = [deviations[t][key] for t in teeth if t in deviations]
            if vals:
                avg = sum(vals) / len(vals)
                var = max(vals) - min(vals)
                return avg, var
            return 0, 0

        # 数据行
        rows_data = []

        # fHbm - fHb的平均值和变异
        left_fHb_avg, left_fHb_var = calc_avg_and_var(left_deviations, 'fHb', left_teeth)
        right_fHb_avg, right_fHb_var = calc_avg_and_var(right_deviations, 'fHb', right_teeth)

        row = ['fHbm']
        for i, t in enumerate(left_teeth):
            if i == 0:
                row.append(f"{left_fHb_avg:.1f}" if left_fHb_avg != 0 else "")
            elif i == 1:
                row.append(f"V {left_fHb_var:.1f}" if left_fHb_var != 0 else "")
            else:
                row.append("")
        row.append('±8 5')
        row.append('±8 5')
        for i, t in enumerate(right_teeth):
            if i == 0:
                row.append(f"{right_fHb_avg:.1f}" if right_fHb_avg != 0 else "")
            elif i == 1:
                row.append(f"V {right_fHb_var:.1f}" if right_fHb_var != 0 else "")
            else:
                row.append("")
        rows_data.append(row)

        # fHb - 每个齿的斜率偏差
        row = ['fHb']
        for t in left_teeth:
            val = left_deviations.get(t, {}).get('fHb', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        row.append('±8 5')
        row.append('±8 5')
        for t in right_teeth:
            val = right_deviations.get(t, {}).get('fHb', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        rows_data.append(row)

        # fb - 每个齿的总偏差
        row = ['fb']
        for t in left_teeth:
            val = left_deviations.get(t, {}).get('fb', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        row.append('8 5')
        row.append('8 5')
        for t in right_teeth:
            val = right_deviations.get(t, {}).get('fb', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        rows_data.append(row)

        # ffb - 每个齿的形状偏差
        row = ['ffb']
        for t in left_teeth:
            val = left_deviations.get(t, {}).get('ffb', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        row.append('4 5')
        row.append('4 5')
        for t in right_teeth:
            val = right_deviations.get(t, {}).get('ffb', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        rows_data.append(row)

        # Cb - 每个齿的鼓形量
        row = ['Cb']
        for t in left_teeth:
            val = left_deviations.get(t, {}).get('Cb', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        row.append('')
        row.append('')
        for t in right_teeth:
            val = right_deviations.get(t, {}).get('Cb', 0)
            row.append(f"{val:.1f}" if val != 0 else "")
        rows_data.append(row)

        table_data = [headers] + rows_data
        table = ax.table(cellText=table_data, cellLoc='center', bbox=[0, 0, 1, 1], edges='closed')
        table.auto_set_font_size(False)
        table.set_fontsize(6)
        table.auto_set_column_width(range(len(table_data[0])))
        
        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor('black')
            cell.set_linewidth(0.5)
            cell.set_height(0.15)
            if row == 0:
                cell.set_text_props(weight='bold', fontsize=6)
            if col == 0:
                cell.set_text_props(weight='bold')
    
    def _create_spacing_page(self, pdf, analyzer):
        """创建周节报告页面（显示所有齿的数据）"""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
        fig.suptitle('Gear Spacing', fontsize=16, fontweight='bold', y=0.98)
        
        gs = gridspec.GridSpec(
            6, 1,
            figure=fig,
            height_ratios=[0.12, 0.22, 0.22, 0.15, 0.20, 0.05],
            hspace=0.4,
            left=0.08, right=0.95, top=0.95, bottom=0.05
        )
        
        # Header
        header_ax = fig.add_subplot(gs[0, 0])
        self._create_spacing_header(header_ax, analyzer)
        
        # 左齿面图表
        left_gs = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gs[1, 0], hspace=0.1)
        ax_fp_left = fig.add_subplot(left_gs[0, 0])
        ax_Fp_left = fig.add_subplot(left_gs[1, 0])
        self._create_spacing_charts(ax_fp_left, ax_Fp_left, analyzer, 'left')
        
        # 右齿面图表
        right_gs = gridspec.GridSpecFromSubplotSpec(2, 1, subplot_spec=gs[2, 0], hspace=0.1)
        ax_fp_right = fig.add_subplot(right_gs[0, 0])
        ax_Fp_right = fig.add_subplot(right_gs[1, 0])
        self._create_spacing_charts(ax_fp_right, ax_Fp_right, analyzer, 'right')
        
        # 数据表格
        table_ax = fig.add_subplot(gs[3, 0])
        self._create_spacing_table(table_ax, analyzer)
        
        # Runout图表
        runout_ax = fig.add_subplot(gs[4, 0])
        self._create_runout_chart(runout_ax, analyzer)
        
        # Footer
        footer_ax = fig.add_subplot(gs[5, 0])
        footer_ax.axis('off')
        
        pdf.savefig(fig, bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)
    
    def _create_spacing_header(self, ax, analyzer):
        """创建周节Header"""
        ax.axis('off')
        
        gear_params = analyzer.gear_params
        info = analyzer.reader.info if hasattr(analyzer.reader, 'info') else {}
        
        def fmt(val, default=""):
            if val is None or val == "":
                return default
            return str(val)
        
        data = [
            ['Prog.No.:', fmt(info.get('program', '')), 'Operator:', fmt(info.get('operator', '')), 'Date:', fmt(info.get('date', ''))],
            ['Type:', fmt(info.get('type_', 'gear')), 'No. of teeth:', fmt(gear_params.teeth_count if gear_params else ''), 'Pressure angle:', fmt(gear_params.pressure_angle if gear_params else '', "{:.0f}°")],
            ['Drawing No.:', fmt(info.get('drawing_no', '')), 'Module m:', fmt(gear_params.module if gear_params else '', "{:.2f}mm"), 'Helix angle:', fmt(gear_params.helix_angle if gear_params else '', "{:.0f}°")],
            ['Order No.:', fmt(info.get('order_no', '')), 'Loc. of check:', fmt(info.get('location', '')), '', ''],
            ['Cust./Mach. No.:', fmt(info.get('customer', '')), 'Condition:', fmt(info.get('condition', '')), '', '']
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
    
    def _create_spacing_charts(self, ax_fp, ax_Fp, analyzer, side):
        """创建周节图表"""
        pitch_data = analyzer.reader.pitch_data.get(side, {})
        
        if not pitch_data or 'teeth' not in pitch_data:
            ax_fp.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax_fp.transAxes)
            ax_Fp.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax_Fp.transAxes)
            return
        
        teeth = pitch_data['teeth']
        fp_values = pitch_data['fp_values']
        Fp_values = pitch_data['Fp_values']
        
        if not teeth or not fp_values:
            ax_fp.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax_fp.transAxes)
            ax_Fp.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax_Fp.transAxes)
            return
        
        # 调整Fp值（从0开始）
        if Fp_values:
            first_value = Fp_values[0]
            Fp_values_adjusted = [fp - first_value for fp in Fp_values]
        else:
            Fp_values_adjusted = []
        
        # fp柱状图
        ax_fp.bar(teeth, fp_values, color='white', edgecolor='black', width=1.0, linewidth=0.5)
        ax_fp.set_title(f'Tooth to tooth spacing fp {side} flank', fontsize=9, fontweight='bold', pad=2)
        ax_fp.grid(True, linestyle=':', alpha=0.5)
        ax_fp.set_xlim(0, len(teeth)+1)
        ax_fp.text(0.02, 0.8, '10µm', transform=ax_fp.transAxes, fontsize=7)
        
        # Fp曲线图
        ax_Fp.plot(teeth, Fp_values_adjusted, 'k-', linewidth=0.8)
        ax_Fp.set_title(f'Index Fp {side} flank', fontsize=9, fontweight='bold', pad=2)
        ax_Fp.grid(True, linestyle=':', alpha=0.5)
        ax_Fp.set_xlim(0, len(teeth)+1)
        ax_Fp.text(0.02, 0.8, '10µm', transform=ax_Fp.transAxes, fontsize=7)
        
        ax_fp.set_xticklabels([])
    
    def _create_spacing_table(self, ax, analyzer):
        """创建周节数据表格"""
        ax.axis('off')
        
        col_labels = ['', 'Act.value', 'Qual.', 'Lim.value Qual.', 'Act.value', 'Qual.', 'Lim.value Qual.']
        
        pitch_left = analyzer.reader.pitch_data.get('left', {})
        pitch_right = analyzer.reader.pitch_data.get('right', {})
        
        # 计算统计数据
        def calc_stats(data):
            if not data or 'teeth' not in data:
                return {}
            teeth = data['teeth']
            fp_vals = data['fp_values']
            Fp_vals = data['Fp_values']
            
            if not fp_vals or not Fp_vals:
                return {}
            
            fp_max = max([abs(x) for x in fp_vals]) if fp_vals else 0
            fu_max = max([abs(fp_vals[i] - fp_vals[i-1]) for i in range(1, len(fp_vals))]) if len(fp_vals) > 1 else 0
            Rp = max(fp_vals) - min(fp_vals) if fp_vals else 0
            Fp = max(Fp_vals) - min(Fp_vals) if Fp_vals else 0
            
            return {'fp_max': fp_max, 'fu_max': fu_max, 'Rp': Rp, 'Fp': Fp}
        
        left_stats = calc_stats(pitch_left)
        right_stats = calc_stats(pitch_right)
        
        rows = [
            ['Worst single pitch deviation fp max', left_stats.get('fp_max', ''), '', '12 5', right_stats.get('fp_max', ''), '', '12 5'],
            ['Worst spacing deviation fu max', left_stats.get('fu_max', ''), '', '', right_stats.get('fu_max', ''), '', ''],
            ['Range of Pitch Error Rp', left_stats.get('Rp', ''), '', '', right_stats.get('Rp', ''), '', ''],
            ['Total cum. pitch dev. Fp', left_stats.get('Fp', ''), '', '36 5', right_stats.get('Fp', ''), '', '36 5'],
            ['Cum. pitch deviation Fp10', '', '', '', '', '', '']
        ]
        
        for row in rows:
            for i in [1, 4]:
                if isinstance(row[i], (int, float)):
                    row[i] = f"{row[i]:.1f}"
        
        table_data = [col_labels] + rows
        table = ax.table(cellText=table_data, cellLoc='center', bbox=[0, 0, 1, 1], edges='closed')
        table.auto_set_font_size(False)
        table.set_fontsize(7)
        
        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor('black')
            cell.set_linewidth(0.5)
            if row == 0:
                cell.set_text_props(weight='bold')
    
    def _create_runout_chart(self, ax, analyzer):
        """创建Runout图表"""
        pitch_data = analyzer.reader.pitch_data.get('left', {})
        
        if not pitch_data or 'teeth' not in pitch_data:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            return
        
        teeth = pitch_data['teeth']
        # 使用Fp值作为Runout数据
        runout_values = pitch_data['Fp_values']
        
        if not teeth or not runout_values:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            return
        
        # 绘制柱状图
        ax.bar(teeth, runout_values, color='white', edgecolor='black', width=1.0, linewidth=0.5)
        
        # 绘制正弦拟合曲线
        if len(teeth) > 2:
            x_smooth = np.linspace(min(teeth), max(teeth), 200)
            # 简单的正弦拟合
            amplitude = (max(runout_values) - min(runout_values)) / 2
            mid = (max(runout_values) + min(runout_values)) / 2
            period = len(teeth)
            y_smooth = mid + amplitude * np.sin(2 * np.pi * (x_smooth - min(teeth)) / period)
            ax.plot(x_smooth, y_smooth, 'k-', linewidth=1.0)
        
        ax.set_title('Runout Fr (Ball-Ø =3mm)', fontsize=10, fontweight='bold')
        ax.grid(True, linestyle=':', alpha=0.5)
        ax.set_xlim(0, len(teeth)+1)
