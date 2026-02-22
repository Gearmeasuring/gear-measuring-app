"""
高级图表模块
包含瀑布图、阶次谱图、3D图表等高级可视化功能
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from scipy.signal import stft
from PyQt5.QtWidgets import QMdiSubWindow, QWidget, QVBoxLayout
from gear_analysis_refactored.config.logging_config import logger
from ui.custom_canvas import CustomFigureCanvas


class WaterfallChartWidget(QWidget):
    """瀑布图组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 创建图表
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = CustomFigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
    def plot_waterfall_analysis(self, ripple_results):
        """绘制时频瀑布图"""
        logger.info("开始绘制时频瀑布图")
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='3d')

        if not ripple_results:
            ax.text2D(0.5, 0.5, "无Ripple分析数据", ha='center', va='center', transform=ax.transAxes)
            self.canvas.draw()
            return
            
        analysis_data = ripple_results.get('order_analysis', {}).get('profile') or ripple_results.get('order_analysis', {}).get('flank')
        
        if not analysis_data or 'stft_results' not in analysis_data or not analysis_data['stft_results']:
            ax.text2D(0.5, 0.5, "无STFT数据，无法生成瀑布图", ha='center', va='center', transform=ax.transAxes)
            ax.set_title("时频瀑布图 (无数据)")
            self.canvas.draw()
            return

        stft_data = analysis_data['stft_results']
        f, t, Zxx = stft_data['frequencies'], stft_data['times'], stft_data['magnitudes']
        T, F = np.meshgrid(t, f)
        
        ax.plot_surface(T, F, Zxx, cmap=plt.get_cmap('viridis'))
        ax.set_title(f"{analysis_data.get('data_type', 'N/A').capitalize()} 时频瀑布图")
        ax.set_xlabel('测量位置')
        ax.set_ylabel('频率 (Hz)')
        ax.set_zlabel('幅值')
        self.canvas.draw()
        logger.info("时频瀑布图绘制完成")


class OrderSpectrumChartWidget(QWidget):
    """阶次谱图组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 创建图表
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = CustomFigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
    def plot_order_spectrum(self, order_analysis, data_type='profile'):
        """绘制阶次谱图"""
        logger.info(f"开始绘制{data_type}阶次谱图")
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if not order_analysis or data_type not in order_analysis:
            ax.text(0.5, 0.5, f"无{data_type}阶次分析数据", ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f"{data_type}阶次谱图 (无数据)")
            self.canvas.draw()
            return
            
        analysis_data = order_analysis[data_type]
        orders = analysis_data.get('orders', [])
        amplitudes = analysis_data.get('amplitudes', [])
        
        if not orders or not amplitudes:
            ax.text(0.5, 0.5, f"无有效的{data_type}阶次数据", ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f"{data_type}阶次谱图 (无数据)")
            self.canvas.draw()
            return
            
        # 绘制阶次谱柱状图
        bars = ax.bar(orders, amplitudes, width=0.8, color='blue', edgecolor='darkblue', alpha=0.8)
        
        # 智能标签（避免重叠）
        max_val = max(amplitudes)
        if max_val > 0:
            # 只显示最大的2个值
            indexed_data = [(j+1, val) for j, val in enumerate(amplitudes)]
            indexed_data.sort(key=lambda x: x[1], reverse=True)
            
            for j, (order, value) in enumerate(indexed_data[:2]):
                if value > max_val * 0.1:  # 只显示大于最大值的10%的标签
                    ax.text(order, value + max_val * 0.02, f'{value:.2f}', 
                            ha='center', va='bottom', fontsize=8, fontweight='bold')
        
        ax.set_xlabel('Order')
        ax.set_ylabel('Amplitude')
        ax.set_title(f'{data_type.capitalize()} Order Spectrum')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0.5, len(orders) + 0.5)
        
        self.canvas.draw()
        logger.info(f"{data_type}阶次谱图绘制完成")


class UndulationDistributionChartWidget(QWidget):
    """波纹度分布图组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 创建图表
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = CustomFigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
    def plot_undulation_distribution(self, undulation_results):
        """绘制波纹度分布图"""
        logger.info("开始绘制波纹度分布图")
        self.figure.clear()
        
        if not undulation_results:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "无波纹度分析数据", ha='center', va='center', transform=ax.transAxes)
            ax.set_title("波纹度分布图 (无数据)")
            self.canvas.draw()
            return
            
        # 创建子图
        fig = self.figure
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        # 齿形波纹度分布
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_side_distribution(undulation_results.get('profile', {}), 'Profile', ax1)
        
        # 齿向波纹度分布
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_side_distribution(undulation_results.get('flank', {}), 'Flank', ax2)
        
        # 统计对比
        ax3 = fig.add_subplot(gs[1, :])
        self._plot_statistics_comparison(undulation_results, ax3)
        
        self.canvas.draw()
        logger.info("波纹度分布图绘制完成")
        
    def _plot_side_distribution(self, side_data, title, ax):
        """绘制单侧波纹度分布"""
        if not side_data:
            ax.text(0.5, 0.5, f"无{title}数据", ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f"{title} 波纹度分布 (无数据)")
            return
            
        # 提取W值和RMS值
        w_values = []
        rms_values = []
        
        for tooth_id, data in side_data.items():
            if isinstance(data, dict):
                w_values.append(data.get('w_value', 0))
                rms_values.append(data.get('rms', 0))
        
        if not w_values:
            ax.text(0.5, 0.5, f"无有效的{title}数据", ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f"{title} 波纹度分布 (无数据)")
            return
            
        # 绘制散点图
        ax.scatter(w_values, rms_values, alpha=0.7, s=50)
        ax.set_xlabel('W值 (μm)')
        ax.set_ylabel('RMS (μm)')
        ax.set_title(f"{title} 波纹度分布")
        ax.grid(True, alpha=0.3)
        
        # 添加统计信息
        if w_values and rms_values:
            ax.text(0.05, 0.95, f'平均W: {np.mean(w_values):.2f}μm\n平均RMS: {np.mean(rms_values):.2f}μm', 
                   transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    def _plot_statistics_comparison(self, undulation_results, ax):
        """绘制统计对比图"""
        stats = undulation_results.get('stats', {})
        
        if not stats:
            ax.text(0.5, 0.5, "无统计数据", ha='center', va='center', transform=ax.transAxes)
            ax.set_title("统计对比 (无数据)")
            return
            
        # 准备数据
        categories = ['Profile', 'Flank']
        total_counts = []
        passed_counts = []
        failed_counts = []
        avg_w_values = []
        avg_rms_values = []
        
        for cat in categories:
            cat_stats = stats.get(cat.lower(), {})
            total_counts.append(cat_stats.get('total', 0))
            passed_counts.append(cat_stats.get('passed', 0))
            failed_counts.append(cat_stats.get('failed', 0))
            avg_w_values.append(cat_stats.get('avg_w', 0))
            avg_rms_values.append(cat_stats.get('avg_rms', 0))
        
        # 创建分组柱状图
        x = np.arange(len(categories))
        width = 0.35
        
        ax.bar(x - width/2, passed_counts, width, label='通过', color='green', alpha=0.7)
        ax.bar(x + width/2, failed_counts, width, label='失败', color='red', alpha=0.7)
        
        ax.set_xlabel('数据类型')
        ax.set_ylabel('齿数')
        ax.set_title('波纹度分析统计对比')
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 添加数值标签
        for i, (passed, failed) in enumerate(zip(passed_counts, failed_counts)):
            ax.text(i - width/2, passed + 0.1, str(passed), ha='center', va='bottom')
            ax.text(i + width/2, failed + 0.1, str(failed), ha='center', va='bottom')


class ProfessionalOrderAnalysisChart:
    """专业阶次分析图表生成器"""
    
    def __init__(self, parent_window):
        self.parent_window = parent_window
        
    def create_professional_chart(self, order_analysis):
        """创建专业阶次分析图表"""
        from PyQt5.QtWidgets import QMdiSubWindow
        import datetime
        import os
        
        # 创建子窗口
        subwindow = QMdiSubWindow()
        subwindow.setWindowTitle("专业阶次分析")
        subwindow.setMinimumSize(1200, 800)
        
        # 创建图表
        fig = Figure(figsize=(15, 10), dpi=100)
        canvas = CustomFigureCanvas(fig)
        
        try:
            # 使用GridSpec创建复杂布局（6行1列）
            gs = fig.add_gridspec(6, 1, height_ratios=[0.4, 1.6, 1.6, 1.6, 1.6, 1.0], hspace=0.6)
            
            # 头部信息区域
            ax_header = fig.add_subplot(gs[0, 0])
            ax_header.axis('off')
            
            # 获取文件基本信息
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            file_name = os.path.basename(self.parent_window.current_file) if hasattr(self.parent_window, 'current_file') and self.parent_window.current_file else "未知文件"
            
            # 头部标题
            ax_header.text(0.02, 0.8, "专业阶次谱分析 (Professional Order Spectrum)", fontsize=12, fontweight='bold', 
                          color='red', transform=ax_header.transAxes)
            ax_header.text(0.98, 0.8, current_time, fontsize=10, ha='right', 
                          transform=ax_header.transAxes)
            ax_header.text(0.02, 0.4, f"文件: {file_name}", fontsize=10, 
                          transform=ax_header.transAxes)
            ax_header.text(0.02, 0.1, "评价方式: 高阶次分析", fontsize=10, 
                          transform=ax_header.transAxes)
            
            # 四个阶次谱图表区域
            section_titles = ["Profile right", "Profile left", "Helix right", "Helix left"]
            
            for i, title in enumerate(section_titles):
                ax = fig.add_subplot(gs[i+1, 0])
                ax.axis('off')
                
                # 绘制区域标题
                ax.text(0.02, 0.95, title, fontsize=11, fontweight='bold', 
                       transform=ax.transAxes, va='top')
                
                # 创建内部绘图区域
                inner_ax = ax.inset_axes([0.08, 0.15, 1.70, 1.75])
                
                # 获取数据并绘制
                data = self._get_section_data(order_analysis, i)
                
                if data is not None and len(data) > 0:
                    # 绘制阶次谱柱状图
                    orders = list(range(1, len(data) + 1))
                    
                    # 绘制柱状图
                    bars = inner_ax.bar(orders, data, width=0.8, color='blue', 
                                      edgecolor='darkblue', alpha=0.8)
                    
                    # 智能标签（避免重叠）
                    max_val = max(data)
                    if max_val > 0:
                        # 只显示最大的2个值
                        indexed_data = [(j+1, val) for j, val in enumerate(data)]
                        indexed_data.sort(key=lambda x: x[1], reverse=True)
                        
                        for j, (order, value) in enumerate(indexed_data[:2]):
                            if value > max_val * 0.1:  # 只显示大于最大值的10%的标签
                                inner_ax.text(order, value + max_val * 0.02, f'{value:.2f}', 
                                            ha='center', va='bottom', fontsize=8, fontweight='bold')
                    
                    # 设置坐标轴
                    inner_ax.set_xlabel('Order', fontsize=10)
                    inner_ax.set_ylabel('Amplitude', fontsize=10)
                    inner_ax.set_title(f'{title} Order Spectrum', fontsize=11, fontweight='bold')
                    inner_ax.grid(True, alpha=0.3)
                    inner_ax.set_xlim(0.5, len(data) + 0.5)
                else:
                    inner_ax.text(0.5, 0.5, "无数据", ha='center', va='center', 
                                transform=inner_ax.transAxes, fontsize=12, color='gray')
                    inner_ax.set_title(f'{title} Order Spectrum', fontsize=11, fontweight='bold')
            
            # 表格区域
            ax_table = fig.add_subplot(gs[5, 0])
            ax_table.axis('off')
            
            # 创建表格数据
            table_data = []
            table_data.append(['Section', 'Max Order', 'Max Amplitude', 'RMS'])
            
            for i, title in enumerate(section_titles):
                data = self._get_section_data(order_analysis, i)
                if data is not None and len(data) > 0:
                    max_order = data.index(max(data)) + 1
                    max_amplitude = max(data)
                    rms = (sum(x*x for x in data) / len(data)) ** 0.5
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
                    if i == 0:  # 表头
                        table[(i, j)].set_facecolor('#4CAF50')
                        table[(i, j)].set_text_props(weight='bold', color='white')
                    else:
                        table[(i, j)].set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')
            
            ax_table.set_title('Order Analysis Summary', fontsize=12, fontweight='bold', pad=20)
            
        except Exception as e:
            # 如果出错，显示错误信息
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, f"创建阶次分析图表时出错:\n{str(e)}", 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=12, color='red')
            ax.set_title("阶次分析错误")
            ax.axis('off')
        
        # 设置子窗口内容
        subwindow.setWidget(canvas)
        return subwindow
    
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