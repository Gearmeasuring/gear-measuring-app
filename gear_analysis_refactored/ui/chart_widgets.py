"""
图表组件模块
提供各种数据可视化图表
"""
import numpy as np
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox
from PyQt5.QtCore import Qt

from gear_analysis_refactored.config.logging_config import logger
from ui.custom_canvas import CustomFigureCanvas


class ChartWidget(QWidget):
    """图表基础组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = CustomFigureCanvas(self.figure)
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.title_label = QLabel("图表")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        toolbar.addWidget(self.title_label)
        
        toolbar.addStretch()
        
        # 导出按钮
        export_btn = QPushButton("💾 导出图表")
        export_btn.clicked.connect(self.export_chart)
        toolbar.addWidget(export_btn)
        
        # 清除按钮
        clear_btn = QPushButton("🗑️ 清除")
        clear_btn.clicked.connect(self.clear_chart)
        toolbar.addWidget(clear_btn)
        
        layout.addLayout(toolbar)
        layout.addWidget(self.canvas)
    
    def set_title(self, title):
        """设置标题"""
        self.title_label.setText(title)
    
    def clear_chart(self):
        """清除图表"""
        self.figure.clear()
        self.canvas.draw()
        logger.info("图表已清除")
    
    def export_chart(self):
        """导出图表"""
        from PyQt5.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "保存图表",
            "",
            "PNG图片 (*.png);;PDF文件 (*.pdf);;所有文件 (*.*)"
        )
        
        if filename:
            try:
                self.figure.savefig(filename, dpi=300, bbox_inches='tight')
                logger.info(f"图表已保存: {filename}")
            except Exception as e:
                logger.exception(f"保存图表失败: {e}")


class ProfileCurveWidget(ChartWidget):
    """齿形曲线图表"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_title("📈 齿形曲线分析")
    
    def plot_data(self, data_dict, side='left', tooth_nums=None):
        """
        绘制齿形数据
        
        Args:
            data_dict: 数据字典 {tooth_num: [values]}
            side: 'left' 或 'right'
            tooth_nums: 要绘制的齿号列表，None表示全部
        """
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            if not data_dict:
                ax.text(0.5, 0.5, '暂无数据', 
                       ha='center', va='center', fontsize=14)
                self.canvas.draw()
                return
            
            # 确定要绘制的齿号
            if tooth_nums is None:
                tooth_nums = sorted(data_dict.keys())[:5]  # 默认前5个齿
            
            # 绘制每个齿的曲线
            for tooth_num in tooth_nums:
                if tooth_num in data_dict:
                    values = data_dict[tooth_num]
                    x = np.arange(len(values))
                    ax.plot(x, values, '-', label=f'齿{tooth_num}', alpha=0.7)
            
            side_text = "左侧" if side == 'left' else "右侧"
            ax.set_title(f'齿形曲线 - {side_text}', fontsize=12, pad=10)
            ax.set_xlabel('测量点', fontsize=10)
            ax.set_ylabel('偏差 (μm)', fontsize=10)
            ax.grid(True, linestyle='--', alpha=0.3)
            ax.legend(loc='best', fontsize=9)
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            logger.info(f"绘制齿形曲线: {side_text}, {len(tooth_nums)}个齿")
            
        except Exception as e:
            logger.exception(f"绘制齿形曲线失败: {e}")


class FlankCurveWidget(ChartWidget):
    """齿向曲线图表"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_title("📉 齿向曲线分析")
    
    def plot_data(self, data_dict, side='left', tooth_nums=None):
        """
        绘制齿向数据
        
        Args:
            data_dict: 数据字典 {tooth_num: [values]}
            side: 'left' 或 'right'
            tooth_nums: 要绘制的齿号列表，None表示全部
        """
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            if not data_dict:
                ax.text(0.5, 0.5, '暂无数据', 
                       ha='center', va='center', fontsize=14)
                self.canvas.draw()
                return
            
            # 确定要绘制的齿号
            if tooth_nums is None:
                tooth_nums = sorted(data_dict.keys())[:5]  # 默认前5个齿
            
            # 绘制每个齿的曲线
            for tooth_num in tooth_nums:
                if tooth_num in data_dict:
                    values = data_dict[tooth_num]
                    x = np.arange(len(values))
                    ax.plot(x, values, '-', label=f'齿{tooth_num}', alpha=0.7)
            
            side_text = "左侧" if side == 'left' else "右侧"
            ax.set_title(f'齿向曲线 - {side_text}', fontsize=12, pad=10)
            ax.set_xlabel('测量点', fontsize=10)
            ax.set_ylabel('偏差 (μm)', fontsize=10)
            ax.grid(True, linestyle='--', alpha=0.3)
            ax.legend(loc='best', fontsize=9)
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            logger.info(f"绘制齿向曲线: {side_text}, {len(tooth_nums)}个齿")
            
        except Exception as e:
            logger.exception(f"绘制齿向曲线失败: {e}")


class StatisticsChartWidget(ChartWidget):
    """统计图表组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_title("📊 统计分析图表")
    
    def plot_distribution(self, data_dict, side='left'):
        """
        绘制数据分布直方图
        
        Args:
            data_dict: 数据字典 {tooth_num: [values]}
            side: 'left' 或 'right'
        """
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            if not data_dict:
                ax.text(0.5, 0.5, '暂无数据', 
                       ha='center', va='center', fontsize=14)
                self.canvas.draw()
                return
            
            # 收集所有数据
            all_values = []
            for values in data_dict.values():
                all_values.extend(values)
            
            if not all_values:
                ax.text(0.5, 0.5, '暂无有效数据', 
                       ha='center', va='center', fontsize=14)
                self.canvas.draw()
                return
            
            # 绘制直方图
            n, bins, patches = ax.hist(all_values, bins=50, 
                                      alpha=0.7, color='skyblue', 
                                      edgecolor='black')
            
            # 添加统计信息
            mean_val = np.mean(all_values)
            std_val = np.std(all_values)
            
            ax.axvline(mean_val, color='red', linestyle='--', 
                      linewidth=2, label=f'平均值: {mean_val:.3f}μm')
            ax.axvline(mean_val + std_val, color='orange', 
                      linestyle='--', alpha=0.7, 
                      label=f'±σ: {std_val:.3f}μm')
            ax.axvline(mean_val - std_val, color='orange', 
                      linestyle='--', alpha=0.7)
            
            side_text = "左侧" if side == 'left' else "右侧"
            ax.set_title(f'数据分布 - {side_text}', fontsize=12, pad=10)
            ax.set_xlabel('偏差 (μm)', fontsize=10)
            ax.set_ylabel('频数', fontsize=10)
            ax.legend(loc='best', fontsize=9)
            ax.grid(True, alpha=0.3)
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            logger.info(f"绘制数据分布: {side_text}, {len(all_values)}个数据点")
            
        except Exception as e:
            logger.exception(f"绘制数据分布失败: {e}")
    
    def plot_box(self, data_dict):
        """
        绘制箱线图
        
        Args:
            data_dict: 数据字典 {tooth_num: [values]}
        """
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            if not data_dict:
                ax.text(0.5, 0.5, '暂无数据', 
                       ha='center', va='center', fontsize=14)
                self.canvas.draw()
                return
            
            # 准备数据
            tooth_nums = sorted(data_dict.keys())[:10]  # 最多10个齿
            data_list = []
            labels = []
            
            for tooth_num in tooth_nums:
                if tooth_num in data_dict and data_dict[tooth_num]:
                    data_list.append(data_dict[tooth_num])
                    labels.append(f'齿{tooth_num}')
            
            if not data_list:
                ax.text(0.5, 0.5, '暂无有效数据', 
                       ha='center', va='center', fontsize=14)
                self.canvas.draw()
                return
            
            # 绘制箱线图
            bp = ax.boxplot(data_list, labels=labels, patch_artist=True)
            
            # 美化箱线图
            for patch in bp['boxes']:
                patch.set_facecolor('lightblue')
                patch.set_alpha(0.7)
            
            ax.set_title('各齿偏差箱线图', fontsize=12, pad=10)
            ax.set_xlabel('齿号', fontsize=10)
            ax.set_ylabel('偏差 (μm)', fontsize=10)
            ax.grid(True, alpha=0.3, axis='y')
            
            # 旋转x轴标签
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            logger.info(f"绘制箱线图: {len(data_list)}个齿")
            
        except Exception as e:
            logger.exception(f"绘制箱线图失败: {e}")


class ComparisonChartWidget(ChartWidget):
    """对比图表组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_title("🔄 左右对比分析")
    
    def plot_comparison(self, left_data, right_data):
        """
        绘制左右齿面对比图
        
        Args:
            left_data: 左侧数据 {tooth_num: [values]}
            right_data: 右侧数据 {tooth_num: [values]}
        """
        try:
            self.figure.clear()
            
            # 创建2x1子图
            ax1 = self.figure.add_subplot(211)
            ax2 = self.figure.add_subplot(212)
            
            # 绘制左侧数据
            if left_data:
                tooth_nums = sorted(left_data.keys())[:3]
                for tooth_num in tooth_nums:
                    if tooth_num in left_data:
                        values = left_data[tooth_num]
                        x = np.arange(len(values))
                        ax1.plot(x, values, '-', label=f'齿{tooth_num}', alpha=0.7)
                
                ax1.set_title('左侧齿面', fontsize=11)
                ax1.set_ylabel('偏差 (μm)', fontsize=9)
                ax1.grid(True, linestyle='--', alpha=0.3)
                ax1.legend(loc='best', fontsize=8)
            else:
                ax1.text(0.5, 0.5, '暂无左侧数据', 
                        ha='center', va='center')
            
            # 绘制右侧数据
            if right_data:
                tooth_nums = sorted(right_data.keys())[:3]
                for tooth_num in tooth_nums:
                    if tooth_num in right_data:
                        values = right_data[tooth_num]
                        x = np.arange(len(values))
                        ax2.plot(x, values, '-', label=f'齿{tooth_num}', alpha=0.7)
                
                ax2.set_title('右侧齿面', fontsize=11)
                ax2.set_xlabel('测量点', fontsize=9)
                ax2.set_ylabel('偏差 (μm)', fontsize=9)
                ax2.grid(True, linestyle='--', alpha=0.3)
                ax2.legend(loc='best', fontsize=8)
            else:
                ax2.text(0.5, 0.5, '暂无右侧数据', 
                        ha='center', va='center')
            
            self.figure.tight_layout()
            self.canvas.draw()
            
            logger.info("绘制左右对比图")
            
        except Exception as e:
            logger.exception(f"绘制对比图失败: {e}")

