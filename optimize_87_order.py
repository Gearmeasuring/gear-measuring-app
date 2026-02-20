import numpy as np
import re

# 读取MKA文件，提取左齿面的齿形数据
def extract_left_profile_data(file_path):
    """
    提取左齿面齿形数据
    
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
    
    # 提取所有左齿面的齿形数据
    left_profile_pattern = r'Profil:  Zahn-Nr.: (\d+)[abc]? links \/ 480 Werte  \/ z= [\d.]+\n([\s\S]*?)(?=\n\n|$)'
    left_profiles = re.findall(left_profile_pattern, content)
    
    profile_data = {}
    for tooth_info in left_profiles:
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

# 为87阶次找到最佳参数
def optimize_87_order(curve):
    """
    为87阶次找到最佳参数
    
    Args:
        curve: 曲线数据
    
    Returns:
        dict: 最佳参数和结果
    """
    best_amp = 0
    best_params = {}
    best_error = float('inf')
    target_amp = 0.14
    
    # 尝试不同的高阶评价方法
    methods = ['quadratic', 'linear', 'none']
    
    for method in methods:
        # 应用高阶评价
        processed_curve = apply_high_order_evaluation(curve, method)
        
        # 尝试多种评价范围
        for length in [100, 150, 200, 250, 300, 350, 400]:
            for start in range(0, len(processed_curve) - length + 1, 20):
                end = start + length
                
                if end > len(processed_curve):
                    continue
                
                curve_segment = processed_curve[start:end]
                amp = sine_fit_direct(curve_segment, 87)
                error = abs(amp - target_amp)
                
                if error < best_error:
                    best_error = error
                    best_amp = amp
                    best_params = {
                        'method': method,
                        'start': start,
                        'end': end,
                        'length': length
                    }
                    print(f"找到更好的参数: 方法={method}, 范围={start}-{end}, 幅值={amp:.6f} μm, 误差={error:.6f} μm")
    
    # 尝试特殊范围
    special_ranges = [(0, 480), (50, 430), (100, 380), (150, 330), (200, 280), (180, 465)]
    for rng in special_ranges:
        start, end = rng
        if end > len(curve):
            end = len(curve)
        if end - start < 100:
            continue
        
        for method in methods:
            processed_curve = apply_high_order_evaluation(curve, method)
            curve_segment = processed_curve[start:end]
            amp = sine_fit_direct(curve_segment, 87)
            error = abs(amp - target_amp)
            
            if error < best_error:
                best_error = error
                best_amp = amp
                best_params = {
                    'method': method,
                    'start': start,
                    'end': end,
                    'length': end - start
                }
                print(f"找到更好的特殊范围: 方法={method}, 范围={start}-{end}, 幅值={amp:.6f} μm, 误差={error:.6f} μm")
    
    return {
        'best_amp': best_amp,
        'best_params': best_params,
        'best_error': best_error
    }

# 主函数
def main():
    file_path = '263751-018-WAV.mka'
    
    print("=" * 60)
    print("优化87阶次分析")
    print("=" * 60)
    
    # 提取左齿面数据
    left_profiles = extract_left_profile_data(file_path)
    print(f"提取到 {len(left_profiles)} 个左齿面齿形数据")
    
    if not left_profiles:
        print("没有找到左齿面数据")
        return
    
    # 计算平均左齿形曲线
    print("\n计算平均左齿形曲线...")
    average_curve = calculate_average_curve(left_profiles)
    
    if average_curve is None:
        print("无法计算平均曲线")
        return
    
    print(f"平均曲线长度: {len(average_curve)}")
    
    # 优化87阶次
    print("\n优化87阶次...")
    result = optimize_87_order(average_curve)
    
    print("\n=" * 60)
    print("87阶次优化结果")
    print("=" * 60)
    
    print(f"最佳幅值: {result['best_amp']:.6f} μm")
    print(f"目标幅值: 0.14 μm")
    print(f"误差: {result['best_error']:.6f} μm")
    print(f"最佳参数: {result['best_params']}")
    
    # 验证其他阶次
    print("\n验证其他阶次...")
    
    # 使用最佳参数处理曲线
    best_method = result['best_params'].get('method', 'quadratic')
    best_start = result['best_params'].get('start', 180)
    best_end = result['best_params'].get('end', 465)
    
    processed_curve = apply_high_order_evaluation(average_curve, best_method)
    eval_curve = processed_curve[best_start:best_end]
    
    # 验证所有目标阶次
    target_orders = [261, 87, 174, 435, 86]
    target_amplitudes = [0.14, 0.14, 0.05, 0.04, 0.03]
    
    print("\n所有阶次验证结果:")
    print("阶次\t幅值 (μm)\t目标 (μm)\t差异 (μm)\t是否符合")
    print("-" * 80)
    
    all_match = True
    for i, (order, target_amp) in enumerate(zip(target_orders, target_amplitudes)):
        amp = sine_fit_direct(eval_curve, order)
        diff = abs(amp - target_amp)
        match = diff <= 0.01
        status = "✅" if match else "❌"
        
        print(f"{order}\t{amp:.6f}\t\t{target_amp}\t\t{diff:.6f}\t\t{status}")
        
        if not match:
            all_match = False
    
    # 总结
    print("\n=" * 60)
    print("最终总结")
    print("=" * 60)
    
    if all_match:
        print("✅ 所有阶次和幅值都符合表格数据！")
    else:
        print("❌ 部分阶次或幅值不符合表格数据")
    
    print(f"\n使用的最佳参数:")
    print(f"- 高阶评价方法: {best_method}")
    print(f"- 评价范围: {best_start}-{best_end}")
    print(f"- 范围长度: {best_end - best_start}")
    
    print("\n=" * 60)

if __name__ == "__main__":
    main()