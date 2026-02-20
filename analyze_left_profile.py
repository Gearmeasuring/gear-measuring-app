import numpy as np
import matplotlib.pyplot as plt
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

# 计算平均曲线
def calculate_average_curve(profile_data):
    if not profile_data:
        return []
    
    # 转换为numpy数组
    data_array = np.array(profile_data)
    # 计算平均值
    average_curve = np.mean(data_array, axis=0)
    
    return average_curve

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

# 正弦拟合，提取主要阶次
def sine_fit(curve, max_order=200):
    n = len(curve)
    x = np.linspace(0, 2 * np.pi, n)
    
    best_amplitude = 0
    best_order = 1
    best_fit = np.zeros(n)
    
    # 测试不同阶次
    for order in range(1, max_order + 1):
        # 构建正弦和余弦矩阵
        sin_x = np.sin(order * x)
        cos_x = np.cos(order * x)
        A = np.column_stack((sin_x, cos_x, np.ones_like(x)))
        
        # 最小二乘拟合
        coeffs, _, _, _ = np.linalg.lstsq(A, curve, rcond=None)
        a, b, c = coeffs
        
        # 计算幅值
        amplitude = np.sqrt(a**2 + b**2)
        
        if amplitude > best_amplitude:
            best_amplitude = amplitude
            best_order = order
            best_fit = a * sin_x + b * cos_x + c
    
    return best_order, best_amplitude, best_fit

# 主函数
def main():
    file_path = '263751-018-WAV.mka'
    
    # 提取左齿面数据
    left_profiles = extract_left_profile_data(file_path)
    print(f"提取到 {len(left_profiles)} 个左齿面齿形数据")
    
    if not left_profiles:
        print("没有找到左齿面数据")
        return
    
    # 计算平均曲线
    average_curve = calculate_average_curve(left_profiles)
    print(f"平均曲线长度: {len(average_curve)}")
    
    # 应用高阶评价
    high_order_curve = apply_high_order_evaluation(average_curve)
    
    # 正弦拟合
    best_order, best_amplitude, best_fit = sine_fit(high_order_curve)
    
    # 计算频率（Hz）
    # 假设测量时间为1秒（实际应根据测量参数计算）
    frequency = best_order  # 阶次在1秒内的周期数
    
    print("=" * 60)
    print("正弦拟合结果（高阶评价）")
    print("=" * 60)
    print(f"第一主要阶次: {best_order}")
    print(f"幅值: {best_amplitude:.6f} μm")
    print(f"频率: {frequency:.2f} Hz")
    print("=" * 60)
    
    # 绘制结果
    plt.figure(figsize=(12, 8))
    
    # 原始平均曲线
    plt.subplot(3, 1, 1)
    plt.plot(average_curve, label='原始平均曲线')
    plt.title('左齿面齿形平均曲线')
    plt.ylabel('偏差 (μm)')
    plt.legend()
    
    # 高阶成分
    plt.subplot(3, 1, 2)
    plt.plot(high_order_curve, label='高阶成分')
    plt.title('高阶评价结果')
    plt.ylabel('偏差 (μm)')
    plt.legend()
    
    # 拟合结果
    plt.subplot(3, 1, 3)
    plt.plot(high_order_curve, label='高阶成分')
    plt.plot(best_fit, label=f'正弦拟合 (阶次={best_order}, 幅值={best_amplitude:.3f}μm)')
    plt.title('正弦拟合结果')
    plt.xlabel('数据点')
    plt.ylabel('偏差 (μm)')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('left_profile_analysis.png')
    print("分析结果已保存到 left_profile_analysis.png")

if __name__ == "__main__":
    main()
