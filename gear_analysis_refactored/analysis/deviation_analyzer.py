import math
import numpy as np
from gear_analysis_refactored.config.logging_config import logger

class DeviationAnalyzer:
    """
    ISO1328 Deviation Analyzer
    Encapsulates the logic for calculating profile and flank deviations.
    """
    
    def __init__(self, gear_data, analysis_settings=None):
        self.gear_data = gear_data
        self.analysis_settings = analysis_settings or {}

    def calculate_tolerances(self, data_type, side):
        """根据ISO1328标准计算公差值"""
        try:
            if not self.gear_data:
                # 默认5级精度公差值
                return 8.0, 5.6, 3.2  # F, fH, ff
            
            # 获取齿轮参数
            module = self.gear_data.get('module', 2.0)
            teeth = self.gear_data.get('teeth', 20)
            width = self.gear_data.get('width', 20)
            
            # 使用分析设置中的公差模式
            tolerance_mode = self.analysis_settings.get('tolerance_mode', '使用MKA文件默认值')
            iso_grade = self.analysis_settings.get('iso_grade', 6)
            custom_tolerances = self.analysis_settings.get('custom_tolerances', {})
            
            # 如果使用自定义公差
            if tolerance_mode == "自定义自由公差":
                if data_type == 'profile':
                    return (custom_tolerances.get('F_alpha', 8.0), 
                           custom_tolerances.get('fH_alpha', 5.6), 
                           custom_tolerances.get('ff_alpha', 3.2))
                else:
                    return (custom_tolerances.get('F_beta', 8.0), 
                           custom_tolerances.get('fH_beta', 5.6), 
                           custom_tolerances.get('ff_beta', 3.2))
            
            # 使用ISO 1328标准或MKA文件默认值
            accuracy_grade = iso_grade if tolerance_mode == "ISO 1328 标准公差" else self.gear_data.get('accuracy_grade', 5)
            
            # 计算分度圆直径
            pitch_diameter = module * teeth
            
            # 精度等级系数 (扩展到4-12级)
            grade_factors = {4: 0.63, 5: 1.0, 6: 1.6, 7: 2.5, 8: 4.0, 9: 6.0, 10: 10.0, 11: 16.0, 12: 25.0}
            k = grade_factors.get(accuracy_grade, 1.0)
            
            if data_type == 'profile':
                # 齿形公差计算
                F_alpha_5 = 0.1 * module + 0.45 * math.sqrt(pitch_diameter) + 5
                F_alpha = k * F_alpha_5
                fH_alpha = F_alpha * 0.7  # 通常为F_alpha的70%
                ff_alpha = F_alpha * 0.4   # 通常为F_alpha的40%
                
                return F_alpha, fH_alpha, ff_alpha
            else:
                # 齿向公差计算
                d_b_ratio = pitch_diameter / width if width > 0 else 1
                F_beta_5 = 0.1 * math.sqrt(d_b_ratio) * width + 0.45 * math.sqrt(width) + 5
                F_beta = k * F_beta_5
                fH_beta = F_beta * 0.7  # 通常为F_beta的70%
                ff_beta = F_beta * 0.4   # 通常为F_beta的40%
                
                return F_beta, fH_beta, ff_beta
                
        except Exception as e:
            logger.error(f"公差计算错误: {e}")
            # 返回默认5级精度公差值
            return 8.0, 5.6, 3.2

    def calculate_profile_deviations(self, profile_data, side='left'):
        """计算齿形偏差 F_alpha, fH_alpha, ff_alpha - 使用评价区间"""
        try:
            # 提取测量数据
            if isinstance(profile_data, dict):
                if 'values' in profile_data:
                    data = np.array(profile_data['values'])
                else:
                    # 如果没有values字段，尝试其他字段
                    data = np.array(list(profile_data.values()))
            elif isinstance(profile_data, (list, np.ndarray)):
                data = np.array(profile_data)
            else:
                return 0.0, 0.0, 0.0
            
            if len(data) == 0:
                return 0.0, 0.0, 0.0
            
            # 获取评价区间参数 - 兼容两种字段名格式
            # 格式1: '齿形起测点展长' (旧格式)
            # 格式2: '齿形起测点直径' (新格式)
            start_spread = self.gear_data.get('齿形起测点展长', self.gear_data.get('齿形起测点直径', {})).get(side, 0.0)
            start_eval_spread = self.gear_data.get('齿形起评点展长', self.gear_data.get('齿形起评点直径', {})).get(side, 0.0)
            end_eval_spread = self.gear_data.get('齿形终评点展长', self.gear_data.get('齿形终评点直径', {})).get(side, 0.0)
            end_spread = self.gear_data.get('齿形终测点展长', self.gear_data.get('齿形终测点直径', {})).get(side, 0.0)
            
            # 计算点间距 - 使用实际数据长度，而不是硬编码479
            point_spacing = (end_spread - start_spread) / (len(data) - 1) if len(data) > 1 else 0.001
            if point_spacing == 0: point_spacing = 0.001 # 避免除零
            
            # 计算评价区间索引
            start_eval_index = max(0, int((start_eval_spread - start_spread) / point_spacing))
            end_eval_index = min(len(data) - 1, int((end_eval_spread - start_spread) / point_spacing))
            
            # 确保评价区间有效
            if end_eval_index <= start_eval_index:
                start_eval_index = 0
                end_eval_index = len(data) - 1
            
            # 提取评价区间数据
            eval_data = data[start_eval_index:end_eval_index + 1]
            
            if len(eval_data) == 0:
                return 0.0, 0.0, 0.0
            
            # 计算总偏差 F_alpha（峰峰值）
            F_alpha = np.max(eval_data) - np.min(eval_data)
            
            # 计算斜率偏差 fH_alpha
            # 根据 ISO 1328 标准：fHα 是评价范围两端平均齿廓迹线的差值
            # 平均齿廓迹线用最小二乘法拟合
            x = np.arange(len(eval_data))
            coeffs = np.polyfit(x, eval_data, 1)
            trend_line = coeffs[0] * x + coeffs[1]
            # fH_alpha = 趋势线终点值 - 趋势线起点值（可正可负）
            fH_alpha = trend_line[-1] - trend_line[0]
            
            # 计算形状偏差 ff_alpha（去除趋势后的残余分量峰峰值）
            residuals = eval_data - trend_line
            ff_alpha = np.max(residuals) - np.min(residuals)
            
            return F_alpha, fH_alpha, ff_alpha
            
        except Exception as e:
            logger.error(f"齿形偏差计算错误: {e}")
            return 0.0, 0.0, 0.0

    def calculate_flank_deviations(self, flank_data, side='left'):
        """计算齿向偏差 F_beta, fH_beta, ff_beta - 使用评价区间"""
        try:
            # 提取测量数据
            if isinstance(flank_data, dict):
                if 'values' in flank_data:
                    data = np.array(flank_data['values'])
                else:
                    # 如果没有values字段，尝试其他字段
                    data = np.array(list(flank_data.values()))
            elif isinstance(flank_data, (list, np.ndarray)):
                data = np.array(flank_data)
            else:
                return 0.0, 0.0, 0.0
            
            if len(data) == 0:
                return 0.0, 0.0, 0.0
            
            # 获取评价区间参数
            start_point = self.gear_data.get('齿向起测点', {}).get(side, 0.0)
            start_eval_point = self.gear_data.get('齿向起评点', {}).get(side, 0.0)
            end_eval_point = self.gear_data.get('齿向终评点', {}).get(side, 0.0)
            end_point = self.gear_data.get('齿向终测点', {}).get(side, 0.0)
            
            # 计算点间距 - 使用实际数据长度，而不是硬编码479
            point_spacing = (end_point - start_point) / (len(data) - 1) if len(data) > 1 else 0.001
            if point_spacing == 0: point_spacing = 0.001
            
            # 计算评价区间索引
            start_eval_index = max(0, int((start_eval_point - start_point) / point_spacing))
            end_eval_index = min(len(data) - 1, int((end_eval_point - start_point) / point_spacing))
            
            # 确保评价区间有效
            if end_eval_index <= start_eval_index:
                start_eval_index = 0
                end_eval_index = len(data) - 1
            
            # 提取评价区间数据
            eval_data = data[start_eval_index:end_eval_index + 1]
            
            if len(eval_data) == 0:
                return 0.0, 0.0, 0.0
            
            # 计算总偏差 F_beta（峰峰值）
            F_beta = np.max(eval_data) - np.min(eval_data)
            
            # 计算斜率偏差 fH_beta
            # 根据 ISO 1328 标准：fHβ 是评价范围两端平均螺旋线迹线的差值
            # 平均螺旋线迹线用最小二乘法拟合
            x = np.arange(len(eval_data))
            coeffs = np.polyfit(x, eval_data, 1)
            trend_line = coeffs[0] * x + coeffs[1]
            # fH_beta = 趋势线终点值 - 趋势线起点值（可正可负）
            fH_beta = trend_line[-1] - trend_line[0]
            
            # 计算形状偏差 ff_beta（去除趋势后的残余分量峰峰值）
            residuals = eval_data - trend_line
            ff_beta = np.max(residuals) - np.min(residuals)
            
            return F_beta, fH_beta, ff_beta
            
        except Exception as e:
            logger.error(f"齿向偏差计算错误: {e}")
            return 0.0, 0.0, 0.0
