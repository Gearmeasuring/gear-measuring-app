#!/usr/bin/env python3
"""
分析齿轮阶次数据，使用迭代残差正弦拟合算法
"""

import sys
import os
import numpy as np

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

from gear_analysis_refactored.utils.file_parser import parse_mka_file
from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum特斯特 import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings

class GearOrderAnalyzer:
    """齿轮阶次分析器"""
    
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
            np.ndarray: 平均曲线
        """
        if not data_dict:
            return None
        
        all_curves = []
        
        for tooth_num, values in data_dict.items():
            if values is None or len(values) == 0:
                continue
            
            vals = np.array(values, dtype=float)
            
            # 提取评价范围（20%-80%）
            n_points = len(vals)
            idx_start = int(n_points * 0.2)
            idx_end = int(n_points * 0.8)
            
            if idx_end <= idx_start + 7:
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
            return None
        
        # 对齐所有曲线到相同长度
        min_len = min(len(c) for c in all_curves)
        if min_len < 8:
            return None
        
        aligned_curves = [c[:min_len] for c in all_curves]
        
        # 计算平均曲线
        avg_curve = np.mean(aligned_curves, axis=0)
        
        return avg_curve
    
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
    
    def analyze_mka_file(self, mka_file_path):
        """
        分析MKA文件，生成阶次数据
        
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
                
                # 存储所有方向的结果
                all_results = {}
                
                for direction_name, data_dict in directions.items():
                    print(f"\n分析{direction_name}...")
                    
                    # 计算平均曲线
                    avg_curve = self._calculate_average_curve(data_dict)
                    if avg_curve is not None:
                        # 使用迭代残差法计算频谱
                        spectrum = self._iterative_residual_sine_fit(avg_curve, max_order=teeth_count*6)
                        
                        # 按幅值降序排序
                        sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
                        
                        # 输出前10个阶次
                        print(f"  前10个阶次（按幅值降序）:")
                        results = []
                        for i, (freq, amp) in enumerate(sorted_spectrum[:10], 1):
                            # 计算ZE倍数
                            ze_multiplier = freq / teeth_count
                            results.append((i, freq, amp, ze_multiplier))
                            print(f"    {i}. 频率: {freq}, 幅值: {amp:.3f}μm, ZE倍数: {ze_multiplier:.2f}")
                        
                        # 保存结果
                        all_results[direction_name] = results
                        
                        # 显示ZE倍数参考
                        print(f"  ZE倍数参考:")
                        for i in range(1, 7):
                            ze_freq = teeth_count * i
                            print(f"    {i}ZE: {ze_freq}")
                    else:
                        print(f"  无有效数据")
                
                # 生成详细报告
                print("\n=== 详细阶次数据报告 ===")
                for direction, results in all_results.items():
                    print(f"\n{direction}:")
                    print("  排序 | 频率 | 幅值(μm) | ZE倍数")
                    print("  -----|------|----------|--------")
                    for rank, freq, amp, ze in results:
                        print(f"  {rank:4} | {freq:4} | {amp:8.3f} | {ze:6.2f}")
                
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
    
    analyzer = GearOrderAnalyzer()
    analyzer.analyze_mka_file(mka_file)

if __name__ == "__main__":
    main()
