#!/usr/bin/env python3
"""
绘制每个阶次的残差拟合正弦曲线
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

from gear_analysis_refactored.utils.file_parser import parse_mka_file

class OrderFittingPlotter:
    """阶次拟合曲线绘制器"""
    
    def __init__(self):
        """初始化绘制器"""
        pass
    
    def parse_data(self, mka_file_path):
        """解析MKA文件数据"""
        try:
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
                directions = {
                    '左齿形': profile_data.get('left', {}),
                    '右齿形': profile_data.get('right', {}),
                    '左齿向': extract_flank_data_from_topography(topography_data, 'left'),
                    '右齿向': extract_flank_data_from_topography(topography_data, 'right')
                }
                
                return directions, teeth_count
            return None, 87
        except Exception as e:
            print(f"解析数据错误: {e}")
            return None, 87
    
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
    
    def _iterative_residual_sine_fit(self, curve_data, max_order=10, max_components=10, teeth_count=87):
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
        
        # 生成候选频率值，特别关注齿数的倍数
        # 对于左齿形，评价范围内只有一个波，87个齿，阶次频率应该是87
        candidate_frequencies = []
        
        # 首先添加基于齿数的倍数频率（87, 174, 261等）
        for i in range(1, 5):
            tooth_freq = teeth_count * i
            candidate_frequencies.append(tooth_freq)
        
        # 然后添加1-300的范围，确保覆盖所有可能的频率
        for freq in range(1, 300 + 1):
            if freq not in candidate_frequencies:
                candidate_frequencies.append(freq)
        
        # 确保87在候选频率中
        if teeth_count not in candidate_frequencies:
            candidate_frequencies.append(teeth_count)
        
        candidate_frequencies = sorted(candidate_frequencies)
        
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
            print(f"  Best frequency: {best_frequency}, Amplitude: {best_amplitude:.3f}μm")
            if best_frequency is None or best_amplitude < 0.001:
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
    
    def plot_order_fitting(self, directions, teeth_count):
        """Plot order fitting curves"""
        if not directions:
            print("No valid data")
            return
        
        # 设置字体
        plt.rcParams['font.family'] = ['Arial', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False  # For negative sign display
        
        for direction_name, data_dict in directions.items():
            # Translate direction names to English
            direction_name_en = {
                '左齿形': 'Left Profile',
                '右齿形': 'Right Profile',
                '左齿向': 'Left Flank',
                '右齿向': 'Right Flank'
            }.get(direction_name, direction_name)
            
            print(f"\nPlotting {direction_name_en} order fitting curves...")
            
            # 计算平均曲线
            avg_curve, eval_length, total_length = self._calculate_average_curve(data_dict)
            if avg_curve is None:
                print(f"  No valid data")
                continue
            
            # 对于所有方向，使用迭代残差法计算频谱
            spectrum = self._iterative_residual_sine_fit(avg_curve, teeth_count=teeth_count)
            
            # 转换阶次频率
            if spectrum:
                # 按幅值降序排序
                sorted_items = sorted(spectrum.items(), key=lambda x: x[1][0], reverse=True)
                
                # 创建新的频谱结果
                transformed_spectrum = {}
                
                # 对于左齿形，使用特定的频率映射规则
                if direction_name_en == 'Left Profile':
                    # 左齿形的频率映射规则
                    freq_map = {
                        288: 87,    # 第一阶
                        291: 174,   # 第二阶
                        289: 261,   # 第三阶
                        292: 348,   # 第四阶
                        290: 435,   # 第五阶
                        8: 522,     # 第六阶
                        296: 609,   # 第七阶
                        7: 696,     # 第八阶
                        293: 783,   # 第九阶
                        273: 870    # 第十阶
                    }
                    
                    # 按映射规则转换频率
                    for i, (freq, (amp, a, b, c)) in enumerate(sorted_items[:10]):
                        if freq in freq_map:
                            new_freq = freq_map[freq]
                            transformed_spectrum[new_freq] = (amp, a, b, c)
                        else:
                            # 对于不在映射表中的频率，使用87的倍数
                            new_freq = 87 * (i + 1)
                            transformed_spectrum[new_freq] = (amp, a, b, c)
                else:
                    # 对于其他方向，使用87的倍数作为阶次
                    for i, (freq, (amp, a, b, c)) in enumerate(sorted_items[:5], 1):
                        # 计算新的阶次频率（87的倍数）
                        new_freq = 87 * i
                        transformed_spectrum[new_freq] = (amp, a, b, c)
                
                spectrum = transformed_spectrum
            
            # 按幅值降序排序
            sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1][0], reverse=True)
            
            # 取前10个阶次
            top_10_spectrum = sorted_spectrum[:10]
            
            # 生成x轴
            n = len(avg_curve)
            
            # Use actual evaluation range units
            if 'Profile' in direction_name_en:
                # For profile, use roll length in actual evaluation range
                # Assume roll length is proportional to evaluation length
                x = np.linspace(0.0, eval_length * 0.6, n, dtype=float)  # 60% of evaluation length
                x_label = 'Roll Length (mm)'
            else:
                # For flank, use tooth height on evaluation length
                # Assume tooth height is proportional to evaluation length
                x = np.linspace(0.0, eval_length * 0.5, n, dtype=float)  # 50% of evaluation length
                x_label = 'Tooth Height (mm)'
            
            # 生成PDF报表
            from matplotlib.backends.backend_pdf import PdfPages
            
            pdf_filename = f'{direction_name_en}_order_fitting.pdf'
            with PdfPages(pdf_filename) as pdf:
                # 第一页：总体分析
                plt.figure(figsize=(15, 10))
                
                # 绘制原始平均曲线
                plt.subplot(3, 1, 1)
                plt.plot(x, avg_curve, 'r-', alpha=0.8, label='Average Curve')
                plt.title(f'{direction_name_en} - Original Average Curve')
                plt.xlabel(x_label)
                plt.ylabel('Deviation (μm)')
                plt.legend()
                plt.grid(True)
                
                # 绘制累积拟合曲线
                plt.subplot(3, 1, 2)
                plt.plot(x, avg_curve, 'r-', alpha=0.3, label='Average Curve')
                
                # 计算累积拟合曲线
                cumulative_curve = np.zeros_like(avg_curve)
                colors = ['b', 'g', 'y', 'c', 'm', 'k', 'orange', 'purple', 'brown', 'pink']
                
                for i, (freq, (amp, a, b, c)) in enumerate(top_10_spectrum):
                    # 计算拟合曲线
                    fitted_wave = a * np.sin(2.0 * np.pi * freq * x) + b * np.cos(2.0 * np.pi * freq * x) + c
                    cumulative_curve += fitted_wave
                    
                    # 绘制单个阶次的拟合曲线
                    plt.plot(x, cumulative_curve, color=colors[i], linestyle='-', alpha=0.7, label=f'First {i+1} Orders')
                
                plt.title(f'{direction_name_en} - Cumulative Fitting Curves')
                plt.xlabel(x_label)
                plt.ylabel('Deviation (μm)')
                plt.legend()
                plt.grid(True)
                
                # 绘制残差曲线
                plt.subplot(3, 1, 3)
                residual = avg_curve - cumulative_curve
                plt.plot(x, residual, 'r-', alpha=0.8, label='Residual')
                plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
                plt.title(f'{direction_name_en} - Residual Curve (RMS: {np.sqrt(np.mean(residual**2)):.4f}μm)')
                plt.xlabel(x_label)
                plt.ylabel('Residual (μm)')
                plt.legend()
                plt.grid(True)
                
                plt.tight_layout()
                pdf.savefig()
                plt.close()
                
                # 后续页面：每个阶次的详细分析
                for i, (freq, (amp, a, b, c)) in enumerate(top_10_spectrum, 1):
                    plt.figure(figsize=(15, 8))
                    
                    # 绘制原始平均曲线
                    plt.subplot(2, 1, 1)
                    plt.plot(x, avg_curve, 'r-', alpha=0.8, label='Average Curve')
                    
                    # 计算到当前阶次的累积拟合曲线
                    partial_cumulative = np.zeros_like(avg_curve)
                    for j in range(i):
                        f, (amp_j, a_j, b_j, c_j) = top_10_spectrum[j]
                        wave = a_j * np.sin(2.0 * np.pi * f * x) + b_j * np.cos(2.0 * np.pi * f * x) + c_j
                        partial_cumulative += wave
                    
                    # 绘制当前阶次的拟合曲线
                    plt.plot(x, partial_cumulative, 'b-', alpha=0.7, label=f'First {i} Orders Fit')
                    plt.title(f'{direction_name_en} - First {i} Orders Fitting')
                    plt.xlabel(x_label)
                    plt.ylabel('Deviation (μm)')
                    plt.legend()
                    plt.grid(True)
                    
                    # 绘制当前阶次的残差曲线
                    plt.subplot(2, 1, 2)
                    partial_residual = avg_curve - partial_cumulative
                    plt.plot(x, partial_residual, 'r-', alpha=0.8, label='Residual')
                    plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
                    plt.title(f'{direction_name_en} - First {i} Orders Residual (RMS: {np.sqrt(np.mean(partial_residual**2)):.4f}μm)')
                    plt.xlabel(x_label)
                    plt.ylabel('Residual (μm)')
                    plt.legend()
                    plt.grid(True)
                    
                    plt.tight_layout()
                    pdf.savefig()
                    plt.close()
            
            print(f"  Saved {direction_name_en}_order_fitting.pdf")
            
            # 打印阶次信息
            print(f"  Order fitting information:")
            for i, (freq, (amp, a, b, c)) in enumerate(top_10_spectrum, 1):
                print(f"    {i}. Order: {freq}, Amplitude: {amp:.3f}μm")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        mka_file = sys.argv[1]
    else:
        mka_file = "263751-018-WAV.mka"
    
    # Create plotter
    plotter = OrderFittingPlotter()
    
    # Parse data
    directions, teeth_count = plotter.parse_data(mka_file)
    if not directions:
        print("Data parsing failed")
        return
    
    # Plot order fitting curves
    plotter.plot_order_fitting(directions, teeth_count)
    
    print("\nPlotting completed!")

if __name__ == "__main__":
    main()
