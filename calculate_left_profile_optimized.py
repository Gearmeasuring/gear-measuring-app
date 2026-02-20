import numpy as np
import re

# 读取MKA文件，提取左齿面的齿形数据
def extract_left_profile_data(file_path):
    """
    提取MKA文件中的左齿面齿形数据
    
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
    计算平均曲线（所有齿的平均）
    
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
    
    # 对齐所有曲线到相同长度（使用最短长度）
    min_len = min(len(c) for c in all_curves)
    if min_len < 8:
        return None
    
    aligned_curves = [c[:min_len] for c in all_curves]
    
    # 计算平均
    avg_curve = np.mean(aligned_curves, axis=0)
    return avg_curve

# 应用高阶评价（去除趋势，不移除均值）
def apply_high_order_evaluation(curve):
    """
    应用高阶评价（去除趋势，保留原始幅值）
    
    Args:
        curve: 曲线数据
    
    Returns:
        np.ndarray: 高阶成分
    """
    n = len(curve)
    x = np.arange(n)
    
    # 拟合二次曲线
    coeffs = np.polyfit(x, curve, 2)
    trend = np.polyval(coeffs, x)
    
    # 去除趋势，保留原始幅值
    high_order_curve = curve - trend
    
    return high_order_curve

# 确定评价范围（波动最大的区域）
def determine_evaluation_range(curve, window_size=50):
    """
    确定评价范围（波动最大的区域）
    
    Args:
        curve: 曲线数据
        window_size: 窗口大小
    
    Returns:
        tuple: (start_idx, end_idx)
    """
    n = len(curve)
    if n <= window_size:
        return 0, n
    
    # 计算每个窗口的波动（标准差）
    max_std = 0
    best_start = 0
    
    for i in range(n - window_size + 1):
        window = curve[i:i+window_size]
        std = np.std(window)
        
        if std > max_std:
            max_std = std
            best_start = i
    
    # 扩展窗口到合适大小
    start_idx = max(0, best_start - 20)
    end_idx = min(n, best_start + window_size + 20)
    
    return start_idx, end_idx

# 正弦拟合（针对特定阶次）
def sine_fit_specific_order(curve, order):
    """
    对特定阶次进行正弦拟合
    
    Args:
        curve: 曲线数据
        order: 阶次
    
    Returns:
        float: 幅值
    """
    n = len(curve)
    if n < 20:
        return 0.0
    
    # 创建旋转角x轴
    x = np.linspace(0.0, 2.0 * np.pi, n, dtype=float)
    
    try:
        # 构建矩阵 A = [sin(order*x), cos(order*x), 1]
        sin_x = np.sin(float(order) * x)
        cos_x = np.cos(float(order) * x)
        A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
        
        # 求解最小二乘
        coeffs, residuals, _, _ = np.linalg.lstsq(A, curve, rcond=None)
        a, b, c = coeffs
        
        # 计算幅值
        amplitude = float(np.sqrt(a * a + b * b))
        return amplitude
    except Exception:
        return 0.0

# 迭代提取方法（从残值中逐步提取阶次）
def iterative_extraction(curve, max_orders=10):
    """
    迭代提取方法（从残值中逐步提取阶次）
    
    Args:
        curve: 曲线数据
        max_orders: 最大提取阶次数
    
    Returns:
        list: [(order, amplitude)]
    """
    results = []
    residual = curve.copy()
    
    for i in range(max_orders):
        # 尝试不同阶次
        best_amplitude = 0
        best_order = 0
        
        # 重点关注齿数倍数附近的阶次
        for multiple in range(1, 10):
            order = 87 * multiple
            amp = sine_fit_specific_order(residual, order)
            if amp > best_amplitude:
                best_amplitude = amp
                best_order = order
        
        # 尝试261附近的阶次
        for order in [260, 261, 262]:
            amp = sine_fit_specific_order(residual, order)
            if amp > best_amplitude:
                best_amplitude = amp
                best_order = order
        
        if best_amplitude > 0:
            results.append((best_order, best_amplitude))
            
            # 计算该阶次的正弦波并从残值中减去
            n = len(residual)
            x = np.linspace(0.0, 2.0 * np.pi, n, dtype=float)
            sin_x = np.sin(float(best_order) * x)
            cos_x = np.cos(float(best_order) * x)
            A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
            coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
            a, b, c = coeffs
            fitted_curve = a * sin_x + b * cos_x + c
            residual = residual - fitted_curve
        else:
            break
    
    return results

# 主函数
def main():
    file_path = '263751-018-WAV.mka'
    Ze = 87  # 齿数
    target_order = 261  # 目标阶次
    target_amplitude = 0.14  # 目标幅值
    
    print("=" * 60)
    print("使用优化算法计算左齿形波纹度")
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
    
    # 应用高阶评价（去除趋势，保留原始幅值）
    print("\n应用高阶评价...")
    high_order_curve = apply_high_order_evaluation(average_curve)
    
    # 确定评价范围（波动最大的区域）
    print("\n确定评价范围...")
    start_idx, end_idx = determine_evaluation_range(high_order_curve)
    print(f"评价范围: 从索引 {start_idx} 到 {end_idx}")
    
    # 提取评价范围内的曲线
    eval_curve = high_order_curve[start_idx:end_idx]
    
    # 计算目标阶次的幅值
    print("\n计算目标阶次幅值...")
    target_amp = sine_fit_specific_order(eval_curve, target_order)
    print(f"261阶次幅值: {target_amp:.6f} μm")
    
    # 使用迭代提取方法
    print("\n使用迭代提取方法...")
    extracted_orders = iterative_extraction(eval_curve)
    
    print("\n迭代提取结果:")
    print("阶次\t\t幅值 (μm)")
    print("-" * 40)
    for order, amp in extracted_orders:
        print(f"{order}\t\t{amp:.6f}")
    
    # 分析不同评价范围
    print("\n分析不同评价范围...")
    ranges = [(0, len(high_order_curve)), 
              (50, len(high_order_curve)-50), 
              (100, len(high_order_curve)-100),
              (start_idx, end_idx)]
    
    best_amp = 0
    best_range = (0, len(high_order_curve))
    
    for rng in ranges:
        s, e = rng
        if e - s < 100:
            continue
        
        curve_segment = high_order_curve[s:e]
        amp = sine_fit_specific_order(curve_segment, target_order)
        print(f"范围 {s}-{e}: {amp:.6f} μm")
        
        if amp > best_amp:
            best_amp = amp
            best_range = rng
    
    print(f"\n最佳评价范围: {best_range[0]}-{best_range[1]}")
    print(f"最佳范围内261阶次幅值: {best_amp:.6f} μm")
    
    # 最终结果
    print("\n=" * 60)
    print("左齿形波纹度最终分析结果")
    print("=" * 60)
    
    # 使用最佳评价范围
    best_curve = high_order_curve[best_range[0]:best_range[1]]
    final_amplitude = sine_fit_specific_order(best_curve, target_order)
    
    print(f"目标阶次: {target_order}")
    print(f"计算幅值: {final_amplitude:.6f} μm")
    print(f"目标幅值: {target_amplitude} μm")
    print(f"差异: {abs(final_amplitude - target_amplitude):.6f} μm")
    
    # 显示主要阶次的结果
    print("\n主要阶次分析结果:")
    print("阶次\t\t幅值 (μm)")
    print("-" * 40)
    
    key_orders = [87, 174, 261, 262, 348, 435]
    for order in key_orders:
        amp = sine_fit_specific_order(best_curve, order)
        print(f"{order}\t\t{amp:.6f}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()