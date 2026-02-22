"""
PDF报告生成器 - 基于 Klingelnberg 格式
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from datetime import datetime
import io

class PDFReportGenerator:
    """生成专业PDF报告"""
    
    def __init__(self):
        plt.rcParams['pdf.fonttype'] = 42
        plt.rcParams['ps.fonttype'] = 42
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
    
    def generate_report(self, analyzer, results, pitch_left, pitch_right, filename="gear_report.pdf"):
        """生成完整PDF报告"""
        buffer = io.BytesIO()
        
        with PdfPages(buffer) as pdf:
            # 第1页：专业报告（齿形分析）
            self._create_profile_page(pdf, analyzer, results)
            
            # 第2页：齿向分析
            self._create_lead_page(pdf, analyzer, results)
            
            # 第3页：周节报表
            self._create_pitch_page(pdf, analyzer, pitch_left, pitch_right)
            
            # 第4页：合并曲线
            self._create_merge_page(pdf, analyzer, results)
            
            # 第5页：频谱分析
            self._create_spectrum_page(pdf, analyzer, results)
        
        buffer.seek(0)
        return buffer
    
    def _create_profile_page(self, pdf, analyzer, results):
        """创建齿形分析页面"""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
        
        gear_params = analyzer.gear_params
        info = {
            'module': gear_params.module if gear_params else 0,
            'teeth': gear_params.teeth_count if gear_params else 0,
            'pressure_angle': gear_params.pressure_angle if gear_params else 0,
            'helix_angle': gear_params.helix_angle if gear_params else 0,
        }
        
        # 标题
        fig.suptitle('Gear Profile/Lead Report - 齿形分析', fontsize=14, fontweight='bold', y=0.98)
        
        # 基本信息表格
        gs = gridspec.GridSpec(3, 1, height_ratios=[0.15, 0.45, 0.4], hspace=0.3)
        
        # Header信息
        ax_header = fig.add_subplot(gs[0, 0])
        ax_header.axis('off')
        
        header_text = f"""
        Prog.No.: {analyzer.file_path if hasattr(analyzer, 'file_path') else 'N/A'}    
        Module: {info['module']:.3f}mm    Teeth: {info['teeth']}    Pressure Angle: {info['pressure_angle']}°
        """
        ax_header.text(0.5, 0.5, header_text, ha='center', va='center', fontsize=9, 
                      transform=ax_header.transAxes, family='monospace')
        
        # 左齿面图表
        ax_left = fig.add_subplot(gs[1, 0])
        self._draw_profile_chart(ax_left, 'Left Flank', analyzer.reader.profile_data.get('left', {}))
        
        # 右齿面图表
        ax_right = fig.add_subplot(gs[2, 0])
        self._draw_profile_chart(ax_right, 'Right Flank', analyzer.reader.profile_data.get('right', {}))
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _draw_profile_chart(self, ax, title, tooth_data):
        """绘制齿形图表"""
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_facecolor('white')
        
        if not tooth_data:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            return
        
        teeth = sorted(list(tooth_data.keys()))[:6]  # 最多显示6个齿
        
        for i, tooth_num in enumerate(teeth):
            x_center = i + 1
            values_dict = tooth_data[tooth_num]
            
            if isinstance(values_dict, dict):
                # 取中间位置的值
                values = list(values_dict.values())[0] if values_dict else []
            else:
                values = values_dict
            
            if len(values) > 0:
                y_positions = np.linspace(0, 8, len(values))
                x_positions = x_center + (np.array(values) / 50.0)
                
                ax.plot(x_positions, y_positions, 'r-', linewidth=0.8)
                ax.axvline(x=x_center, color='black', linestyle='-', linewidth=0.5)
                
                # 齿号标签
                ax.text(x_center, -0.5, str(tooth_num), ha='center', fontsize=8)
        
        ax.set_xlim(0.5, len(teeth) + 0.5)
        ax.set_ylim(-1, 9)
        ax.set_xlabel('Tooth Number')
        ax.set_ylabel('Evaluation Length (mm)')
        ax.grid(True, alpha=0.3)
    
    def _create_lead_page(self, pdf, analyzer, results):
        """创建齿向分析页面"""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
        fig.suptitle('Lead Analysis - 齿向分析', fontsize=14, fontweight='bold', y=0.98)
        
        gs = gridspec.GridSpec(2, 1, height_ratios=[0.5, 0.5], hspace=0.3)
        
        ax_left = fig.add_subplot(gs[0, 0])
        self._draw_lead_chart(ax_left, 'Left Lead', analyzer.reader.helix_data.get('left', {}))
        
        ax_right = fig.add_subplot(gs[1, 0])
        self._draw_lead_chart(ax_right, 'Right Lead', analyzer.reader.helix_data.get('right', {}))
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _draw_lead_chart(self, ax, title, tooth_data):
        """绘制齿向图表"""
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_facecolor('white')
        
        if not tooth_data:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            return
        
        teeth = sorted(list(tooth_data.keys()))[:6]
        
        for i, tooth_num in enumerate(teeth):
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
                ax.axvline(x=x_center, color='black', linestyle='-', linewidth=0.5)
                ax.text(x_center, -2, str(tooth_num), ha='center', fontsize=8)
        
        ax.set_xlim(0.5, len(teeth) + 0.5)
        ax.set_ylim(-5, 45)
        ax.set_xlabel('Tooth Number')
        ax.set_ylabel('Face Width (mm)')
        ax.grid(True, alpha=0.3)
    
    def _create_pitch_page(self, pdf, analyzer, pitch_left, pitch_right):
        """创建周节报表页面"""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
        fig.suptitle('Gear Spacing Report - 周节报表', fontsize=14, fontweight='bold', y=0.98)
        
        gs = gridspec.GridSpec(3, 1, height_ratios=[0.2, 0.4, 0.4], hspace=0.3)
        
        # 统计信息
        ax_stats = fig.add_subplot(gs[0, 0])
        ax_stats.axis('off')
        
        stats_text = ""
        if pitch_left:
            stats_text += f"左齿面: fp_max={pitch_left.fp_max:.2f}μm, Fp_max={pitch_left.Fp_max:.2f}μm, Fr={pitch_left.Fr:.2f}μm\n"
        if pitch_right:
            stats_text += f"右齿面: fp_max={pitch_right.fp_max:.2f}μm, Fp_max={pitch_right.Fp_max:.2f}μm, Fr={pitch_right.Fr:.2f}μm"
        
        ax_stats.text(0.5, 0.5, stats_text, ha='center', va='center', 
                     transform=ax_stats.transAxes, fontsize=10, family='monospace')
        
        # 左齿面图表
        ax_left = fig.add_subplot(gs[1, 0])
        self._draw_pitch_chart(ax_left, 'Left Flank Pitch', pitch_left)
        
        # 右齿面图表
        ax_right = fig.add_subplot(gs[2, 0])
        self._draw_pitch_chart(ax_right, 'Right Flank Pitch', pitch_right)
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _draw_pitch_chart(self, ax, title, pitch_data):
        """绘制周节图表"""
        ax.set_title(title, fontsize=12, fontweight='bold')
        
        if not pitch_data or not pitch_data.teeth:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            return
        
        teeth = pitch_data.teeth
        fp_values = pitch_data.fp_values
        Fp_values = pitch_data.Fp_values
        
        ax.plot(teeth, fp_values, 'b-o', label='fp', linewidth=1, markersize=3)
        ax.plot(teeth, Fp_values, 'r-s', label='Fp', linewidth=1, markersize=3)
        
        ax.set_xlabel('Tooth Number')
        ax.set_ylabel('Deviation (μm)')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _create_merge_page(self, pdf, analyzer, results):
        """创建合并曲线页面"""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
        fig.suptitle('Merged Curve Analysis (0-360°) - 合并曲线分析', fontsize=14, fontweight='bold', y=0.98)
        
        gs = gridspec.GridSpec(4, 1, height_ratios=[0.25, 0.25, 0.25, 0.25], hspace=0.3)
        
        name_mapping = {
            'profile_left': 'Left Profile',
            'profile_right': 'Right Profile',
            'helix_left': 'Left Lead',
            'helix_right': 'Right Lead'
        }
        
        for idx, (name, result) in enumerate(results.items()):
            if idx >= 4:
                break
            
            ax = fig.add_subplot(gs[idx, 0])
            display_name = name_mapping.get(name, name)
            
            if result and len(result.angles) > 0:
                ax.plot(result.angles, result.values, 'b-', linewidth=0.5, alpha=0.7, label='Original')
                ax.plot(result.angles, result.reconstructed_signal, 'r-', linewidth=1.5, label='High-order Reconstructed')
                ax.set_title(f"{display_name} - High-order Amp: {result.high_order_amplitude:.4f}μm, RMS: {result.high_order_rms:.4f}μm")
            else:
                ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            
            ax.set_xlabel('Rotation Angle (°)')
            ax.set_ylabel('Deviation (μm)')
            ax.set_xlim(0, 360)
            ax.legend()
            ax.grid(True, alpha=0.3)
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def _create_spectrum_page(self, pdf, analyzer, results):
        """创建频谱分析页面"""
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
        fig.suptitle('Spectrum Analysis - 频谱分析', fontsize=14, fontweight='bold', y=0.98)
        
        gs = gridspec.GridSpec(4, 1, height_ratios=[0.25, 0.25, 0.25, 0.25], hspace=0.4)
        
        name_mapping = {
            'profile_left': 'Left Profile',
            'profile_right': 'Right Profile',
            'helix_left': 'Left Lead',
            'helix_right': 'Right Lead'
        }
        
        ze = analyzer.gear_params.teeth_count if analyzer.gear_params else 87
        
        for idx, (name, result) in enumerate(results.items()):
            if idx >= 4:
                break
            
            ax = fig.add_subplot(gs[idx, 0])
            display_name = name_mapping.get(name, name)
            
            if result and result.spectrum_components:
                sorted_comps = sorted(result.spectrum_components[:20], key=lambda c: c.order)
                orders = [c.order for c in sorted_comps]
                amplitudes = [c.amplitude for c in sorted_comps]
                
                colors = ['red' if o >= ze else 'steelblue' for o in orders]
                ax.bar(orders, amplitudes, color=colors, alpha=0.7, width=3)
                ax.axvline(x=ze, color='green', linestyle='--', linewidth=2, label=f'ZE={ze}')
                
                # 显示前3个主要阶次
                top3 = result.spectrum_components[:3]
                top3_text = ', '.join([f"{c.order:.0f}({c.amplitude:.3f})" for c in top3])
                ax.set_title(f"{display_name} - Top 3: {top3_text}")
            else:
                ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            
            ax.set_xlabel('Order')
            ax.set_ylabel('Amplitude (μm)')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
        
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
