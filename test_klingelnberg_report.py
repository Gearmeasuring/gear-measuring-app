#!/usr/bin/env python3
"""
生成Klingelnberg格式的齿轮偏差分析报表
复刻图2的报表格式，显示所有评价区域内的曲线、第一阶正弦拟合线、幅值和频率
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

from gear_analysis_refactored.utils.file_parser import parse_mka_file
from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum特斯特 import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings

class KlingelnbergDeviationReport:
    """
    Klingelnberg格式的齿轮偏差分析报表生成器
    """
    
    def __init__(self):
        """
        初始化报表生成器
        """
        self.settings = RippleSpectrumSettings()
        self.ripple_report = KlingelnbergRippleSpectrumReport(self.settings)
    
    def _calculate_order_fit(self, curve_data, order=1):
        """
        计算指定阶次的正弦拟合
        
        Args:
            curve_data: 曲线数据
            order: 阶次
            
        Returns:
            tuple: (amplitude, frequency, phase, fitted_curve)
        """
        if curve_data is None:
            return 0.0, float(order), 0.0, None
        
        # 确保curve_data是numpy数组
        y = np.array(curve_data, dtype=float)
        
        if len(y) < 8:
            return 0.0, float(order), 0.0, None
        
        # 生成时间坐标x轴
        n = len(y)
        x = np.linspace(0.0, 1.0, n, dtype=float)
        
        # 去趋势
        try:
            p = np.polyfit(x, y, 1)
            trend = np.polyval(p, x)
            y_detrended = y - trend
        except:
            y_detrended = y - np.mean(y)
        
        # 计算指定阶次的正弦拟合
        frequency = float(order)
        
        # 构建矩阵 A = [sin(2π*f*x), cos(2π*f*x), 1]
        sin_x = np.sin(2.0 * np.pi * frequency * x)
        cos_x = np.cos(2.0 * np.pi * frequency * x)
        A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
        
        # 求解最小二乘
        try:
            coeffs, _, _, _ = np.linalg.lstsq(A, y_detrended, rcond=None)
            a, b, c = coeffs
        except Exception as e:
            # 如果最小二乘失败，使用备选方法
            a = 2.0 * np.mean(y_detrended * sin_x)
            b = 2.0 * np.mean(y_detrended * cos_x)
            c = np.mean(y_detrended)
        
        # 计算幅值：A = sqrt(a^2 + b^2)
        amplitude = float(np.sqrt(a * a + b * b))
        
        # 计算相位
        phase = float(np.arctan2(b, a))
        
        # 生成拟合曲线
        fitted_curve = a * sin_x + b * cos_x + c
        
        return amplitude, frequency, phase, fitted_curve
    
    def _calculate_first_order_fit(self, curve_data):
        """
        计算第一阶正弦拟合
        
        Args:
            curve_data: 曲线数据
            
        Returns:
            tuple: (amplitude, frequency, phase, fitted_curve)
        """
        return self._calculate_order_fit(curve_data, order=1)
    
    def _get_all_curves_in_evaluation_region(self, data_dict, eval_markers=None):
        """
        获取所有齿在评价区域内的曲线
        
        Args:
            data_dict: {齿号: [数据点]}
            eval_markers: 评价范围标记点
            
        Returns:
            list: 所有齿的评价区域曲线
        """
        all_curves = []
        
        for tooth_num, values in data_dict.items():
            if values is None or len(values) == 0:
                continue
            
            vals = np.array(values, dtype=float)
            
            # 提取评价范围
            if eval_markers and len(eval_markers) == 4:
                start_meas, start_eval, end_eval, end_meas = eval_markers
                n_points = len(vals)
                total_len = abs(end_meas - start_meas)
                
                if total_len == 0:
                    idx_start = int(n_points * 0.2)
                    idx_end = int(n_points * 0.8)
                else:
                    dist_to_start = abs(start_eval - start_meas)
                    dist_to_end = abs(end_eval - start_meas)
                    idx_start = int(n_points * (dist_to_start / total_len))
                    idx_end = int(n_points * (dist_to_end / total_len))
            else:
                # 使用默认范围（20%-80%）
                n_points = len(vals)
                idx_start = int(n_points * 0.2)
                idx_end = int(n_points * 0.8)
            
            # 确保索引在有效范围内
            idx_start = max(0, min(idx_start, len(vals) - 1))
            idx_end = max(0, min(idx_end, len(vals) - 1))
            
            # 确保评价范围至少有8个点
            if idx_end <= idx_start + 7:
                continue
            
            # 提取评价范围数据
            eval_curve = vals[idx_start:idx_end]
            
            # 去趋势
            try:
                x = np.arange(len(eval_curve))
                p = np.polyfit(x, eval_curve, 1)
                trend = np.polyval(p, x)
                detrended = eval_curve - trend
            except:
                detrended = eval_curve - np.mean(eval_curve)
            
            all_curves.append(detrended)
        
        return all_curves
    
    def _plot_profile_helix_section(self, ax, title, data_dict, eval_markers=None, is_profile=True, order=1):
        """
        绘制齿形或齿向部分
        
        Args:
            ax: matplotlib轴对象
            title: 标题
            data_dict: 数据字典
            eval_markers: 评价范围标记点
            is_profile: 是否为齿形数据
            order: 阶次
        """
        ax.set_title(title, fontsize=10, fontweight='bold', pad=5)
        
        # 获取所有齿在评价区域内的曲线
        all_curves = self._get_all_curves_in_evaluation_region(data_dict, eval_markers)
        
        if not all_curves:
            ax.text(0.5, 0.5, "No Data", ha='center', va='center', transform=ax.transAxes)
            return 0.0, float(order)
        
        # 对齐所有曲线到相同长度
        min_len = min(len(c) for c in all_curves)
        if min_len < 8:
            ax.text(0.5, 0.5, "Insufficient Data", ha='center', va='center', transform=ax.transAxes)
            return 0.0, float(order)
        
        aligned_curves = [c[:min_len] for c in all_curves]
        
        # 生成x轴
        x = np.linspace(0, 1, min_len)
        
        # 绘制所有曲线（红色）
        for curve in aligned_curves:
            ax.plot(x, curve, color='red', linewidth=0.5, alpha=0.6)
        
        # 计算平均曲线
        avg_curve = np.mean(aligned_curves, axis=0)
        
        # 计算指定阶次的正弦拟合
        amplitude, frequency, phase, fitted_curve = self._calculate_order_fit(avg_curve, order=order)
        
        # 绘制指定阶次的正弦拟合线（蓝色）
        if fitted_curve is not None:
            ax.plot(x, fitted_curve, color='blue', linewidth=1.5)
        
        # 添加比例尺
        if is_profile:
            ax.text(0.5, 0.9, '2.000 mm', ha='center', transform=ax.transAxes, fontsize=8)
        else:
            ax.text(0.5, 0.9, '1.500 mm', ha='center', transform=ax.transAxes, fontsize=8)
        ax.text(0.5, 0.85, '1.0 μm', ha='center', transform=ax.transAxes, fontsize=8)
        ax.text(0.5, 0.8, '10000:1', ha='center', transform=ax.transAxes, fontsize=8)
        
        # 设置坐标轴
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.5, 0.5)  # 适当调整y轴范围
        ax.grid(True, linestyle=':', alpha=0.5)
        
        return amplitude, frequency
    
    def create_klingelnberg_report(self, output_pdf, measurement_data, order=1):
        """
        创建Klingelnberg格式的偏差分析报表
        
        Args:
            output_pdf: PdfPages对象
            measurement_data: 测量数据对象
            order: 阶次
        """
        # 获取基本信息
        basic_info = measurement_data.basic_info
        teeth = getattr(basic_info, 'teeth', 87)
        order_no = getattr(basic_info, 'order_no', '263751-018-WAV')
        program = getattr(basic_info, 'program', '263751-018-WAV')
        
        # 处理左右齿面的齿形和齿向数据
        data_sets = [
            ('left', measurement_data.profile_data, measurement_data.flank_data),
            ('right', measurement_data.profile_data_right, measurement_data.flank_data_right)
        ]
        
        for side, profile_data, flank_data in data_sets:
            if not profile_data or not flank_data:
                continue
                
            # 创建A4横向页面
            fig = plt.figure(figsize=(11.69, 8.27), dpi=150)
            
            # 布局：标题、齿形部分、齿向部分、数据表格
            gs = plt.GridSpec(3, 1, figure=fig, height_ratios=[0.1, 0.45, 0.45], hspace=0.2)
            
            # 1. 标题部分
            title_ax = fig.add_subplot(gs[0, 0])
            title_ax.axis('off')
            
            # 添加Klingelnberg标志
            title_ax.text(0.1, 0.8, "KLINGELNBERG", ha='left', fontsize=12, fontweight='bold', color='blue')
            
            # 添加标题和基本信息
            title_ax.text(0.5, 0.8, f"Analysis of deviations - {side.capitalize()} Flank (Order {order})", ha='center', fontsize=14, fontweight='bold')
            title_ax.text(0.2, 0.6, f"Drawing no.: {getattr(basic_info, 'drawing_no', '84-T3.2.47.02.76-G-WAV')}", fontsize=8)
            title_ax.text(0.2, 0.4, f"Teeth: {teeth}", fontsize=8)
            title_ax.text(0.8, 0.6, f"Serial no.: {order_no}", fontsize=8, ha='right')
            title_ax.text(0.8, 0.4, f"File: {program}", fontsize=8, ha='right')
            title_ax.text(0.8, 0.2, f"Date: {datetime.now().strftime('%d.%m.%y')}", fontsize=8, ha='right')
            
            # 添加齿轮参数
            title_ax.text(0.5, 0.1, f"z={teeth} mn=1.8590 sn=2.4474 αn=18.6000 βo=25.3000", ha='center', fontsize=8)
            
            # 2. 齿形部分
            profile_ax = fig.add_subplot(gs[1, 0])
            
            # 绘制齿形部分
            profile_amplitude, profile_frequency = self._plot_profile_helix_section(
                profile_ax, f"Profile without actual modifications - {side.capitalize()}", 
                profile_data, None, is_profile=True, order=order
            )
            
            # 3. 齿向部分
            helix_ax = fig.add_subplot(gs[2, 0])
            
            # 绘制齿向部分
            helix_amplitude, helix_frequency = self._plot_profile_helix_section(
                helix_ax, f"Helix without actual modifications - {side.capitalize()}", 
                flank_data, None, is_profile=False, order=order
            )
            
            # 4. 添加数据表格
            # 在底部添加数据表格
            table_ax = fig.add_axes([0.1, 0.05, 0.8, 0.08])
            table_ax.axis('off')
            
            # 表格数据
            table_data = [
                ['', f'A{order}', f'O({order})'],
                ['Profile', f'{profile_amplitude:.3f}', f'{int(profile_frequency)}'],
                ['Helix', f'{helix_amplitude:.3f}', f'{int(helix_frequency)}']
            ]
            
            # 创建表格
            table = table_ax.table(cellText=table_data, cellLoc='center', loc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.scale(1, 1.5)
            
            # 保存到PDF
            output_pdf.savefig(fig, orientation='landscape')
            plt.close(fig)

def analyze_orders_until_threshold(report_generator, measurement_data, threshold=0.02, max_orders=100):
    """
    分析阶数直到幅值小于阈值
    
    Args:
        report_generator: 报表生成器对象
        measurement_data: 测量数据对象
        threshold: 幅值阈值
        max_orders: 最大分析阶数
        
    Returns:
        dict: {side: [(order, amplitude), ...]}
    """
    print(f"\n=== 分析阶数直到幅值小于 {threshold}μm ===")
    
    results = {
        'left': [],
        'right': []
    }
    
    # 分析左齿面
    print("\n分析左齿面...")
    left_amplitude_above_threshold = True
    order = 1
    
    while left_amplitude_above_threshold and order <= max_orders:
        try:
            all_curves = report_generator._get_all_curves_in_evaluation_region(measurement_data.profile_data)
            if all_curves:
                min_len = min(len(c) for c in all_curves)
                if min_len >= 8:
                    aligned_curves = [c[:min_len] for c in all_curves]
                    avg_curve = np.mean(aligned_curves, axis=0)
                    amplitude, frequency, phase, fitted_curve = report_generator._calculate_order_fit(avg_curve, order=order)
                    
                    if amplitude >= threshold:
                        results['left'].append((order, amplitude))
                        print(f"  左齿面第{order}阶幅值: {amplitude:.4f}μm (≥ {threshold}μm)")
                    else:
                        print(f"  左齿面第{order}阶幅值: {amplitude:.4f}μm (< {threshold}μm，停止分析)")
                        left_amplitude_above_threshold = False
                else:
                    print(f"  左齿面第{order}阶数据不足，停止分析")
                    left_amplitude_above_threshold = False
            else:
                print(f"  左齿面第{order}阶无数据，停止分析")
                left_amplitude_above_threshold = False
        except Exception as e:
            print(f"  左齿面第{order}阶分析出错: {e}")
            left_amplitude_above_threshold = False
        
        order += 1
    
    # 分析右齿面
    print("\n分析右齿面...")
    right_amplitude_above_threshold = True
    order = 1
    
    while right_amplitude_above_threshold and order <= max_orders:
        try:
            all_curves = report_generator._get_all_curves_in_evaluation_region(measurement_data.profile_data_right)
            if all_curves:
                min_len = min(len(c) for c in all_curves)
                if min_len >= 8:
                    aligned_curves = [c[:min_len] for c in all_curves]
                    avg_curve = np.mean(aligned_curves, axis=0)
                    amplitude, frequency, phase, fitted_curve = report_generator._calculate_order_fit(avg_curve, order=order)
                    
                    if amplitude >= threshold:
                        results['right'].append((order, amplitude))
                        print(f"  右齿面第{order}阶幅值: {amplitude:.4f}μm (≥ {threshold}μm)")
                    else:
                        print(f"  右齿面第{order}阶幅值: {amplitude:.4f}μm (< {threshold}μm，停止分析)")
                        right_amplitude_above_threshold = False
                else:
                    print(f"  右齿面第{order}阶数据不足，停止分析")
                    right_amplitude_above_threshold = False
            else:
                print(f"  右齿面第{order}阶无数据，停止分析")
                right_amplitude_above_threshold = False
        except Exception as e:
            print(f"  右齿面第{order}阶分析出错: {e}")
            right_amplitude_above_threshold = False
        
        order += 1
    
    return results

def main():
    """
    主函数：生成Klingelnberg格式的偏差分析报表
    """
    print("=== 生成Klingelnberg格式的偏差分析报表 ===")
    
    # MKA文件路径
    mka_file_path = "263751-018-WAV.mka"
    
    try:
        # 从MKA文件读取数据
        print(f"1. 读取MKA文件: {mka_file_path}")
        from gear_analysis_refactored.utils.file_parser import parse_mka_file
        parsed_data = parse_mka_file(mka_file_path)
        
        if parsed_data:
            # 创建简化的MeasurementData对象
            class MockBasicInfo:
                def __init__(self, **kwargs):
                    for key, value in kwargs.items():
                        setattr(self, key, value)
            
            class MockMeasurementData:
                def __init__(self, basic_info, profile_data_left, flank_data_left, profile_data_right, flank_data_right):
                    self.basic_info = basic_info
                    self.profile_data = profile_data_left
                    self.flank_data = flank_data_left
                    self.profile_data_right = profile_data_right
                    self.flank_data_right = flank_data_right
            
            # 提取齿轮基本数据
            gear_data = parsed_data.get('gear_data', {})
            teeth_count = gear_data.get('teeth', 87)
            
            # 提取测量数据
            profile_data = parsed_data.get('profile_data', {})
            topography_data = parsed_data.get('topography_data', {})
            
            # 打印调试信息
            print(f"\n调试信息:")
            print(f"  profile_data 类型: {type(profile_data)}")
            print(f"  left 齿形数据长度: {len(profile_data.get('left', {}))}")
            print(f"  right 齿形数据长度: {len(profile_data.get('right', {}))}")
            print(f"  topography_data 类型: {type(topography_data)}")
            print(f"  topography_data 包含的齿数: {len(topography_data)}")
            
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
            
            print(f"  从topography_data提取的左齿向数据长度: {len(helix_left)}")
            print(f"  从topography_data提取的右齿向数据长度: {len(helix_right)}")
            
            # 创建基本信息对象
            mock_basic_info = MockBasicInfo(
                teeth=teeth_count,
                drawing_no="84-T3.2.47.02.76-G-WAV",
                order_no="263751-018-WAV",
                program="263751-018-WAV",
                profile_markers_left=None,
                profile_markers_right=None,
                lead_markers_left=None,
                lead_markers_right=None
            )
            
            # 创建报表生成器
            report_generator = KlingelnbergDeviationReport()
            
            # 生成1到10阶的PDF报表
            print("2. 生成1到10阶的Klingelnberg格式PDF报表")
            
            # 创建测量数据对象，包含左右齿面的齿形和齿向数据
            mock_measurement_data = MockMeasurementData(
                basic_info=mock_basic_info,
                profile_data_left=profile_left,    # 左齿形数据
                flank_data_left=helix_left,        # 左齿向数据
                profile_data_right=profile_right,  # 右齿形数据
                flank_data_right=helix_right       # 右齿向数据
            )
            
            # 存储每个阶次的幅值数据
            order_amplitudes = []
            
            # 循环生成1到10阶的报表
            for order in range(1, 11):
                print(f"  生成第{order}阶报表...")
                pdf_filename = f'klingelnberg_deviation_report_order{order}.pdf'
                
                try:
                    with PdfPages(pdf_filename) as pdf:
                        # 保存create_klingelnberg_report方法的返回值，以便获取幅值数据
                        # 注意：需要修改create_klingelnberg_report方法，使其返回幅值数据
                        report_generator.create_klingelnberg_report(pdf, mock_measurement_data, order=order)
                    print(f"  第{order}阶报表已保存为: {pdf_filename}")
                except PermissionError:
                    print(f"  警告: 无法创建文件 {pdf_filename}，可能被其他程序占用")
                except Exception as e:
                    print(f"  错误: 生成第{order}阶报表时出错: {e}")
            
            print("\n=== 报表生成完成 ===")
            print("已生成1到10阶的PDF报表文件")
            
            # 由于create_klingelnberg_report方法没有返回幅值数据，我们需要直接计算每个阶次的幅值
            print("\n=== 计算并排序各阶次幅值 ===")
            
            # 计算左齿面每个阶次的幅值
            print("\n=== 计算并排序左齿面各阶次幅值 ===")
            left_order_amplitudes = []
            for order in range(1, 11):
                try:
                    # 使用左侧齿形数据进行计算
                    all_curves = report_generator._get_all_curves_in_evaluation_region(mock_measurement_data.profile_data)
                    if all_curves:
                        min_len = min(len(c) for c in all_curves)
                        if min_len >= 8:
                            aligned_curves = [c[:min_len] for c in all_curves]
                            avg_curve = np.mean(aligned_curves, axis=0)
                            amplitude, frequency, phase, fitted_curve = report_generator._calculate_order_fit(avg_curve, order=order)
                            left_order_amplitudes.append((order, amplitude))
                            print(f"  第{order}阶幅值: {amplitude:.4f}μm")
                except Exception as e:
                    print(f"  错误: 计算左齿面第{order}阶幅值时出错: {e}")
            
            # 计算右齿面每个阶次的幅值
            print("\n=== 计算并排序右齿面各阶次幅值 ===")
            right_order_amplitudes = []
            for order in range(1, 11):
                try:
                    # 使用右侧齿形数据进行计算
                    all_curves = report_generator._get_all_curves_in_evaluation_region(mock_measurement_data.profile_data_right)
                    if all_curves:
                        min_len = min(len(c) for c in all_curves)
                        if min_len >= 8:
                            aligned_curves = [c[:min_len] for c in all_curves]
                            avg_curve = np.mean(aligned_curves, axis=0)
                            amplitude, frequency, phase, fitted_curve = report_generator._calculate_order_fit(avg_curve, order=order)
                            right_order_amplitudes.append((order, amplitude))
                            print(f"  第{order}阶幅值: {amplitude:.4f}μm")
                except Exception as e:
                    print(f"  错误: 计算右齿面第{order}阶幅值时出错: {e}")
            
            # 按幅值降序排序左齿面
            if left_order_amplitudes:
                left_order_amplitudes.sort(key=lambda x: x[1], reverse=True)
                print("\n=== 左齿面按幅值降序排序 ===")
                for i, (order, amplitude) in enumerate(left_order_amplitudes, 1):
                    print(f"  {i}. 第{order}阶: {amplitude:.4f}μm")
            else:
                print("\n无法计算左齿面幅值数据")
            
            # 按幅值降序排序右齿面
            if right_order_amplitudes:
                right_order_amplitudes.sort(key=lambda x: x[1], reverse=True)
                print("\n=== 右齿面按幅值降序排序 ===")
                for i, (order, amplitude) in enumerate(right_order_amplitudes, 1):
                    print(f"  {i}. 第{order}阶: {amplitude:.4f}μm")
            else:
                print("\n无法计算右齿面幅值数据")
            
            # 分析阶数直到幅值小于阈值
            threshold_results = analyze_orders_until_threshold(report_generator, mock_measurement_data, threshold=0.02)
            
            # 显示大于阈值的阶数结果
            print("\n=== 大于0.02μm幅值的阶数结果 ===")
            
            # 显示左齿面结果
            print("\n左齿面大于0.02μm幅值的阶数:")
            if threshold_results['left']:
                for order, amplitude in threshold_results['left']:
                    print(f"  第{order}阶: {amplitude:.4f}μm")
            else:
                print("  无")
            
            # 显示右齿面结果
            print("\n右齿面大于0.02μm幅值的阶数:")
            if threshold_results['right']:
                for order, amplitude in threshold_results['right']:
                    print(f"  第{order}阶: {amplitude:.4f}μm")
            else:
                print("  无")
            
            # 分析ZE倍数阶次（按Klingelnberg图表方式）- 直接对ZE倍数频率进行拟合
            def analyze_ze_orders(report_generator, measurement_data, teeth_count=87, max_multiplier=6):
                """
                按ZE倍数分析阶次（ZE=齿数）
                
                Args:
                    report_generator: 报表生成器对象
                    measurement_data: 测量数据对象
                    teeth_count: 齿轮齿数
                    max_multiplier: 最大倍数
                    
                Returns:
                    dict: {direction: [(ze_order, amplitude), ...]}
                """
                print(f"\n=== 按ZE倍数分析阶次 (ZE={teeth_count}) ===")
                
                results = {
                    'profile_left': [],
                    'profile_right': [],
                    'helix_left': [],
                    'helix_right': []
                }
                
                # 导入迭代残差正弦拟合函数
                from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum特斯特 import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings
                
                # 创建设置和报表对象
                settings = RippleSpectrumSettings()
                ripple_report = KlingelnbergRippleSpectrumReport(settings)
                
                # 分析每个方向的数据
                directions = [
                    ('profile_left', '齿形左齿面', measurement_data.profile_data),
                    ('profile_right', '齿形右齿面', measurement_data.profile_data_right),
                    ('helix_left', '齿向左齿面', measurement_data.flank_data),
                    ('helix_right', '齿向右齿面', measurement_data.flank_data_right)
                ]
                
                for direction_key, direction_name, data_dict in directions:
                    print(f"\n分析{direction_name}ZE倍数阶次...")
                    try:
                        if data_dict:
                            # 优化：先计算平均曲线，再分析
                            avg_curve = ripple_report._calculate_average_curve(data_dict)
                            if avg_curve is not None:
                                # 生成ZE倍数的候选频率
                                candidate_frequencies = [teeth_count * i for i in range(1, max_multiplier + 1)]
                                
                                # 直接对每个ZE倍数频率进行正弦拟合
                                n = len(avg_curve)
                                x = np.linspace(0.0, 1.0, n, dtype=float)
                                residual = np.array(avg_curve, dtype=float)
                                
                                for freq in candidate_frequencies:
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
                                        
                                        if amplitude >= 0.01:  # 使用0.01μm阈值
                                            results[direction_key].append((freq, amplitude))
                                            print(f"  {direction_name}{freq//teeth_count}ZE ({freq})阶幅值: {amplitude:.4f}μm")
                                        else:
                                            print(f"  {direction_name}{freq//teeth_count}ZE ({freq})阶幅值: {amplitude:.4f}μm (小于阈值)")
                                    except Exception as e:
                                        print(f"  {direction_name}{freq//teeth_count}ZE ({freq})阶分析出错: {e}")
                    except Exception as e:
                        print(f"  {direction_name}ZE倍数分析出错: {e}")
                
                return results
            
            # 分析ZE倍数阶次
            ze_results = analyze_ze_orders(report_generator, mock_measurement_data, teeth_count=teeth_count)
            
            # 显示ZE倍数阶次结果
            print("\n=== ZE倍数阶次分析结果 ===")
            
            # 显示每个方向的结果
            direction_names = {
                'profile_left': '齿形左齿面',
                'profile_right': '齿形右齿面',
                'helix_left': '齿向左齿面',
                'helix_right': '齿向右齿面'
            }
            
            for direction_key, direction_name in direction_names.items():
                print(f"\n{direction_name}ZE倍数阶次:")
                if ze_results[direction_key]:
                    for ze_order, amplitude in ze_results[direction_key]:
                        multiplier = ze_order // teeth_count
                        print(f"  {multiplier}ZE ({ze_order}): {amplitude:.4f}μm")
                else:
                    print("  无")
            
            # 比较与Klingelnberg图表数据
            print("\n=== 与Klingelnberg图表数据比较 ===")
            print("Klingelnberg图表显示的阶次（ZE倍数）:")
            print("  1ZE=87, 2ZE=174, 3ZE=261, 4ZE=348, 5ZE=435, 6ZE=522")
            print("\n右齿面Profile right幅值:")
            print("  1ZE: 0.15μm, 2ZE: 0.06μm, 3ZE: 0.08μm, 4ZE: 0.07μm, 5ZE: 0.03μm, 6ZE: 0.03μm")
            print("\n左齿面Profile left幅值:")
            print("  1ZE: 0.14μm, 2ZE: 0.06μm, 3ZE: 0.14μm, 4ZE: 0.04μm")
            print("\n右齿面Helix right幅值:")
            print("  1ZE: 0.09μm, 2ZE: 0.10μm, 3ZE: 0.05μm")
            print("\n左齿面Helix left幅值:")
            print("  1ZE: 0.12μm, 2ZE: 0.04μm, 3ZE: 0.02μm, 4ZE: 0.03μm")
            
        else:
            print("无法从MKA文件读取数据")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
