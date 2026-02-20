import numpy as np
import re

# 读取MKA文件，提取左齿面的齿形数据
def extract_left_profile_data(file_path):
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
    left_profile_pattern = r'Profil:  Zahn-Nr.: \d+[abc] links \/ 480 Werte  \/ z= [\d.]+\n([\s\S]*?)(?=\n\n|$)'
    left_profiles = re.findall(left_profile_pattern, content)
    
    profile_data = []
    for profile in left_profiles:
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
            profile_data.append(values)
    
    return profile_data

# 应用高阶评价（去除低阶成分）
def apply_high_order_evaluation(curve):
    # 去除趋势（线性和二次）
    n = len(curve)
    x = np.arange(n)
    
    # 拟合二次曲线
    coeffs = np.polyfit(x, curve, 2)
    trend = np.polyval(coeffs, x)
    
    # 去除趋势，得到高阶成分
    high_order_curve = curve - trend
    
    return high_order_curve

# 正弦拟合，重点关注齿数倍数阶次
def sine_fit_focusing_ze_multiples(curve_data, ze, max_order=600):
    """
    正弦拟合，重点关注齿数倍数阶次
    
    Args:
        curve_data: 曲线数据
        ze: 齿数
        max_order: 最大阶次
    
    Returns:
        {阶次: 幅值(μm)}
    """
    n = len(curve_data)
    if n < 20:
        return {}
    
    # 生成候选阶次：重点关注齿数的倍数
    candidate_orders = []
    # 添加齿数的1-9倍
    for multiple in range(1, 10):
        order = ze * multiple
        if order <= max_order:
            candidate_orders.append(order)
            # 添加附近的阶次
            for offset in [-2, -1, 1, 2]:
                nearby_order = order + offset
                if nearby_order >= 1 and nearby_order <= max_order:
                    candidate_orders.append(nearby_order)
    
    # 添加原程序中提到的特定阶次
    reference_orders = {261, 262, 87, 174, 348}
    for order in reference_orders:
        if order <= max_order and order not in candidate_orders:
            candidate_orders.append(order)
    
    candidate_orders = sorted(list(set(candidate_orders)))
    
    if not candidate_orders:
        return {}
    
    # 创建旋转角x轴（0到2π代表整个旋转周期）
    x = np.linspace(0.0, 2.0 * np.pi, n, dtype=float)
    
    # 对每个候选阶次进行拟合
    results = {}
    for order in candidate_orders:
        try:
            # 构建矩阵 A = [sin(order*x), cos(order*x), 1]
            sin_x = np.sin(float(order) * x)
            cos_x = np.cos(float(order) * x)
            A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
            
            # 求解最小二乘
            coeffs, _, _, _ = np.linalg.lstsq(A, curve_data, rcond=None)
            a, b, c = coeffs
            
            # 计算幅值
            amplitude = float(np.sqrt(a * a + b * b))
            results[order] = amplitude
        except Exception:
            continue
    
    return results

# 主函数
def main():
    file_path = '263751-018-WAV.mka'
    ze = 87  # 齿数
    
    # 提取左齿面数据
    left_profiles = extract_left_profile_data(file_path)
    print(f"提取到 {len(left_profiles)} 个左齿面齿形数据")
    
    if not left_profiles:
        print("没有找到左齿面数据")
        return
    
    # 计算平均曲线
    data_array = np.array(left_profiles)
    average_curve = np.mean(data_array, axis=0)
    print(f"平均曲线长度: {len(average_curve)}")
    
    # 应用高阶评价
    high_order_curve = apply_high_order_evaluation(average_curve)
    
    # 正弦拟合，重点关注齿数倍数阶次
    results = sine_fit_focusing_ze_multiples(high_order_curve, ze)
    
    # 按幅值排序
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    
    print("=" * 60)
    print("齿轮波纹度分析结果")
    print("=" * 60)
    
    if sorted_results:
        # 第一主导阶次(O1)和对应幅值(A1)
        O1, A1 = sorted_results[0]
        print(f"第一主导阶次 (O1): {O1}")
        print(f"对应幅值 (A1): {A1:.6f} μm")
        print("=" * 60)
        
        # 打印前5个主要阶次
        print("前5个主要阶次:")
        for i, (order, amplitude) in enumerate(sorted_results[:5]):
            print(f"第{i+1}阶: {order}, 幅值: {amplitude:.6f} μm")
        
        # 特别关注261阶
        if 261 in results:
            print(f"\n261阶（齿数的3倍）幅值: {results[261]:.6f} μm")
    else:
        print("没有找到有效阶次")

if __name__ == "__main__":
    main()
