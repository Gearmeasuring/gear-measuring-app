#!/usr/bin/env python
"""
基于现有MKA文件数据执行迭代残差法正弦拟合频谱分析
"""
import os
import sys
import logging
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass

# 添加项目根目录到路径
sys.path.append(os.path.abspath('gear_analysis_refactored'))

# 导入必要的模块
from reports.klingelnberg_ import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings
from reports.klingelnberg_ import SineFitParams
from config.logging_config import setup_logging

# 导入文件处理模块
try:
    from models.gear_data import GearData
    from threads.worker_threads import FileProcessingThread
except ImportError:
    # 如果导入失败，使用简化的数据结构
    class MockGearData:
        """模拟齿轮数据类"""
        def __init__(self, file_path):
            # 这里可以添加简单的文件读取逻辑
            self.file_path = file_path
            self.basic_info = type('obj', (), {
                'teeth': 92,
                'module': 1.0,
                'pressure_angle': 20.0,
                'profile_eval_start': 43.829,
                'profile_eval_end': 51.2,
                'profile_range_left': (42.81, 51.75),
                'profile_range_right': (42.81, 51.75),
                'lead_range_left': (0.0, 45.7),
                'lead_range_right': (0.0, 45.7),
                'helix_eval_start': 2.1,
                'helix_eval_end': 43.7
            })
            # 生成模拟数据
            self.profile_data = type('obj', (), {
                'left': self._generate_mock_data(92, 200),
                'right': self._generate_mock_data(92, 200)
            })
            self.flank_data = type('obj', (), {
                'left': self._generate_mock_data(92, 200),
                'right': self._generate_mock_data(92, 200)
            })
        
        def _generate_mock_data(self, num_teeth, points_per_tooth):
            """生成模拟数据"""
            data = {}
            for tooth_id in range(num_teeth):
                # 生成包含多个阶次的信号
                x = np.linspace(0, 1, points_per_tooth)
                signal = 0.5 * np.sin(2 * np.pi * 10 * x)  # 10阶
                signal += 0.3 * np.sin(2 * np.pi * 20 * x)  # 20阶
                signal += 0.2 * np.sin(2 * np.pi * 30 * x)  # 30阶
                signal += 0.1 * np.sin(2 * np.pi * 40 * x)  # 40阶
                signal += 0.05 * np.random.randn(len(x))  # 噪声
                data[tooth_id] = {'values': signal}
            return data

class RippleSpectrumAnalyzer:
    """波纹度频谱分析器"""
    
    def __init__(self, mka_file_path):
        """初始化分析器"""
        self.mka_file_path = mka_file_path
        self.settings = RippleSpectrumSettings()
        self.report = KlingelnbergRippleSpectrumReport(settings=self.settings)
        self.gear_data = None
    
    def load_data(self):
        """加载MKA文件数据"""
        try:
            # 尝试使用GearData类加载
            try:
                self.gear_data = GearData(self.mka_file_path)
                self.gear_data.load_mka_file()
                print(f"成功加载MKA文件: {self.mka_file_path}")
                print(f"齿数: {self.gear_data.basic_info.teeth}")
                print(f"模数: {self.gear_data.basic_info.module}")
                print(f"压力角: {self.gear_data.basic_info.pressure_angle}")
                return True
            except Exception as e:
                print(f"使用GearData加载失败: {e}")
                print("使用模拟数据进行分析")
                # 使用模拟数据
                self.gear_data = MockGearData(self.mka_file_path)
                return True
        except Exception as e:
            print(f"加载数据失败: {e}")
            return False
    
    def analyze_ripple_spectrum(self):
        """执行波纹度频谱分析"""
        if not self.gear_data:
            print("请先加载数据")
            return
        
        # 选择一个齿的数据进行分析
        tooth_id = 1
        side = 'left'
        data_type = 'profile'
        
        # 获取数据
        if data_type == 'profile':
            data_dict = getattr(self.gear_data.profile_data, side, {})
        else:  # flank
            data_dict = getattr(self.gear_data.flank_data, side, {})
        
        if tooth_id not in data_dict:
            print(f"齿 {tooth_id} 不存在，使用齿 0")
            tooth_id = 0
        
        tooth_data = data_dict.get(tooth_id, {})
        if isinstance(tooth_data, dict) and 'values' in tooth_data:
            curve_data = np.array(tooth_data['values'], dtype=float)
        else:
            curve_data = np.array(tooth_data, dtype=float)
        
        print(f"分析数据长度: {len(curve_data)}")
        print(f"数据范围: {np.min(curve_data):.4f} ~ {np.max(curve_data):.4f}")
        
        # 创建正弦拟合参数
        params = SineFitParams(
            curve_data=curve_data,
            ze=self.gear_data.basic_info.teeth,
            max_order=500,
            max_components=10
        )
        
        # 执行迭代残差法正弦拟合分析
        print("\n执行迭代残差法正弦拟合频谱分析...")
        spectrum_results = self.report._iterative_residual_sine_fit(params)
        
        # 显示结果
        print("\n频谱分析结果:")
        print("阶次\t幅值(μm)")
        print("-" * 30)
        for order, amplitude in sorted(spectrum_results.items(), key=lambda x: x[1], reverse=True):
            print(f"{order}\t{amplitude:.4f}")
        
        # 可视化结果
        self._visualize_results(curve_data, spectrum_results)
    
    def _visualize_results(self, original_data, spectrum_results):
        """可视化分析结果"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # 绘制原始数据
        ax1.plot(original_data, label='Original Data')
        ax1.set_title('Original Measurement Data')
        ax1.set_xlabel('Points')
        ax1.set_ylabel('Deviation (μm)')
        ax1.grid(True)
        ax1.legend()
        
        # 绘制频谱结果
        orders = list(spectrum_results.keys())
        amplitudes = list(spectrum_results.values())
        ax2.bar(orders, amplitudes, color='blue')
        ax2.set_title('Ripple Spectrum Analysis Results')
        ax2.set_xlabel('Order')
        ax2.set_ylabel('Amplitude (μm)')
        ax2.grid(True)
        
        # 突出显示前5个最大幅值的阶次
        top_5 = sorted(spectrum_results.items(), key=lambda x: x[1], reverse=True)[:5]
        for order, amplitude in top_5:
            ax2.bar(order, amplitude, color='red')
        
        plt.tight_layout()
        plt.show()

def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("=== Klingelnberg 波纹频谱分析 ===")
    print("使用迭代残差法正弦拟合分析齿轮波纹度")
    
    # 选择MKA文件
    mka_files = [f for f in os.listdir('.') if f.endswith('.mka')]
    if mka_files:
        print("\n找到的MKA文件:")
        for i, file in enumerate(mka_files):
            print(f"{i+1}. {file}")
        
        # 用户选择了第二个文件
        choice = "2"
        if choice.isdigit() and 1 <= int(choice) <= len(mka_files):
            mka_file = mka_files[int(choice) - 1]
        else:
            mka_file = mka_files[0]
        
        print(f"\n选择文件: {mka_file}")
    else:
        print("\n未找到MKA文件，使用模拟数据进行分析")
        mka_file = "模拟数据"
    
    # 创建分析器
    analyzer = RippleSpectrumAnalyzer(mka_file)
    
    # 加载数据
    if analyzer.load_data():
        # 执行分析
        analyzer.analyze_ripple_spectrum()
    else:
        print("加载数据失败，无法执行分析")

if __name__ == "__main__":
    main()
