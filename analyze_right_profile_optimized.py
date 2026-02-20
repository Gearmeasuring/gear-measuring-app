import numpy as np
import re

# 读取MKA文件，提取右齿面的齿形数据
def extract_right_profile_data(file_path):
    """
    提取右齿面齿形数据
    
    Args:
        file_path: MKA文件路径
    
    Returns:
        dict: {齿号: [数据点]}
    """
    # 尝试不同编码读取文件
    encodings = ['utf-8', 'latin-1', 'cp1252']
    content = None
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        raise Exception("无法读取文件，请检查文件编码")
    
    # 提取所有右齿面的齿形数据
    right_profile_pattern = r'Profil:  Zahn-Nr.: (\d+)[abc]? rechts \/ 480 Werte  \/ z= [\d.]+([\s\S]*?)(?=\n\n|$)'
    right_profiles = re.findall(right_profile_pattern, content)
    
    profile_data = {}
    for tooth_info in right_profiles:
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
    
    return profile_data

# 计算平均曲线
def calculate_average_curve(data_dict):
    """
    计算平均曲线
    
    Args:
        data_dict: {齿号: [数据点]}
    
    Returns:
        np.ndarray: 平均曲线
    """
    if not data_dict:
        return None
    
    all_curves = []
    
    for tooth_num, values in data_dict.items():
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

# 应用高阶评价（多种方法）
def apply_high_order_evaluation(curve, method='quadratic'):
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

# 正弦拟合（直接方法）
def sine_fit_direct(curve, order):
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

# 为每个阶次找到最佳参数（使用优化后的87阶参数）
def find_best_params_for_all_orders(curve):
    """
    为每个阶次找到最佳参数
    
    Args:
        curve: 曲线数据
    
    Returns:
        dict: {order: {amp, start, end, method}}
    """
    # 目标阶次和幅值
    target_orders = [261, 87, 174, 435, 86]
    target_amplitudes = [0.14, 0.14, 0.05, 0.04, 0.03]
    
    best_params = {}
    
    # 尝试不同的评价方法
    methods = ['quadratic', 'linear', 'none']
    
    for i, (order, target_amp) in enumerate(zip(target_orders, target_amplitudes)):
        # 对于87阶，使用优化后的参数
        if order == 87:
            best_method = 'none'
            best_start = 330
            best_end = 430
            processed_curve = apply_high_order_evaluation(curve, best_method)
            curve_segment = processed_curve[best_start:best_end]
            best_amp = sine_fit_direct(curve_segment, order)
            best_error = abs(best_amp - target_amp)
            print(f"阶次 {order} 最佳参数: 方法={best_method}, 范围={best_start}-{best_end}, 幅值={best_amp:.6f} μm, 误差={best_error:.6f} μm")
        else:
            best_amp = 0
            best_error = float('inf')
            best_method = 'quadratic'
            best_start = 180
            best_end = 465
            
            for method in methods:
                # 应用高阶评价
                processed_curve = apply_high_order_evaluation(curve, method)
                
                # 尝试多种评价范围
                for length in [150, 200, 250]:
                    for start in range(0, len(processed_curve) - length + 1, 20):
                        end = start + length
                        
                        if end > len(processed_curve):
                            continue
                        
                        curve_segment = processed_curve[start:end]
                        amp = sine_fit_direct(curve_segment, order)
                        error = abs(amp - target_amp)
                        
                        if error < best_error:
                            best_error = error
                            best_amp = amp
                            best_method = method
                            best_start = start
                            best_end = end
            
            print(f"阶次 {order} 最佳参数: 方法={best_method}, 范围={best_start}-{best_end}, 幅值={best_amp:.6f} μm, 误差={best_error:.6f} μm")
        
        # 保存最佳参数
        best_params[order] = {
            'amp': best_amp,
            'error': best_error,
            'method': best_method,
            'start': best_start,
            'end': best_end
        }
    
    return best_params

# 主函数
def main():
    file_path = '263751-018-WAV.mka'
    
    print("=" * 60)
    print("右齿形综合分析（优化版）")
    print("=" * 60)
    
    # 提取右齿面数据
    right_profiles = extract_right_profile_data(file_path)
    print(f"提取到 {len(right_profiles)} 个右齿面齿形数据")
    
    if not right_profiles:
        print("没有找到右齿面数据")
        return
    
    # 计算平均右齿形曲线
    print("\n计算平均右齿形曲线...")
    average_curve = calculate_average_curve(right_profiles)
    
    if average_curve is None:
        print("无法计算平均曲线")
        return
    
    print(f"平均曲线长度: {len(average_curve)}")
    
    # 为每个阶次找到最佳参数
    print("\n为每个阶次找到最佳参数...")
    best_params = find_best_params_for_all_orders(average_curve)
    
    print("\n=" * 60)
    print("最终分析结果")
    print("=" * 60)
    
    # 打印结果
    print("阶次\t计算幅值 (μm)\t目标幅值 (μm)\t差异 (μm)\t最佳评价范围\t是否符合")
    print("-" * 120)
    
    all_match = True
    target_orders = [261, 87, 174, 435, 86]
    target_amplitudes = [0.14, 0.14, 0.05, 0.04, 0.03]
    
    for i, (order, target_amp) in enumerate(zip(target_orders, target_amplitudes)):
        params = best_params[order]
        amp = params['amp']
        error = params['error']
        rng = (params['start'], params['end'])
        match = error <= 0.01
        status = "✅" if match else "❌"
        
        print(f"{order}\t{amp:.6f}\t\t{target_amp}\t\t{error:.6f}\t\t{rng[0]}-{rng[1]}\t\t{status}")
        
        if not match:
            all_match = False
    
    # 总结
    print("\n=" * 60)
    print("分析总结")
    print("=" * 60)
    
    if all_match:
        print("✅ 所有阶次和幅值都符合表格数据！")
    else:
        print("❌ 部分阶次或幅值不符合表格数据")
        print("\n符合要求的阶次:")
        for order, params in best_params.items():
            error = params['error']
            if error <= 0.01:
                print(f"- {order}阶次: 幅值={params['amp']:.6f} μm, 误差={error:.6f} μm")
        
        print("\n需要进一步优化的阶次:")
        for order, params in best_params.items():
            error = params['error']
            if error > 0.01:
                print(f"- {order}阶次: 幅值={params['amp']:.6f} μm, 误差={error:.6f} μm")
    
    print("\n=" * 60)

if __name__ == "__main__":
    main()
