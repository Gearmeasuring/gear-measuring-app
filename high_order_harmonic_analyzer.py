#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
高阶谐波分离分析器
专门用于从齿轮测量数据中分离高阶谐波分量
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from scipy import signal

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HighOrderHarmonicAnalyzer:
    """高阶谐波分离分析器"""
    
    def __init__(self, teeth_count: int = 30):
        """
        初始化分析器
        
        Args:
            teeth_count: 齿轮齿数，用于确定基础阶次
        """
        self.teeth_count = teeth_count
        self.base_order = teeth_count  # 基础阶次（齿数对应的阶次）
        
        # 高阶谐波定义：通常为基频阶次的2-3倍以上
        self.high_order_threshold = self.base_order * 2.5
        
        # 默认滤波参数
        self.default_filter_params = {
            'high_pass_cutoff': self.base_order * 0.8,  # 高通滤波截止频率
            'band_pass_low': self.base_order * 2,       # 带通滤波下限
            'band_pass_high': self.base_order * 10,     # 带通滤波上限
            'filter_order': 4                           # 滤波器阶数
        }
        
    def extract_high_orders(self, data_dict: Dict[int, List[float]], 
                          method: str = 'bandpass', 
                          **filter_params) -> Dict[str, np.ndarray]:
        """
        从齿轮测量数据中提取高阶谐波分量
        
        Args:
            data_dict: 齿轮测量数据字典 {齿号: [数据点]}
            method: 分离方法，可选 'bandpass'(带通滤波), 'highpass'(高通滤波), 'threshold'(阈值筛选)
            filter_params: 滤波器参数
            
        Returns:
            Dict: 包含高阶谐波信息的字典
        """
        if not data_dict:
            logger.warning("数据字典为空")
            return {}
            
        # 合并滤波器参数
        params = {**self.default_filter_params, **filter_params}
        
        # 收集所有齿的数据进行平均
        all_data = []
        for tooth_num, values in data_dict.items():
            if values is not None and len(values) > 8:
                all_data.append(np.array(values))
        
        if not all_data:
            logger.warning("没有有效数据")
            return {}
            
        # 平均数据
        avg_data = np.mean(all_data, axis=0)
        
        # 去趋势
        detrended_data = self._detrend_data(avg_data)
        
        # 执行FFT分析
        orders, amplitudes = self._perform_fft_analysis(detrended_data)
        
        # 根据选择的方法分离高阶谐波
        if method == 'bandpass':
            result = self._bandpass_filter_method(orders, amplitudes, detrended_data, params)
        elif method == 'highpass':
            result = self._highpass_filter_method(orders, amplitudes, detrended_data, params)
        elif method == 'threshold':
            result = self._threshold_method(orders, amplitudes, params)
        else:
            logger.warning(f"未知方法: {method}，使用默认带通滤波")
            result = self._bandpass_filter_method(orders, amplitudes, detrended_data, params)
        
        # 添加基本信息
        result.update({
            'base_order': self.base_order,
            'high_order_threshold': self.high_order_threshold,
            'method_used': method,
            'total_orders': len(orders),
            'high_order_count': len(result.get('high_order_orders', []))
        })
        
        return result
    
    def _detrend_data(self, data: np.ndarray) -> np.ndarray:
        """去除数据的线性趋势"""
        x = np.arange(len(data))
        try:
            p = np.polyfit(x, data, 1)
            trend = np.polyval(p, x)
            return data - trend
        except Exception as e:
            logger.warning(f"去趋势失败: {e}，使用去均值")
            return data - np.mean(data)
    
    def _perform_fft_analysis(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """执行FFT分析，返回阶次和幅值"""
        n = len(data)
        
        # 使用rfft（实值FFT）
        fft_vals = np.fft.rfft(data)
        
        # 正确的归一化：除以n
        amplitudes = np.abs(fft_vals) / n
        
        # 阶次：FFT索引直接对应阶次（跳过DC分量）
        orders = np.arange(1, len(amplitudes))
        amplitudes = amplitudes[1:]  # 跳过DC分量
        
        return orders, amplitudes
    
    def _bandpass_filter_method(self, orders: np.ndarray, amplitudes: np.ndarray, 
                              time_data: np.ndarray, params: Dict) -> Dict:
        """带通滤波方法分离高阶谐波"""
        
        # 创建带通滤波器
        sampling_rate = len(time_data)  # 采样率等于数据点数
        nyquist = sampling_rate / 2
        
        low_cutoff = min(params['band_pass_low'], nyquist * 0.95)
        high_cutoff = min(params['band_pass_high'], nyquist * 0.95)
        
        # 设计带通滤波器
        b, a = signal.butter(params['filter_order'], 
                           [low_cutoff/nyquist, high_cutoff/nyquist], 
                           btype='band')
        
        # 应用滤波器
        filtered_data = signal.filtfilt(b, a, time_data)
        
        # 对滤波后的数据进行FFT分析
        filtered_orders, filtered_amplitudes = self._perform_fft_analysis(filtered_data)
        
        # 识别高阶谐波
        high_order_mask = (filtered_orders >= params['band_pass_low']) & \
                         (filtered_orders <= params['band_pass_high'])
        
        high_order_orders = filtered_orders[high_order_mask]
        high_order_amplitudes = filtered_amplitudes[high_order_mask]
        
        # 找出主要的高阶谐波
        if len(high_order_amplitudes) > 0:
            dominant_indices = np.argsort(high_order_amplitudes)[-3:]  # 取幅值最大的3个
            dominant_orders = high_order_orders[dominant_indices]
            dominant_amplitudes = high_order_amplitudes[dominant_indices]
        else:
            dominant_orders = np.array([])
            dominant_amplitudes = np.array([])
        
        return {
            'high_order_orders': high_order_orders,
            'high_order_amplitudes': high_order_amplitudes,
            'dominant_orders': dominant_orders,
            'dominant_amplitudes': dominant_amplitudes,
            'filtered_time_data': filtered_data,
            'filter_params': {
                'low_cutoff': low_cutoff,
                'high_cutoff': high_cutoff,
                'filter_order': params['filter_order']
            }
        }
    
    def _highpass_filter_method(self, orders: np.ndarray, amplitudes: np.ndarray,
                              time_data: np.ndarray, params: Dict) -> Dict:
        """高通滤波方法分离高阶谐波"""
        
        sampling_rate = len(time_data)
        nyquist = sampling_rate / 2
        
        cutoff_freq = min(params['high_pass_cutoff'], nyquist * 0.95)
        
        # 设计高通滤波器
        b, a = signal.butter(params['filter_order'], cutoff_freq/nyquist, btype='high')
        
        # 应用滤波器
        filtered_data = signal.filtfilt(b, a, time_data)
        
        # FFT分析滤波后的数据
        filtered_orders, filtered_amplitudes = self._perform_fft_analysis(filtered_data)
        
        # 识别高阶谐波
        high_order_mask = filtered_orders >= params['high_pass_cutoff']
        
        high_order_orders = filtered_orders[high_order_mask]
        high_order_amplitudes = filtered_amplitudes[high_order_mask]
        
        # 主要高阶谐波
        if len(high_order_amplitudes) > 0:
            dominant_indices = np.argsort(high_order_amplitudes)[-3:]
            dominant_orders = high_order_orders[dominant_indices]
            dominant_amplitudes = high_order_amplitudes[dominant_indices]
        else:
            dominant_orders = np.array([])
            dominant_amplitudes = np.array([])
        
        return {
            'high_order_orders': high_order_orders,
            'high_order_amplitudes': high_order_amplitudes,
            'dominant_orders': dominant_orders,
            'dominant_amplitudes': dominant_amplitudes,
            'filtered_time_data': filtered_data,
            'filter_params': {
                'cutoff_freq': cutoff_freq,
                'filter_order': params['filter_order']
            }
        }
    
    def _threshold_method(self, orders: np.ndarray, amplitudes: np.ndarray, params: Dict) -> Dict:
        """阈值筛选方法分离高阶谐波"""
        
        # 设置阈值：高于平均幅值的1.5倍
        amplitude_threshold = np.mean(amplitudes) * 1.5
        
        # 高阶谐波条件：阶次高于阈值且幅值高于阈值
        high_order_mask = (orders >= self.high_order_threshold) & (amplitudes >= amplitude_threshold)
        
        high_order_orders = orders[high_order_mask]
        high_order_amplitudes = amplitudes[high_order_mask]
        
        # 主要高阶谐波
        if len(high_order_amplitudes) > 0:
            dominant_indices = np.argsort(high_order_amplitudes)[-3:]
            dominant_orders = high_order_orders[dominant_indices]
            dominant_amplitudes = high_order_amplitudes[dominant_indices]
        else:
            dominant_orders = np.array([])
            dominant_amplitudes = np.array([])
        
        return {
            'high_order_orders': high_order_orders,
            'high_order_amplitudes': high_order_amplitudes,
            'dominant_orders': dominant_orders,
            'dominant_amplitudes': dominant_amplitudes,
            'threshold_params': {
                'order_threshold': self.high_order_threshold,
                'amplitude_threshold': amplitude_threshold
            }
        }
    
    def analyze_gear_quality(self, profile_data: Dict, flank_data: Dict) -> Dict:
        """
        综合分析齿轮质量，包括齿形和齿向的高阶谐波
        
        Args:
            profile_data: 齿形数据 {侧: {齿号: [数据点]}}
            flank_data: 齿向数据 {侧: {齿号: [数据点]}}
            
        Returns:
            Dict: 综合质量分析结果
        """
        results = {}
        
        # 分析齿形数据
        for side in ['left', 'right']:
            if side in profile_data:
                profile_result = self.extract_high_orders(profile_data[side], method='bandpass')
                results[f'profile_{side}'] = profile_result
        
        # 分析齿向数据
        for side in ['left', 'right']:
            if side in flank_data:
                flank_result = self.extract_high_orders(flank_data[side], method='bandpass')
                results[f'flank_{side}'] = flank_result
        
        # 计算综合质量指标
        quality_metrics = self._calculate_quality_metrics(results)
        results['quality_metrics'] = quality_metrics
        
        return results
    
    def _calculate_quality_metrics(self, results: Dict) -> Dict:
        """计算齿轮质量指标"""
        metrics = {
            'total_high_order_energy': 0.0,
            'dominant_high_orders': [],
            'high_order_rms': 0.0,
            'quality_grade': 'Good'
        }
        
        all_high_order_amplitudes = []
        all_dominant_orders = []
        
        # 收集所有高阶谐波信息
        for key, result in results.items():
            if 'high_order_amplitudes' in result:
                amplitudes = result['high_order_amplitudes']
                if len(amplitudes) > 0:
                    metrics['total_high_order_energy'] += np.sum(amplitudes ** 2)
                    all_high_order_amplitudes.extend(amplitudes)
                
                if 'dominant_orders' in result and len(result['dominant_orders']) > 0:
                    all_dominant_orders.extend(zip(result['dominant_orders'], 
                                                 result['dominant_amplitudes']))
        
        # 计算RMS值
        if all_high_order_amplitudes:
            metrics['high_order_rms'] = np.sqrt(np.mean(np.square(all_high_order_amplitudes)))
        
        # 找出主要的高阶谐波
        if all_dominant_orders:
            all_dominant_orders.sort(key=lambda x: x[1], reverse=True)
            metrics['dominant_high_orders'] = all_dominant_orders[:5]  # 取前5个
        
        # 质量等级评估
        if metrics['high_order_rms'] < 0.1:
            metrics['quality_grade'] = 'Excellent'
        elif metrics['high_order_rms'] < 0.3:
            metrics['quality_grade'] = 'Good'
        elif metrics['high_order_rms'] < 0.5:
            metrics['quality_grade'] = 'Fair'
        else:
            metrics['quality_grade'] = 'Poor'
        
        return metrics
    
    def generate_report(self, analysis_results: Dict) -> str:
        """生成分析报告"""
        report = []
        report.append("=" * 60)
        report.append("高阶谐波分析报告")
        report.append("=" * 60)
        report.append(f"齿轮齿数: {self.teeth_count}")
        report.append(f"基础阶次: {self.base_order}")
        report.append(f"高阶谐波阈值: {self.high_order_threshold:.1f}")
        report.append("")
        
        # 各侧分析结果
        for key, result in analysis_results.items():
            if key == 'quality_metrics':
                continue
                
            report.append(f"{key.upper()} 分析结果:")
            report.append(f"  高阶谐波数量: {result.get('high_order_count', 0)}")
            
            if 'dominant_orders' in result and len(result['dominant_orders']) > 0:
                report.append("  主要高阶谐波:")
                for i, (order, amp) in enumerate(zip(result['dominant_orders'], 
                                                   result['dominant_amplitudes'])):
                    report.append(f"    第{i+1}阶: 阶次={order:.1f}, 幅值={amp:.6f}")
            
            report.append("")
        
        # 质量评估
        if 'quality_metrics' in analysis_results:
            metrics = analysis_results['quality_metrics']
            report.append("综合质量评估:")
            report.append(f"  高阶谐波RMS值: {metrics['high_order_rms']:.6f}")
            report.append(f"  质量等级: {metrics['quality_grade']}")
            
            if metrics['dominant_high_orders']:
                report.append("  主要高阶谐波分布:")
                for order, amp in metrics['dominant_high_orders'][:3]:
                    report.append(f"    阶次 {order:.1f}: 幅值 {amp:.6f}")
        
        report.append("=" * 60)
        return '\n'.join(report)


def demo_high_order_analysis():
    """演示高阶谐波分析功能"""
    
    # 创建示例数据（模拟齿轮测量数据）
    np.random.seed(42)
    
    # 生成包含基础阶次和高阶谐波的测试数据
    t = np.linspace(0, 10, 480)
    
    # 基础信号（低频）
    base_signal = 0.5 * np.sin(2 * np.pi * 3 * t)  # 3阶基础信号
    
    # 高阶谐波信号
    high_order_signals = [
        0.1 * np.sin(2 * np.pi * 8 * t),   # 8阶
        0.08 * np.sin(2 * np.pi * 12 * t), # 12阶
        0.06 * np.sin(2 * np.pi * 18 * t), # 18阶
    ]
    
    # 噪声
    noise = 0.02 * np.random.normal(size=len(t))
    
    # 合成信号
    signal = base_signal + sum(high_order_signals) + noise
    
    # 创建数据字典
    data_dict = {i: signal for i in range(1, 31)}  # 30个齿
    
    # 创建分析器
    analyzer = HighOrderHarmonicAnalyzer(teeth_count=30)
    
    # 执行分析
    result = analyzer.extract_high_orders(data_dict, method='bandpass')
    
    # 打印结果
    print("演示分析结果:")
    print(f"基础阶次: {analyzer.base_order}")
    print(f"高阶谐波阈值: {analyzer.high_order_threshold:.1f}")
    print(f"找到的高阶谐波数量: {len(result.get('high_order_orders', []))}")
    
    if 'dominant_orders' in result and len(result['dominant_orders']) > 0:
        print("主要高阶谐波:")
        for i, (order, amp) in enumerate(zip(result['dominant_orders'], 
                                           result['dominant_amplitudes'])):
            print(f"  第{i+1}阶: 阶次={order:.1f}, 幅值={amp:.6f}")


if __name__ == "__main__":
    demo_high_order_analysis()