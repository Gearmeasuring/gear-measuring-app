"""统计分析模块"""
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional


class StatisticalAnalyzer:
    """齿轮测量数据统计分析器"""
    
    def __init__(self):
        """初始化统计分析器"""
        pass
    
    def calculate_mean(self, data: List[float]) -> float:
        """计算平均值
        
        Args:
            data: 数据列表
            
        Returns:
            平均值
        """
        return np.mean(data)
    
    def calculate_median(self, data: List[float]) -> float:
        """计算中位数
        
        Args:
            data: 数据列表
            
        Returns:
            中位数
        """
        return np.median(data)
    
    def calculate_std_dev(self, data: List[float]) -> float:
        """计算标准差
        
        Args:
            data: 数据列表
            
        Returns:
            标准差
        """
        return np.std(data, ddof=1)  # 样本标准差
    
    def calculate_variance(self, data: List[float]) -> float:
        """计算方差
        
        Args:
            data: 数据列表
            
        Returns:
            方差
        """
        return np.var(data, ddof=1)  # 样本方差
    
    def calculate_range(self, data: List[float]) -> float:
        """计算极差
        
        Args:
            data: 数据列表
            
        Returns:
            极差
        """
        return max(data) - min(data)
    
    def calculate_rms(self, data: List[float]) -> float:
        """计算均方根值
        
        Args:
            data: 数据列表
            
        Returns:
            均方根值
        """
        return np.sqrt(np.mean(np.square(data)))
    
    def calculate_waviness(self, data: List[float], cutoff: int = 50) -> float:
        """计算波纹度
        
        Args:
            data: 数据列表
            cutoff: 截止频率
            
        Returns:
            波纹度值
        """
        # 简单实现：计算高频分量的RMS值
        fft_result = np.fft.fft(data)
        freq = np.fft.fftfreq(len(data))
        
        # 只保留高频分量
        high_freq_mask = np.abs(freq) > cutoff / len(data)
        high_freq_fft = fft_result * high_freq_mask
        
        # 逆变换回时域
        high_freq_data = np.fft.ifft(high_freq_fft).real
        
        return self.calculate_rms(high_freq_data)
    
    def calculate_skewness(self, data: List[float]) -> float:
        """计算偏度
        
        Args:
            data: 数据列表
            
        Returns:
            偏度值
        """
        return stats.skew(data)
    
    def calculate_kurtosis(self, data: List[float]) -> float:
        """计算峰度
        
        Args:
            data: 数据列表
            
        Returns:
            峰度值
        """
        return stats.kurtosis(data)
    
    def calculate_correlation(self, data1: List[float], data2: List[float]) -> float:
        """计算两个数据集的相关系数
        
        Args:
            data1: 第一个数据集
            data2: 第二个数据集
            
        Returns:
            相关系数
        """
        return np.corrcoef(data1, data2)[0, 1]
    
    def perform_fft_analysis(self, data: List[float], sampling_rate: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """执行FFT分析
        
        Args:
            data: 时域数据
            sampling_rate: 采样率
            
        Returns:
            (频率轴, 幅值谱)
        """
        n = len(data)
        fft_result = np.fft.fft(data)
        freq = np.fft.fftfreq(n, 1/sampling_rate)
        
        # 只返回正频率部分
        positive_freq_mask = freq >= 0
        freq = freq[positive_freq_mask]
        amp = np.abs(fft_result[positive_freq_mask]) / n
        
        return freq, amp
    
    def analyze_data(self, data: List[float]) -> Dict[str, float]:
        """全面分析数据
        
        Args:
            data: 数据列表
            
        Returns:
            包含各种统计量的字典
        """
        if not data:
            return {}
        
        return {
            'mean': self.calculate_mean(data),
            'median': self.calculate_median(data),
            'std_dev': self.calculate_std_dev(data),
            'variance': self.calculate_variance(data),
            'range': self.calculate_range(data),
            'rms': self.calculate_rms(data),
            'skewness': self.calculate_skewness(data),
            'kurtosis': self.calculate_kurtosis(data)
        }
