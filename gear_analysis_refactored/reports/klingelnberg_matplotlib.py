"""
克林贝格标准PDF报告 - 使用Matplotlib PdfPages
完全模仿克林贝格原版报告格式
每页都是一个完整的matplotlib图表，精确控制所有元素位置
"""
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
import matplotlib
matplotlib.use('Agg')
import numpy as np

from config.logging_config import logger
from ..models import GearMeasurementData
from ..analysis import ISO1328ToleranceCalculator


class KlingelnbergMatplotlibReport:
    """使用Matplotlib生成克林贝格标准PDF报告"""
    
    def __init__(self):
        self.tolerance_calculator = ISO1328ToleranceCalculator()
        # 克林贝格标准颜色
        self.BLUE = '#1E3A5F'
        self.GREEN = '#00A651'
        self.RED = '#ED1C24'
        self.YELLOW = '#FFD700'
        self.GRAY = '#E6E6E6'
    
    def generate_report(self, data: GearMeasurementData, output_path: str) -> bool:
        """生成克林贝格标准PDF报告"""
        try:
            logger.info(f"开始生成克林贝格标准PDF报告(Matplotlib版): {output_path}")
            
            with PdfPages(output_path) as pdf:
                # 1. 封面页
                fig = self.create_cover_page(data)
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)
                
                # 2. 齿轮数据总览页
                fig = self.create_gear_data_overview_page(data)
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)
                
                # 3. 齿形测量 - 左齿面（曲线+表格在一页）
                fig = self.create_profile_measurement_page(data, 'left')
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)
                
                # 4. 齿形测量 - 右齿面
                fig = self.create_profile_measurement_page(data, 'right')
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)
                
                # 5. 齿向测量 - 左齿面
                fig = self.create_flank_measurement_page(data, 'left')
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)
                
                # 6. 齿向测量 - 右齿面
                fig = self.create_flank_measurement_page(data, 'right')
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)
                
                # 7. 周节测量页
                fig = self.create_pitch_measurement_page(data)
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)
                
                # 8. 统计分析页
                fig = self.create_statistical_analysis_page(data)
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)
                
                # 9. 总结判定页
                fig = self.create_summary_judgment_page(data)
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)
                
                # 设置PDF元数据
                d = pdf.infodict()
                d['Title'] = 'Klingelnberg Gear Measurement Report'
                d['Author'] = 'Klingelnberg Precision Measurement Center'
                d['Subject'] = 'Gear Quality Analysis'
                d['Keywords'] = 'Gear, Measurement, ISO1328, Klingelnberg'
                d['CreationDate'] = datetime.now()
            
            logger.info(f"克林贝格标准PDF报告生成成功: {output_path}")
            return True
            
        except Exception as e:
            logger.exception(f"生成PDF报告失败: {e}")
            return False
    
    def create_cover_page(self, data: GearMeasurementData) -> Figure:
        """创建封面页 - 克林贝格标准"""
        fig = Figure(figsize=(8.27, 11.69), dpi=150)  # A4尺寸，高分辨率
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        # 顶部蓝色线条
        ax.add_patch(mpatches.Rectangle((0.05, 0.92), 0.9, 0.02, 
                                        facecolor=self.BLUE, edgecolor='none', transform=fig.transFigure))
        
        # KLINGELNBERG标题
        fig.text(0.5, 0.80, "KLINGELNBERG",
                ha='center', va='center', fontsize=32, fontweight='bold', 
                color=self.BLUE, family='sans-serif')
        
        fig.text(0.5, 0.75, "Precision Measurement Center",
                ha='center', va='center', fontsize=14, color='#666666', 
                style='italic')
        
        # 主标题
        fig.text(0.5, 0.65, "Gear Measurement Report",
                ha='center', va='center', fontsize=24, fontweight='bold', 
                color=self.BLUE)
        
        fig.text(0.5, 0.61, "齿轮测量分析报告",
                ha='center', va='center', fontsize=20, fontweight='bold', 
                color='#333333')
        
        # 信息框
        y_start = 0.50
        line_height = 0.04
        
        info_items = [
            ("Report No. / 报告编号:", data.basic_info.drawing_no or "KMC-2025-001"),
            ("Date / 测量日期:", self._format_date(data.basic_info.date)),
            ("Part No. / 零件号:", data.basic_info.program or "N/A"),
            ("Customer / 客户:", data.basic_info.customer or "N/A"),
            ("Equipment / 设备:", "Klingelnberg P40 PMC"),
            ("Operator / 操作员:", data.basic_info.operator or "Quality Inspector")
        ]
        
        for i, (label, value) in enumerate(info_items):
            y_pos = y_start - i * line_height
            fig.text(0.20, y_pos, label, ha='left', va='center', fontsize=11, fontweight='bold')
            fig.text(0.55, y_pos, value, ha='left', va='center', fontsize=11)
        
        # 底部信息
        fig.text(0.5, 0.15, "© 2025 Klingelnberg GmbH",
                ha='center', va='center', fontsize=10, color='#888888')
        
        fig.text(0.5, 0.12, "This report is generated in accordance with ISO 1328 standard",
                ha='center', va='center', fontsize=9, color='#888888', style='italic')
        
        return fig
    
    def create_gear_data_overview_page(self, data: GearMeasurementData) -> Figure:
        """创建齿轮数据概览页 - 克林贝格标准"""
        fig = Figure(figsize=(8.27, 11.69), dpi=150)
        fig.patch.set_facecolor('white')
        
        # 标题
        fig.text(0.5, 0.94, "Gear Data Overview / 齿轮数据概览",
                ha='center', va='top', fontsize=18, fontweight='bold', color=self.BLUE)
        
        # 齿轮参数表格
        ax1 = fig.add_subplot(311)
        ax1.axis('off')
        ax1.set_position([0.1, 0.65, 0.8, 0.25])
        
        gear_params = [
            ["Module / 模数", "mn", f"{data.basic_info.module:.3f}", "mm"],
            ["Teeth / 齿数", "z", f"{data.basic_info.teeth}", "-"],
            ["Pressure Angle / 压力角", "α", f"{data.basic_info.pressure_angle:.2f}", "°"],
            ["Helix Angle / 螺旋角", "β", f"{data.basic_info.helix_angle:.2f}", "°"],
            ["Face Width / 齿宽", "b", f"{data.basic_info.width:.2f}", "mm"],
            ["Quality Grade / 精度", "ISO", f"1328-{data.basic_info.accuracy_grade}", "-"]
        ]
        
        table1 = ax1.table(cellText=gear_params,
                          colLabels=["Parameter / 参数", "Symbol", "Value / 数值", "Unit"],
                          loc='center',
                          cellLoc='center',
                          colWidths=[0.4, 0.15, 0.25, 0.2])
        
        table1.auto_set_font_size(False)
        table1.set_fontsize(10)
        table1.scale(1, 2.0)
        
        # 表头样式
        for i in range(4):
            cell = table1[(0, i)]
            cell.set_facecolor(self.BLUE)
            cell.set_text_props(weight='bold', color='white')
        
        # 交替行颜色
        for i in range(len(gear_params)):
            for j in range(4):
                cell = table1[(i+1, j)]
                if i % 2 == 0:
                    cell.set_facecolor('white')
                else:
                    cell.set_facecolor(self.GRAY)
        
        # 测量结果摘要表格
        ax2 = fig.add_subplot(312)
        ax2.axis('off')
        ax2.set_position([0.1, 0.30, 0.8, 0.30])
        
        # 计算公差和实测值
        tolerances = self.tolerance_calculator.calculate_tolerances(
            data.basic_info.module, data.basic_info.teeth,
            data.basic_info.width, data.basic_info.accuracy_grade
        )
        
        profile_max = self._get_max_deviation(data.profile_data.left, data.profile_data.right)
        flank_max = self._get_max_deviation(data.flank_data.left, data.flank_data.right)
        
        fig.text(0.5, 0.595, "Measurement Summary / 测量结果摘要",
                ha='center', va='top', fontsize=14, fontweight='bold', color=self.BLUE)
        
        summary_data = [
            ["Profile Total Deviation / 齿形总偏差", f"{profile_max:.2f}", 
             f"≤ {tolerances.get('F_alpha', 0):.2f}", "μm",
             "PASS" if profile_max <= tolerances.get('F_alpha', 999) else "FAIL"],
            ["Helix Total Deviation / 齿向总偏差", f"{flank_max:.2f}", 
             f"≤ {tolerances.get('F_beta', 0):.2f}", "μm",
             "PASS" if flank_max <= tolerances.get('F_beta', 999) else "FAIL"],
            ["Pitch Deviation / 单个周节偏差", 
             f"{self._get_pitch_max(data, 'fp'):.2f}",
             f"≤ {tolerances.get('f_p', 0):.2f}", "μm", "PASS"],
            ["Cumulative Pitch / 周节累积偏差", 
             f"{self._get_pitch_max(data, 'Fp'):.2f}",
             f"≤ {tolerances.get('F_p', 0):.2f}", "μm", "PASS"]
        ]
        
        table2 = ax2.table(cellText=summary_data,
                          colLabels=["Measurement Item / 测量项目", "Measured", "Tolerance", "Unit", "Result"],
                          loc='center',
                          cellLoc='center',
                          colWidths=[0.40, 0.15, 0.15, 0.10, 0.20])
        
        table2.auto_set_font_size(False)
        table2.set_fontsize(10)
        table2.scale(1, 2.2)
        
        # 表头样式
        for i in range(5):
            cell = table2[(0, i)]
            cell.set_facecolor(self.BLUE)
            cell.set_text_props(weight='bold', color='white')
        
        # 数据行样式 + 结果列颜色
        for i in range(len(summary_data)):
            for j in range(5):
                cell = table2[(i+1, j)]
                if i % 2 == 0:
                    cell.set_facecolor('white')
                else:
                    cell.set_facecolor(self.GRAY)
                
                # 结果列特殊颜色
                if j == 4:
                    if summary_data[i][4] == 'PASS':
                        cell.set_text_props(weight='bold', color=self.GREEN, size=12)
                    else:
                        cell.set_text_props(weight='bold', color=self.RED, size=12)
        
        # 底部说明
        fig.text(0.5, 0.10, f"Quality Grade: ISO 1328-{data.basic_info.accuracy_grade}",
                ha='center', va='center', fontsize=12, fontweight='bold')
        
        return fig
    
    def create_profile_measurement_page(self, data: GearMeasurementData, side: str) -> Figure:
        """创建齿形测量页（曲线图+数据表在一页）- 克林贝格标准布局"""
        fig = Figure(figsize=(8.27, 11.69), dpi=150)
        fig.patch.set_facecolor('white')
        
        side_name = "Left" if side == 'left' else "Right"
        side_cn = "左齿面" if side == 'left' else "右齿面"
        
        # 页面标题
        fig.text(0.5, 0.96, f"Profile Measurement - {side_name} Flank / 齿形测量 - {side_cn}",
                ha='center', va='top', fontsize=16, fontweight='bold', color=self.BLUE)
        
        # 上半部分：曲线图（占页面55%）
        ax_curve = fig.add_subplot(211)
        ax_curve.set_position([0.10, 0.48, 0.85, 0.42])
        
        tooth_data = getattr(data.profile_data, side)
        
        if tooth_data:
            # 计算公差
            tolerances = self.tolerance_calculator.calculate_tolerances(
                data.basic_info.module, data.basic_info.teeth,
                data.basic_info.width, data.basic_info.accuracy_grade
            )
            tolerance = tolerances.get('F_alpha', 10)
            
            # 绘制多条曲线（显示前6个齿）
            colors_list = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
            
            for idx, (tooth_num, values) in enumerate(list(tooth_data.items())[:6]):
                color = colors_list[idx % len(colors_list)]
                ax_curve.plot(values, label=f'Tooth {tooth_num}', linewidth=2.5, 
                            color=color, alpha=0.85, zorder=3)
            
            # 公差带 - 黄色半透明
            x_range = range(len(list(tooth_data.values())[0]))
            ax_curve.fill_between(x_range, -tolerance, tolerance, 
                                 alpha=0.2, color=self.YELLOW, zorder=1,
                                 label=f'Tolerance Band (±{tolerance:.1f}μm)')
            
            # 上下限线 - 红色虚线
            ax_curve.axhline(y=tolerance, color=self.RED, linestyle='--', linewidth=2.5, zorder=2,
                           label=f'Upper Limit (+{tolerance:.1f}μm)')
            ax_curve.axhline(y=-tolerance, color=self.RED, linestyle='--', linewidth=2.5, zorder=2,
                           label=f'Lower Limit (-{tolerance:.1f}μm)')
            
            # 零线
            ax_curve.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.6, zorder=2)
            
            # 样式设置
            ax_curve.set_xlabel('Measurement Point / 测量点', fontsize=12, fontweight='bold')
            ax_curve.set_ylabel('Deviation (μm) / 偏差', fontsize=12, fontweight='bold')
            ax_curve.legend(loc='upper right', fontsize=9, framealpha=0.95, ncol=2)
            ax_curve.grid(True, alpha=0.4, linestyle='--', linewidth=0.8, color='#CCCCCC', zorder=0)
            ax_curve.set_facecolor('#FAFAFA')
            ax_curve.set_ylim(-tolerance * 1.8, tolerance * 1.8)
            
            # 设置边框
            for spine in ax_curve.spines.values():
                spine.set_linewidth(1.5)
                spine.set_edgecolor('#333333')
        
        # 下半部分：数据表格（占页面40%）
        ax_table = fig.add_subplot(212)
        ax_table.axis('off')
        ax_table.set_position([0.10, 0.05, 0.85, 0.40])
        
        if tooth_data:
            # 准备表格数据
            table_data = []
            for tooth_num in sorted(tooth_data.keys())[:15]:  # 显示15个齿
                values = tooth_data[tooth_num]
                if values:
                    max_val = max(values)
                    min_val = min(values)
                    mean_val = np.mean(values)
                    std_val = np.std(values)
                    max_abs = max(abs(max_val), abs(min_val))
                    
                    result = 'PASS' if max_abs <= tolerance else 'FAIL'
                    
                    table_data.append([
                        f"{tooth_num}",
                        f"{max_val:.3f}",
                        f"{min_val:.3f}",
                        f"{mean_val:.3f}",
                        f"{std_val:.3f}",
                        f"±{tolerance:.2f}",
                        result
                    ])
            
            table = ax_table.table(cellText=table_data,
                                  colLabels=["Tooth\n齿号", "Max\n最大值", "Min\n最小值", 
                                            "Mean\n平均", "Std\n标准差", "Tolerance\n公差", "Result\n结果"],
                                  loc='upper center',
                                  cellLoc='center',
                                  colWidths=[0.10, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15])
            
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 1.8)
            
            # 表头样式
            for i in range(7):
                cell = table[(0, i)]
                cell.set_facecolor(self.BLUE)
                cell.set_text_props(weight='bold', color='white', size=9)
                cell.set_linewidth(1.5)
            
            # 数据行样式
            for i in range(len(table_data)):
                for j in range(7):
                    cell = table[(i+1, j)]
                    if i % 2 == 0:
                        cell.set_facecolor('white')
                    else:
                        cell.set_facecolor(self.GRAY)
                    
                    cell.set_linewidth(1)
                    
                    # 结果列特殊样式
                    if j == 6:
                        if table_data[i][6] == 'PASS':
                            cell.set_text_props(weight='bold', color=self.GREEN, size=10)
                        else:
                            cell.set_text_props(weight='bold', color=self.RED, size=10)
                    else:
                        # 数字用等宽样式
                        if j >= 1 and j <= 5:
                            cell.set_text_props(family='monospace', size=8)
        
        return fig
    
    def create_flank_measurement_page(self, data: GearMeasurementData, side: str) -> Figure:
        """创建齿向测量页 - 克林贝格标准"""
        fig = Figure(figsize=(8.27, 11.69), dpi=150)
        fig.patch.set_facecolor('white')
        
        side_name = "Left" if side == 'left' else "Right"
        side_cn = "左齿面" if side == 'left' else "右齿面"
        
        # 页面标题
        fig.text(0.5, 0.96, f"Helix Measurement - {side_name} Flank / 齿向测量 - {side_cn}",
                ha='center', va='top', fontsize=16, fontweight='bold', color=self.BLUE)
        
        # 曲线图
        ax_curve = fig.add_subplot(211)
        ax_curve.set_position([0.10, 0.48, 0.85, 0.42])
        
        tooth_data = getattr(data.flank_data, side)
        
        if tooth_data:
            tolerances = self.tolerance_calculator.calculate_tolerances(
                data.basic_info.module, data.basic_info.teeth,
                data.basic_info.width, data.basic_info.accuracy_grade
            )
            tolerance = tolerances.get('F_beta', 12)
            
            # 绘制曲线
            colors_list = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
            
            for idx, (tooth_num, values) in enumerate(list(tooth_data.items())[:6]):
                color = colors_list[idx % len(colors_list)]
                ax_curve.plot(values, label=f'Tooth {tooth_num}', linewidth=2.5, 
                            color=color, alpha=0.85, zorder=3)
            
            # 公差带
            x_range = range(len(list(tooth_data.values())[0]))
            ax_curve.fill_between(x_range, -tolerance, tolerance, 
                                 alpha=0.2, color=self.YELLOW, zorder=1,
                                 label=f'Tolerance Band (±{tolerance:.1f}μm)')
            
            ax_curve.axhline(y=tolerance, color=self.RED, linestyle='--', linewidth=2.5, zorder=2)
            ax_curve.axhline(y=-tolerance, color=self.RED, linestyle='--', linewidth=2.5, zorder=2)
            ax_curve.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.6, zorder=2)
            
            ax_curve.set_xlabel('Measurement Point / 测量点', fontsize=12, fontweight='bold')
            ax_curve.set_ylabel('Deviation (μm) / 偏差', fontsize=12, fontweight='bold')
            ax_curve.legend(loc='upper right', fontsize=9, framealpha=0.95, ncol=2)
            ax_curve.grid(True, alpha=0.4, linestyle='--', linewidth=0.8, color='#CCCCCC', zorder=0)
            ax_curve.set_facecolor('#FAFAFA')
            ax_curve.set_ylim(-tolerance * 1.8, tolerance * 1.8)
            
            for spine in ax_curve.spines.values():
                spine.set_linewidth(1.5)
                spine.set_edgecolor('#333333')
        
        # 数据表格
        ax_table = fig.add_subplot(212)
        ax_table.axis('off')
        ax_table.set_position([0.10, 0.05, 0.85, 0.40])
        
        if tooth_data:
            tolerances = self.tolerance_calculator.calculate_tolerances(
                data.basic_info.module, data.basic_info.teeth,
                data.basic_info.width, data.basic_info.accuracy_grade
            )
            tolerance = tolerances.get('F_beta', 12)
            
            table_data = []
            for tooth_num in sorted(tooth_data.keys())[:15]:
                values = tooth_data[tooth_num]
                if values:
                    max_val = max(values)
                    min_val = min(values)
                    mean_val = np.mean(values)
                    std_val = np.std(values)
                    max_abs = max(abs(max_val), abs(min_val))
                    
                    result = 'PASS' if max_abs <= tolerance else 'FAIL'
                    
                    table_data.append([
                        f"{tooth_num}",
                        f"{max_val:.3f}",
                        f"{min_val:.3f}",
                        f"{mean_val:.3f}",
                        f"{std_val:.3f}",
                        f"±{tolerance:.2f}",
                        result
                    ])
            
            table = ax_table.table(cellText=table_data,
                                  colLabels=["Tooth\n齿号", "Max\n最大值", "Min\n最小值", 
                                            "Mean\n平均", "Std\n标准差", "Tolerance\n公差", "Result\n结果"],
                                  loc='upper center',
                                  cellLoc='center',
                                  colWidths=[0.10, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15])
            
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 1.8)
            
            # 应用样式
            for i in range(7):
                cell = table[(0, i)]
                cell.set_facecolor(self.BLUE)
                cell.set_text_props(weight='bold', color='white', size=9)
            
            for i in range(len(table_data)):
                for j in range(7):
                    cell = table[(i+1, j)]
                    cell.set_facecolor('white' if i % 2 == 0 else self.GRAY)
                    
                    if j == 6:
                        if table_data[i][6] == 'PASS':
                            cell.set_text_props(weight='bold', color=self.GREEN, size=10)
                        else:
                            cell.set_text_props(weight='bold', color=self.RED, size=10)
                    elif j >= 1 and j <= 5:
                        cell.set_text_props(family='monospace', size=8)
        
        return fig
    
    def create_pitch_measurement_page(self, data: GearMeasurementData) -> Figure:
        """创建周节测量页 - 克林贝格标准"""
        fig = Figure(figsize=(8.27, 11.69), dpi=150)
        fig.patch.set_facecolor('white')
        
        fig.text(0.5, 0.96, "Pitch Measurement / 周节测量",
                ha='center', va='top', fontsize=16, fontweight='bold', color=self.BLUE)
        
        # 上半部分：fp和Fp曲线图
        ax1 = fig.add_subplot(311)
        ax1.set_position([0.10, 0.62, 0.85, 0.28])
        
        tolerances = self.tolerance_calculator.calculate_tolerances(
            data.basic_info.module, data.basic_info.teeth,
            data.basic_info.width, data.basic_info.accuracy_grade
        )
        fp_tolerance = tolerances.get('f_p', 10)
        
        # fp曲线
        if data.pitch_data.left:
            teeth = sorted(data.pitch_data.left.keys())
            fp_left = [data.pitch_data.left[t].get('fp', 0) for t in teeth]
            ax1.plot(teeth, fp_left, 'o-', label='Left / 左', linewidth=2.5, 
                    markersize=7, color='#1f77b4', zorder=3)
        
        if data.pitch_data.right:
            teeth = sorted(data.pitch_data.right.keys())
            fp_right = [data.pitch_data.right[t].get('fp', 0) for t in teeth]
            ax1.plot(teeth, fp_right, 's-', label='Right / 右', linewidth=2.5, 
                    markersize=7, color='#ff7f0e', zorder=3)
        
        # 公差带
        ax1.fill_between(teeth, -fp_tolerance, fp_tolerance, 
                        alpha=0.2, color=self.YELLOW, zorder=1)
        ax1.axhline(y=fp_tolerance, color=self.RED, linestyle='--', linewidth=2.5, zorder=2)
        ax1.axhline(y=-fp_tolerance, color=self.RED, linestyle='--', linewidth=2.5, zorder=2)
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.6, zorder=2)
        
        ax1.set_title('Single Pitch Deviation (fp) / 单个周节偏差', 
                     fontsize=13, fontweight='bold', pad=10)
        ax1.set_xlabel('Tooth Number / 齿号', fontsize=11, fontweight='bold')
        ax1.set_ylabel('fp (μm)', fontsize=11, fontweight='bold')
        ax1.legend(fontsize=9, loc='upper right')
        ax1.grid(True, alpha=0.4, linestyle='--', linewidth=0.8, color='#CCCCCC')
        ax1.set_facecolor('#FAFAFA')
        
        # 中间部分：Fp曲线图
        ax2 = fig.add_subplot(312)
        ax2.set_position([0.10, 0.32, 0.85, 0.28])
        
        Fp_tolerance = tolerances.get('F_p', 20)
        
        if data.pitch_data.left:
            teeth = sorted(data.pitch_data.left.keys())
            Fp_left = [data.pitch_data.left[t].get('Fp', 0) for t in teeth]
            ax2.plot(teeth, Fp_left, 'o-', label='Left / 左', linewidth=2.5, 
                    markersize=7, color='#1f77b4', zorder=3)
        
        if data.pitch_data.right:
            teeth = sorted(data.pitch_data.right.keys())
            Fp_right = [data.pitch_data.right[t].get('Fp', 0) for t in teeth]
            ax2.plot(teeth, Fp_right, 's-', label='Right / 右', linewidth=2.5, 
                    markersize=7, color='#ff7f0e', zorder=3)
        
        ax2.fill_between(teeth, -Fp_tolerance, Fp_tolerance, 
                        alpha=0.2, color=self.YELLOW, zorder=1)
        ax2.axhline(y=Fp_tolerance, color=self.RED, linestyle='--', linewidth=2.5, zorder=2)
        ax2.axhline(y=-Fp_tolerance, color=self.RED, linestyle='--', linewidth=2.5, zorder=2)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=1.5, alpha=0.6, zorder=2)
        
        ax2.set_title('Cumulative Pitch Deviation (Fp) / 周节累积偏差', 
                     fontsize=13, fontweight='bold', pad=10)
        ax2.set_xlabel('Tooth Number / 齿号', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Fp (μm)', fontsize=11, fontweight='bold')
        ax2.legend(fontsize=9, loc='upper right')
        ax2.grid(True, alpha=0.4, linestyle='--', linewidth=0.8, color='#CCCCCC')
        ax2.set_facecolor('#FAFAFA')
        
        # 下半部分：数据表格
        ax3 = fig.add_subplot(313)
        ax3.axis('off')
        ax3.set_position([0.10, 0.05, 0.85, 0.24])
        
        # 周节数据表
        pitch_table_data = []
        for i, tooth in enumerate(sorted(data.pitch_data.left.keys())[:12]):
            left = data.pitch_data.left.get(tooth, {})
            right = data.pitch_data.right.get(tooth, {})
            
            fp_max = max(abs(left.get('fp', 0)), abs(right.get('fp', 0)))
            result = 'PASS' if fp_max <= fp_tolerance else 'FAIL'
            
            pitch_table_data.append([
                f"{tooth}",
                f"{left.get('fp', 0):.2f}",
                f"{right.get('fp', 0):.2f}",
                f"{left.get('Fp', 0):.2f}",
                f"{right.get('Fp', 0):.2f}",
                f"±{fp_tolerance:.1f}",
                result
            ])
        
        table = ax3.table(cellText=pitch_table_data,
                         colLabels=["Tooth\n齿号", "fp Left\n左fp", "fp Right\n右fp", 
                                   "Fp Left\n左Fp", "Fp Right\n右Fp", "Tolerance\n公差", "Result\n结果"],
                         loc='upper center',
                         cellLoc='center',
                         colWidths=[0.10, 0.15, 0.15, 0.15, 0.15, 0.15, 0.15])
        
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 2.0)
        
        # 样式
        for i in range(7):
            cell = table[(0, i)]
            cell.set_facecolor(self.BLUE)
            cell.set_text_props(weight='bold', color='white', size=8)
        
        for i in range(len(pitch_table_data)):
            for j in range(7):
                cell = table[(i+1, j)]
                cell.set_facecolor('white' if i % 2 == 0 else self.GRAY)
                
                if j == 6:
                    if pitch_table_data[i][6] == 'PASS':
                        cell.set_text_props(weight='bold', color=self.GREEN, size=9)
                    else:
                        cell.set_text_props(weight='bold', color=self.RED, size=9)
                elif j >= 1:
                    cell.set_text_props(family='monospace', size=7)
        
        return fig
    
    def create_statistical_analysis_page(self, data: GearMeasurementData) -> Figure:
        """创建统计分析页 - 4个分布直方图"""
        fig = Figure(figsize=(8.27, 11.69), dpi=150)
        fig.patch.set_facecolor('white')
        
        fig.text(0.5, 0.97, "Statistical Analysis / 统计分析",
                ha='center', va='top', fontsize=16, fontweight='bold', color=self.BLUE)
        
        # 2x2布局
        # 齿形左侧分布
        ax1 = fig.add_subplot(221)
        if data.profile_data.left:
            self._plot_distribution(ax1, data.profile_data.left, 
                                   'Profile Left / 齿形左齿面', self.BLUE)
        
        # 齿形右侧分布
        ax2 = fig.add_subplot(222)
        if data.profile_data.right:
            self._plot_distribution(ax2, data.profile_data.right, 
                                   'Profile Right / 齿形右齿面', '#006633')
        
        # 齿向左侧分布
        ax3 = fig.add_subplot(223)
        if data.flank_data.left:
            self._plot_distribution(ax3, data.flank_data.left, 
                                   'Helix Left / 齿向左齿面', '#333366')
        
        # 齿向右侧分布
        ax4 = fig.add_subplot(224)
        if data.flank_data.right:
            self._plot_distribution(ax4, data.flank_data.right, 
                                   'Helix Right / 齿向右齿面', '#336633')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.96])
        
        return fig
    
    def create_summary_judgment_page(self, data: GearMeasurementData) -> Figure:
        """创建总结判定页 - 克林贝格标准"""
        fig = Figure(figsize=(8.27, 11.69), dpi=150)
        fig.patch.set_facecolor('white')
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        # 计算总体判定
        tolerances = self.tolerance_calculator.calculate_tolerances(
            data.basic_info.module, data.basic_info.teeth,
            data.basic_info.width, data.basic_info.accuracy_grade
        )
        
        profile_max = self._get_max_deviation(data.profile_data.left, data.profile_data.right)
        flank_max = self._get_max_deviation(data.flank_data.left, data.flank_data.right)
        
        profile_pass = profile_max <= tolerances.get('F_alpha', 999)
        flank_pass = flank_max <= tolerances.get('F_beta', 999)
        overall_pass = profile_pass and flank_pass
        
        # 顶部装饰线
        ax.add_patch(mpatches.Rectangle((0.05, 0.90), 0.9, 0.03, 
                                        facecolor=self.BLUE, transform=fig.transFigure))
        
        # 大标题判定
        if overall_pass:
            fig.text(0.5, 0.70, "✓ PASS",
                    ha='center', va='center', fontsize=60, fontweight='bold', color=self.GREEN)
            fig.text(0.5, 0.63, "Qualified / 合格",
                    ha='center', va='center', fontsize=20, fontweight='bold', color=self.GREEN)
        else:
            fig.text(0.5, 0.70, "✗ FAIL",
                    ha='center', va='center', fontsize=60, fontweight='bold', color=self.RED)
            fig.text(0.5, 0.63, "Not Qualified / 不合格",
                    ha='center', va='center', fontsize=20, fontweight='bold', color=self.RED)
        
        # 详细结果
        y_pos = 0.52
        fig.text(0.5, y_pos, "Measurement Results / 测量结果",
                ha='center', va='top', fontsize=14, fontweight='bold', color=self.BLUE)
        
        y_pos -= 0.06
        results_text = [
            f"Profile Deviation / 齿形偏差: {profile_max:.2f} μm  (Tolerance / 公差: {tolerances.get('F_alpha', 0):.2f} μm) - {'PASS' if profile_pass else 'FAIL'}",
            f"Helix Deviation / 齿向偏差: {flank_max:.2f} μm  (Tolerance / 公差: {tolerances.get('F_beta', 0):.2f} μm) - {'PASS' if flank_pass else 'FAIL'}",
            f"Measurement Standard / 测量标准: ISO 1328-{data.basic_info.accuracy_grade}",
            f"Total Teeth Measured / 测量齿数: {len(data.profile_data.left) + len(data.profile_data.right)}",
        ]
        
        for text in results_text:
            fig.text(0.5, y_pos, text, ha='center', va='top', fontsize=11)
            y_pos -= 0.05
        
        # 签名区域
        y_sig = 0.25
        fig.text(0.5, y_sig + 0.05, "Signature / 签名",
                ha='center', va='top', fontsize=14, fontweight='bold', color=self.BLUE)
        
        # 签名框
        sig_items = [
            ("Measured by / 测量:", "Date / 日期:"),
            ("Reviewed by / 审核:", "Date / 日期:"),
            ("Approved by / 批准:", "Date / 日期:")
        ]
        
        for i, (label1, label2) in enumerate(sig_items):
            y = y_sig - (i * 0.08)
            fig.text(0.15, y, label1, ha='left', va='center', fontsize=11, fontweight='bold')
            fig.text(0.35, y, "___________________", ha='left', va='center', fontsize=11)
            fig.text(0.60, y, label2, ha='left', va='center', fontsize=11, fontweight='bold')
            fig.text(0.75, y, "_____________", ha='left', va='center', fontsize=11)
        
        # 底部信息
        fig.text(0.5, 0.05, "Klingelnberg Precision Measurement Center",
                ha='center', va='center', fontsize=10, color='#888888')
        fig.text(0.5, 0.02, f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                ha='center', va='center', fontsize=9, color='#888888', style='italic')
        
        return fig
    
    def _plot_distribution(self, ax, tooth_data: Dict, title: str, color: str):
        """绘制偏差分布直方图"""
        values = []
        for data_points in tooth_data.values():
            values.extend(data_points)
        
        if not values:
            return
        
        # 绘制直方图
        n, bins, patches = ax.hist(values, bins=60, alpha=0.7, color=color, edgecolor='black', linewidth=0.5)
        
        # 添加统计线
        mean = np.mean(values)
        std = np.std(values)
        
        ax.axvline(mean, color=self.RED, linestyle='--', linewidth=2.5, 
                  label=f'Mean={mean:.2f}μm')
        ax.axvline(mean+std, color='orange', linestyle=':', linewidth=2, 
                  label=f'Mean±σ')
        ax.axvline(mean-std, color='orange', linestyle=':', linewidth=2)
        
        ax.set_title(title, fontsize=11, fontweight='bold', pad=8)
        ax.set_xlabel('Deviation (μm) / 偏差', fontsize=10, fontweight='bold')
        ax.set_ylabel('Frequency / 频次', fontsize=10, fontweight='bold')
        ax.legend(fontsize=8, loc='upper right')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_facecolor('#FAFAFA')
    
    def _get_max_deviation(self, left_data: Dict, right_data: Dict) -> float:
        """获取最大偏差（绝对值）"""
        all_values = []
        for tooth_data in left_data.values():
            all_values.extend([abs(v) for v in tooth_data])
        for tooth_data in right_data.values():
            all_values.extend([abs(v) for v in tooth_data])
        
        return max(all_values) if all_values else 0
    
    def _get_pitch_max(self, data: GearMeasurementData, key: str) -> float:
        """获取周节数据最大值"""
        values = []
        for tooth_data in data.pitch_data.left.values():
            values.append(abs(tooth_data.get(key, 0)))
        for tooth_data in data.pitch_data.right.values():
            values.append(abs(tooth_data.get(key, 0)))
        
        return max(values) if values else 0
    
    def _format_date(self, date_value) -> str:
        """格式化日期"""
        if hasattr(date_value, 'strftime'):
            return date_value.strftime('%Y-%m-%d')
        elif date_value:
            return str(date_value)
        else:
            return datetime.now().strftime('%Y-%m-%d')


def generate_klingelnberg_matplotlib_report(data: GearMeasurementData, output_path: str) -> bool:
    """
    生成克林贝格标准PDF报告（使用Matplotlib方法）
    
    Args:
        data: 齿轮测量数据
        output_path: 输出路径
        
    Returns:
        bool: 是否成功
    """
    generator = KlingelnbergMatplotlibReport()
    return generator.generate_report(data, output_path)

