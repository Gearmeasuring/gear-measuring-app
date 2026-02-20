"""
专业阶次谱PDF报告生成器
仿照原程序的专业阶次谱分析报告
"""
import os
import datetime
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from config.logging_config import logger


class OrderSpectrumPDFReportGenerator:
    """专业阶次谱PDF报告生成器"""
    
    def __init__(self, ripple_results, gear_data, file_path):
        self.ripple_results = ripple_results
        self.gear_data = gear_data
        self.file_path = file_path
    
    def generate_report(self, output_path):
        """生成专业阶次谱PDF报告"""
        try:
            # 配置PDF生成
            self._configure_pdf_settings()
            
            # 创建PDF文件
            with PdfPages(output_path) as pdf:
                # 生成专业阶次谱报告页面
                fig = self.create_professional_order_spectrum()
                pdf.savefig(fig, bbox_inches='tight', facecolor='white', edgecolor='none')
                plt.close(fig)
            
            logger.info(f"专业阶次谱PDF报告生成成功: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"生成专业阶次谱PDF报告失败: {e}")
            return False
    
    def _configure_pdf_settings(self):
        """配置PDF生成设置"""
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
            'pdf.fonttype': 42,
            'ps.fonttype': 42,
            'font.sans-serif': ['SimHei', 'Arial Unicode MS', 'DejaVu Sans'],
            'axes.unicode_minus': False,
        })
    
    def create_professional_order_spectrum(self):
        """创建专业阶次谱分析报告页面"""
        # A4横向尺寸：297mm x 210mm = 11.69英寸 x 8.27英寸
        fig = Figure(figsize=(11.69, 8.27), dpi=100)
        
        try:
            # 使用GridSpec创建复杂布局（6行1列）
            gs = fig.add_gridspec(6, 1, height_ratios=[0.4, 1.6, 1.6, 1.6, 1.6, 1.0], hspace=0.6)
            
            # 头部信息区域
            ax_header = fig.add_subplot(gs[0, 0])
            ax_header.axis('off')
            
            # 获取文件基本信息
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            file_name = os.path.basename(self.file_path) if self.file_path else "未知文件"
            
            # 头部标题
            ax_header.text(0.02, 0.8, "专业阶次谱分析 (Professional Order Spectrum)", 
                          fontsize=12, fontweight='bold', color='red', transform=ax_header.transAxes)
            ax_header.text(0.98, 0.8, current_time, fontsize=10, ha='right', 
                          transform=ax_header.transAxes)
            ax_header.text(0.02, 0.4, f"文件: {file_name}", fontsize=10, 
                          transform=ax_header.transAxes)
            ax_header.text(0.02, 0.1, "评价方式: 高阶次分析", fontsize=10, 
                          transform=ax_header.transAxes)
            
            # 获取阶次分析数据
            order_analysis = self.ripple_results.get('order_analysis', {})
            
            # 四个阶次谱图表区域
            section_titles = ["Profile right", "Profile left", "Helix right", "Helix left"]
            section_data_map = {
                "Profile right": ('profile', 'right'),
                "Profile left": ('profile', 'left'),
                "Helix right": ('flank', 'right'),
                "Helix left": ('flank', 'left')
            }
            
            for i, title in enumerate(section_titles):
                ax = fig.add_subplot(gs[i+1, 0])
                ax.axis('off')
                
                # 绘制区域标题
                ax.text(0.02, 0.95, title, fontsize=11, fontweight='bold', 
                       transform=ax.transAxes, va='top')
                
                # 创建内部绘图区域
                inner_ax = ax.inset_axes([0.08, 0.15, 0.85, 0.75])
                
                # 获取数据并绘制
                data = self._get_section_data(order_analysis, i)
                
                if data is not None and len(data) > 0:
                    # 绘制阶次谱柱状图
                    orders = list(range(1, len(data) + 1))
                    
                    # 绘制柱状图
                    bars = inner_ax.bar(orders, data, width=0.8, color='blue', 
                                      edgecolor='darkblue', alpha=0.8)
                    
                    # 智能标签（避免重叠）
                    max_val = max(data) if data else 0
                    if max_val > 0:
                        # 只显示最大的3个值
                        indexed_data = [(j+1, val) for j, val in enumerate(data)]
                        indexed_data.sort(key=lambda x: x[1], reverse=True)
                        
                        for j, (order, value) in enumerate(indexed_data[:3]):
                            if value > max_val * 0.1:  # 只显示大于最大值的10%的标签
                                inner_ax.text(order, value + max_val * 0.02, f'{value:.2f}', 
                                            ha='center', va='bottom', fontsize=8, fontweight='bold')
                    
                    # 设置坐标轴
                    inner_ax.set_xlabel('Order', fontsize=10)
                    inner_ax.set_ylabel('Amplitude (μm)', fontsize=10)
                    inner_ax.set_title(f'{title} Order Spectrum', fontsize=11, fontweight='bold')
                    inner_ax.grid(True, alpha=0.3)
                    inner_ax.set_xlim(0.5, min(len(data), 50) + 0.5)  # 只显示前50阶
                else:
                    inner_ax.text(0.5, 0.5, "无数据", ha='center', va='center', 
                                transform=inner_ax.transAxes, fontsize=12, color='gray')
                    inner_ax.set_title(f'{title} Order Spectrum', fontsize=11, fontweight='bold')
            
            # 表格区域
            ax_table = fig.add_subplot(gs[5, 0])
            ax_table.axis('off')
            
            # 创建表格数据
            table_data = []
            table_data.append(['Section', 'Max Order', 'Max Amplitude (μm)', 'RMS (μm)'])
            
            for i, title in enumerate(section_titles):
                data = self._get_section_data(order_analysis, i)
                if data is not None and len(data) > 0:
                    max_idx = np.argmax(data)
                    max_order = max_idx + 1
                    max_amplitude = data[max_idx]
                    rms = np.sqrt(np.mean(np.array(data)**2))
                    table_data.append([title, str(max_order), f'{max_amplitude:.3f}', f'{rms:.3f}'])
                else:
                    table_data.append([title, 'N/A', 'N/A', 'N/A'])
            
            # 绘制表格
            table = ax_table.table(cellText=table_data[1:], colLabels=table_data[0],
                                 cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 2)
            
            # 设置表格样式
            for i in range(len(table_data)):
                for j in range(len(table_data[0])):
                    cell = table[(i, j)] if i > 0 else table[(0, j)]
                    if i == 0:  # 表头
                        cell.set_facecolor('#4CAF50')
                        cell.set_text_props(weight='bold', color='white')
                    else:
                        cell.set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')
            
            ax_table.set_title('Order Analysis Summary', fontsize=12, fontweight='bold', pad=20)
            
        except Exception as e:
            # 如果出错，显示错误信息
            logger.exception(f"创建专业阶次谱报告时出错: {e}")
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, f"创建阶次谱报告时出错:\n{str(e)}", 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=12, color='red')
            ax.set_title("阶次谱报告错误")
            ax.axis('off')
        
        return fig
    
    def _get_section_data(self, order_analysis, section_index):
        """获取指定区域的数据"""
        section_mapping = {
            0: ('profile', 'right'),
            1: ('profile', 'left'),
            2: ('flank', 'right'),
            3: ('flank', 'left')
        }
        
        data_type, side = section_mapping.get(section_index, ('profile', 'right'))
        
        if data_type in order_analysis:
            analysis_data = order_analysis[data_type]
            if 'amplitudes' in analysis_data:
                return analysis_data['amplitudes']
        
        return None


def generate_order_spectrum_pdf(ripple_results, gear_data, file_path, output_path):
    """生成专业阶次谱PDF报告（便捷函数）"""
    generator = OrderSpectrumPDFReportGenerator(ripple_results, gear_data, file_path)
    return generator.generate_report(output_path)

