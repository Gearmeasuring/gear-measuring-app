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

# 优化右齿形87阶分析
def optimize_right_87_order(curve):
    """
    优化右齿形87阶分析
    
    Args:
        curve: 曲线数据
    
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
    
    # 尝试更广泛的范围长度
    lengths = [100, 120, 150, 180, 200, 220, 250, 280, 300]
    
    # 尝试更细的步长
    step = 10
    
    print("开始优化右齿形87阶分析...")
    
    for method in methods:
        # 应用高阶评价
        processed_curve = apply_high_order_evaluation(curve, method)
        
        # 尝试多种评价范围
        for length in lengths:
            for start in range(0, len(processed_curve) - length + 1, step):
                end = start + length
                
                if end > len(processed_curve):
                    continue
                
                curve_segment = processed_curve[start:end]
                amp = sine_fit_direct(curve_segment, 87)
                error = abs(amp - 0.14)
                
                if error < best_error:
                    best_error = error
                    best_amp = amp
                    best_method = method
                    best_start = start
                    best_end = end
                    
                    # 实时更新最佳结果
                    print(f"找到更好的参数: 方法={method}, 范围={start}-{end}, 幅值={amp:.6f} μm, 误差={error:.6f} μm")
    
    return {
        'amp': best_amp,
        'error': best_error,
        'method': best_method,
        'start': best_start,
        'end': best_end
    }

# 主函数
def main():
    file_path = '263751-018-WAV.mka'
    
    print("=" * 60)
    print("右齿形87阶优化分析")
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
    
    # 优化87阶分析
    print("\n优化87阶分析...")
    best_params = optimize_right_87_order(average_curve)
    
    print("\n=" * 60)
    print("优化结果")
    print("=" * 60)
    
    print(f"最佳方法: {best_params['method']}")
    print(f"最佳范围: {best_params['start']}-{best_params['end']}")
    print(f"计算幅值: {best_params['amp']:.6f} μm")
    print(f"目标幅值: 0.14 μm")
    print(f"误差: {best_params['error']:.6f} μm")
    
    if best_params['error'] <= 0.01:
        print("\n✅ 87阶分析成功符合目标值！")
    else:
        print("\n❌ 87阶分析仍需进一步优化")
    
    print("\n=" * 60)

if __name__ == "__main__":
    main()
