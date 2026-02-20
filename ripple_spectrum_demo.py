import numpy as np
import matplotlib.pyplot as plt
import math

class RippleSpectrumDemo:
    """波纹频谱分析演示类"""
    
    def __init__(self):
        pass
    
    def _generate_test_data(self, n_points=1000):
        """生成测试数据，包含多个频率分量"""
        x = np.linspace(0.0, 1.0, n_points, dtype=float)
        
        # 生成包含多个频率分量的信号
        # 主要分量：10Hz, 25Hz, 40Hz, 60Hz
        signal = (
            2.0 * np.sin(2 * np.pi * 10 * x) +  # 10Hz, 幅值2.0
            1.5 * np.sin(2 * np.pi * 25 * x) +  # 25Hz, 幅值1.5
            1.0 * np.sin(2 * np.pi * 40 * x) +  # 40Hz, 幅值1.0
            0.5 * np.sin(2 * np.pi * 60 * x) +  # 60Hz, 幅值0.5
            0.2 * np.random.randn(n_points)     # 噪声
        )
        
        return x, signal
    
    def _sine_fit(self, x, y, frequency):
        """对特定频率进行正弦拟合"""
        try:
            # 构建矩阵 A = [sin(2π*f*x), cos(2π*f*x), 1]
            sin_x = np.sin(2.0 * np.pi * frequency * x)
            cos_x = np.cos(2.0 * np.pi * frequency * x)
            A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
            
            # 求解最小二乘
            coeffs, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
            a, b, c = coeffs
            
            # 计算幅值：A = sqrt(a^2 + b^2)
            amplitude = float(np.sqrt(a * a + b * b))
            
            return amplitude, a, b, c
        except Exception as e:
            return 0.0, 0.0, 0.0, 0.0
    
    def _extract_frequency(self, x, residual, candidate_frequencies):
        """从残差信号中提取幅值最大的频率分量"""
        best_frequency = None
        best_amplitude = 0.0
        best_coeffs = None
        
        # 对每个候选频率进行拟合
        for freq in candidate_frequencies:
            amplitude, a, b, c = self._sine_fit(x, residual, freq)
            
            # 检查幅值是否合理
            if amplitude > best_amplitude and amplitude < 10.0:
                best_amplitude = amplitude
                best_frequency = freq
                best_coeffs = (a, b, c)
        
        return best_frequency, best_amplitude, best_coeffs
    
    def _remove_frequency_component(self, x, residual, frequency, coeffs):
        """从残差信号中移除指定频率分量"""
        a, b, c = coeffs
        fitted_wave = a * np.sin(2.0 * np.pi * frequency * x) + \
                     b * np.cos(2.0 * np.pi * frequency * x) + c
        new_residual = residual - fitted_wave
        return new_residual
    
    def iterative_residual_analysis(self, signal, x, max_iterations=10, max_frequency=100):
        """使用迭代残差法进行频谱分析"""
        # 初始化
        residual = np.array(signal, dtype=float)
        spectrum_results = {}
        iteration_history = []
        
        # 生成候选频率
        candidate_frequencies = list(range(1, max_frequency + 1))
        
        print(f"=== 迭代残差法正弦拟合频谱分析 ===")
        print(f"信号长度: {len(signal)}, 最大迭代次数: {max_iterations}, 最大频率: {max_frequency}")
        print(f"初始信号范围: [{np.min(signal):.4f}, {np.max(signal):.4f}]")
        print()
        
        # 迭代提取频率分量
        for iteration in range(max_iterations):
            print(f"--- 迭代 {iteration + 1}/{max_iterations} ---")
            
            # 提取幅值最大的频率分量
            best_freq, best_amp, best_coeffs = self._extract_frequency(x, residual, candidate_frequencies)
            
            if best_freq is None or best_amp < 0.01:
                print(f"没有找到有效的频率分量（最大幅值: {best_amp:.4f} < 0.01），停止迭代")
                break
            
            print(f"找到频率分量: {best_freq}Hz, 幅值: {best_amp:.4f}")
            
            # 保存结果
            spectrum_results[best_freq] = best_amp
            
            # 记录迭代历史
            iteration_history.append({
                'iteration': iteration + 1,
                'frequency': best_freq,
                'amplitude': best_amp,
                'residual': residual.copy()
            })
            
            # 从残差中移除该频率分量
            residual = self._remove_frequency_component(x, residual, best_freq, best_coeffs)
            
            # 计算残差的RMS
            residual_rms = np.sqrt(np.mean(np.square(residual)))
            print(f"移除后残差范围: [{np.min(residual):.4f}, {np.max(residual):.4f}]")
            print(f"残差RMS: {residual_rms:.4f}")
            print()
            
            # 如果残差足够小，停止迭代
            if residual_rms < 0.01:
                print(f"残差RMS过小（{residual_rms:.4f} < 0.01），停止迭代")
                break
        
        print(f"=== 迭代完成 ===")
        print(f"提取的频率分量: {len(spectrum_results)}")
        print("详细结果:")
        for freq, amp in sorted(spectrum_results.items(), key=lambda x: x[1], reverse=True):
            print(f"  {freq}Hz: {amp:.4f}")
        
        return spectrum_results, iteration_history, residual
    
    def plot_results(self, x, original_signal, spectrum_results, iteration_history, final_residual):
        """绘制分析结果"""
        fig, axes = plt.subplots(3, 2, figsize=(15, 12))
        fig.suptitle('波纹频谱分析 - 迭代残差法演示', fontsize=16)
        
        # 1. 原始信号
        axes[0, 0].plot(x, original_signal, 'b-', linewidth=1.5)
        axes[0, 0].set_title('1. 原始信号')
        axes[0, 0].set_xlabel('归一化位置')
        axes[0, 0].set_ylabel('振幅')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 频谱分析结果
        freq_list = sorted(spectrum_results.keys())
        amp_list = [spectrum_results[freq] for freq in freq_list]
        axes[0, 1].bar(freq_list, amp_list, color='g', alpha=0.7)
        axes[0, 1].set_title('2. 频谱分析结果')
        axes[0, 1].set_xlabel('频率 (Hz)')
        axes[0, 1].set_ylabel('振幅')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 迭代过程中的残差变化（前3次迭代）
        axes[1, 0].set_title('3. 迭代过程中的残差变化')
        axes[1, 0].set_xlabel('归一化位置')
        axes[1, 0].set