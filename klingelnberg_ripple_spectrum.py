"""
克林贝格波纹度频谱分析模块
Klingelnberg ripple spectrum analysis module

实现迭代正弦拟合算法，用于分析齿轮测量数据的频谱特性
Implements iterative sine fit algorithm for spectrum analysis of gear measurement data
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from scipy.optimize import curve_fit
import math
from typing import List, Dict, Tuple, Optional


class KlingelnbergRippleSpectrumReport:
    """克林贝格波纹度频谱分析报告类"""
    
    def __init__(self):
        pass
    
    def _sin_function(self, x: np.ndarray, amplitude: float, frequency: float, phase: float, offset: float) -> np.ndarray:
        """正弦函数模型"""
        return amplitude * np.sin(2 * np.pi * frequency * x + phase) + offset
    
    def _fit_sine_wave(self, x: np.ndarray, y: np.ndarray, initial_frequency: float = None) -> Tuple[float, float, float, float]:
        """
        拟合正弦波到数据
        使用最小二乘法拟合，不依赖FFT分析
        
        Args:
            x: 归一化的x轴数据（0到1对应一个完整的旋转）
            y: 输入数据
            initial_frequency: 初始频率猜测值
        
        Returns:
            (amplitude, frequency, phase, offset)
        """
        # 初始猜测值
        # 振幅初始猜测：数据范围的一半
        amp_guess = (np.max(y) - np.min(y)) / 2
        # 频率初始猜测：如果没有提供，使用合理的默认值
        freq_guess = initial_frequency if initial_frequency is not None else 1.0
        # 相位初始猜测：0
        phase_guess = 0
        # 偏移初始猜测：数据平均值
        offset_guess = np.mean(y)
        
        try:
            # 使用最小二乘法拟合正弦波
            popt, _ = curve_fit(
                self._sin_function, 
                x, 
                y, 
                p0=[amp_guess, freq_guess, phase_guess, offset_guess],
                maxfev=10000
            )
            amplitude, frequency, phase, offset = popt
            return amplitude, frequency, phase, offset
        except Exception as e:
            # 拟合失败，返回初始猜测值
            return amp_guess, freq_guess, phase_guess, offset_guess
    
    def _preprocess_data(self, data: np.ndarray) -> np.ndarray:
        """
        预处理数据，移除起始不稳定部分、去倾斜和鼓形，然后平滑
        
        Args:
            data: 输入数据
        
        Returns:
            预处理后的数据
        """
        # 复制数据以避免修改原始数据
        processed_data = np.copy(data)
        
        # 移除起始不稳定部分（前1%的数据）
        # 计算要移除的点数
        remove_points = max(1, int(len(processed_data) * 0.01))
        # 如果数据长度足够，移除起始部分
        if len(processed_data) > remove_points:
            processed_data = processed_data[remove_points:]
        
        # 去倾斜和鼓形
        n = len(processed_data)
        if n > 5:
            # 创建归一化的x坐标（0到1）
            x = np.linspace(0, 1, n)
            
            # 去除线性趋势（倾斜）
            # 使用最小二乘法拟合线性模型
            coeffs = np.polyfit(x, processed_data, 1)
            linear_trend = np.polyval(coeffs, x)
            processed_data -= linear_trend
            
            # 去除二次趋势（鼓形）
            # 使用最小二乘法拟合二次模型
            coeffs = np.polyfit(x, processed_data, 2)
            quadratic_trend = np.polyval(coeffs, x)
            processed_data -= quadratic_trend
        
        # 平滑处理：使用移动平均滤波
        window_size = 5
        if len(processed_data) > window_size:
            # 创建移动平均窗口
            window = np.ones(window_size) / window_size
            # 应用移动平均滤波
            processed_data = np.convolve(processed_data, window, mode='same')
        
        return processed_data
    
    def _calculate_ripple_spectrum(self, data: np.ndarray, max_harmonics: int = 10, min_order: int = 87, max_order: int = 100, target_order: int = 87) -> List[Dict]:
        """
        计算波纹度频谱
        通过最小二乘法先分解阶次最大的正弦波，从原始信号中移除已提取的最大阶次正弦波，计算频谱
        随后最大阶次正弦波被分解计算频谱
        对剩余信号重复上述过程，直到提取出第十个较大的阶次
        最终第十较大阶次的正弦波被分解并计算，得出频谱图像
        
        Args:
            data: 输入数据
            max_harmonics: 要提取的最大谐波数量
            min_order: 要考虑的最小阶次
            max_order: 要考虑的最大阶次
            target_order: 特别关注的目标阶次（如87阶）
        
        Returns:
            频谱分析结果列表
        """
        # 预处理数据，移除起始不稳定部分并平滑
        processed_data = self._preprocess_data(data)
        
        # 准备x轴数据（归一化的位置）
        x = np.linspace(0, 1, len(processed_data))
        # 初始化剩余偏差
        residual = np.copy(processed_data)
        # 存储频谱结果
        spectrum = []
        
        # 存储已提取的阶次，避免重复
        extracted_orders = set()
        
        # 迭代提取主导频率，直到提取出max_harmonics个较大的阶次
        for i in range(max_harmonics):  # 减少迭代次数，提高效率
            # 优先寻找高阶次成分
            # 从高到低尝试可能的阶次
            best_amplitude = 0
            best_result = None
            
            # 尝试不同的初始频率，优先寻找高阶次和26及其倍数
            # 只尝试最重要的几个频率，减少计算时间
            test_frequencies = []
            
            # 首先尝试目标阶次
            if target_order and target_order >= min_order and target_order <= max_order and target_order not in extracted_orders:
                test_frequencies.append(target_order)
            
            # 然后尝试26及其倍数（最多到max_order）
            for multiple in range(1, 7):  # 26, 52, 78, 104, 130, 156
                freq = 26 * multiple
                if freq >= min_order and freq <= max_order and freq not in test_frequencies and freq not in extracted_orders:
                    test_frequencies.append(freq)
            
            # 然后尝试一些关键的高阶次
            key_orders = [max_order, max_order - 1, max_order - 2, target_order - 1, target_order + 1]
            for freq in key_orders:
                if freq >= min_order and freq <= max_order and freq not in test_frequencies and freq not in extracted_orders:
                    test_frequencies.append(freq)
            
            # 如果没有可用的测试频率，跳过
            if not test_frequencies:
                break
            
            # 对每个测试频率进行拟合，选择振幅最大的结果
            for test_freq in test_frequencies:
                amp, freq, phase, offset = self._fit_sine_wave(x, residual, initial_frequency=test_freq)
                # 计算拟合的正弦波
                fitted_sine = self._sin_function(x, amp, freq, phase, offset)
                # 计算拟合后的振幅
                current_amplitude = abs(amp)
                
                # 如果当前振幅大于最佳振幅，更新最佳结果
                if current_amplitude > best_amplitude:
                    best_amplitude = current_amplitude
                    best_result = (amp, freq, phase, offset, fitted_sine)
            
            # 如果找到了有效的拟合结果
            if best_result is not None:
                amplitude, frequency, phase, offset, fitted_sine = best_result
                
                # 计算频率对应的阶次
                # 由于x轴是归一化的旋转位置（0到1对应一个完整的旋转）
                # 频率值直接对应阶次（每转的周期数）
                order = frequency
                # 对于齿轮分析，我们通常只关心正的阶次
                order = abs(order)
                # 阶次应该是整数，表示齿轮一周范围内的完整波数
                order = max(1, round(order))
                
                # 跳过阶次为0的成分（直流分量）
                if order == 0:
                    continue
                
                # 跳过不在指定范围内的阶次
                if order < min_order or order > max_order:
                    continue
                
                # 跳过已经提取过的阶次
                if order in extracted_orders:
                    continue
                
                # 添加到已提取的阶次集合
                extracted_orders.add(order)
                
                # 从剩余偏差中减去拟合的正弦波
                residual -= fitted_sine
                
                # 存储结果
                spectrum.append({
                    'harmonic': i + 1,
                    'amplitude': abs(amplitude),
                    'frequency': frequency,
                    'order': order,
                    'phase': phase,
                    'offset': offset,
                    'fitted_sine': fitted_sine
                })
        
        # 按阶次大小排序，先处理阶次大的
        spectrum.sort(key=lambda x: x['order'], reverse=True)
        # 然后取前max_harmonics个较大阶次的结果
        spectrum = spectrum[:max_harmonics]
        # 最后按振幅排序，确保显示最重要的成分
        spectrum.sort(key=lambda x: x['amplitude'], reverse=True)
        return spectrum
    
    def analyze_target_order(self, data: np.ndarray, target_order: int = 87, order_range: int = 5, min_order: int = 87, max_order: int = 100) -> List[Dict]:
        """
        分析目标阶次附近的频谱成分
        
        Args:
            data: 输入数据
            target_order: 目标阶次（如87阶）
            order_range: 目标阶次附近的范围
            min_order: 要考虑的最小阶次
            max_order: 要考虑的最大阶次
        
        Returns:
            目标阶次附近的频谱成分列表
        """
        # 预处理数据，移除起始不稳定部分并平滑
        processed_data = self._preprocess_data(data)
        
        # 准备x轴数据（归一化的位置）
        x = np.linspace(0, 1, len(processed_data))
        # 初始化剩余偏差
        residual = np.copy(processed_data)
        # 存储频谱结果
        spectrum = []
        
        # 迭代提取主导频率
        for i in range(20):  # 提取更多成分，以便找到目标阶次附近的成分
            # 尝试不同的初始频率，优先寻找目标阶次附近的成分
            best_amplitude = 0
            best_result = None
            
            # 尝试目标阶次附近的频率，在min_order和max_order之间
            test_frequencies = []
            for freq in range(target_order - order_range, target_order + order_range + 1):
                if freq >= min_order and freq <= max_order:
                    test_frequencies.append(freq)
            
            # 对每个测试频率进行拟合，选择振幅最大的结果
            for test_freq in test_frequencies:
                amp, freq, phase, offset = self._fit_sine_wave(x, residual, initial_frequency=test_freq)
                # 计算拟合的正弦波
                fitted_sine = self._sin_function(x, amp, freq, phase, offset)
                # 计算拟合后的振幅
                current_amplitude = abs(amp)
                
                # 如果当前振幅大于最佳振幅，更新最佳结果
                if current_amplitude > best_amplitude:
                    best_amplitude = current_amplitude
                    best_result = (amp, freq, phase, offset, fitted_sine)
            
            # 如果找到了有效的拟合结果
            if best_result is not None:
                amplitude, frequency, phase, offset, fitted_sine = best_result
                
                # 计算频率对应的阶次
                order = frequency
                order = abs(order)
                order = max(1, round(order))
                
                # 跳过阶次为0的成分（直流分量）
                if order == 0:
                    continue
                
                # 跳过超过最大阶次的成分
                if order > max_order:
                    continue
                
                # 从剩余偏差中减去拟合的正弦波
                residual -= fitted_sine
                
                # 存储结果
                spectrum.append({
                    'harmonic': i + 1,
                    'amplitude': abs(amplitude),
                    'frequency': frequency,
                    'order': order,
                    'phase': phase,
                    'offset': offset,
                    'fitted_sine': fitted_sine
                })
        
        # 过滤出目标阶次附近的成分，且在min_order和max_order之间
        target_spectrum = [item for item in spectrum if abs(item['order'] - target_order) <= order_range and item['order'] >= min_order and item['order'] <= max_order]
        
        # 按振幅排序
        target_spectrum.sort(key=lambda x: x['amplitude'], reverse=True)
        
        return target_spectrum
    
    def create_page(self, pdf: PdfPages, measurement_data) -> None:
        """
        在PDF中创建波纹度频谱分析页面
        """
        # 创建页面
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)  # A4尺寸
        
        # 标题
        fig.suptitle('Ripple Spectrum Analysis', fontsize=16, fontweight='bold')
        
        # 提取数据
        profile_left_data = []
        profile_right_data = []
        flank_left_data = []
        flank_right_data = []
        
        # 尝试从measurement_data中提取数据
        if hasattr(measurement_data, 'profile_data'):
            if hasattr(measurement_data.profile_data, 'left'):
                for tooth_data in measurement_data.profile_data.left.values():
                    if isinstance(tooth_data, (list, np.ndarray)):
                        profile_left_data.extend(tooth_data)
            if hasattr(measurement_data.profile_data, 'right'):
                for tooth_data in measurement_data.profile_data.right.values():
                    if isinstance(tooth_data, (list, np.ndarray)):
                        profile_right_data.extend(tooth_data)
        
        if hasattr(measurement_data, 'flank_data'):
            if hasattr(measurement_data.flank_data, 'left'):
                for tooth_data in measurement_data.flank_data.left.values():
                    if isinstance(tooth_data, (list, np.ndarray)):
                        flank_left_data.extend(tooth_data)
            if hasattr(measurement_data.flank_data, 'right'):
                for tooth_data in measurement_data.flank_data.right.values():
                    if isinstance(tooth_data, (list, np.ndarray)):
                        flank_right_data.extend(tooth_data)
        
        # 分析数据
        datasets = [
            ('Profile Left', profile_left_data, 'blue'),
            ('Profile Right', profile_right_data, 'red'),
            ('Flank Left', flank_left_data, 'green'),
            ('Flank Right', flank_right_data, 'magenta')
        ]
        
        # 创建子图
        gs = fig.add_gridspec(4, 1, height_ratios=[1, 1, 1, 1])
        
        for i, (title, data, color) in enumerate(datasets):
            if len(data) > 0:
                ax = fig.add_subplot(gs[i])
                ax.set_title(title, fontsize=12, fontweight='bold')
                
                # 计算频谱
                spectrum = self._calculate_ripple_spectrum(np.array(data))
                
                # 绘制原始数据
                x = np.linspace(0, 1, len(data))
                ax.plot(x, data, label='Original Data', color='gray', alpha=0.5, linewidth=0.5)
                
                # 绘制前3个主导频率的正弦波
                for j in range(min(3, len(spectrum))):
                    harmonic = spectrum[j]
                    ax.plot(x, harmonic['fitted_sine'], label=f'Harmonic {j+1}: Amp={harmonic["amplitude"]:.2f}', 
                            color=color, alpha=0.7, linewidth=0.8)
                
                # 绘制频谱
                ax2 = ax.twinx()
                orders = [item['order'] for item in spectrum[:10]]
                amplitudes = [item['amplitude'] for item in spectrum[:10]]
                ax2.bar(range(1, len(orders) + 1), amplitudes, alpha=0.3, color=color)
                ax2.set_ylabel('Amplitude', fontsize=8)
                
                # 设置图例和标签
                ax.legend(fontsize=8, loc='upper right')
                ax.set_xlabel('Normalized Position', fontsize=8)
                ax.set_ylabel('Deviation (μm)', fontsize=8)
                ax.tick_params(axis='both', labelsize=8)
                ax2.tick_params(axis='y', labelsize=8)
                ax.grid(True, alpha=0.3, linestyle='--')
            else:
                ax = fig.add_subplot(gs[i])
                ax.set_title(title, fontsize=12, fontweight='bold')
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)
                ax.set_xlabel('Normalized Position', fontsize=8)
                ax.set_ylabel('Deviation (μm)', fontsize=8)
        
        # 添加分析总结
        summary_text = "Ripple Spectrum Analysis Summary:\n"
        summary_text += "- Iterative sine wave fitting algorithm\n"
        summary_text += "- Extracts 10 dominant frequencies\n"
        summary_text += "- Amplitude-based frequency ranking\n"
        summary_text += "- Each harmonic is removed before next iteration"
        
        fig.text(0.5, 0.02, summary_text, ha='center', fontsize=10, 
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 调整布局
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        # 添加页面到PDF
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
    
    def generate_standalone_report(self, measurement_data, output_path: str) -> bool:
        """
        生成独立的波纹度频谱分析报告
        """
        try:
            with PdfPages(output_path) as pdf:
                self.create_page(pdf, measurement_data)
            return True
        except Exception as e:
            print(f"Error generating ripple spectrum report: {e}")
            return False


if __name__ == '__main__':
    """测试波纹度频谱分析"""
    # 创建测试数据
    x = np.linspace(0, 1, 1000)
    # 创建包含多个谐波的测试信号
    y = 10 * np.sin(2 * np.pi * 1 * x) + \
        5 * np.sin(2 * np.pi * 3 * x) + \
        3 * np.sin(2 * np.pi * 5 * x) + \
        np.random.normal(0, 1, 1000)
    
    # 测试频谱分析
    analyzer = KlingelnbergRippleSpectrumReport()
    spectrum = analyzer._calculate_ripple_spectrum(y)
    
    # 打印结果
    print("Ripple Spectrum Analysis Results:")
    print("Harmonic | Amplitude | Frequency | Order")
    print("----------------------------------------")
    for item in spectrum:
        print(f"{item['harmonic']:8} | {item['amplitude']:9.2f} | {item['frequency']:9.4f} | {item['order']:6.2f}")
    
    # 绘制结果
    plt.figure(figsize=(12, 6))
    plt.subplot(211)
    plt.plot(x, y, label='Original Signal')
    for i in range(min(3, len(spectrum))):
        plt.plot(x, spectrum[i]['fitted_sine'], label=f'Harmonic {i+1}')
    plt.legend()
    plt.title('Original Signal and Fitted Harmonics')
    
    plt.subplot(212)
    orders = [item['order'] for item in spectrum]
    amplitudes = [item['amplitude'] for item in spectrum]
    plt.bar(range(1, len(orders) + 1), amplitudes)
    plt.xlabel('Harmonic')
    plt.ylabel('Amplitude')
    plt.title('Ripple Spectrum')
    
    plt.tight_layout()
    plt.savefig('ripple_spectrum_test.png')
    print("Test completed. Results saved to ripple_spectrum_test.png")
