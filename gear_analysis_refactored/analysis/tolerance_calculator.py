"""ISO1328公差计算器"""
import numpy as np
from typing import Dict, Tuple, Optional


class ISO1328ToleranceCalculator:
    """ISO1328齿轮公差计算器"""
    
    def __init__(self):
        """初始化公差计算器"""
        self.base_tolerances = {
            'profile': {
                'basic': [0.8, 1.0, 1.25, 1.6, 2.0, 2.5, 3.2, 4.0, 5.0, 6.3, 8.0, 10, 12.5, 16, 20, 25, 32, 40, 50, 63, 80, 100],
                'factors': [0.008, 0.010, 0.012, 0.016, 0.020, 0.025, 0.032, 0.040, 0.050, 0.063, 0.080, 0.100, 0.125, 0.160, 0.200, 0.250, 0.320, 0.400, 0.500, 0.630, 0.800, 1.000]
            },
            'pitch': {
                'basic': [0.8, 1.0, 1.25, 1.6, 2.0, 2.5, 3.2, 4.0, 5.0, 6.3, 8.0, 10, 12.5, 16, 20, 25, 32, 40, 50, 63, 80, 100],
                'factors': [0.008, 0.010, 0.012, 0.016, 0.020, 0.025, 0.032, 0.040, 0.050, 0.063, 0.080, 0.100, 0.125, 0.160, 0.200, 0.250, 0.320, 0.400, 0.500, 0.630, 0.800, 1.000]
            },
            'runout': {
                'basic': [1.0, 1.25, 1.6, 2.0, 2.5, 3.2, 4.0, 5.0, 6.3, 8.0, 10, 12.5, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125],
                'factors': [0.010, 0.012, 0.016, 0.020, 0.025, 0.032, 0.040, 0.050, 0.063, 0.080, 0.100, 0.125, 0.160, 0.200, 0.250, 0.320, 0.400, 0.500, 0.630, 0.800, 1.000, 1.250]
            }
        }
    
    def calculate_tolerance(self, module: float, quality: int, tolerance_type: str) -> float:
        """计算公差值
        
        Args:
            module: 模数 (mm)
            quality: 精度等级 (3-12)
            tolerance_type: 公差类型 ('profile', 'pitch', 'runout')
            
        Returns:
            公差值 (μm)
        """
        if tolerance_type not in self.base_tolerances:
            raise ValueError(f"不支持的公差类型: {tolerance_type}")
        
        if quality < 3 or quality > 12:
            raise ValueError(f"精度等级必须在3-12之间，当前值: {quality}")
        
        # 获取基础公差数据
        tolerance_data = self.base_tolerances[tolerance_type]
        basic_tolerances = tolerance_data['basic']
        factors = tolerance_data['factors']
        
        # 计算公差
        if module <= basic_tolerances[0]:
            base_tolerance = basic_tolerances[0]
        elif module >= basic_tolerances[-1]:
            base_tolerance = basic_tolerances[-1]
        else:
            # 线性插值计算基础公差
            for i in range(len(basic_tolerances) - 1):
                if basic_tolerances[i] <= module <= basic_tolerances[i+1]:
                    base_tolerance = basic_tolerances[i] + (module - basic_tolerances[i]) * (basic_tolerances[i+1] - basic_tolerances[i]) / (basic_tolerances[i+1] - basic_tolerances[i])
                    break
        
        # 计算最终公差
        tolerance = base_tolerance * factors[quality - 3]
        
        return tolerance
    
    def calculate_profile_tolerance(self, module: float, quality: int) -> float:
        """计算齿廓公差"""
        return self.calculate_tolerance(module, quality, 'profile')
    
    def calculate_pitch_tolerance(self, module: float, quality: int) -> float:
        """计算周节公差"""
        return self.calculate_tolerance(module, quality, 'pitch')
    
    def calculate_runout_tolerance(self, module: float, quality: int) -> float:
        """计算径向跳动公差"""
        return self.calculate_tolerance(module, quality, 'runout')
    
    def evaluate_deviation(self, deviation: float, tolerance: float) -> str:
        """评估偏差是否合格
        
        Args:
            deviation: 实际偏差 (μm)
            tolerance: 允许公差 (μm)
            
        Returns:
            评估结果 ('合格', '不合格')
        """
        if abs(deviation) <= tolerance:
            return '合格'
        else:
            return '不合格'
    
    def calculate_tolerances(self, module: float, teeth: int, width: float, quality: int) -> Dict[str, float]:
        """计算所有公差值
        
        Args:
            module: 模数 (mm)
            teeth: 齿数
            width: 齿宽 (mm)
            quality: 精度等级 (3-12)
            
        Returns:
            包含各种公差值的字典
        """
        return {
            'profile': self.calculate_profile_tolerance(module, quality),
            'pitch': self.calculate_pitch_tolerance(module, quality),
            'runout': self.calculate_runout_tolerance(module, quality),
            # 其他公差计算...
        }
