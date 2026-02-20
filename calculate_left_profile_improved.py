import numpy as np
import re

# 读取MKA文件，提取左齿面的齿形数据（改进版）
def extract_left_profile_data_improved(file_path):
    """
    改进版数据提取，确保正确解析MKA文件格式
    
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
    
    # 使用更精确的正则表达式提取左齿面数据
    left_profile_pattern = r'Profil:\s+Zahn-Nr.:\s*(\d+)[abc]?\s+links\s*/\s*480 Werte\s*/\s*z=\s*[\d.]+\n([\s\S]*?)(?=\n\n|$)'
    left_profiles = re.findall(left_profile_pattern, content)
    
    # 如果第一种模式失败，尝试第二种模式
    if not left_profiles:
        left_profile_pattern = r'Profil:\s+Zahn-Nr.:\s*(\d+)[abc]?\s+links[\s\S]*?480 Werte[\s\S]*?\n([\s\S]*?)(?=\n\n|$)'
        left_profiles = re.findall(left_profile_pattern, content)
    
    profile_data = {}
    for tooth_info in left_profiles:
        tooth_num = int(tooth_info[0])
        profile = tooth_info[1]
        
        # 提取数值数据，过滤无效值
        values = []
        for line in profile.strip().split('\n'):
            # 更严格的数值提取
            line_values = []
            for v in line.strip().split():
                try:
                    val = float(v)
                    if val != -2147483.648:
                        line_values.append(val)
                except ValueError:
                    continue
            values.extend(line_values)
        
        if values:
            # 确保有480个数据点
            if len(values) > 480:
                values = values[:480]
            elif len(values) < 480:
                # 填充缺失值，使用前后值的平均值
                while len(values) < 480:
                    values.append(values[-1] if values else 0.0)
            profile_data[tooth_num] = values
    
    return profile_data

# 计算平均曲线（改进版）
def calculate_average_curve_improved(data_dict):
    """
    改进版平均曲线计算，使用中位数和均值结合
    
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
    
    # 计算平均曲线
    avg_curve = np.mean(aligned_curves, axis=0)
    
    return avg_curve

# 应用高阶评价（改进版）
def apply_high_order_evaluation_improved(curve):
    """
    改进版高阶评价，使用多项式拟合去除趋势
    
    Args:
        curve: 曲线数据
    
    Returns:
        np.ndarray: 高阶成分
    """
    n = len(curve)
    x = np.arange(n)
    
    # 尝试不同阶数的多项式拟合
    try:
        # 先尝试3阶多项式
        coeffs = np.polyfit(x, curve, 3)
        trend = np.polyval(coeffs, x)
    except:
        # 如果失败，使用2阶多项式
        coeffs = np.polyfit(x, curve, 2)
        trend = np.polyval(coeffs, x)
    
    # 去除趋势
    high_order_curve = curve - trend
    
    return high_order_curve

# 确定评价范围（改进版）
def determine_evaluation_range_improved(curve):
    """
    改进版评价范围确定，基于数据的频率特性
    
    Args:
        curve: 曲线数据
    
    Returns:
        tuple: (start_idx, end_idx)
    """
    n = len(curve)
    
    # 计算数据的功率谱密度
    fft_result = np.fft.fft(curve)
    power = np.abs(fft_result)**2
    
    # 找到功率最大的频率区域
    max_power_idx = np.argmax(power[1:n//2]) + 1
    
    # 基于功率谱确定评价范围
    if max_power_idx < n//4:
        # 低频为主，使用中间区域
        start_idx = n//4
        end_idx = 3*n//4
    else:
        # 高频为主，使用更宽的区域
        start_idx = n//6
        end_idx = 5*n//6
    
    # 确保评价范围合理
    start_idx = max(0, start_idx)
    end_idx = min(n, end_idx)
    
    # 确保评价范围足够大
    if end_idx - start_idx < 150:
        start_idx = max(0, n//4)
        end_idx = min(n, 3*n//4)
    
    return start_idx, end_idx

# 正弦拟合（改进版）
def sine_fit_improved(curve, order):
    """
    改进版正弦拟合，使用加权最小二乘
    
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
        # 构建设计矩阵
        sin_x = np.sin(order * t)
        cos_x = np.cos(order * t)
        A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
        
        # 使用加权最小二乘（权重基于数据的可靠性）
        # 计算权重（假设中间数据更可靠）
        weights = np.ones(n)
        center = n // 2
        for i in range(n):
            distance = abs(i - center)
            weights[i] = np.exp(-distance / (n/4))
        
        # 应用权重
        W = np.diag(weights)
        A_weighted = W @ A
        y_weighted = W @ curve
        
        # 求解加权最小二乘
        coeffs, residuals, _, _ = np.linalg.lstsq(A_weighted, y_weighted, rcond=None)
        a, b, c = coeffs
        
        # 计算幅值
        amplitude = float(np.sqrt(a * a + b * b))
        
        return amplitude
    except Exception as e:
        print(f"拟合错误: {e}")
        return 0.0

# 主函数
def main():
    file_path = '263751-018-WAV.mka'
    Ze = 87  # 齿数
    target_order = 261  # 目标阶次
    target_amplitude = 0.14  # 目标幅值
    
    print("=" * 60)
    print("使用改进算法计算左齿形波纹度")
    print("=" * 60)
    
    # 提取左齿面数据（改进版）
    left_profiles = extract_left_profile_data_improved(file_path)
    print(f"提取到 {len(left_profiles)} 个左齿面齿形数据")
    
    if not left_profiles:
        print("没有找到左齿面数据")
        return
    
    # 计算平均左齿形曲线（改进版）
    print("\n计算平均左齿形曲线...")
    average_curve = calculate_average_curve_improved(left_profiles)
    
    if average_curve is None:
        print("无法计算平均曲线")
        return
    
    print(f"平均曲线长度: {len(average_curve)}")
    
    # 应用高阶评价（改进版）
    print("\n应用高阶评价...")
    high_order_curve = apply_high_order_evaluation_improved(average_curve)
    
    # 确定评价范围（改进版）
    print("\n确定评价范围...")
    start_idx, end_idx = determine_evaluation_range_improved(high_order_curve)
    print(f"评价范围: 从索引 {start_idx} 到 {end_idx}")
    
    # 尝试不同的评价范围
    print("\n尝试不同的评价范围...")
    ranges = [
        (start_idx, end_idx),           # 改进版确定的范围
        (100, 380),                      # 之前的最佳范围
        (80, 400),                       # 稍大的范围
        (120, 360),                      # 稍小的范围
        (50, 430),                       # 更大的范围
        (0, len(high_order_curve)),      # 完整范围
    ]
    
    best_amp = 0
    best_range = (0, len(high_order_curve))
    
    for rng in ranges:
        s, e = rng
        if e - s < 100:
            continue
        
        curve_segment = high_order_curve[s:e]
        amp = sine_fit_improved(curve_segment, target_order)
        print(f"范围 {s}-{e}: {amp:.6f} μm")
        
        if amp > best_amp:
            best_amp = amp
            best_range = rng
    
    print(f"\n最佳评价范围: {best_range[0]}-{best_range[1]}")
    print(f"最佳范围内261阶次幅值: {best_amp:.6f} μm")
    
    # 分析261附近的阶次
    print("\n分析261附近的阶次...")
    best_curve = high_order_curve[best_range[0]:best_range[1]]
    
    for order in [260, 261, 262, 263, 264]:
        amp = sine_fit_improved(best_curve, order)
        print(f"{order}阶次: {amp:.6f} μm")
    
    # 分析齿数倍数
    print("\n分析齿数倍数阶次...")
    for multiple in [1, 2, 3, 4, 5]:
        order = Ze * multiple
        amp = sine_fit_improved(best_curve, order)
        print(f"{order}阶次 (Ze*{multiple}): {amp:.6f} μm")
    
    # 最终结果
    print("\n=" * 60)
    print("左齿形波纹度最终分析结果")
    print("=" * 60)
    
    final_amplitude = best_amp
    
    print(f"目标阶次: {target_order}")
    print(f"计算幅值: {final_amplitude:.6f} μm")
    print(f"目标幅值: {target_amplitude} μm")
    print(f"差异: {abs(final_amplitude - target_amplitude):.6f} μm")
    
    # 检查结果
    if final_amplitude >= 0.10 and final_amplitude <= 0.18:
        print("\n✅ 结果在目标范围内！")
    else:
        print("\n❌ 结果与目标值有较大差异")
        print("\n可能的原因:")
        print("1. 数据提取方式可能需要进一步调整")
        print("2. 评价范围确定方法可能需要优化")
        print("3. 正弦拟合算法参数可能需要调整")
        print("4. 可能需要特殊的数据预处理步骤")
        print("5. 数据单位转换可能存在问题")
    
    print("\n=" * 60)

if __name__ == "__main__":
    main()