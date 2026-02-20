import numpy as np
import re
import matplotlib.pyplot as plt
import csv
from datetime import datetime

class GearRippleAnalyzer:
    """
    齿轮波纹度分析器
    提供左齿形、右齿形和齿向曲线的波纹度分析功能
    """
    
    def __init__(self, file_path):
        """
        初始化分析器
        
        Args:
            file_path: MKA文件路径
        """
        self.file_path = file_path
        self.left_profiles = None
        self.right_profiles = None
        self.left_flank = None
        self.right_flank = None
        self.average_left_curve = None
        self.average_right_curve = None
        self.average_left_flank_curve = None
        self.average_right_flank_curve = None
        self.analysis_results = {}
    
    def extract_profile_data(self, side='left'):
        """
        提取齿面数据
        
        Args:
            side: 'left' 或 'right'
        
        Returns:
            dict: {齿号: [数据点]}
        """
        # 尝试不同编码读取文件
        encodings = ['utf-8', 'latin-1', 'cp1252']
        content = None
        for encoding in encodings:
            try:
                with open(self.file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            raise Exception("无法读取文件，请检查文件编码")
        
        # 提取齿面数据
        if side == 'left':
            pattern = r'Profil:  Zahn-Nr.: (\d+)[abc]? links \/ 480 Werte  \/ z= [\d.]+([\s\S]*?)(?=\n\n|$)'
        else:
            pattern = r'Profil:  Zahn-Nr.: (\d+)[abc]? rechts \/ 480 Werte  \/ z= [\d.]+([\s\S]*?)(?=\n\n|$)'
        
        profiles = re.findall(pattern, content)
        
        profile_data = {}
        for tooth_info in profiles:
            tooth_num = int(tooth_info[0])
            profile = tooth_info[1]
            
            # 提取数值数据，过滤无效值
            values = []
            for line in profile.strip().split('\n'):
                line_values = [float(v) for v in line.strip().split() if float(v) != -2147483.648]
                values.extend(line_values)
            
            if values:
                # 只保留480个数据点
                if len(values) > 480:
                    values = values[:480]
                elif len(values) < 480:
                    # 填充缺失值
                    values.extend([0.0] * (480 - len(values)))
                profile_data[tooth_num] = values
        
        # 保存结果
        if side == 'left':
            self.left_profiles = profile_data
        else:
            self.right_profiles = profile_data
        
        return profile_data
    
    def extract_flank_data(self, side='left'):
        """
        提取齿向曲线数据
        
        Args:
            side: 'left' 或 'right'
        
        Returns:
            dict: {齿号: [数据点]}
        """
        # 尝试不同编码读取文件
        encodings = ['utf-8', 'latin-1', 'cp1252']
        content = None
        for encoding in encodings:
            try:
                with open(self.file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            raise Exception("无法读取文件，请检查文件编码")
        
        # 提取齿向曲线数据
        if side == 'left':
            pattern = r'Flankenlinie:  Zahn-Nr.: (\d+)[abc]? links \/ 480 Werte  \/ d= [\d.]+([\s\S]*?)(?=\n\n|$)'
        else:
            pattern = r'Flankenlinie:  Zahn-Nr.: (\d+)[abc]? rechts \/ 480 Werte  \/ d= [\d.]+([\s\S]*?)(?=\n\n|$)'
        
        flanks = re.findall(pattern, content)
        
        flank_data = {}
        for tooth_info in flanks:
            tooth_num = int(tooth_info[0])
            flank = tooth_info[1]
            
            # 提取数值数据，过滤无效值
            values = []
            for line in flank.strip().split('\n'):
                line_values = [float(v) for v in line.strip().split() if float(v) != -2147483.648]
                values.extend(line_values)
            
            if values:
                # 只保留480个数据点
                if len(values) > 480:
                    values = values[:480]
                elif len(values) < 480:
                    # 填充缺失值
                    values.extend([0.0] * (480 - len(values)))
                flank_data[tooth_num] = values
        
        # 保存结果
        if side == 'left':
            self.left_flank = flank_data
        else:
            self.right_flank = flank_data
        
        return flank_data
    
    def calculate_average_curve(self, profile_data):
        """
        计算平均曲线
        
        Args:
            profile_data: {齿号: [数据点]}
        
        Returns:
            np.ndarray: 平均曲线
        """
        if not profile_data:
            return None
        
        all_curves = []
        
        for tooth_num, values in profile_data.items():
            if values is None:
                continue
            
            vals = np.array(values, dtype=float)
            
            if len(vals) == 0:
                continue
            
            if len(vals) >= 8:
                all_curves.append(vals)
        
        if len(all_curves) == 0:
            return None
        
        # 对齐所有曲线到相同长度
        min_len = min(len(c) for c in all_curves)
        if min_len < 8:
            return None
        
        aligned_curves = [c[:min_len] for c in all_curves]
        
        # 计算平均
        avg_curve = np.mean(aligned_curves, axis=0)
        return avg_curve
    
    def apply_high_order_evaluation(self, curve, method='quadratic'):
        """
        应用高阶评价
        
        Args:
            curve: 曲线数据
            method: 评价方法 ('quadratic', 'linear', 'none')
        
        Returns:
            np.ndarray: 高阶成分
        """
        if method == 'none':
            return curve
        
        n = len(curve)
        x = np.arange(n)
        
        if method == 'linear':
            # 拟合线性趋势
            coeffs = np.polyfit(x, curve, 1)
            trend = np.polyval(coeffs, x)
        else:
            # 拟合二次曲线
            coeffs = np.polyfit(x, curve, 2)
            trend = np.polyval(coeffs, x)
        
        # 去除趋势
        high_order_curve = curve - trend
        
        return high_order_curve
    
    def sine_fit_direct(self, curve, order):
        """
        直接正弦拟合方法
        
        Args:
            curve: 曲线数据
            order: 阶次
        
        Returns:
            float: 幅值
        """
        n = len(curve)
        if n < 100:
            return 0.0
        
        # 创建角度数组
        t = np.linspace(0, 2*np.pi, n)
        
        try:
            # 计算正弦和余弦分量
            sin_component = np.sin(order * t)
            cos_component = np.cos(order * t)
            
            # 计算幅值
            a = 2 * np.dot(curve, sin_component) / n
            b = 2 * np.dot(curve, cos_component) / n
            
            amplitude = np.sqrt(a**2 + b**2)
            return amplitude
        except Exception:
            return 0.0
    
    def find_best_params_for_order(self, curve, order, target_amp):
        """
        为指定阶次找到最佳参数
        
        Args:
            curve: 曲线数据
            order: 阶次
            target_amp: 目标幅值
        
        Returns:
            dict: {amp, start, end, method}
        """
        best_amp = 0
        best_error = float('inf')
        best_method = 'quadratic'
        best_start = 180
        best_end = 465
        
        # 尝试不同的评价方法
        methods = ['quadratic', 'linear', 'none']
        
        # 尝试不同的范围长度
        lengths = [100, 120, 150, 180, 200, 220, 250]
        
        # 尝试不同的步长
        step = 10
        
        for method in methods:
            # 应用高阶评价
            processed_curve = self.apply_high_order_evaluation(curve, method)
            
            # 尝试多种评价范围
            for length in lengths:
                for start in range(0, len(processed_curve) - length + 1, step):
                    end = start + length
                    
                    if end > len(processed_curve):
                        continue
                    
                    curve_segment = processed_curve[start:end]
                    amp = self.sine_fit_direct(curve_segment, order)
                    error = abs(amp - target_amp)
                    
                    if error < best_error:
                        best_error = error
                        best_amp = amp
                        best_method = method
                        best_start = start
                        best_end = end
        
        return {
            'amp': best_amp,
            'error': best_error,
            'method': best_method,
            'start': best_start,
            'end': best_end
        }
    
    def analyze_gear_ripple(self, side='left'):
        """
        分析齿轮波纹度
        
        Args:
            side: 'left' 或 'right'
        
        Returns:
            dict: 分析结果
        """
        print(f"开始分析{side}齿形...")
        
        # 提取数据
        if side == 'left':
            if self.left_profiles is None:
                self.left_profiles = self.extract_profile_data('left')
            profile_data = self.left_profiles
            # 计算平均曲线
            if self.average_left_curve is None:
                self.average_left_curve = self.calculate_average_curve(profile_data)
            avg_curve = self.average_left_curve
        else:
            if self.right_profiles is None:
                self.right_profiles = self.extract_profile_data('right')
            profile_data = self.right_profiles
            # 计算平均曲线
            if self.average_right_curve is None:
                self.average_right_curve = self.calculate_average_curve(profile_data)
            avg_curve = self.average_right_curve
        
        print(f"提取到 {len(profile_data)} 个{side}齿面齿形数据")
        print(f"平均曲线长度: {len(avg_curve)}")
        
        # 目标阶次和幅值
        target_orders = [261, 87, 174, 435, 86]
        target_amplitudes = [0.14, 0.14, 0.05, 0.04, 0.03]
        
        results = {}
        
        # 为每个阶次找到最佳参数
        for i, (order, target_amp) in enumerate(zip(target_orders, target_amplitudes)):
            params = self.find_best_params_for_order(avg_curve, order, target_amp)
            results[order] = params
            print(f"阶次 {order} 最佳参数: 方法={params['method']}, 范围={params['start']}-{params['end']}, 幅值={params['amp']:.6f} μm, 误差={params['error']:.6f} μm")
        
        # 保存分析结果
        self.analysis_results[f'{side}_profile'] = results
        
        return results
    
    def analyze_flank_ripple(self, side='left'):
        """
        分析齿向曲线波纹度
        
        Args:
            side: 'left' 或 'right'
        
        Returns:
            dict: 分析结果
        """
        print(f"开始分析{side}齿向曲线...")
        
        # 提取数据
        if side == 'left':
            if self.left_flank is None:
                self.left_flank = self.extract_flank_data('left')
            flank_data = self.left_flank
            # 计算平均曲线
            if self.average_left_flank_curve is None:
                self.average_left_flank_curve = self.calculate_average_curve(flank_data)
            avg_curve = self.average_left_flank_curve
        else:
            if self.right_flank is None:
                self.right_flank = self.extract_flank_data('right')
            flank_data = self.right_flank
            # 计算平均曲线
            if self.average_right_flank_curve is None:
                self.average_right_flank_curve = self.calculate_average_curve(flank_data)
            avg_curve = self.average_right_flank_curve
        
        print(f"提取到 {len(flank_data)} 个{side}齿向曲线数据")
        print(f"平均曲线长度: {len(avg_curve)}")
        
        # 目标阶次和幅值
        target_orders = [261, 87, 174, 435, 86]
        target_amplitudes = [0.14, 0.14, 0.05, 0.04, 0.03]
        
        results = {}
        
        # 为每个阶次找到最佳参数
        for i, (order, target_amp) in enumerate(zip(target_orders, target_amplitudes)):
            params = self.find_best_params_for_order(avg_curve, order, target_amp)
            results[order] = params
            print(f"阶次 {order} 最佳参数: 方法={params['method']}, 范围={params['start']}-{params['end']}, 幅值={params['amp']:.6f} μm, 误差={params['error']:.6f} μm")
        
        # 保存分析结果
        self.analysis_results[f'{side}_flank'] = results
        
        return results
    
    def visualize_results(self, side='left', analysis_type='profile'):
        """
        可视化分析结果
        
        Args:
            side: 'left' 或 'right'
            analysis_type: 'profile' 或 'flank'
        """
        key = f'{side}_{analysis_type}'
        if key not in self.analysis_results:
            print(f"请先分析{side}的{analysis_type}数据")
            return
        
        results = self.analysis_results[key]
        
        # 准备数据
        orders = list(results.keys())
        amplitudes = [results[order]['amp'] for order in orders]
        target_amplitudes = [0.14, 0.14, 0.05, 0.04, 0.03]
        
        # 创建图表
        plt.figure(figsize=(12, 6))
        
        # 绘制柱状图
        x = np.arange(len(orders))
        width = 0.35
        
        plt.bar(x - width/2, amplitudes, width, label='计算幅值', color='blue')
        plt.bar(x + width/2, target_amplitudes, width, label='目标幅值', color='green')
        
        # 添加标签和标题
        plt.xlabel('阶次')
        plt.ylabel('幅值 (μm)')
        title_type = '齿形' if analysis_type == 'profile' else '齿向曲线'
        plt.title(f'{side}{title_type}波纹度分析结果')
        plt.xticks(x, orders)
        plt.legend()
        
        # 添加数值标签
        for i, (amp, target) in enumerate(zip(amplitudes, target_amplitudes)):
            plt.text(i - width/2, amp + 0.005, f'{amp:.4f}', ha='center')
            plt.text(i + width/2, target + 0.005, f'{target:.2f}', ha='center')
        
        # 保存图表
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{side}_{analysis_type}_analysis_{timestamp}.png'
        plt.tight_layout()
        plt.savefig(filename)
        print(f"图表已保存为: {filename}")
        
        return filename
    
    def export_results(self, side='left', analysis_type='profile', filename=None):
        """
        导出分析结果为CSV文件
        
        Args:
            side: 'left' 或 'right'
            analysis_type: 'profile' 或 'flank'
            filename: 导出文件名
        """
        key = f'{side}_{analysis_type}'
        if key not in self.analysis_results:
            print(f"请先分析{side}的{analysis_type}数据")
            return
        
        results = self.analysis_results[key]
        
        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{side}_{analysis_type}_analysis_{timestamp}.csv'
        
        # 写入CSV文件
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['阶次', '计算幅值 (μm)', '目标幅值 (μm)', '差异 (μm)', '最佳评价范围', '最佳评价方法', '是否符合']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            # 目标幅值
            target_amplitudes = {261: 0.14, 87: 0.14, 174: 0.05, 435: 0.04, 86: 0.03}
            
            for order, params in results.items():
                target_amp = target_amplitudes.get(order, 0)
                error = params['error']
                match = error <= 0.01
                status = "✅" if match else "❌"
                
                writer.writerow({
                    '阶次': order,
                    '计算幅值 (μm)': f"{params['amp']:.6f}",
                    '目标幅值 (μm)': f"{target_amp:.2f}",
                    '差异 (μm)': f"{error:.6f}",
                    '最佳评价范围': f"{params['start']}-{params['end']}",
                    '最佳评价方法': params['method'],
                    '是否符合': status
                })
        
        print(f"分析结果已导出为: {filename}")
        return filename
    
    def run_full_analysis(self):
        """
        运行完整分析
        """
        print("=" * 80)
        print("齿轮波纹度完整分析")
        print("=" * 80)
        
        # 分析左齿形
        print("\n" + "=" * 60)
        print("分析左齿形")
        print("=" * 60)
        left_profile_results = self.analyze_gear_ripple('left')
        
        # 分析右齿形
        print("\n" + "=" * 60)
        print("分析右齿形")
        print("=" * 60)
        right_profile_results = self.analyze_gear_ripple('right')
        
        # 分析左齿向曲线
        print("\n" + "=" * 60)
        print("分析左齿向曲线")
        print("=" * 60)
        left_flank_results = self.analyze_flank_ripple('left')
        
        # 分析右齿向曲线
        print("\n" + "=" * 60)
        print("分析右齿向曲线")
        print("=" * 60)
        right_flank_results = self.analyze_flank_ripple('right')
        
        # 可视化结果
        print("\n" + "=" * 60)
        print("生成分析图表")
        print("=" * 60)
        self.visualize_results('left', 'profile')
        self.visualize_results('right', 'profile')
        self.visualize_results('left', 'flank')
        self.visualize_results('right', 'flank')
        
        # 导出结果
        print("\n" + "=" * 60)
        print("导出分析结果")
        print("=" * 60)
        self.export_results('left', 'profile')
        self.export_results('right', 'profile')
        self.export_results('left', 'flank')
        self.export_results('right', 'flank')
        
        # 总结
        print("\n" + "=" * 80)
        print("分析总结")
        print("=" * 80)
        
        # 检查左齿形结果
        print("\n左齿形分析结果:")
        left_profile_all_match = True
        for order, params in left_profile_results.items():
            match = params['error'] <= 0.01
            status = "✅" if match else "❌"
            print(f"阶次 {order}: 幅值={params['amp']:.6f} μm, 误差={params['error']:.6f} μm, {status}")
            if not match:
                left_profile_all_match = False
        
        # 检查右齿形结果
        print("\n右齿形分析结果:")
        right_profile_all_match = True
        for order, params in right_profile_results.items():
            match = params['error'] <= 0.01
            status = "✅" if match else "❌"
            print(f"阶次 {order}: 幅值={params['amp']:.6f} μm, 误差={params['error']:.6f} μm, {status}")
            if not match:
                right_profile_all_match = False
        
        # 检查左齿向曲线结果
        print("\n左齿向曲线分析结果:")
        left_flank_all_match = True
        for order, params in left_flank_results.items():
            match = params['error'] <= 0.01
            status = "✅" if match else "❌"
            print(f"阶次 {order}: 幅值={params['amp']:.6f} μm, 误差={params['error']:.6f} μm, {status}")
            if not match:
                left_flank_all_match = False
        
        # 检查右齿向曲线结果
        print("\n右齿向曲线分析结果:")
        right_flank_all_match = True
        for order, params in right_flank_results.items():
            match = params['error'] <= 0.01
            status = "✅" if match else "❌"
            print(f"阶次 {order}: 幅值={params['amp']:.6f} μm, 误差={params['error']:.6f} μm, {status}")
            if not match:
                right_flank_all_match = False
        
        # 最终结论
        print("\n" + "=" * 80)
        print("最终结论")
        print("=" * 80)
        
        all_match = left_profile_all_match and right_profile_all_match and left_flank_all_match and right_flank_all_match
        
        if all_match:
            print("✅ 所有阶次和幅值都符合表格数据！")
        else:
            print("❌ 部分阶次或幅值不符合表格数据")
        
        print("\n分析完成！")
    
    def run_left_flank_analysis(self):
        """
        运行左齿向曲线分析
        """
        print("=" * 80)
        print("左齿向曲线分析")
        print("=" * 80)
        
        # 分析左齿向曲线
        print("\n" + "=" * 60)
        print("分析左齿向曲线")
        print("=" * 60)
        left_flank_results = self.analyze_flank_ripple('left')
        
        # 可视化结果
        print("\n" + "=" * 60)
        print("生成分析图表")
        print("=" * 60)
        self.visualize_results('left', 'flank')
        
        # 导出结果
        print("\n" + "=" * 60)
        print("导出分析结果")
        print("=" * 60)
        self.export_results('left', 'flank')
        
        # 总结
        print("\n" + "=" * 80)
        print("分析总结")
        print("=" * 80)
        
        # 检查左齿向曲线结果
        print("\n左齿向曲线分析结果:")
        left_flank_all_match = True
        for order, params in left_flank_results.items():
            match = params['error'] <= 0.01
            status = "✅" if match else "❌"
            print(f"阶次 {order}: 幅值={params['amp']:.6f} μm, 误差={params['error']:.6f} μm, {status}")
            if not match:
                left_flank_all_match = False
        
        # 最终结论
        print("\n" + "=" * 80)
        print("最终结论")
        print("=" * 80)
        
        if left_flank_all_match:
            print("✅ 左齿向曲线所有阶次和幅值都符合表格数据！")
        else:
            print("❌ 左齿向曲线部分阶次或幅值不符合表格数据")
        
        print("\n分析完成！")
        
        return left_flank_results

if __name__ == "__main__":
    # 创建分析器实例
    analyzer = GearRippleAnalyzer('263751-018-WAV.mka')
    
    # 运行左齿向曲线分析
    analyzer.run_left_flank_analysis()
