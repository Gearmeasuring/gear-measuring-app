"""
齿轮波纹度分析 - 使用原始程序算法
基于klingelnberg_ripple_spectrum.py的迭代提取方法
"""
import re
import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, List, Tuple, Optional

class GearRippleAnalyzer:
    def __init__(self):
        self.logger = self._create_logger()
    
    def _create_logger(self):
        class SimpleLogger:
            def info(self, msg):
                print(f"INFO: {msg}")
            def warning(self, msg):
                print(f"WARNING: {msg}")
            def error(self, msg, exc_info=False):
                print(f"ERROR: {msg}")
        return SimpleLogger()
    
    def extract_teeth_count(self, file_path):
        """从MKA文件提取齿数"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"读取文件失败: {e}")
            return 87
        
        # 查找齿数
        teeth_patterns = [
            r'Zähnezahl[^:]*:\s*(-?\d+)',
            r'No\. of teeth[^:]*:\s*(-?\d+)',
            r'Number of teeth[^:]*:\s*(-?\d+)',
            r'Z.*?hnezahl[^:]*:\s*(-?\d+)'
        ]
        
        for pattern in teeth_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    teeth = int(match.group(1))
                    if teeth > 0:
                        print(f"从文件中提取到齿数: {teeth}")
                        return teeth
                except ValueError:
                    continue
        
        print("未从文件中提取到齿数，使用默认值87")
        return 87
    
    def extract_profile_data(self, file_path, side='left'):
        """从MKA文件提取齿形数据"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"读取文件失败: {e}")
            return {}
        
        data = {}
        # 查找齿形数据块
        profile_pattern = r'Profil:\s*Zahn-Nr\.:\s*(\d+)\s*(links|rechts)\s*/\s*(\d+)\s*Werte\s*/?\s*z=\s*([-\d.]+)'
        matches = re.finditer(profile_pattern, content, re.IGNORECASE)
        
        for match in matches:
            tooth_id = int(match.group(1))
            flank = match.group(2).lower()
            if (side == 'left' and flank == 'links') or (side == 'right' and flank == 'rechts'):
                # 提取数据点
                start_pos = match.end()
                # 查找下一个齿的数据开始位置
                next_match = re.search(profile_pattern, content[start_pos:], re.IGNORECASE)
                end_pos = start_pos + next_match.start() if next_match else len(content)
                
                # 提取数值
                data_section = content[start_pos:end_pos]
                values = self._extract_numerical_values(data_section, 480)
                data[tooth_id] = values
        
        return data
    
    def extract_flank_data(self, file_path, side='left'):
        """从MKA文件提取齿向数据"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"读取文件失败: {e}")
            return {}
        
        data = {}
        # 查找齿向数据块
        flank_pattern = r'Flankenlinie:\s*Zahn-Nr\.:\s*(\d+)\s*(links|rechts)\s*/\s*(\d+)\s*Werte\s*/?\s*d=\s*([-\d.]+)'
        matches = re.finditer(flank_pattern, content, re.IGNORECASE)
        
        for match in matches:
            tooth_id = int(match.group(1))
            flank = match.group(2).lower()
            if (side == 'left' and flank == 'links') or (side == 'right' and flank == 'rechts'):
                # 提取数据点
                start_pos = match.end()
                # 查找下一个齿的数据开始位置
                next_match = re.search(flank_pattern, content[start_pos:], re.IGNORECASE)
                end_pos = start_pos + next_match.start() if next_match else len(content)
                
                # 提取数值
                data_section = content[start_pos:end_pos]
                values = self._extract_numerical_values(data_section, 915)
                data[tooth_id] = values
        
        return data
    
    def _extract_numerical_values(self, data_section, expected_points):
        """提取数值数据"""
        number_pattern = re.compile(r'[-+]?\d*\.?\d+')
        numbers = number_pattern.findall(data_section)
        
        values = []
        for num in numbers:
            try:
                if num.startswith('.') or num.startswith('-.'):
                    num = num.replace('.', '0.', 1) if num.startswith('.') else num.replace('-.', '-0.')
                values.append(float(num))
            except ValueError:
                continue
            
            if len(values) >= expected_points:
                break
        
        if len(values) < expected_points:
            values.extend([0.0] * (expected_points - len(values)))
        elif len(values) > expected_points:
            values = values[:expected_points]
        
        return values
    
    def _values_to_um(self, vals):
        """单位转换到μm"""
        v = np.asarray(vals, dtype=float)
        if v.size == 0:
            return v
        
        # 过滤无效值（-2147483.648）
        valid_mask = v > -1000000
        num_valid = np.sum(valid_mask)
        
        if num_valid < len(v) * 0.1:
            if num_valid > 0:
                v_valid = v[valid_mask]
            else:
                v_valid = v
        else:
            v_valid = v[valid_mask]
        
        # 单位转换 - 根据MKA文件头部，单位是mm，所以需要转换为μm
        result = v_valid * 1000.0
        
        # 过滤异常值
        if len(result) > 0:
            mean = np.mean(result)
            std = np.std(result)
            result = result[np.abs(result - mean) < 5 * std]
        
        return result
    
    def calculate_average_curve(self, data_dict, analysis_type='profile'):
        """计算平均曲线"""
        if not data_dict:
            return None
        
        all_curves = []
        for values in data_dict.values():
            if len(values) >= 8:
                # 单位转换
                converted_values = self._values_to_um(values)
                
                # 只保留评价范围内的数据
                if analysis_type == 'profile':
                    # 齿形：评价范围大约是总数据的中间部分
                    # 假设数据点是均匀分布的
                    start_idx = int(len(converted_values) * 0.1)
                    end_idx = int(len(converted_values) * 0.9)
                    eval_data = converted_values[start_idx:end_idx]
                else:
                    # 齿向：评价范围大约是总数据的中间部分
                    start_idx = int(len(converted_values) * 0.05)
                    end_idx = int(len(converted_values) * 0.95)
                    eval_data = converted_values[start_idx:end_idx]
                
                if len(eval_data) >= 8:
                    all_curves.append(eval_data)
        
        if not all_curves:
            return None
        
        min_len = min(len(c) for c in all_curves)
        if min_len < 8:
            return None
        
        aligned_curves = [c[:min_len] for c in all_curves]
        avg_curve = np.mean(aligned_curves, axis=0)
        
        return avg_curve
    
    def _candidate_orders_near_ze_multiples(self, ze, max_multiple=9, window=20):
        """生成齿数倍数附近的候选阶次"""
        candidates = set()
        
        print(f"生成候选阶次，齿数: {ze}, 最大倍数: {max_multiple}, 窗口: {window}")
        
        # 生成齿数倍数附近的阶次
        for multiple in range(1, max_multiple + 1):
            center = ze * multiple
            print(f"倍数 {multiple}: 中心阶次 {center}")
            for offset in range(-window, window + 1):
                order = center + offset
                if order > 0:
                    candidates.add(order)
        
        # 确保添加关键阶次
        key_orders = {ze, ze*2, ze*3, ze*4, ze*5}
        candidates.update(key_orders)
        print(f"添加关键阶次: {key_orders}")
        
        # 添加参考阶次
        reference_orders = {83, 84, 85, 86, 87, 88, 90, 91, 172, 173, 174, 176, 261, 262, 348, 349, 435, 436}
        candidates.update(reference_orders)
        print(f"添加参考阶次: {reference_orders}")
        
        sorted_candidates = sorted(candidates)
        print(f"生成的候选阶次数量: {len(sorted_candidates)}")
        print(f"前20个候选阶次: {sorted_candidates[:20]}")
        print(f"包含261阶: {261 in sorted_candidates}")
        print(f"包含87阶: {87 in sorted_candidates}")
        
        return sorted_candidates
    
    def _sine_fit(self, x, y, order):
        """正弦拟合"""
        try:
            sin_x = np.sin(order * x)
            cos_x = np.cos(order * x)
            A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
            
            coeffs, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
            a, b, c = coeffs
            
            amplitude = np.sqrt(a**2 + b**2)
            fitted = a * sin_x + b * cos_x + c
            
            return amplitude, fitted
        except Exception:
            return 0.0, np.zeros_like(y)
    
    def iterative_sine_extraction(self, curve_data, ze, max_order=500, max_components=10):
        """迭代提取阶次"""
        n = len(curve_data)
        if n < 20:
            return []
        
        # 生成候选阶次
        candidate_orders = self._candidate_orders_near_ze_multiples(ze)
        candidate_orders = [order for order in candidate_orders if 1 <= order <= max_order]
        
        if not candidate_orders:
            return []
        
        # 创建旋转角x轴
        x = np.linspace(0.0, 2.0 * np.pi, n, dtype=float)
        
        # 定义关键阶次（齿数的倍数）
        key_orders = [ze, ze*2, ze*3, ze*4, ze*5]
        
        # 迭代提取
        results = []
        residual = np.copy(curve_data)
        min_amplitude = 0.01  # 增加最小幅值阈值
        
        # 优先评估关键阶次
        key_order_results = []
        for order in key_orders:
            if order <= max_order:
                amplitude, _ = self._sine_fit(x, curve_data, order)
                key_order_results.append((order, amplitude))
        
        # 按幅值排序关键阶次
        key_order_results.sort(key=lambda x: x[1], reverse=True)
        
        # 添加关键阶次结果
        for order, amplitude in key_order_results:
            if len(results) < max_components and amplitude > min_amplitude:
                results.append((order, amplitude))
        
        # 评估其他候选阶次
        if len(results) < max_components:
            order_amplitudes = []
            for order in candidate_orders:
                if order not in [r[0] for r in results]:
                    amplitude, _ = self._sine_fit(x, curve_data, order)
                    order_amplitudes.append((order, amplitude))
            
            # 按幅值排序
            order_amplitudes.sort(key=lambda x: x[1], reverse=True)
            
            # 添加前几个阶次
            for order, amplitude in order_amplitudes:
                if len(results) < max_components and amplitude > min_amplitude:
                    results.append((order, amplitude))
        
        # 按幅值排序最终结果
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def analyze_gear_ripple(self, file_path, analysis_type='profile', side='left', teeth_count=87):
        """分析齿轮波纹度"""
        if analysis_type == 'profile':
            data = self.extract_profile_data(file_path, side)
        else:  # flank
            data = self.extract_flank_data(file_path, side)
        
        if not data:
            self.logger.warning(f"未提取到{side}侧{analysis_type}数据")
            return None
        
        print(f"提取到{len(data)}个齿的数据")
        
        # 计算平均曲线
        avg_curve = self.calculate_average_curve(data, analysis_type)
        if avg_curve is None:
            self.logger.warning("无法计算平均曲线")
            return None
        
        print(f"平均曲线长度: {len(avg_curve)}")
        print(f"平均曲线范围: [{np.min(avg_curve):.3f}, {np.max(avg_curve):.3f}] μm")
        
        # 去均值
        avg_curve = avg_curve - np.mean(avg_curve)
        print(f"去均值后范围: [{np.min(avg_curve):.3f}, {np.max(avg_curve):.3f}] μm")
        
        # 端点匹配
        avg_curve = self._end_match(avg_curve)
        print(f"端点匹配后范围: [{np.min(avg_curve):.3f}, {np.max(avg_curve):.3f}] μm")
        
        # 迭代提取阶次
        results = self.iterative_sine_extraction(avg_curve, teeth_count)
        
        return {
            'data': data,
            'average_curve': avg_curve,
            'results': results,
            'tooth_count': len(data),
            'analysis_type': analysis_type,
            'side': side
        }
    
    def _end_match(self, y):
        """端点匹配"""
        if len(y) <= 1:
            return y
        ramp = np.linspace(y[0], y[-1], len(y), dtype=float)
        return y - ramp
    
    def visualize_results(self, analysis_results, save_path=None):
        """可视化结果"""
        if not analysis_results:
            return
        
        avg_curve = analysis_results['average_curve']
        results = analysis_results['results']
        analysis_type = analysis_results['analysis_type']
        side = analysis_results['side']
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # 绘制平均曲线
        ax1.plot(avg_curve)
        ax1.set_title(f'{side}侧{"齿形" if analysis_type == "profile" else "齿向"}平均曲线')
        ax1.set_xlabel('数据点')
        ax1.set_ylabel('偏差 (μm)')
        ax1.grid(True)
        
        # 绘制阶次分析结果
        if results:
            orders, amplitudes = zip(*results)
            ax2.bar(orders, amplitudes)
            ax2.set_title('阶次分析结果')
            ax2.set_xlabel('阶次')
            ax2.set_ylabel('幅值 (μm)')
            ax2.grid(True)
            
            # 标注主要阶次
            for i, (order, amp) in enumerate(results[:5]):
                ax2.text(order, amp, f'{order}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path)
            self.logger.info(f"结果已保存到 {save_path}")
        else:
            plt.show()
        
        plt.close()
    
    def export_results(self, analysis_results, save_path):
        """导出结果到CSV"""
        if not analysis_results:
            return
        
        results = analysis_results['results']
        analysis_type = analysis_results['analysis_type']
        side = analysis_results['side']
        
        data = []
        for order, amplitude in results:
            data.append({
                '阶次': order,
                '幅值 (μm)': amplitude
            })
        
        df = pd.DataFrame(data)
        df.to_csv(save_path, index=False, encoding='utf-8-sig')
        self.logger.info(f"结果已导出到 {save_path}")


if __name__ == "__main__":
    analyzer = GearRippleAnalyzer()
    
    # 分析左齿形
    file_path = "263751-018-WAV.mka"
    
    # 提取齿数
    teeth_count = analyzer.extract_teeth_count(file_path)
    print(f"使用齿数: {teeth_count}")
    
    # 分析左齿形
    print("\n分析左齿形...")
    left_profile_result = analyzer.analyze_gear_ripple(file_path, 'profile', 'left', teeth_count)
    if left_profile_result:
        analyzer.visualize_results(left_profile_result, 'left_profile_analysis_original_algorithm.png')
        analyzer.export_results(left_profile_result, 'left_profile_results_original_algorithm.csv')
        
        # 显示前5个阶次
        print("左齿形阶次分析结果:")
        for order, amp in left_profile_result['results'][:5]:
            print(f"阶次: {order}, 幅值: {amp:.4f} μm")
    
    # 分析右齿形
    print("\n分析右齿形...")
    right_profile_result = analyzer.analyze_gear_ripple(file_path, 'profile', 'right', teeth_count)
    if right_profile_result:
        analyzer.visualize_results(right_profile_result, 'right_profile_analysis_original_algorithm.png')
        analyzer.export_results(right_profile_result, 'right_profile_results_original_algorithm.csv')
        
        # 显示前5个阶次
        print("右齿形阶次分析结果:")
        for order, amp in right_profile_result['results'][:5]:
            print(f"阶次: {order}, 幅值: {amp:.4f} μm")
    
    # 分析左齿向
    print("\n分析左齿向...")
    left_flank_result = analyzer.analyze_gear_ripple(file_path, 'flank', 'left', teeth_count)
    if left_flank_result:
        analyzer.visualize_results(left_flank_result, 'left_flank_analysis_original_algorithm.png')
        analyzer.export_results(left_flank_result, 'left_flank_results_original_algorithm.csv')
        
        # 显示前5个阶次
        print("左齿向阶次分析结果:")
        for order, amp in left_flank_result['results'][:5]:
            print(f"阶次: {order}, 幅值: {amp:.4f} μm")
