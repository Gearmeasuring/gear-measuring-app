"""齿轮波纹度分析 - 正确实现"""
import re
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, List, Tuple, Optional

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
            print(f"读取文件失败: {e}")
            return {}
        
        data = {}
        # 查找齿形数据块
        profile_pattern = r'Profil:\s*Zahn-Nr\.:\s*(\d+)\s*(links|rechts)\s*/\s*(\d+)\s*Werte\s*/?\s*z=\s*([-\d.]+)'
        matches = re.finditer(profile_pattern, content, re.IGNORECASE)
        
        print(f"提取{side}侧齿形数据...")
        count = 0
        
        for match in matches:
            tooth_id = int(match.group(1))
            flank = match.group(2).lower()
            
            # 确保只提取正确侧的数据
            if (side == 'left' and flank == 'links') or (side == 'right' and flank == 'rechts'):
                # 提取数据点
                start_pos = match.end()
                # 查找下一个齿的数据开始位置
                next_match = re.search(profile_pattern, content[start_pos:], re.IGNORECASE)
                end_pos = start_pos + next_match.start() if next_match else len(content)
                
                # 提取数值
                data_section = content[start_pos:end_pos]
                values = self._extract_numerical_values(data_section, 480)
                
                # 只添加有效数据
                if len(values) >= 100:
                    data[tooth_id] = values
                    count += 1
        
        print(f"成功提取{count}个齿的{side}侧齿形数据")
        return data
    
    def extract_flank_data(self, file_path, side='left'):
        """从MKA文件提取齿向数据"""
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
    
    def calculate_average_curve(self, data_dict, analysis_type='profile'):
        """计算平均曲线"""
        if not data_dict:
            return None
        
        all_curves = []
        for values in data_dict.values():
            if len(values) >= 8:
                # 转换为数组
                converted_values = np.array(values, dtype=float)
                
                # 过滤无效值
                valid_mask = converted_values > -1000000
                converted_values = converted_values[valid_mask]
                
                if len(converted_values) < 20:
                    continue
                
                # 只保留评价范围内的数据
                if analysis_type == 'profile':
                    # 齿形：评价范围大约是总数据的中间部分
                    # 对于480个数据点，评价范围通常是中间的300-350个点
                    total_len = len(converted_values)
                    start_idx = int(total_len * 0.25)
                    end_idx = int(total_len * 0.85)
                    eval_data = converted_values[start_idx:end_idx]
                else:
                    # 齿向：评价范围大约是总数据的中间部分
                    total_len = len(converted_values)
                    start_idx = int(total_len * 0.15)
                    end_idx = int(total_len * 0.85)
                    eval_data = converted_values[start_idx:end_idx]
                
                if len(eval_data) < 20:
                    continue
                
                # 过滤异常值
                mean = np.mean(eval_data)
                std = np.std(eval_data)
                filtered_data = eval_data[np.abs(eval_data - mean) < 3 * std]
                
                if len(filtered_data) < 20:
                    continue
                
                all_curves.append(filtered_data)
        
        if not all_curves:
            return None
        
        min_len = min(len(c) for c in all_curves)
        if min_len < 20:
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
        """正弦拟合"""
        n = len(curve_data)
        if n < 10:
            return 0.0
        
        # 创建旋转角x轴
        x = np.linspace(0.0, 2.0 * np.pi, n, dtype=float)
        
        # 正弦拟合
        sin_x = np.sin(order * x)
        cos_x = np.cos(order * x)
        
        # 构建矩阵
        A = np.column_stack((sin_x, cos_x))
        
        # 最小二乘拟合
        try:
            coeffs, _, _, _ = np.linalg.lstsq(A, curve_data, rcond=None)
            a, b = coeffs
            
            # 计算幅值
            amplitude = np.sqrt(a**2 + b**2)
            
            return amplitude
        except Exception:
            return 0.0
    
    def analyze_gear_ripple(self, file_path, analysis_type='profile', side='left', teeth_count=87):
        """分析齿轮波纹度"""
        if analysis_type == 'profile':
            data = self.extract_profile_data(file_path, side)
        else:  # flank
            data = self.extract_flank_data(file_path, side)
        
        if not data:
            print(f"未提取到{side}侧{analysis_type}数据")
            return None
        
        print(f"提取到{len(data)}个齿的数据")
        
        # 计算平均曲线
        avg_curve = self.calculate_average_curve(data, analysis_type)
        if avg_curve is None:
            print("无法计算平均曲线")
            return None
        
        print(f"平均曲线长度: {len(avg_curve)}")
        print(f"平均曲线范围: [{np.min(avg_curve):.3f}, {np.max(avg_curve):.3f}] μm")
        
        # 评估齿数倍数的阶次
        key_orders = [teeth_count, teeth_count*2, teeth_count*3, teeth_count*4, teeth_count*5]
        results = []
        
        for order in key_orders:
            amplitude = self.sine_fit(avg_curve, order)
            results.append((order, amplitude))
        
        # 按幅值排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'data': data,
            'average_curve': avg_curve,
            'results': results,
            'tooth_count': len(data),
            'analysis_type': analysis_type,
            'side': side
        }
    
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
            print(f"结果已保存到 {save_path}")
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
        print(f"结果已导出到 {save_path}")


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
        analyzer.visualize_results(left_profile_result, 'left_profile_analysis_correct.png')
        analyzer.export_results(left_profile_result, 'left_profile_results_correct.csv')
        
        # 显示结果
        print("左齿形阶次分析结果:")
        for order, amp in left_profile_result['results']:
            print(f"阶次: {order}, 幅值: {amp:.4f} μm")
    
    # 分析右齿形
    print("\n分析右齿形...")
    right_profile_result = analyzer.analyze_gear_ripple(file_path, 'profile', 'right', teeth_count)
    if right_profile_result:
        analyzer.visualize_results(right_profile_result, 'right_profile_analysis_correct.png')
        analyzer.export_results(right_profile_result, 'right_profile_results_correct.csv')
        
        # 显示结果
        print("右齿形阶次分析结果:")
        for order, amp in right_profile_result['results']:
            print(f"阶次: {order}, 幅值: {amp:.4f} μm")
    
    # 分析左齿向
    print("\n分析左齿向...")
    left_flank_result = analyzer.analyze_gear_ripple(file_path, 'flank', 'left', teeth_count)
    if left_flank_result:
        analyzer.visualize_results(left_flank_result, 'left_flank_analysis_correct.png')
        analyzer.export_results(left_flank_result, 'left_flank_results_correct.csv')
        
        # 显示结果
        print("左齿向阶次分析结果:")
        for order, amp in left_flank_result['results']:
            print(f"阶次: {order}, 幅值: {amp:.4f} μm")
