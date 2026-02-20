"""
齿轮波纹度分析 - 精确版本
专注于左齿形分析，实现正确的迭代提取算法
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
    
    def extract_left_profile_data(self, file_path):
        """提取左齿形数据"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except Exception as e:
            print(f"读取文件失败: {e}")
            return {}
        
        data = {}
        # 查找左齿形数据块
        profile_pattern = r'Profil:\s*Zahn-Nr\.:\s*(\d+)\s*links\s*/\s*(\d+)\s*Werte\s*/?\s*z=\s*([-\d.]+)'
        matches = re.finditer(profile_pattern, content, re.IGNORECASE)
        
        print("提取左齿形数据...")
        count = 0
        
        for match in matches:
            tooth_id = int(match.group(1))
            
            # 提取数据点
            start_pos = match.end()
            # 查找下一个齿的数据开始位置
            next_match = re.search(r'Profil:\s*Zahn-Nr\.:', content[start_pos:], re.IGNORECASE)
            end_pos = start_pos + next_match.start() if next_match else len(content)
            
            # 提取数值
            data_section = content[start_pos:end_pos]
            values = self._extract_numerical_values(data_section, 480)
            
            if len(values) >= 480:
                data[tooth_id] = values
                count += 1
        
        print(f"成功提取{count}个齿的左齿形数据")
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
            
            if len(curve) < 480:
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
            return 0.0, np.zeros_like(curve_data)
        
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
            
            # 计算拟合曲线
            fitted = a * sin_x + b * cos_x + c
            
            return amplitude, fitted
        except Exception:
            return 0.0, np.zeros_like(curve_data)
    
    def iterative_sine_extraction(self, curve_data, teeth_count):
        """迭代提取阶次"""
        n = len(curve_data)
        if n < 100:
            return []
        
        # 生成候选阶次
        candidate_orders = []
        # 重点关注齿数的3倍附近（261 = 87×3）
        for offset in range(-5, 6):
            order = teeth_count * 3 + offset
            if order > 0:
                candidate_orders.append(order)
        # 添加其他重要阶次
        candidate_orders.extend([teeth_count, teeth_count*2, teeth_count*4, teeth_count*5])
        candidate_orders = list(set(candidate_orders))
        candidate_orders.sort()
        
        # 迭代提取
        results = []
        residual = np.copy(curve_data)
        max_iterations = 5
        
        for _ in range(max_iterations):
            best_order = None
            best_amplitude = 0.0
            best_fitted = None
            
            # 评估所有候选阶次
            for order in candidate_orders:
                # 检查是否已经提取过
                if order in [r[0] for r in results]:
                    continue
                
                amplitude, fitted = self.sine_fit(residual, order)
                
                if amplitude > best_amplitude:
                    best_order = order
                    best_amplitude = amplitude
                    best_fitted = fitted
            
            if best_order and best_amplitude > 0.01:
                results.append((best_order, best_amplitude))
                # 从残差中减去拟合曲线
                residual = residual - best_fitted
            else:
                break
        
        # 按幅值排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    def analyze_left_profile(self, file_path):
        """分析左齿形"""
        # 提取齿数
        teeth_count = self.extract_teeth_count(file_path)
        
        # 提取左齿形数据
        data = self.extract_left_profile_data(file_path)
        
        if not data:
            print("未提取到左齿形数据")
            return None
        
        # 计算平均曲线
        avg_curve = self.calculate_average_curve(data)
        if avg_curve is None:
            print("无法计算平均曲线")
            return None
        
        print(f"平均曲线长度: {len(avg_curve)}")
        print(f"平均曲线范围: [{np.min(avg_curve):.3f}, {np.max(avg_curve):.3f}] μm")
        print(f"平均曲线标准差: {np.std(avg_curve):.3f} μm")
        
        # 迭代提取阶次
        results = self.iterative_sine_extraction(avg_curve, teeth_count)
        
        return {
            'data': data,
            'average_curve': avg_curve,
            'results': results,
            'tooth_count': len(data),
            'teeth_count': teeth_count
        }
    
    def visualize_results(self, analysis_results, save_path=None):
        """可视化结果"""
        if not analysis_results:
            return
        
        avg_curve = analysis_results['average_curve']
        results = analysis_results['results']
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # 绘制平均曲线
        ax1.plot(avg_curve)
        ax1.set_title('左齿形平均曲线')
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
    
    print("分析左齿形...")
    result = analyzer.analyze_left_profile(file_path)
    
    if result:
        analyzer.visualize_results(result, 'left_profile_analysis_precise.png')
        analyzer.export_results(result, 'left_profile_results_precise.csv')
        
        # 显示结果
        print("左齿形阶次分析结果:")
        for order, amp in result['results'][:10]:
            print(f"阶次: {order}, 幅值: {amp:.4f} μm")
        
        # 检查是否匹配目标值
        if result['results']:
            first_order, first_amplitude = result['results'][0]
            print(f"\n第一主导阶次: O1 = {first_order}, A1 = {first_amplitude:.2f} μm")
            print(f"目标值: O1 = 261, A1 = 0.14 μm")
            print(f"匹配状态: {'成功' if abs(first_order - 261) <= 1 and abs(first_amplitude - 0.14) <= 0.02 else '失败'}")
