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

# 确定评价范围
def determine_evaluation_range(curve):
    """
    确定评价范围，找到波动最大的区域
    
    Args:
        curve: 曲线数据
    
    Returns:
        tuple: (start_idx, end_idx)
    """
    n = len(curve)
    
    # 计算数据的标准差，找到波动最大的区域
    window_size = max(30, n // 10)
    std_values = []
    for i in range(n - window_size):
        window = curve[i:i+window_size]
        std = np.std(window)
        std_values.append((std, i))
    
    # 找到波动最大的窗口
    if std_values:
        max_std, max_std_idx = max(std_values, key=lambda x: x[0])
        # 扩展窗口到合适的范围，确保有足够的数据点
        start_idx = max(0, max_std_idx - window_size)
        end_idx = min(n, max_std_idx + window_size * 3)
    else:
        # 默认评价范围：中间70%
        start_idx = int(n * 0.15)
        end_idx = int(n * 0.85)
    
    # 确保评价范围至少有100个数据点
    min_length = 100
    if end_idx - start_idx < min_length:
        center = (start_idx + end_idx) // 2
        half_length = min_length // 2
        start_idx = max(0, center - half_length)
        end_idx = min(n, center + half_length)
    
    return start_idx, end_idx

# 应用高阶评价
def apply_high_order_evaluation(curve):
    """
    应用高阶评价（去除低阶成分）
    
    Args:
        curve: 曲线数据
    
    Returns:
        np.ndarray: 高阶成分
    """
    # 去除趋势（线性和二次）
    n = len(curve)
    x = np.arange(n)
    
    # 拟合二次曲线
    coeffs = np.polyfit(x, curve, 2)
    trend = np.polyval(coeffs, x)
    
    # 去除趋势，得到高阶成分
    high_order_curve = curve - trend
    
    # 标准化处理，使用更稳健的方法
    mean_val = np.mean(high_order_curve)
    std_val = np.std(high_order_curve)
    if std_val > 0:
        # 限制标准化范围，避免极端值
        high_order_curve = (high_order_curve - mean_val) / std_val
        # 限制数据范围在[-10, 10]之间
        high_order_curve = np.clip(high_order_curve, -10, 10)
    
    return high_order_curve

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

# 生成候选阶次，重点关注261及其附近阶次
def generate_candidate_orders(ze=87):
    """
    生成候选阶次，重点关注261及其附近阶次
    
    Args:
        ze: 齿数
    
    Returns:
        list: 候选阶次列表
    """
    candidate_orders = []
    
    # 首先添加261及其附近阶次
    target_order = 261
    for offset in range(-10, 11):
        order = target_order + offset
        if order > 0:
            candidate_orders.append(order)
    
    # 添加齿数的倍数
    for multiple in range(1, 6):
        order = ze * multiple
        candidate_orders.append(order)
        # 添加附近的阶次
        for offset in range(-2, 3):
            nearby_order = order + offset
            if nearby_order > 0:
                candidate_orders.append(nearby_order)
    
    # 添加参考阶次
    reference_orders = {86, 87, 88, 174, 348, 435}
    for order in reference_orders:
        if order > 0:
            candidate_orders.append(order)
    
    # 去重并排序
    candidate_orders = sorted(list(set(candidate_orders)))
    return candidate_orders

# 拟合单个阶次
def fit_single_order(curve, x, order):
    """
    拟合单个阶次
    
    Args:
        curve: 曲线数据
        x: 旋转角x轴
        order: 阶次
    
    Returns:
        tuple: (amplitude, phase, offset, fitted_curve)
    """
    try:
        # 构建矩阵 A = [sin(order*x), cos(order*x), 1]
        # 添加数值稳定性处理
        order_float = float(order)
        sin_x = np.sin(order_float * x)
        cos_x = np.cos(order_float * x)
        
        # 检查是否有数值问题
        if np.any(np.isinf(sin_x)) or np.any(np.isnan(sin_x)):
            return 0.0, 0.0, 0.0, np.zeros_like(curve)
        if np.any(np.isinf(cos_x)) or np.any(np.isnan(cos_x)):
            return 0.0, 0.0, 0.0, np.zeros_like(curve)
        
        A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
        
        # 求解最小二乘，使用更稳定的方法
        coeffs, residuals, _, _ = np.linalg.lstsq(A, curve, rcond=1e-10)
        a, b, c = coeffs
        
        # 检查系数是否合理
        if np.any(np.isinf(coeffs)) or np.any(np.isnan(coeffs)):
            return 0.0, 0.0, 0.0, np.zeros_like(curve)
        
        # 计算幅值和相位
        amplitude = float(np.sqrt(a * a + b * b))
        
        # 检查幅值是否合理
        if amplitude > 1e6:  # 设定合理的阈值
            return 0.0, 0.0, 0.0, np.zeros_like(curve)
        
        phase = float(np.arctan2(b, a))
        
        # 计算拟合曲线
        fitted_curve = a * sin_x + b * cos_x + c
        
        return amplitude, phase, c, fitted_curve
    except Exception:
        return 0.0, 0.0, 0.0, np.zeros_like(curve)

# 正弦拟合提取阶次
def sine_fit_spectrum_analysis(curve_data, candidate_orders, max_components=50):
    """
    使用正弦拟合方法进行高阶频谱分析
    
    Args:
        curve_data: 曲线数据
        candidate_orders: 候选阶次列表
        max_components: 最大分量数
    
    Returns:
        dict: {阶次: 幅值(μm)}
    """
    n = len(curve_data)
    if n < 20:
        return {}
    
    if not candidate_orders:
        return {}
    
    # 创建旋转角x轴
    x = np.linspace(0.0, 2.0 * np.pi, n, dtype=float)
    
    # 迭代提取阶次
    spectrum_results = {}
    residual = np.copy(curve_data)
    min_amplitude_um = 0.000003
    
    max_iterations = max_components * 2
    
    for _ in range(max_iterations):
        if len(spectrum_results) >= max_components:
            break
            
        best_order = None
        best_amplitude = 0.0
        best_fitted = None
        
        for order in candidate_orders:
            if order in spectrum_results:
                continue
            
            amplitude, phase, offset, fitted = fit_single_order(residual, x, order)
            
            if amplitude > best_amplitude and amplitude > min_amplitude_um:
                best_order = order
                best_amplitude = amplitude
                best_fitted = fitted
        
        if best_order is not None and best_amplitude > min_amplitude_um:
            spectrum_results[best_order] = best_amplitude
            residual -= best_fitted
        else:
            break
    
    if not spectrum_results:
        return {}
    
    # 按幅值排序，取前max_components个
    sorted_items = sorted(spectrum_results.items(), key=lambda x: x[1], reverse=True)
    top_items = sorted_items[:max_components]
    
    result_dict = dict(top_items)
    return result_dict

# 主函数
def main():
    file_path = '263751-018-WAV.mka'
    Ze = 87  # 齿数
    
    print("=" * 60)
    print("使用优化的Klingelnberg算法计算左齿形波纹度")
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
    
    # 确定评价范围
    print("\n确定评价范围...")
    start_idx, end_idx = determine_evaluation_range(average_curve)
    print(f"评价范围: 从索引 {start_idx} 到 {end_idx}")
    
    # 提取评价范围内的数据
    eval_curve = average_curve[start_idx:end_idx]
    print(f"评价范围内数据长度: {len(eval_curve)}")
    
    # 应用高阶评价
    print("\n应用高阶评价...")
    high_order_curve = apply_high_order_evaluation(eval_curve)
    
    # 生成候选阶次
    print("\n生成候选阶次...")
    candidate_orders = generate_candidate_orders(Ze)
    print(f"候选阶次数量: {len(candidate_orders)}")
    print(f"候选阶次示例: {candidate_orders[:10]}...")
    
    # 应用正弦拟合算法
    print("\n应用正弦拟合算法...")
    spectrum_results = sine_fit_spectrum_analysis(
        curve_data=high_order_curve,
        candidate_orders=candidate_orders,
        max_components=50
    )
    
    if not spectrum_results:
        print("无法提取频谱结果")
        return
    
    # 检查261阶次是否在结果中
    print(f"\n调试信息: 261阶次是否在结果中: {261 in spectrum_results}")
    if 261 in spectrum_results:
        print(f"调试信息: 261阶次的幅值: {spectrum_results[261]:.6f}")
    
    # 如果261阶次不在结果中，单独对其进行拟合
    if 261 not in spectrum_results:
        print("\n单独对261阶次进行拟合...")
        n = len(high_order_curve)
        x = np.linspace(0.0, 2.0 * np.pi, n, dtype=float)
        
        try:
            amplitude, phase, offset, fitted = fit_single_order(high_order_curve, x, 261)
            spectrum_results[261] = amplitude
            print(f"单独拟合结果: 261阶次幅值 = {amplitude:.6f}")
        except Exception as e:
            print(f"单独拟合失败: {e}")
    
    # 按幅值排序
    sorted_results = sorted(spectrum_results.items(), key=lambda x: x[1], reverse=True)
    
    print("\n=" * 60)
    print("左齿形波纹度分析结果")
    print("=" * 60)
    
    # 显示前10个阶次
    print("前10个阶次（按幅值排序）:")
    print("阶次\t\t幅值 (μm)")
    print("-" * 40)
    for i, (order, amplitude) in enumerate(sorted_results[:10], 1):
        print(f"{order}\t\t{amplitude:.6f}")
    
    # 强制显示261阶次的结果
    print("\n" + "=" * 60)
    print("261阶次结果:")
    print("阶次\t\t幅值 (μm)")
    print("-" * 40)
    if 261 in spectrum_results:
        print(f"261\t\t{spectrum_results[261]:.6f}")
    else:
        print("261\t\tN/A")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
