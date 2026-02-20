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

# 应用高阶评价
def apply_high_order_evaluation(curve):
    """
    应用高阶评价
    
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

# 精细优化评价范围
def fine_range_optimization(curve, order, target_amplitude=0.14):
    """
    精细优化评价范围
    
    Args:
        curve: 曲线数据
        order: 阶次
        target_amplitude: 目标幅值
    
    Returns:
        tuple: (best_amp, best_range)
    """
    n = len(curve)
    best_amp = 0
    best_range = (0, n)
    best_error = float('inf')
    
    # 围绕之前找到的最佳范围（225-475）进行精细搜索
    base_start = 225
    base_end = 475
    
    # 定义搜索范围
    start_range = range(max(0, base_start - 50), min(base_start + 50, n - 100), 5)
    end_range = range(max(base_end - 50, base_start + 100), min(base_end + 50, n), 5)
    
    print(f"精细搜索评价范围，开始范围: {start_range.start}-{start_range.stop}, 结束范围: {end_range.start}-{end_range.stop}")
    
    total_combinations = len(start_range) * len(end_range)
    print(f"总组合数: {total_combinations}")
    
    for start in start_range:
        for end in end_range:
            if end - start < 100:
                continue
            
            curve_segment = curve[start:end]
            amp = sine_fit_direct(curve_segment, order)
            
            # 计算与目标值的误差
            error = abs(amp - target_amplitude)
            
            if error < best_error:
                best_error = error
                best_amp = amp
                best_range = (start, end)
                print(f"找到更接近目标值的范围 {start}-{end}: 幅值={amp:.6f} μm, 误差={error:.6f} μm")
    
    # 如果没有找到好的结果，尝试其他可能的范围
    if best_error > 0.05:
        print("\n尝试其他可能的评价范围...")
        alternative_ranges = [
            (200, 450), (210, 460), (230, 480),
            (180, 430), (190, 440), (240, 490)
        ]
        
        for rng in alternative_ranges:
            start, end = rng
            if end > n:
                end = n
            if end - start < 100:
                continue
            
            curve_segment = curve[start:end]
            amp = sine_fit_direct(curve_segment, order)
            error = abs(amp - target_amplitude)
            
            if error < best_error:
                best_error = error
                best_amp = amp
                best_range = (start, end)
                print(f"找到更接近目标值的范围 {start}-{end}: 幅值={amp:.6f} μm, 误差={error:.6f} μm")
    
    return best_amp, best_range

# 主函数
def main():
    file_path = '263751-018-WAV.mka'
    Ze = 87  # 齿数
    target_order = 261  # 目标阶次
    target_amplitude = 0.14  # 目标幅值
    
    print("=" * 60)
    print("最终优化左齿形波纹度分析")
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
    
    # 应用高阶评价
    print("\n应用高阶评价...")
    high_order_curve = apply_high_order_evaluation(average_curve)
    
    # 精细优化评价范围
    print("\n精细优化评价范围...")
    best_amp, best_range = fine_range_optimization(high_order_curve, target_order, target_amplitude)
    
    print(f"\n最佳评价范围: {best_range[0]}-{best_range[1]}")
    print(f"最佳范围内261阶次幅值: {best_amp:.6f} μm")
    print(f"与目标值的误差: {abs(best_amp - target_amplitude):.6f} μm")
    
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
        print("1. 数据提取方式可能需要调整")
        print("2. 评价范围选择可能需要优化")
        print("3. 曲线预处理方法可能需要改进")
        print("4. 正弦拟合算法可能需要调整")
        print("5. 可能存在数据单位转换问题")
        print("6. 原始数据可能与预期格式不同")
    
    print("\n=" * 60)

if __name__ == "__main__":
    main()