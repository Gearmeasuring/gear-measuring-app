"""
Ripple分析PDF报告生成器
生成专业的Ripple分析PDF报告
"""
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from config.logging_config import logger


class RipplePDFReportGenerator:
    """Ripple分析PDF报告生成器"""
    
    def __init__(self, ripple_results, gear_data, file_path):
        self.ripple_results = ripple_results
        self.gear_data = gear_data
        self.file_path = file_path
        
    def generate_report(self, output_path):
        """生成Ripple分析PDF报告"""
        try:
            # 配置PDF生成
            self._configure_pdf_settings()
            
            # 创建PDF文件
            with PdfPages(output_path) as pdf:
                # 1. 封面页
                fig = self.create_ripple_report_cover()
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)

                # 2. 基本信息页
                fig = self.create_ripple_info_page()
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)

                # 3. 统计信息页
                fig = self.create_ripple_stats_page()
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)

                # 4. 阶次分析页
                fig = self.create_order_analysis_page()
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)

                # 5. 诊断建议页
                fig = self.create_diagnosis_page()
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)

                # 6. 详细数据页
                fig = self.create_ripple_detail_page()
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)

            logger.info(f"Ripple分析PDF报告生成成功: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成Ripple分析PDF报告失败: {e}")
            return False
    
    def _configure_pdf_settings(self):
        """配置PDF生成设置"""
        import matplotlib
        
        # 临时切换后端
        original_backend = matplotlib.get_backend()
        matplotlib.use('Agg')  # 使用非交互式后端
        plt.ioff()  # 关闭交互模式
        
        # 完整的PDF参数配置
        matplotlib.rcParams.update({
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'savefig.facecolor': 'white',
            'savefig.edgecolor': 'none',
            'patch.facecolor': 'white',
            'text.color': 'black',
            'axes.labelcolor': 'black',
            'xtick.color': 'black',
            'ytick.color': 'black',
            'axes.edgecolor': 'black',
            'pdf.fonttype': 42,  # TrueType字体
            'ps.fonttype': 42,
            'font.sans-serif': ['SimHei', 'Arial Unicode MS', 'DejaVu Sans'],
            'axes.unicode_minus': False,
        })
    
    def create_ripple_report_cover(self):
        """创建Ripple报告封面"""
        fig, ax = plt.subplots(figsize=(8.5, 11), dpi=100)
        ax.axis('off')
        
        # 标题
        ax.text(0.5, 0.8, "Ripple分析报告", fontsize=24, fontweight='bold', 
                ha='center', va='center', transform=ax.transAxes)
        
        # 文件信息
        file_name = os.path.basename(self.file_path) if self.file_path else "未知文件"
        ax.text(0.5, 0.7, f"文件: {file_name}", fontsize=14, 
                ha='center', va='center', transform=ax.transAxes)
        
        # 生成时间
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ax.text(0.5, 0.6, f"生成时间: {current_time}", fontsize=12, 
                ha='center', va='center', transform=ax.transAxes)
        
        # 软件信息
        ax.text(0.5, 0.5, "齿轮分析系统 v1.0", fontsize=12, 
                ha='center', va='center', transform=ax.transAxes)
        
        return fig
    
    def create_ripple_info_page(self):
        """创建Ripple基本信息页"""
        fig, ax = plt.subplots(figsize=(8.5, 11), dpi=100)
        ax.axis('off')
        
        # 标题
        ax.text(0.5, 0.95, "Ripple分析基本信息", fontsize=18, fontweight='bold', 
                ha='center', va='center', transform=ax.transAxes)
        
        # 齿轮参数
        if self.gear_data:
            y_pos = 0.85
            ax.text(0.1, y_pos, "齿轮参数:", fontsize=14, fontweight='bold', 
                    transform=ax.transAxes)
            y_pos -= 0.05
            
            params = [
                f"模数: {self.gear_data.get('module', 'N/A')} mm",
                f"齿数: {self.gear_data.get('teeth', 'N/A')}",
                f"压力角: {self.gear_data.get('pressure_angle', 'N/A')}°",
                f"螺旋角: {self.gear_data.get('helix_angle', 'N/A')}°",
                f"齿宽: {self.gear_data.get('width', 'N/A')} mm",
                f"分度圆直径: {self.gear_data.get('pitch_diameter', 'N/A')} mm"
            ]
            
            for param in params:
                ax.text(0.15, y_pos, param, fontsize=12, transform=ax.transAxes)
                y_pos -= 0.04
        
        # Ripple分析参数
        if self.ripple_results and 'settings' in self.ripple_results:
            y_pos = 0.5
            ax.text(0.1, y_pos, "Ripple分析参数:", fontsize=14, fontweight='bold', 
                    transform=ax.transAxes)
            y_pos -= 0.05
            
            settings = self.ripple_results['settings']
            param_texts = [
                f"截止波长: {settings.get('cutoff_wavelength', 'N/A')} mm",
                f"高通截止频率: {settings.get('highpass_cutoff', 'N/A')} 周期/mm",
                f"低通截止频率: {settings.get('lowpass_cutoff', 'N/A')} 周期/mm",
                f"滤波器类型: {settings.get('filter_type', 'N/A')}",
                f"滤波器阶数: {settings.get('filter_order', 'N/A')}",
                f"阶次分析范围: {settings.get('min_order', 'N/A')}-{settings.get('max_order', 'N/A')}"
            ]
            
            for param_text in param_texts:
                ax.text(0.15, y_pos, param_text, fontsize=12, transform=ax.transAxes)
                y_pos -= 0.04
        
        return fig
    
    def create_ripple_stats_page(self):
        """创建Ripple统计信息页"""
        fig, ax = plt.subplots(figsize=(8.5, 11), dpi=100)
        ax.axis('off')
        
        # 标题
        ax.text(0.5, 0.95, "Ripple分析统计信息", fontsize=18, fontweight='bold', 
                ha='center', va='center', transform=ax.transAxes)
        
        if not self.ripple_results:
            ax.text(0.5, 0.5, "无Ripple分析数据", fontsize=14, 
                    ha='center', va='center', transform=ax.transAxes)
            return fig
        
        # 统计信息
        stats = self.ripple_results.get('stats', {})
        y_pos = 0.85
        
        # Profile统计
        if 'profile' in stats:
            ax.text(0.1, y_pos, "齿形波纹度统计:", fontsize=14, fontweight='bold', 
                    transform=ax.transAxes)
            y_pos -= 0.05
            
            profile_stats = stats['profile']
            stat_texts = [
                f"总齿数: {profile_stats.get('total', 0)}",
                f"通过齿数: {profile_stats.get('passed', 0)}",
                f"失败齿数: {profile_stats.get('failed', 0)}",
                f"平均W值: {profile_stats.get('avg_w', 0):.3f} μm",
                f"平均RMS: {profile_stats.get('avg_rms', 0):.3f} μm"
            ]
            
            for stat_text in stat_texts:
                ax.text(0.15, y_pos, stat_text, fontsize=12, transform=ax.transAxes)
                y_pos -= 0.04
            
            y_pos -= 0.02
        
        # Flank统计
        if 'flank' in stats:
            ax.text(0.1, y_pos, "齿向波纹度统计:", fontsize=14, fontweight='bold', 
                    transform=ax.transAxes)
            y_pos -= 0.05
            
            flank_stats = stats['flank']
            stat_texts = [
                f"总齿数: {flank_stats.get('total', 0)}",
                f"通过齿数: {flank_stats.get('passed', 0)}",
                f"失败齿数: {flank_stats.get('failed', 0)}",
                f"平均W值: {flank_stats.get('avg_w', 0):.3f} μm",
                f"平均RMS: {flank_stats.get('avg_rms', 0):.3f} μm"
            ]
            
            for stat_text in stat_texts:
                ax.text(0.15, y_pos, stat_text, fontsize=12, transform=ax.transAxes)
                y_pos -= 0.04
        
        return fig
    
    def create_order_analysis_page(self):
        """创建阶次分析页"""
        fig, ax = plt.subplots(figsize=(8.5, 11), dpi=100)
        ax.axis('off')
        
        # 标题
        ax.text(0.5, 0.95, "阶次分析结果", fontsize=18, fontweight='bold', 
                ha='center', va='center', transform=ax.transAxes)
        
        if not self.ripple_results or 'order_analysis' not in self.ripple_results:
            ax.text(0.5, 0.5, "无阶次分析数据", fontsize=14, 
                    ha='center', va='center', transform=ax.transAxes)
            return fig
        
        order_analysis = self.ripple_results['order_analysis']
        y_pos = 0.85
        
        # 绘制阶次谱图
        for data_type in ['profile', 'flank']:
            if data_type in order_analysis:
                analysis_data = order_analysis[data_type]
                orders = analysis_data.get('orders', [])
                amplitudes = analysis_data.get('amplitudes', [])
                
                if orders and amplitudes:
                    # 创建子图
                    sub_ax = fig.add_subplot(2, 1, 1 if data_type == 'profile' else 2)
                    sub_ax.bar(orders, amplitudes, width=0.8, color='blue', alpha=0.7)
                    sub_ax.set_title(f'{data_type.capitalize()} 阶次谱')
                    sub_ax.set_xlabel('阶次')
                    sub_ax.set_ylabel('幅值')
                    sub_ax.grid(True, alpha=0.3)
        
        return fig
    
    def create_diagnosis_page(self):
        """创建诊断建议页"""
        fig, ax = plt.subplots(figsize=(8.5, 11), dpi=100)
        ax.axis('off')
        
        # 标题
        ax.text(0.5, 0.95, "诊断建议", fontsize=18, fontweight='bold', 
                ha='center', va='center', transform=ax.transAxes)
        
        # 诊断建议内容
        y_pos = 0.85
        diagnosis_texts = [
            "基于Ripple分析结果的诊断建议:",
            "",
            "1. 质量等级评定:",
            "   - A级: Wt ≤ 2.0μm, Wq ≤ 0.5μm (精密齿轮)",
            "   - B级: Wt ≤ 4.0μm, Wq ≤ 1.0μm (高质量齿轮)",
            "   - C级: Wt ≤ 8.0μm, Wq ≤ 2.0μm (标准齿轮)",
            "   - D级: Wt > 8.0μm, Wq > 2.0μm (需要改进)",
            "",
            "2. 常见问题诊断:",
            "   - 1×转速频率: 不平衡、偏心",
            "   - 2×转速频率: 热变形、装配误差",
            "   - 齿数×转速频率: 齿轮啮合误差",
            "   - 高阶谐波: 加工质量问题",
            "",
            "3. 改进建议:",
            "   - 检查轴系平衡，调整装配精度",
            "   - 检查热处理工艺，改善装配工艺",
            "   - 检查齿形精度，调整啮合间隙",
            "   - 改善加工工艺，检查刀具磨损"
        ]
        
        for text in diagnosis_texts:
            if text:
                ax.text(0.1, y_pos, text, fontsize=12, transform=ax.transAxes)
            y_pos -= 0.04
        
        return fig
    
    def create_ripple_detail_page(self):
        """创建Ripple详细数据页"""
        fig, ax = plt.subplots(figsize=(8.5, 11), dpi=100)
        ax.axis('off')
        
        # 标题
        ax.text(0.5, 0.95, "详细数据表", fontsize=18, fontweight='bold', 
                ha='center', va='center', transform=ax.transAxes)
        
        if not self.ripple_results:
            ax.text(0.5, 0.5, "无详细数据", fontsize=14, 
                    ha='center', va='center', transform=ax.transAxes)
            return fig
        
        # 创建数据表格
        y_pos = 0.85
        
        # Profile数据
        if 'profile' in self.ripple_results:
            ax.text(0.1, y_pos, "齿形波纹度详细数据:", fontsize=14, fontweight='bold', 
                    transform=ax.transAxes)
            y_pos -= 0.05
            
            profile_data = self.ripple_results['profile']
            for tooth_id, data in list(profile_data.items())[:10]:  # 只显示前10个齿
                if isinstance(data, dict):
                    w_value = data.get('w_value', 0)
                    rms = data.get('rms', 0)
                    status = "通过" if data.get('passed', False) else "失败"
                    
                    ax.text(0.15, y_pos, f"齿{tooth_id}: W={w_value:.3f}μm, RMS={rms:.3f}μm, {status}", 
                            fontsize=10, transform=ax.transAxes)
                    y_pos -= 0.03
        
        # Flank数据
        if 'flank' in self.ripple_results:
            y_pos -= 0.05
            ax.text(0.1, y_pos, "齿向波纹度详细数据:", fontsize=14, fontweight='bold', 
                    transform=ax.transAxes)
            y_pos -= 0.05
            
            flank_data = self.ripple_results['flank']
            for tooth_id, data in list(flank_data.items())[:10]:  # 只显示前10个齿
                if isinstance(data, dict):
                    w_value = data.get('w_value', 0)
                    rms = data.get('rms', 0)
                    status = "通过" if data.get('passed', False) else "失败"
                    
                    ax.text(0.15, y_pos, f"齿{tooth_id}: W={w_value:.3f}μm, RMS={rms:.3f}μm, {status}", 
                            fontsize=10, transform=ax.transAxes)
                    y_pos -= 0.03
        
        return fig
