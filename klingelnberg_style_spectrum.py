"""
克林贝格风格的波纹度频谱分析报告生成器
Klingelnberg-style ripple spectrum analysis report generator
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
from parse_mka_file import MKAParser
from klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport


class KlingelnbergStyleSpectrumReport:
    """克林贝格风格的频谱分析报告"""
    
    def __init__(self):
        self.analyzer = KlingelnbergRippleSpectrumReport()
    
    def _calculate_orders(self, teeth_count=87, max_order=6):
        """计算阶次序列"""
        orders = []
        for i in range(1, max_order + 1):
            orders.append(i)
        return orders
    
    def _extract_spectrum_data(self, data, teeth_count=87, max_order=6):
        """提取指定阶次的频谱数据"""
        # 计算频谱
        spectrum = self.analyzer._calculate_ripple_spectrum(np.array(data))
        
        # 计算目标阶次（1到max_order）
        target_orders = self._calculate_orders(teeth_count, max_order)
        
        # 提取每个阶次的振幅
        amplitudes = []
        for target_order in target_orders:
            # 找到最接近目标阶次的频谱成分
            closest = None
            min_diff = float('inf')
            
            for item in spectrum:
                diff = abs(item['order'] - target_order)
                if diff < min_diff:
                    min_diff = diff
                    closest = item
            
            if closest:
                amplitudes.append(closest['amplitude'])
            else:
                amplitudes.append(0.0)
        
        return target_orders, amplitudes
    
    def generate_report(self, output_path='klingelnberg_style_spectrum_updated.pdf'):
        """生成克林贝格风格的频谱分析报告"""
        # 读取MKA文件数据
        mka_file = '263751-018-WAV.mka'
        parser = MKAParser(mka_file)
        
        # 获取旋转图表数据
        combined_data = parser.get_combined_data(use_evaluation_range=True)
        
        # 提取四个曲线的数据
        datasets = {
            'Profile right': [],
            'Profile left': [],
            'Helix right': [],
            'Helix left': []
        }
        
        # 从combined_data中提取数据
        if 'profile_right' in combined_data:
            for angle, value in combined_data['profile_right']:
                datasets['Profile right'].append(value)
        
        if 'profile_left' in combined_data:
            for angle, value in combined_data['profile_left']:
                datasets['Profile left'].append(value)
        
        if 'flank_right' in combined_data:
            for angle, value in combined_data['flank_right']:
                datasets['Helix right'].append(value)
        
        if 'flank_left' in combined_data:
            for angle, value in combined_data['flank_left']:
                datasets['Helix left'].append(value)
        
        # 创建PDF报告
        with PdfPages(output_path) as pdf:
            # 创建页面
            fig = plt.figure(figsize=(8.27, 11.69), dpi=150)  # A4尺寸
            
            # 设置整体布局
            gs = gridspec.GridSpec(
                5, 1, 
                height_ratios=[0.15, 0.18, 0.18, 0.18, 0.31],
                hspace=0.3
            )
            
            # 1. 标题区域
            header_ax = fig.add_subplot(gs[0, 0])
            header_ax.axis('off')
            
            # 添加克林贝格标志
            header_ax.text(0.1, 0.8, '♦', fontsize=30, ha='center', va='center', transform=header_ax.transAxes)
            header_ax.text(0.1, 0.4, 'KLINGELNBERG', fontsize=12, fontweight='bold', ha='center', va='center', transform=header_ax.transAxes)
            
            # 添加分析信息
            info_text = "Analysis of ripple\n"
            info_text += f"Order no.: 263751-018-WAV\n"
            info_text += f"Drawing no.: 84-T3.2.47.02.76-G-WAV\n"
            info_text += f"Way of evaluation: High orders\n"
            
            header_ax.text(0.3, 0.8, info_text, fontsize=8, ha='left', va='top', transform=header_ax.transAxes)
            
            # 添加序列号和日期信息
            serial_text = f"Serial no.: 263751-018-WAV\n"
            serial_text += f"Part name:\n"
            serial_text += f"File: 263751-018-WAV\n"
            serial_text += f"z = 87"
            
            header_ax.text(0.7, 0.8, serial_text, fontsize=8, ha='left', va='top', transform=header_ax.transAxes)
            
            # 添加时间信息
            time_text = f"14.02.25\n"
            time_text += f"21:04:11"
            
            header_ax.text(0.9, 0.8, time_text, fontsize=8, ha='right', va='top', transform=header_ax.transAxes)
            
            # 2. 频谱图表区域
            teeth_count = 87
            max_order = 6
            
            # 颜色映射
            colors = {
                'Profile right': 'blue',
                'Profile left': 'red',
                'Helix right': 'green',
                'Helix left': 'magenta'
            }
            
            # 创建频谱图表
            spectrum_axes = []
            spectrum_data = {}
            
            for i, (title, data) in enumerate(datasets.items()):
                ax = fig.add_subplot(gs[i+1, 0])
                spectrum_axes.append(ax)
                
                if len(data) > 0:
                    # 提取频谱数据
                    orders, amplitudes = self._extract_spectrum_data(data, teeth_count, max_order)
                    
                    # 存储数据
                    spectrum_data[title] = {'orders': orders, 'amplitudes': amplitudes}
                    
                    # 绘制频谱柱状图
                    x_positions = np.arange(len(orders))
                    ax.bar(x_positions, amplitudes, color=colors[title], alpha=0.7)
                    
                    # 设置标题
                    ax.set_title(title, fontsize=10, fontweight='bold')
                    
                    # 设置X轴标签（阶次）
                    ax.set_xticks(x_positions)
                    ax.set_xticklabels([str(int(order)) for order in orders], fontsize=8)
                    
                    # 设置Y轴范围
                    max_amp = max(amplitudes) * 1.2 if amplitudes else 0.2
                    ax.set_ylim(0, max_amp)
                    
                    # 添加振幅值标签
                    for j, amp in enumerate(amplitudes):
                        if amp > 0:
                            ax.text(j, amp + max_amp * 0.05, f'{amp:.2f}', 
                                    ha='center', va='bottom', fontsize=7)
                    
                    # 添加参考线
                    ax.axhline(y=0, color='black', linewidth=0.5)
                    
                else:
                    ax.set_title(title, fontsize=10, fontweight='bold')
                    ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
                    
                # 隐藏右侧和顶部边框
                ax.spines['right'].set_visible(False)
                ax.spines['top'].set_visible(False)
            
            # 3. 表格区域
            table_ax = fig.add_subplot(gs[4, 0])
            table_ax.axis('off')
            
            # 构建表格数据
            table_data = []
            
            # 表头
            table_data.append(['', 'A', 'O', 'A', 'O', 'A', 'O', 'A', 'O', 'A', 'O', 'A', 'O'])
            # 添加说明
            table_ax.text(0.05, 0.95, 'A: Amplitude (μm), O: Order (Frequency)', fontsize=8, ha='left', va='top', transform=table_ax.transAxes)
            
            # 添加数据行
            for title, data in spectrum_data.items():
                row = [title]
                for i in range(len(data['amplitudes'])):
                    row.append(f"{data['amplitudes'][i]:.2f}")
                    row.append(str(data['orders'][i]))
                # 填充剩余列
                while len(row) < 13:
                    row.append('')
                table_data.append(row)
            
            # 创建表格
            table = table_ax.table(
                cellText=table_data,
                cellLoc='center',
                bbox=[0.05, 0.1, 0.9, 0.8]
            )
            
            # 设置表格样式
            table.auto_set_font_size(False)
            table.set_fontsize(7)
            
            # 设置表头样式
            for (row, col), cell in table.get_celld().items():
                cell.set_edgecolor('black')
                cell.set_linewidth(0.5)
                if row == 0:
                    cell.set_text_props(weight='bold')
                if col == 0:
                    cell.set_text_props(weight='bold')
            
            # 添加低通滤波器信息
            table_ax.text(0.95, 0.05, 'Low-pass filter RC', fontsize=8, ha='right', va='bottom', transform=table_ax.transAxes)
            
            # 添加比例尺
            table_ax.text(0.8, 0.95, '0.10 μm', fontsize=8, ha='left', va='top', transform=table_ax.transAxes)
            table_ax.text(0.8, 0.9, '100000:1', fontsize=8, ha='left', va='top', transform=table_ax.transAxes)
            
            # 添加转速信息
            table_ax.text(0.95, 0.8, 'rpm: 1.454', fontsize=8, ha='right', va='top', transform=table_ax.transAxes)
            table_ax.text(0.95, 0.75, 'lox:33.578', fontsize=8, ha='right', va='top', transform=table_ax.transAxes)
            table_ax.text(0.95, 0.7, 'lu:24.775', fontsize=8, ha='right', va='top', transform=table_ax.transAxes)
            
            # 调整布局
            plt.tight_layout(rect=[0, 0, 1, 0.98])
            
            # 添加页面到PDF
            pdf.savefig(fig, bbox_inches='tight')
            plt.close(fig)
        
        print(f"Klingelnberg-style spectrum report generated: {output_path}")
        return output_path


if __name__ == '__main__':
    """测试克林贝格风格频谱报告"""
    generator = KlingelnbergStyleSpectrumReport()
    generator.generate_report()
