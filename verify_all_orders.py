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

# 验证所有阶次
def verify_all_orders(curve, target_orders):
    """
    验证所有目标阶次
    
    Args:
        curve: 曲线数据
        target_orders: 目标阶次列表
    
    Returns:
        dict: {order: amplitude}
    """
    results = {}
    
    for order in target_orders:
        amp = sine_fit_direct(curve, order)
        results[order] = amp
    
    return results

# 主函数
def main():
    file_path = '263751-018-WAV.mka'
    
    # 目标阶次（从表格中获取）
    target_orders = [261, 87, 174, 435, 86]
    # 目标幅值（从表格中获取）
    target_amplitudes = [0.14, 0.14, 0.05, 0.04, 0.03]
    
    print("=" * 60)
    print("验证所有阶次和幅值")
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
    
    # 使用之前找到的最佳评价范围 (180-465)
    best_start = 180
    best_end = 465
    print(f"\n使用最佳评价范围: {best_start}-{best_end}")
    
    # 提取评价范围内的曲线
    eval_curve = high_order_curve[best_start:best_end]
    
    # 验证所有目标阶次
    print("\n验证所有目标阶次...")
    results = verify_all_orders(eval_curve, target_orders)
    
    # 打印验证结果
    print("\n验证结果:")
    print("阶次\t计算幅值 (μm)\t目标幅值 (μm)\t差异 (μm)\t是否符合")
    print("-" * 80)
    
    all_match = True
    for i, (order, amp) in enumerate(results.items()):
        target_amp = target_amplitudes[i]
        diff = abs(amp - target_amp)
        match = diff <= 0.01  # 允许0.01μm的误差
        status = "✅" if match else "❌"
        
        print(f"{order}\t{amp:.6f}\t\t{target_amp}\t\t{diff:.6f}\t\t{status}")
        
        if not match:
            all_match = False
    
    # 最终结论
    print("\n=" * 60)
    print("验证结论")
    print("=" * 60)
    
    if all_match:
        print("✅ 所有阶次和幅值都符合表格数据！")
    else:
        print("❌ 部分阶次或幅值不符合表格数据")
    
    # 显示详细对比
    print("\n详细对比:")
    print("表格数据:")
    print("阶次: 261, 87, 174, 435, 86")
    print("幅值: 0.14, 0.14, 0.05, 0.04, 0.03")
    
    print("\n计算数据:")
    for order, amp in results.items():
        print(f"{order}阶次: {amp:.6f} μm")
    
    print("\n=" * 60)

if __name__ == "__main__":
    main()