#!/usr/bin/env python3
"""
生成齿轮分析PDF报表
"""

import sys
import os
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

from gear_analysis_refactored.utils.file_parser import parse_mka_file

class PDFReportGenerator:
    """PDF报表生成器"""
    
    def __init__(self, mka_file_path):
        """初始化生成器"""
        self.mka_file_path = mka_file_path
        self.parsed_data = None
        self.gear_data = None
        self.analysis_results = {}
    
    def parse_data(self):
        """解析MKA文件数据"""
        try:
            print(f"1. 读取MKA文件: {self.mka_file_path}")
            self.parsed_data = parse_mka_file(self.mka_file_path)
            
            if self.parsed_data:
                # 提取齿轮基本数据
                self.gear_data = self.parsed_data.get('gear_data', {})
                return True
            return False
        except Exception as e:
            print(f"解析数据错误: {e}")
            return False
    
    def analyze_gear(self):
        """分析齿轮数据"""
        if not self.parsed_data:
            return False
        
        # 提取测量数据
        profile_data = self.parsed_data.get('profile_data', {})
        topography_data = self.parsed_data.get('topography_data', {})
        
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
        directions = {
            '左齿形': profile_data.get('left', {}),
            '右齿形': profile_data.get('right', {}),
            '左齿向': extract_flank_data_from_topography(topography_data, 'left'),
            '右齿向': extract_flank_data_from_topography(topography_data, 'right')
        }
        
        # 分析每个方向
        for direction_name, data_dict in directions.items():
            print(f"\n分析{direction_name}...")
            results = self._analyze_direction(data_dict)
            self.analysis_results[direction_name] = results
        
        return True
    
    def _analyze_direction(self, data_dict):
        """分析单个方向的数据"""
        if not data_dict:
            return []
        
        # 计算平均曲线
        avg_curve, _, _ = self._calculate_average_curve(data_dict)
        if avg_curve is None:
            return []
        
        # 使用迭代残差法计算频谱
        spectrum = self._iterative_residual_sine_fit(avg_curve)
        
        # 按幅值降序排序
        sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1][0], reverse=True)
        
        # 取前10个阶次
        results = []
        for i, (freq, (amp, a, b, c)) in enumerate(sorted_spectrum[:10], 1):
            results.append((i, freq, amp))
            print(f"  {i}. 阶次: {freq}, 幅值: {amp:.3f}μm")
        
        return results
    
    def _calculate_average_curve(self, data_dict):
        """计算平均曲线"""
        if not data_dict:
            return None, 0, 0
        
        all_curves = []
        eval_length = 0
        total_length = 0
        
        for tooth_num, values in data_dict.items():
            if values is None or len(values) == 0:
                continue
            
            vals = np.array(values, dtype=float)
            n_points = len(vals)
            total_length = n_points
            
            # 提取评价范围（20%-80%）
            idx_start = int(n_points * 0.2)
            idx_end = int(n_points * 0.8)
            eval_length = idx_end - idx_start
            
            if eval_length < 8:
                continue
            
            vals = vals[idx_start:idx_end]
            
            # 去趋势
            try:
                x = np.arange(len(vals))
                p = np.polyfit(x, vals, 1)
                trend = np.polyval(p, x)
                detrended = vals - trend
            except:
                detrended = vals - np.mean(vals)
            
            all_curves.append(detrended)
        
        if not all_curves:
            return None, 0, 0
        
        # 对齐所有曲线到相同长度
        min_len = min(len(c) for c in all_curves)
        if min_len < 8:
            return None, 0, 0
        
        aligned_curves = [c[:min_len] for c in all_curves]
        
        # 计算平均曲线
        avg_curve = np.mean(aligned_curves, axis=0)
        
        return avg_curve, min_len, total_length
    
    def _iterative_residual_sine_fit(self, curve_data, max_order=500, max_components=10):
        """使用迭代残差法进行正弦拟合频谱分析"""
        if curve_data is None or len(curve_data) < 8:
            return {}
        
        n = len(curve_data)
        
        # 生成时间坐标x轴（0到1秒，假设转速为1转/秒）
        x = np.linspace(0.0, 1.0, n, dtype=float)
        
        # 初始化残差信号为原始信号
        residual = np.array(curve_data, dtype=float)
        
        # 存储提取的频谱分量
        spectrum_results = {}
        
        # 生成候选频率值
        candidate_frequencies = list(range(1, max_order + 1))
        
        # 迭代提取最大频率分量
        for iteration in range(max_components):
            # 对每个候选频率进行正弦拟合
            frequency_amplitudes = {}
            
            for freq in candidate_frequencies:
                try:
                    # 直接使用freq作为频率值
                    frequency = float(freq)
                    
                    # 构建矩阵 A = [sin(2π*f*x), cos(2π*f*x), 1]
                    sin_x = np.sin(2.0 * np.pi * frequency * x)
                    cos_x = np.cos(2.0 * np.pi * frequency * x)
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
                    
                    # 检查幅值是否合理
                    max_reasonable_amplitude = 10.0
                    if amplitude > max_reasonable_amplitude:
                        continue
                    
                    # 存储拟合结果
                    frequency_amplitudes[freq] = (amplitude, a, b, c)
                    
                except Exception as e:
                    continue
            
            # 选择幅值最大的频率
            if not frequency_amplitudes:
                break
            
            best_frequency = max(frequency_amplitudes.keys(), key=lambda f: frequency_amplitudes[f][0])
            best_amplitude, a, b, c = frequency_amplitudes[best_frequency]
            
            # 检查是否找到有效的最大频率
            if best_frequency is None or best_amplitude < 0.02:
                break
            
            # 保存提取的频谱分量
            spectrum_results[best_frequency] = (best_amplitude, a, b, c)
            
            # 从残差信号中移除已提取的正弦波
            best_freq_float = float(best_frequency)
            fitted_wave = a * np.sin(2.0 * np.pi * best_freq_float * x) + b * np.cos(2.0 * np.pi * best_freq_float * x) + c
            residual = residual - fitted_wave
            
            # 检查残差信号是否已经足够小
            residual_rms = np.sqrt(np.mean(np.square(residual)))
            if residual_rms < 0.001:
                break
        
        return spectrum_results
    
    def generate_pdf(self, output_path):
        """生成PDF报表"""
        try:
            # 创建PDF文档
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            elements = []
            
            # 添加标题
            styles = getSampleStyleSheet()
            title = Paragraph("<b>齿轮分析报表</b>", styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 20))
            
            # 添加齿轮基本信息
            if self.gear_data:
                info_table_data = [
                    ['参数', '值'],
                    ['文件名', os.path.basename(self.mka_file_path)],
                    ['模数', f"{self.gear_data.get('module', 'N/A')}"],
                    ['齿数', f"{self.gear_data.get('teeth', 'N/A')}"],
                    ['压力角', f"{self.gear_data.get('pressure_angle', 'N/A')}°"],
                    ['螺旋角', f"{self.gear_data.get('helix_angle', 'N/A')}°"],
                    ['齿宽', f"{self.gear_data.get('width', 'N/A')}"],
                ]
                info_table = Table(info_table_data, colWidths=[6*cm, 10*cm])
                info_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(Paragraph("<b>齿轮基本信息</b>", styles['Heading2']))
                elements.append(info_table)
                elements.append(Spacer(1, 20))
            
            # 添加分析结果
            elements.append(Paragraph("<b>分析结果</b>", styles['Heading2']))
            elements.append(Spacer(1, 10))
            
            for direction, results in self.analysis_results.items():
                elements.append(Paragraph(f"<b>{direction}</b>", styles['Heading3']))
                if results:
                    table_data = [['排序', '阶次', '幅值(μm)']]
                    for rank, freq, amp in results:
                        table_data.append([str(rank), str(freq), f"{amp:.3f}"])
                    table = Table(table_data, colWidths=[2*cm, 4*cm, 6*cm])
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ]))
                    elements.append(table)
                else:
                    elements.append(Paragraph("无有效数据", styles['Normal']))
                elements.append(Spacer(1, 15))
            
            # 生成PDF
            doc.build(elements)
            print(f"\nPDF报表已生成: {output_path}")
            return True
        except Exception as e:
            print(f"生成PDF错误: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    if len(sys.argv) > 1:
        mka_file = sys.argv[1]
    else:
        mka_file = "263751-018-WAV.mka"
    
    # 创建生成器
    generator = PDFReportGenerator(mka_file)
    
    # 解析数据
    if not generator.parse_data():
        print("解析数据失败")
        return
    
    # 分析齿轮
    if not generator.analyze_gear():
        print("分析齿轮失败")
        return
    
    # 生成PDF
    output_path = f"gear_analysis_report_{os.path.basename(mka_file).replace('.mka', '')}.pdf"
    if generator.generate_pdf(output_path):
        print("PDF报表生成成功")
    else:
        print("PDF报表生成失败")

if __name__ == "__main__":
    main()
