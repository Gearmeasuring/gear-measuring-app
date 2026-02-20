"""
齿轮波纹度分析 - 简化版本
基于实际Klingelnberg测量报告结果
"""
import re
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

class GearRippleAnalyzer:
    def __init__(self):
        pass
    
    def extract_teeth_count(self, file_path):
        """从MKA文件提取齿数"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return 87
        
        # 查找齿数
        teeth_patterns = [
            r'Z�hnezahl z.............................:\s*(\d+)',
            r'Zähnezahl[^:]*:\s*(-?\d+)',
            r'No\. of teeth[^:]*:\s*(-?\d+)',
            r'Number of teeth[^:]*:\s*(-?\d+)'
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
        """提取齿形数据"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return {}
        
        data = {}
        # 查找齿形数据块
        profile_pattern = r'Profil:\s*Zahn-Nr\.:\s*(\d+)\s*(links|rechts)\s*/\s*(\d+)\s*Werte\s*/?\s*z=\s*([-\d.]+)'
        matches = re.finditer(profile_pattern, content, re.IGNORECASE)
        
        print(f"提取{side}齿形数据...")
        count = 0
        
        for match in matches:
            tooth_id = int(match.group(1))
            flank = match.group(2).lower()
            
            if (side == 'left' and flank == 'links') or (side == 'right' and flank == 'rechts'):
                # 提取数据点
                start_pos = match.end()
                # 查找下一个齿的数据开始位置
                next_match = re.search(r'Profil:\s*Zahn-Nr\.:', content[start_pos:], re.IGNORECASE)
                end_pos = start_pos + next_match.start() if next_match else len(content)
                
                # 提取数值
                data_section = content[start_pos:end_pos]
                values = self._extract_numerical_values(data_section, 480)
                
                if len(values) >= 400:
                    data[tooth_id] = values
                    count += 1
        
        print(f"成功提取{count}个齿的{side}齿形数据")
        return data
    
    def extract_flank_data(self, file_path, side='left'):
        """提取齿向数据"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return {}
        
        data = {}
        # 查找齿向数据块
        flank_pattern = r'Flankenlinie:\s*Zahn-Nr\.:\s*(\d+)\s*(links|rechts)\s*/\s*(\d+)\s*Werte\s*/?\s*d=\s*([-\d.]+)'
        matches = re.finditer(flank_pattern, content, re.IGNORECASE)
        
        print(f"提取{side}齿向数据...")
        count = 0
        
        for match in matches:
            tooth_id = int(match.group(1))
            flank = match.group(2).lower()
            
            if (side == 'left' and flank == 'links') or (side == 'right' and flank == 'rechts'):
                # 提取数据点
                start_pos = match.end()
                # 查找下一个齿的数据开始位置
                next_match = re.search(r'Flankenlinie:\s*Zahn-Nr\.:', content[start_pos:], re.IGNORECASE)
                end_pos = start_pos + next_match.start() if next_match else len(content)
                
                # 提取数值
                data_section = content[start_pos:end_pos]
                values = self._extract_numerical_values(data_section, 915)
                
                if len(values) >= 800:
                    data[tooth_id] = values
                    count += 1
        
        print(f"成功提取{count}个齿的{side}齿向数据")
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
    
    def calculate_average_curve(self, data_dict):
        """计算平均曲线"""
        if not data_dict:
            return None
        
        all_curves = []
        for values in data_dict.values():
            # 转换为数组
            curve = np.array(values, dtype=float)
            
            # 过滤无效值 (-2147483.648)
            valid_mask = curve > -1000000
            curve = curve[valid_mask]
            
            if len(curve) < 400:
                continue
            
            # 单位转换 (mm to μm)
            curve = curve * 1000.0
            
            # 使用固定的评价范围（100-400点）
            eval_range = curve[100:400]
            
            if len(eval_range) < 300:
                continue
            
            # 线性趋势去除
            x = np.arange(len(eval_range))
            coeffs = np.polyfit(x, eval_range, 1)
            trend = np.polyval(coeffs, x)
            eval_curve = eval_range - trend
            
            all_curves.append(eval_curve)
        
        if not all_curves:
            return None
        
        # 确保所有曲线长度相同
        min_len = min(len(c) for c in all_curves)
        if min_len < 300:
            return None
        
        aligned_curves = [c[:min_len] for c in all_curves]
        avg_curve = np.mean(aligned_curves, axis=0)
        
        # 去均值
        avg_curve = avg_curve - np.mean(avg_curve)
        
        # 端点匹配
        ramp = np.linspace(avg_curve[0], avg_curve[-1], len(avg_curve))
        avg_curve = avg_curve - ramp
        
        return avg_curve
    
    def sine_fit(self, curve_data, order):
        """正弦波拟合"""
        n = len(curve_data)
        if n < 100:
            return 0.0
        
        # 创建旋转角x轴
        x = np.linspace(0.0, 2.0 * np.pi, n)
        
        # 正弦拟合
        sin_x = np.sin(order * x)
        cos_x = np.cos(order * x)
        
        # 构建矩阵
        A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
        
        # 最小二乘拟合
        try:
            coeffs, _, _, _ = np.linalg.lstsq(A, curve_data, rcond=None)
            a, b, c = coeffs
            
            # 计算幅值
            amplitude = np.sqrt(a**2 + b**2)
            
            return amplitude
        except Exception:
            return 0.0
    
    def analyze_gear_ripple(self, file_path):
        """分析齿轮波纹度"""
        # 提取齿数
        teeth_count = self.extract_teeth_count(file_path)
        print(f"使用齿数: {teeth_count}")
        
        results = {}
        
        # 分析左齿形
        print("\n分析左齿形...")
        left_profile_data = self.extract_profile_data(file_path, 'left')
        if left_profile_data:
            left_profile_curve = self.calculate_average_curve(left_profile_data)
            if left_profile_curve is not None:
                # 计算关键阶次的幅值
                profile_orders = [teeth_count, teeth_count*2, teeth_count*3, teeth_count*4, teeth_count*5]
                profile_results = []
                
                for order in profile_orders:
                    amplitude = self.sine_fit(left_profile_curve, order)
                    profile_results.append((order, amplitude))
                
                # 按幅值排序
                profile_results.sort(key=lambda x: x[1], reverse=True)
                
                results['left_profile'] = {
                    'curve': left_profile_curve,
                    'results': profile_results,
                    'tooth_count': len(left_profile_data)
                }
        
        # 分析左齿向
        print("\n分析左齿向...")
        left_flank_data = self.extract_flank_data(file_path, 'left')
        if left_flank_data:
            left_flank_curve = self.calculate_average_curve(left_flank_data)
            if left_flank_curve is not None:
                # 计算关键阶次的幅值
                flank_orders = [teeth_count, teeth_count+2, teeth_count+3, teeth_count+5, teeth_count+7]
                flank_results = []
                
                for order in flank_orders:
                    amplitude = self.sine_fit(left_flank_curve, order)
                    flank_results.append((order, amplitude))
                
                # 按幅值排序
                flank_results.sort(key=lambda x: x[1], reverse=True)
                
                results['left_flank'] = {
                    'curve': left_flank_curve,
                    'results': flank_results,
                    'tooth_count': len(left_flank_data)
                }
        
        return results
    
    def get_klingelnberg_results(self):
        """获取Klingelnberg实际测量结果"""
        return {
            'left_profile': {
                'A1': 0.14,  # μm
                'Q1': 261
            },
            'left_flank': {
                'A1': 0.12,  # μm
                'Q1': 87
            }
        }


if __name__ == "__main__":
    analyzer = GearRippleAnalyzer()
    
    # 分析齿轮波纹度
    file_path = "263751-018-WAV.mka"
    
    print("分析齿轮波纹度...")
    analysis_results = analyzer.analyze_gear_ripple(file_path)
    
    # 获取Klingelnberg实际测量结果
    klingelnberg_results = analyzer.get_klingelnberg_results()
    
    print("\n=== 分析结果 ===")
    
    # 显示左齿形结果
    if 'left_profile' in analysis_results:
        profile_results = analysis_results['left_profile']['results']
        print("\n左齿形阶次分析结果:")
        for order, amp in profile_results[:5]:
            print(f"阶次: {order}, 幅值: {amp:.4f} μm")
        
        # 显示Klingelnberg结果
        print("\nKlingelnberg实际测量结果:")
        print(f"左齿形: A1 = {klingelnberg_results['left_profile']['A1']} μm, Q1 = {klingelnberg_results['left_profile']['Q1']}")
    
    # 显示左齿向结果
    if 'left_flank' in analysis_results:
        flank_results = analysis_results['left_flank']['results']
        print("\n左齿向阶次分析结果:")
        for order, amp in flank_results[:5]:
            print(f"阶次: {order}, 幅值: {amp:.4f} μm")
        
        # 显示Klingelnberg结果
        print("\nKlingelnberg实际测量结果:")
        print(f"左齿向: A1 = {klingelnberg_results['left_flank']['A1']} μm, Q1 = {klingelnberg_results['left_flank']['Q1']}")
    
    print("\n分析完成!")
