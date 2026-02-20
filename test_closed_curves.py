#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：使用新算法生成闭合曲线
"""

import sys
import os
import logging
import numpy as np
import matplotlib.pyplot as plt

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_closed_curve')

# 模拟必要的类和函数
class MockInfo:
    """模拟基本信息对象"""
    def __init__(self):
        self.teeth = 87  # 齿数
        self.pitch_diameter = 50.0  # 节圆直径
        self.helix_angle = 15.0  # 螺旋角（度）
        self.base_diameter = 48.3  # 基圆直径
        self.module = 1.0  # 模数

class MockSettings:
    """模拟设置对象"""
    def __init__(self):
        self.log_level = 'INFO'
        self.profile_helix_settings = {
            'order_filtering': {'max_order': 500},
            'detrend_settings': {'enabled': True},
            'filter_params': {'enabled': True}
        }
        self.display_settings = {
            'table_settings': {'max_components': 10}
        }

class MockMeasurementData:
    """模拟测量数据对象"""
    def __init__(self):
        self.basic_info = MockInfo()
        
        # 生成模拟的齿形数据
        self.profile_left = {}
        self.profile_right = {}
        
        # 生成模拟的齿向数据
        self.helix_left = {}
        self.helix_right = {}
        
        # 生成10个齿的齿形数据
        for tooth_id in range(10):
            # 生成带有噪声的正弦曲线作为齿形数据
            n_points = 100
            x = np.linspace(0, 1, n_points)
            # 生成基本信号
            signal = 0.5 * np.sin(2 * np.pi * 3 * x)  # 3阶信号
            signal += 0.2 * np.sin(2 * np.pi * 6 * x)  # 6阶信号
            # 添加随机噪声
            noise = 0.08 * np.random.randn(n_points)
            signal += noise
            
            # 转换为列表并存储
            self.profile_left[tooth_id] = signal.tolist()
            self.profile_right[tooth_id] = signal.tolist()
        
        # 生成10个齿的齿向数据
        for tooth_id in range(10):
            # 生成带有噪声的正弦曲线作为齿向数据
            n_points = 100
            x = np.linspace(0, 1, n_points)
            # 生成基本信号
            signal = 0.5 * np.sin(2 * np.pi * 5 * x)  # 5阶信号
            signal += 0.3 * np.sin(2 * np.pi * 10 * x)  # 10阶信号
            signal += 0.2 * np.sin(2 * np.pi * 15 * x)  # 15阶信号
            # 添加随机噪声
            noise = 0.1 * np.random.randn(n_points)
            signal += noise
            
            # 转换为列表并存储
            self.helix_left[tooth_id] = signal.tolist()
            self.helix_right[tooth_id] = signal.tolist()

# 模拟 KlingelnbergRippleSpectrumReport 类的核心方法
class MockRippleSpectrumReport:
    """模拟 KlingelnbergRippleSpectrumReport 类"""
    def __init__(self, settings):
        self.settings = settings
        self._table_components = {}
    
    def _values_to_um(self, values):
        """将值转换为微米单位"""
        return values
    
    def _calculate_rms(self, amplitudes):
        """计算RMS值"""
        if len(amplitudes) == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(amplitudes))))
    
    def _calculate_delta_z(self, z, z0=None):
        """计算轴向位置差Δz"""
        if z0 is None:
            z0 = 0.0
        return float(z) - float(z0)
    
    def _calculate_alpha2(self, delta_z, d0, beta0):
        """计算轴向角度差α₂"""
        if d0 <= 0:
            return 0.0
        tan_beta0 = math.tan(beta0)
        alpha2 = (2.0 * float(delta_z) * tan_beta0) / float(d0)
        return alpha2
    
    def _calculate_final_angle(self, xi, alpha2, tau):
        """计算最终旋转角度α"""
        alpha = float(xi) + float(alpha2) + float(tau)
        alpha = alpha % (2.0 * math.pi)
        if alpha < 0:
            alpha += 2.0 * math.pi
        return alpha
    
    def _calculate_average_curve(self, data_dict, eval_markers):
        """计算平均曲线"""
        if not data_dict:
            return None
        
        # 计算所有齿的平均曲线
        all_data = []
        for values in data_dict.values():
            if values:
                all_data.extend(values)
        
        if not all_data:
            return None
        
        return np.array(all_data)
    
    def _build_helix_closed_curve_angle(self, all_tooth_data, eval_length, base_diameter, teeth_count, info, pitch_data, use_weighted_average=True):
        """使用角度计算构建齿向闭合曲线"""
        import math
        
        if not all_tooth_data:
            return None
        
        min_len = min(len(d) for d in all_tooth_data)
        if min_len < 8:
            min_len = 8
        
        try:
            # 获取齿轮参数
            d0 = getattr(info, 'pitch_diameter', base_diameter) if info else base_diameter
            beta0 = math.radians(getattr(info, 'helix_angle', 0.0)) if info else 0.0
            
            # 确保d0是有效的
            if d0 <= 0:
                d0 = 50.0
            
            # 确保beta0是有效的
            if abs(beta0) < 0.0001:
                beta0 = math.radians(5.0)
            
            # 轴向坐标到旋转角的转换
            total_angle = 2.0 * math.pi
            
            # 计算每个轴向位置的旋转角
            axial_coords = np.linspace(0.0, float(eval_length), min_len, dtype=float)
            
            # 计算轴向位置差Δz（相对于中点）
            z0 = float(eval_length) / 2.0
            delta_z_values = [self._calculate_delta_z(z, z0) for z in axial_coords]
            
            # 计算轴向角度差α₂
            alpha2_values = [self._calculate_alpha2(dz, d0, beta0) for dz in delta_z_values]
            
            # 检查计算结果
            if not alpha2_values:
                return None
            
            # 计算旋转角步长
            alpha2_range = max(alpha2_values) - min(alpha2_values)
            if alpha2_range <= 0:
                alpha2_values = np.linspace(0.0, 2 * np.pi, min_len).tolist()
                alpha2_range = max(alpha2_values) - min(alpha2_values)
            
            # 计算全局点数量，确保覆盖整圈
            n_global = max(400, min_len * teeth_count * 2)
            
            sum_arr = np.zeros(n_global, dtype=float)
            cnt_arr = np.zeros(n_global, dtype=float)
            
            # 处理每个齿的数据
            for i, segment in enumerate(all_tooth_data):
                seg = np.asarray(segment, dtype=float)
                if len(seg) > min_len:
                    seg = seg[:min_len]
                
                # 计算每个齿的旋转角偏移
                tooth_offset = (float(i) * total_angle / float(teeth_count)) % total_angle
                
                # 使用更新的算法计算每个点的最终旋转角α
                thetas = []
                for j, alpha2 in enumerate(alpha2_values):
                    if j < len(seg):
                        # 计算最终旋转角度α = ξ + α₂ + τ
                        alpha = self._calculate_final_angle(0.0, alpha2, 0.0)
                        # 添加齿偏移
                        theta = (tooth_offset + alpha) % total_angle
                        thetas.append(theta)
                
                # 转换为numpy数组
                thetas = np.array(thetas, dtype=float)
                indices = np.round((thetas / total_angle) * n_global).astype(int) % n_global
                
                # 累加数据
                np.add.at(sum_arr, indices, seg)
                np.add.at(cnt_arr, indices, 1.0)
            
            # 计算平均值，处理分母为0的情况
            with np.errstate(divide='ignore', invalid='ignore'):
                avg_curve = np.where(cnt_arr > 0, sum_arr / cnt_arr, 0.0)
            
            return avg_curve
            
        except Exception as e:
            logger.error(f"_build_helix_closed_curve_angle 失败: {e}")
            return None
    
    def _sine_fit_spectrum_analysis(self, curve_data, max_order=100, max_components=10, x_coords=None):
        """使用正弦拟合进行频谱分析"""
        if len(curve_data) < 8:
            return {}
        
        # 使用提供的x坐标或生成等距坐标
        if x_coords is None:
            x = np.linspace(0.0, 1.0, len(curve_data), dtype=float)
        else:
            x = np.array(x_coords, dtype=float)
            if len(x) != len(curve_data):
                x = np.linspace(0.0, 1.0, len(curve_data), dtype=float)
        
        # 初始化残差信号为原始信号
        residual = np.array(curve_data, dtype=float)
        
        # 存储提取的频谱分量
        spectrum_results = {}
        
        # 迭代提取最大阶次
        max_iterations = 15
        amplitude_threshold = 0.001
        target_components = max_components
        
        for iteration in range(max_iterations):
            # 生成候选阶次
            candidate_orders = set()
            for freq in range(1, max_order + 1):
                if freq not in spectrum_results:
                    candidate_orders.add(freq)
            
            candidate_orders = sorted(candidate_orders)
            if not candidate_orders:
                break
            
            # 对每个候选阶次进行正弦拟合
            order_amplitudes = {}
            
            for order in candidate_orders:
                try:
                    frequency = float(order)
                    sin_x = np.sin(2.0 * np.pi * frequency * x)
                    cos_x = np.cos(2.0 * np.pi * frequency * x)
                    
                    # 求解最小二乘
                    try:
                        A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
                        coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
                        a, b, c = coeffs
                    except:
                        # 使用备选方法
                        a = 2.0 * np.mean(residual * sin_x)
                        b = 2.0 * np.mean(residual * cos_x)
                        c = np.mean(residual)
                    
                    # 计算幅值
                    amplitude = float(np.sqrt(a * a + b * b))
                    
                    # 检查幅值是否合理
                    max_reasonable_amplitude = 10.0
                    if amplitude > max_reasonable_amplitude:
                        continue
                    
                    order_amplitudes[order] = (amplitude, a, b, c)
                    
                except Exception as e:
                    continue
            
            if not order_amplitudes:
                break
            
            # 选择幅值最大的频率
            best_order = max(order_amplitudes.keys(), key=lambda o: order_amplitudes[o][0])
            best_amplitude = order_amplitudes[best_order][0]
            best_coeffs = order_amplitudes[best_order][1:4]
            
            # 检查幅值是否小于阈值
            if best_amplitude < amplitude_threshold:
                break
            
            # 保存提取的频谱分量
            spectrum_results[int(best_order)] = best_amplitude
            
            # 从残差信号中移除已提取的正弦波
            a, b, c = best_coeffs
            best_frequency = float(best_order)
            fitted = a * np.sin(2.0 * np.pi * best_frequency * x) + b * np.cos(2.0 * np.pi * best_frequency * x) + c
            residual = residual - fitted
            
            # 检查是否已提取足够的分量
            if len(spectrum_results) >= target_components:
                break
        
        # 按幅值排序，取前max_components个
        sorted_items = sorted(spectrum_results.items(), key=lambda x: x[1], reverse=True)[:max_components]
        filtered_items = [(order, amp) for order, amp in sorted_items if amp >= 0.001 and amp <= 10.0]
        filtered_items = [(int(order), amp) for order, amp in filtered_items]
        
        result_dict = dict(filtered_items)
        return result_dict

def test_closed_curve_generation():
    """测试新算法生成闭合曲线"""
    logger.info("=== 测试新算法生成闭合曲线 ===")
    
    try:
        # 创建必要的对象
        settings = MockSettings()
        measurement_data = MockMeasurementData()
        
        # 创建报告对象
        ripple_report = MockRippleSpectrumReport(settings=settings)
        
        # 测试生成闭合曲线
        test_cases = [
            ('profile', 'left', '左齿形'),
            ('profile', 'right', '右齿形'),
            ('flank', 'left', '左齿向'),
            ('flank', 'right', '右齿向')
        ]
        
        for data_type, side, name in test_cases:
            logger.info(f"\n=== 生成 {name} 闭合曲线 ===")
            
            # 获取数据
            if data_type == 'profile':
                data_dict = getattr(measurement_data, f'profile_{side}', {})
            else:  # flank
                data_dict = getattr(measurement_data, f'helix_{side}', {})
            
            logger.info(f"使用 {len(data_dict)} 个齿的数据")
            
            # 准备参数
            teeth_count = measurement_data.basic_info.teeth
            eval_markers = (0.0, 10.0, 20.0, 30.0)
            eval_length = 1.0
            base_diameter = measurement_data.basic_info.base_diameter
            
            # 生成闭合曲线
            if data_type == 'flank':
                # 对于齿向数据，使用新算法
                logger.info("使用新算法生成齿向闭合曲线")
                closed_curve = ripple_report._build_helix_closed_curve_angle(
                    [np.array(values) for values in data_dict.values() if values],
                    eval_length,
                    base_diameter,
                    teeth_count,
                    measurement_data.basic_info,
                    None,
                    use_weighted_average=True
                )
            else:
                # 对于齿形数据，使用原有的平均曲线方法
                logger.info("使用原有算法生成齿形闭合曲线")
                closed_curve = ripple_report._calculate_average_curve(data_dict, eval_markers)
            
            # 验证结果
            if closed_curve is not None and len(closed_curve) > 0:
                logger.info(f"✅ 成功生成 {name} 闭合曲线")
                logger.info(f"曲线长度: {len(closed_curve)}")
                logger.info(f"曲线范围: [{np.min(closed_curve):.6f}, {np.max(closed_curve):.6f}]")
                logger.info(f"曲线均值: {np.mean(closed_curve):.6f}")
                logger.info(f"曲线标准差: {np.std(closed_curve):.6f}")
                
                # 打印前10个点的数据
                logger.info("前10个点的数据:")
                for i, val in enumerate(closed_curve[:10]):
                    logger.info(f"点 {i}: {val:.6f}")
            else:
                logger.error(f"❌ 生成 {name} 闭合曲线失败")
        
        # 可视化闭合曲线
        visualize_closed_curves(ripple_report, measurement_data)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def visualize_closed_curves(ripple_report, measurement_data):
    """可视化闭合曲线"""
    logger.info("\n=== 可视化闭合曲线 ===")
    
    try:
        # 创建一个2x2的图表
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('新算法生成的闭合曲线', fontsize=16)
        
        test_cases = [
            ('profile', 'left', '左齿形', axes[0, 0]),
            ('profile', 'right', '右齿形', axes[0, 1]),
            ('flank', 'left', '左齿向', axes[1, 0]),
            ('flank', 'right', '右齿向', axes[1, 1])
        ]
        
        for data_type, side, name, ax in test_cases:
            # 获取数据
            if data_type == 'profile':
                data_dict = getattr(measurement_data, f'profile_{side}', {})
            else:  # flank
                data_dict = getattr(measurement_data, f'helix_{side}', {})
            
            # 准备参数
            teeth_count = measurement_data.basic_info.teeth
            eval_markers = (0.0, 10.0, 20.0, 30.0)
            eval_length = 1.0
            base_diameter = measurement_data.basic_info.base_diameter
            
            # 生成闭合曲线
            if data_type == 'flank':
                closed_curve = ripple_report._build_helix_closed_curve_angle(
                    [np.array(values) for values in data_dict.values() if values],
                    eval_length,
                    base_diameter,
                    teeth_count,
                    measurement_data.basic_info,
                    None,
                    use_weighted_average=True
                )
            else:
                closed_curve = ripple_report._calculate_average_curve(data_dict, eval_markers)
            
            # 绘制曲线
            if closed_curve is not None and len(closed_curve) > 0:
                x = np.arange(len(closed_curve))
                ax.plot(x, closed_curve, 'b-', linewidth=1.5)
                ax.set_title(name)
                ax.set_xlabel('点序号')
                ax.set_ylabel('偏差值 (μm)')
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, len(closed_curve) - 1)
                ax.set_ylim(np.min(closed_curve) - 0.1, np.max(closed_curve) + 0.1)
            else:
                ax.set_title(name)
                ax.text(0.5, 0.5, '生成失败', transform=ax.transAxes, ha='center', va='center', color='red')
                ax.set_xlabel('点序号')
                ax.set_ylabel('偏差值 (μm)')
                ax.grid(True, alpha=0.3)
        
        # 调整布局
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        # 保存图表
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_path = os.path.join(output_dir, 'closed_curves.png')
        plt.savefig(output_path, dpi=150)
        logger.info(f"✅ 闭合曲线图表保存到: {output_path}")
        
        # 显示图表
        plt.show()
        
    except Exception as e:
        logger.error(f"❌ 可视化闭合曲线失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    logger.info("启动闭合曲线生成测试...")
    test_closed_curve_generation()
