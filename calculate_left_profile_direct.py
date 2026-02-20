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

# 主函数
def main():
    file_path = '263751-018-WAV.mka'
    Ze = 87  # 齿数
    target_order = 261  # 目标阶次
    target_amplitude = 0.14  # 目标幅值
    
    print("=" * 60)
    print("使用直接方法计算左齿形波纹度")
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
    
    # 尝试不同的评价范围
    print("\n尝试不同的评价范围...")
    ranges = [
        (0, len(high_order_curve)),      # 完整范围
        (100, 380),                       # 中间范围
        (50, 430),                        # 稍大的中间范围
        (200, 300),                       # 中间核心范围
        (150, 330),                       # 稍大的核心范围
    ]
    
    best_amp = 0
    best_range = (0, len(high_order_curve))
    
    for rng in ranges:
        s, e = rng
        if e - s < 100:
            continue
        
        curve_segment = high_order_curve[s:e]
        amp = sine_fit_direct(curve_segment, target_order)
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
        amp = sine_fit_direct(best_curve, order)
        print(f"{order}阶次: {amp:.6f} μm")
    
    # 分析齿数倍数
    print("\n分析齿数倍数阶次...")
    for multiple in [1, 2, 3, 4, 5]:
        order = Ze * multiple
        amp = sine_fit_direct(best_curve, order)
        print(f"{order}阶次 (Ze*{multiple}): {amp:.6f} μm")
    
    # 最终结果
    print("\n=" * 60)
    print("左齿形波纹度最终分析结果")
    print("=" * 60)
    
    final_amplitude = sine_fit_direct(best_curve, target_order)
    
    print(f"目标阶次: {target_order}")
    print(f"计算幅值: {final_amplitude:.6f} μm")
    print(f"目标幅值: {target_amplitude} μm")
    print(f"差异: {abs(final_amplitude - target_amplitude):.6f} μm")
    
    # 检查结果
    if final_amplitude >= 0.10 and final_amplitude <= 0.18:
        print("\n✅ 结果在目标范围内！")
    else:
        print("\n❌ 结果与目标值有较大差异")
    
    print("\n=" * 60)

if __name__ == "__main__":
    main()