#!/usr/bin/env python3
"""
分析齿轮阶次数据，使用方法B（基于测量长度的谐波次数）
"""

import sys
import os
import numpy as np

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

from gear_analysis_refactored.utils.file_parser import parse_mka_file
from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum特斯特 import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings

class GearOrderAnalyzerMethodB:
    """齿轮阶次分析器（使用方法B）"""
    
    def __init__(self):
        """初始化分析器"""
        self.settings = RippleSpectrumSettings()
        self.ripple_report = KlingelnbergRippleSpectrumReport(self.settings)
    
    def _calculate_average_curve(self, data_dict):
        """
        计算平均曲线
        
        Args:
            data_dict: {齿号: [数据点]}
            
        Returns:
            tuple: (平均曲线, 评价范围长度, 总长度)
        """
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
    
    def _iterative_residual_sine_fit(self, curve_data, max_order=500, max_components=50):
        """
        使用迭代残差法进行正弦拟合频谱分析
        
        Args:
            curve_data: 曲线数据
            max_order: 最大阶次（频率）
            max_components: 最大分量数
        
        Returns:
            dict: {频率: 幅值(μm)}
        """
        if curve_data is None or len(curve_data) < 8:
            return {}
        
        n = len(curve_data)
        
        # 生成时间坐标x轴（0到1秒，假设转速为1转/秒）
        x = np.linspace(0.0, 1.0, n, dtype=float)
        
        # 初始化残差信号为原始信号
        residual = np.array(curve_data, dtype=float)
        
        # 存储提取的频谱分量
        spectrum_results = {}
        
        # 生成均匀分布的候选频率值（1到max_order）
        candidate_frequencies = list(range(1, max_order + 1))
        
        # 迭代提取最大频率分量
        for iteration in range(max_components):
            # 对每个候选频率进行正弦拟合
            best_frequency = None
            best_amplitude = 0.0
            best_coeffs = None
            
            # 存储所有候选频率的拟合结果
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
            best_amplitude, best_coeffs = frequency_amplitudes[best_frequency][0], frequency_amplitudes[best_frequency][1:4]
            
            # 检查是否找到有效的最大频率
            if best_frequency is None or best_amplitude < 0.02:
                break
            
            # 保存提取的频谱分量
            spectrum_results[best_frequency] = best_amplitude
            
            # 从残差信号中移除已提取的正弦波
            a, b, c = best_coeffs
            best_freq_float = float(best_frequency)
            fitted_wave = a * np.sin(2.0 * np.pi * best_freq_float * x) + b * np.cos(2.0 * np.pi * best_freq_float * x) + c
            residual = residual - fitted_wave
            
            # 检查残差信号是否已经足够小
            residual_rms = np.sqrt(np.mean(np.square(residual)))
            if residual_rms < 0.001:
                break
        
        return spectrum_results
    
    def _calculate_method_a_order(self, frequency, gear_data):
        """
        使用方法A计算阶次：阶次 = 空间频率 × 基圆周长
        
        Args:
            frequency: 每转波数（频率）
            gear_data: 齿轮基本数据
            
        Returns:
            float: 方法A阶次
        """
        # 从齿轮数据中获取参数
        module = gear_data.get('module', 0.0)
        teeth = gear_data.get('teeth', 0)
        pressure_angle = gear_data.get('pressure_angle', 20.0)  # 默认压力角20度
        
        if module <= 0 or teeth <= 0:
            return 0.0
        
        # 计算基圆半径 (mm)
        import math
        pressure_angle_rad = math.radians(pressure_angle)
        base_radius = (module * teeth) / 2 * math.cos(pressure_angle_rad)
        
        # 计算基圆周长 (mm)
        base_circumference = 2 * math.pi * base_radius
        
        # 计算空间频率 f_s (1/mm)
        # 空间频率 = 每转波数 / 基圆周长
        spatial_frequency = frequency / base_circumference
        
        # 计算阶次 = 空间频率 × 基圆周长
        method_a_order = spatial_frequency * base_circumference
        
        return method_a_order
    
    def _calculate_method_b_order(self, frequency, gear_data, eval_length, total_length):
        """
        使用方法B计算阶次：阶次k = 空间频率 × 测量长度L
        
        Args:
            frequency: 每转波数（频率）
            gear_data: 齿轮基本数据
            eval_length: 评价范围长度（数据点数）
            total_length: 总长度（数据点数）
            
        Returns:
            float: 方法B阶次
        """
        # 从齿轮数据中获取参数
        module = gear_data.get('module', 0.0)
        teeth = gear_data.get('teeth', 0)
        pressure_angle = gear_data.get('pressure_angle', 20.0)  # 默认压力角20度
        
        if module <= 0 or teeth <= 0:
            return 0.0
        
        # 计算基圆半径 (mm)
        import math
        pressure_angle_rad = math.radians(pressure_angle)
        base_radius = (module * teeth) / 2 * math.cos(pressure_angle_rad)
        
        # 计算基圆周长 (mm)
        base_circumference = 2 * math.pi * base_radius
        
        # 计算评价范围对应的物理长度 (mm) - 测量长度L
        if total_length > 0:
            eval_physical_length = (eval_length / total_length) * base_circumference
        else:
            eval_physical_length = 0.0
        
        # 计算空间频率 f_s (1/mm)
        # 空间频率 = 每转波数 / 基圆周长
        spatial_frequency = frequency / base_circumference
        
        # 计算阶次 k = 空间频率 × 测量长度L
        method_b_order = spatial_frequency * eval_physical_length
        
        return method_b_order
    
    def analyze_mka_file(self, mka_file_path):
        """
        分析MKA文件，使用方法B生成阶次数据
        
        Args:
            mka_file_path: MKA文件路径
        """
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
                directions = {
                    '左齿形': profile_data.get('left', {}),
                    '右齿形': profile_data.get('right', {}),
                    '左齿向': extract_flank_data_from_topography(topography_data, 'left'),
                    '右齿向': extract_flank_data_from_topography(topography_data, 'right')
                }
                
                # 分析每个方向
                print(f"\n=== 齿轮阶次数据分析 (ZE={teeth_count}) ===")
                print("使用方法A: 阶次 = 空间频率 × 基圆周长")
                
                # 计算基圆半径和周长
                import math
                module = gear_data.get('module', 0.0)
                pressure_angle = gear_data.get('pressure_angle', 20.0)
                if module > 0:
                    pressure_angle_rad = math.radians(pressure_angle)
                    base_radius = (module * teeth_count) / 2 * math.cos(pressure_angle_rad)
                    base_circumference = 2 * math.pi * base_radius
                    print(f"齿轮参数: 模数={module}, 齿数={teeth_count}, 压力角={pressure_angle}°")
                    print(f"基圆半径: {base_radius:.3f}mm, 基圆周长: {base_circumference:.3f}mm")
                
                # 存储所有方向的结果
                all_results = {}
                
                for direction_name, data_dict in directions.items():
                    print(f"\n分析{direction_name}...")
                    
                    # 计算平均曲线、评价范围长度和总长度
                    avg_curve, eval_length, total_length = self._calculate_average_curve(data_dict)
                    if avg_curve is not None and eval_length > 0 and total_length > 0:
                        # 使用迭代残差法计算频谱
                        spectrum = self._iterative_residual_sine_fit(avg_curve, max_order=teeth_count*6)
                        
                        # 按幅值降序排序
                        sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
                        
                        # 输出前10个阶次
                        print(f"  前10个阶次（按幅值降序）:")
                        results = []
                        for i, (freq, amp) in enumerate(sorted_spectrum[:10], 1):
                            # 使用方法A计算阶次
                            method_a_order = self._calculate_method_a_order(freq, gear_data)
                            results.append((i, freq, amp, method_a_order))
                            print(f"    {i}. 频率: {freq}, 幅值: {amp:.3f}μm, 方法A阶次: {method_a_order:.2f}")
                        
                        # 保存结果
                        all_results[direction_name] = results
                        
                        # 显示ZE倍数参考
                        print(f"  ZE倍数参考:")
                        for i in range(1, 7):
                            ze_freq = teeth_count * i
                            method_a_ze = self._calculate_method_a_order(ze_freq, gear_data)
                            print(f"    {i}ZE: {ze_freq} (方法A阶次: {method_a_ze:.2f})")
                    else:
                        print(f"  无有效数据")
                
                # 生成详细报告
                print("\n=== 详细阶次数据报告（方法A）===")
                for direction, results in all_results.items():
                    print(f"\n{direction}:")
                    print("  排序 | 频率 | 幅值(μm) |  方法A阶次")
                    print("  -----|------|----------|----------")
                    for rank, freq, amp, method_a in results:
                        print(f"  {rank:4} | {freq:4} | {amp:8.3f} | {method_a:8.2f}")
                
            else:
                print("无法从MKA文件读取数据")
                
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

def main():
    """
    主函数
    """
    if len(sys.argv) > 1:
        mka_file = sys.argv[1]
    else:
        mka_file = "263751-018-WAV.mka"
    
    analyzer = GearOrderAnalyzerMethodB()
    analyzer.analyze_mka_file(mka_file)

if __name__ == "__main__":
    main()
