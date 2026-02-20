#!/usr/bin/env python3
"""
生成Klingelnberg格式的齿轮波纹频谱图表
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

from gear_analysis_refactored.utils.file_parser import parse_mka_file
from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum特斯特 import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings

class KlingelnbergSpectrumGenerator:
    """
    Klingelnberg格式的齿轮波纹频谱图表生成器
    """
    
    def __init__(self):
        """
        初始化频谱生成器
        """
        self.settings = RippleSpectrumSettings()
        self.ripple_report = KlingelnbergRippleSpectrumReport(self.settings)
    
    def _calculate_spectrum(self, data_dict, teeth_count=87, max_order=6):
        """
        计算ZE倍数阶次的频谱
        
        Args:
            data_dict: {齿号: [数据点]}
            teeth_count: 齿数
            max_order: 最大ZE倍数
            
        Returns:
            dict: {频率: 幅值}
        """
        if not data_dict:
            return {}
        
        # 计算平均曲线
        avg_curve = self.ripple_report._calculate_average_curve(data_dict)
        if avg_curve is None:
            return {}
        
        # 生成ZE倍数的候选频率
        spectrum_results = {}
        n = len(avg_curve)
        x = np.linspace(0.0, 1.0, n, dtype=float)
        residual = np.array(avg_curve, dtype=float)
        
        for multiplier in range(1, max_order + 1):
            freq = teeth_count * multiplier
            try:
                # 构建矩阵 A = [sin(2π*f*x), cos(2π*f*x), 1]
                sin_x = np.sin(2.0 * np.pi * float(freq) * x)
                cos_x = np.cos(2.0 * np.pi * float(freq) * x)
                A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
                
                # 求解最小二乘
                try:
                    coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
                    a, b, c = coeffs
                except Exception as e:
                    # 如果最小二乘失败，使用备选方法
                    a = 2.0 * np.mean(residual * sin_x)
                    b = 2.0 * np.mean(residual * cos_x)
                    c = np.mean(residual)
                
                # 计算幅值：A = sqrt(a^2 + b^2)
                amplitude = float(np.sqrt(a * a + b * b))
                spectrum_results[freq] = amplitude
            except Exception as e:
                spectrum_results[freq] = 0.0
        
        return spectrum_results
    
    def create_spectrum_chart(self, output_pdf):
        """
        创建Klingelnberg格式的频谱图表
        
        Args:
            output_pdf: 输出PDF文件名
        """
        # MKA文件路径
        mka_file_path = "263751-018-WAV.mka"
        
        try:
            # 从MKA文件读取数据
            print(f"1. 读取MKA文件: {mka_file_path}")
            parsed_data = parse_mka_file(mka_file_path)
            
            if parsed_data:
                # 提取齿轮基本数据
                gear_data = parsed_data.get('gear_data', {})
                teeth_count = gear_data.get('teeth', 87)
                
                # 提取测量数据
                profile_data = parsed_data.get('profile_data', {})
                topography_data = parsed_data.get('topography_data', {})
                
                # 从topography_data中提取齿向数据
                def extract_flank_data_from_topography(topography_data, side):
                    """从topography_data中提取齿向数据"""
                    flank_data = {}
                    for tooth_num, tooth_data in topography_data.items():
                        if side in tooth_data:
                            flank_lines = tooth_data[side].get('flank_lines', {})
                            if flank_lines:
                                # 取中间位置的齿向数据（idx=2）
                                if 2 in flank_lines:
                                    flank_data[tooth_num] = flank_lines[2].get('values', [])
                                elif 1 in flank_lines:
                                    flank_data[tooth_num] = flank_lines[1].get('values', [])
                                elif 3 in flank_lines:
                                    flank_data[tooth_num] = flank_lines[3].get('values', [])
                    return flank_data
                
                # 获取各个方向的数据
                profile_left = profile_data.get('left', {})
                profile_right = profile_data.get('right', {})
                
                # 从topography_data中提取齿向数据
                helix_left = extract_flank_data_from_topography(topography_data, 'left')
                helix_right = extract_flank_data_from_topography(topography_data, 'right')
                
                # 计算各个方向的频谱
                print("2. 计算各个方向的频谱")
                spectrum_profile_left = self._calculate_spectrum(profile_left, teeth_count)
                spectrum_profile_right = self._calculate_spectrum(profile_right, teeth_count)
                spectrum_helix_left = self._calculate_spectrum(helix_left, teeth_count)
                spectrum_helix_right = self._calculate_spectrum(helix_right, teeth_count)
                
                # 创建图表
                print("3. 创建Klingelnberg格式的频谱图表")
                
                # 创建A4横向页面
                fig = plt.figure(figsize=(11.69, 8.27), dpi=150)
                
                # 布局：标题、四个频谱图表、数据表格
                gs = plt.GridSpec(6, 1, figure=fig, height_ratios=[0.12, 0.18, 0.18, 0.18, 0.18, 0.16], hspace=0.25)
                
                # 1. 标题部分
                title_ax = fig.add_subplot(gs[0, 0])
                title_ax.axis('off')
                
                # 添加Klingelnberg标志
                title_ax.text(0.1, 0.8, "KLINGELNBERG", ha='left', fontsize=12, fontweight='bold', color='blue')
                
                # 添加标题和基本信息
                title_ax.text(0.5, 0.8, "Analysis of ripple", ha='center', fontsize=14, fontweight='bold')
                title_ax.text(0.2, 0.6, f"Order no.: 263751-018-WAV", fontsize=8)
                title_ax.text(0.2, 0.4, f"Drawing no.: 84-T3.2.47.02.76-G-WAV", fontsize=8)
                title_ax.text(0.8, 0.6, f"Serial no.: 263751-018-WAV", fontsize=8, ha='right')
                title_ax.text(0.8, 0.4, f"Date: {datetime.now().strftime('%d.%m.%y')}", fontsize=8, ha='right')
                title_ax.text(0.8, 0.2, f"z={teeth_count}", fontsize=10, fontweight='bold', ha='right')
                
                # 添加Spectrum of the ripple标题
                title_ax.text(0.5, 0.1, "Spectrum of the ripple", ha='center', fontsize=16, fontweight='bold')
                
                # 2. Profile right图表
                profile_right_ax = fig.add_subplot(gs[1, 0])
                self._plot_spectrum_bar(profile_right_ax, "Profile right", spectrum_profile_right, teeth_count)
                
                # 3. Profile left图表
                profile_left_ax = fig.add_subplot(gs[2, 0])
                self._plot_spectrum_bar(profile_left_ax, "Profile left", spectrum_profile_left, teeth_count)
                
                # 4. Helix right图表
                helix_right_ax = fig.add_subplot(gs[3, 0])
                self._plot_spectrum_bar(helix_right_ax, "Helix right", spectrum_helix_right, teeth_count)
                
                # 5. Helix left图表
                helix_left_ax = fig.add_subplot(gs[4, 0])
                self._plot_spectrum_bar(helix_left_ax, "Helix left", spectrum_helix_left, teeth_count)
                
                # 6. 数据表格
                table_ax = fig.add_subplot(gs[5, 0])
                self._create_data_table(table_ax, {
                    'Profile right': spectrum_profile_right,
                    'Profile left': spectrum_profile_left,
                    'Helix right': spectrum_helix_right,
                    'Helix left': spectrum_helix_left
                }, teeth_count)
                
                # 保存到PDF
                fig.savefig(output_pdf, orientation='landscape', bbox_inches='tight')
                plt.close(fig)
                
                print(f"4. 图表已保存为: {output_pdf}")
                
                # 显示计算结果
                print("\n=== 计算结果 ===")
                print("Profile right:")
                for freq, amp in spectrum_profile_right.items():
                    print(f"  {freq}: {amp:.3f}μm")
                print("\nProfile left:")
                for freq, amp in spectrum_profile_left.items():
                    print(f"  {freq}: {amp:.3f}μm")
                print("\nHelix right:")
                for freq, amp in spectrum_helix_right.items():
                    print(f"  {freq}: {amp:.3f}μm")
                print("\nHelix left:")
                for freq, amp in spectrum_helix_left.items():
                    print(f"  {freq}: {amp:.3f}μm")
                
            else:
                print("无法从MKA文件读取数据")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    def _plot_spectrum_bar(self, ax, title, spectrum, teeth_count):
        """
        绘制频谱柱状图
        
        Args:
            ax: matplotlib轴对象
            title: 图表标题
            spectrum: 频谱数据 {频率: 幅值}
            teeth_count: 齿数
        """
        # 生成ZE倍数的频率
        frequencies = [teeth_count * i for i in range(1, 7)]
        amplitudes = [spectrum.get(f, 0.0) for f in frequencies]
        
        # 设置图表
        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.set_xlabel('Frequency (ZE multiples)')
        ax.set_ylabel('Amplitude (μm)')
        
        # 绘制柱状图
        x_pos = np.arange(len(frequencies))
        ax.bar(x_pos, amplitudes, width=0.6, color='blue')
        
        # 设置x轴标签
        ax.set_xticks(x_pos)
        ax.set_xticklabels([str(f) for f in frequencies], fontsize=8)
        
        # 在柱状图上显示幅值
        for i, amp in enumerate(amplitudes):
            if amp > 0:
                ax.text(x_pos[i], amp + 0.005, f'{amp:.3f}', ha='center', fontsize=7)
        
        # 设置y轴范围
        max_amp = max(amplitudes) if amplitudes else 0.2
        ax.set_ylim(0, max_amp * 1.2)
        
        # 添加网格
        ax.grid(axis='y', linestyle=':', alpha=0.5)
    
    def _create_data_table(self, ax, spectrum_dict, teeth_count):
        """
        创建数据表格
        
        Args:
            ax: matplotlib轴对象
            spectrum_dict: {方向: {频率: 幅值}}
            teeth_count: 齿数
        """
        ax.axis('off')
        
        # 生成ZE倍数的频率
        frequencies = [teeth_count * i for i in range(1, 7)]
        
        # 准备表格数据
        table_data = []
        
        # 添加表头
        header = ['', '87', '174', '261', '348', '435', '522']
        table_data.append(header)
        
        # 添加数据行
        for direction, spectrum in spectrum_dict.items():
            row = [direction]
            for freq in frequencies:
                amp = spectrum.get(freq, 0.0)
                row.append(f'{amp:.3f}')
            table_data.append(row)
        
        # 创建表格
        table = ax.table(cellText=table_data, cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.2)

def main():
    """
    主函数：生成Klingelnberg格式的频谱图表
    """
    print("=== 生成Klingelnberg格式的频谱图表 ===")
    
    generator = KlingelnbergSpectrumGenerator()
    output_pdf = "klingelnberg_spectrum_chart.pdf"
    generator.create_spectrum_chart(output_pdf)
    
    print("\n=== 图表生成完成 ===")
    print(f"频谱图表已保存为: {output_pdf}")

if __name__ == "__main__":
    main()
