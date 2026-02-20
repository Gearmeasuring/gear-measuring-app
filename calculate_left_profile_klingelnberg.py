import numpy as np
import re
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入Klingelnberg标准算法
try:
    from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings, SineFitParams
    print("✓ 成功导入Klingelnberg标准算法")
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

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
    left_profile_pattern = r'Profil:  Zahn-Nr.: (\d+)[abc] links \/ 480 Werte  \/ z= [\d.]+\n([\s\S]*?)(?=\n\n|$)'
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

# 主函数
def main():
    file_path = '263751-018-WAV.mka'
    Ze = 87  # 齿数
    
    print("=" * 60)
    print("使用Klingelnberg标准算法计算左齿形波纹度")
    print("=" * 60)
    
    # 提取左齿面数据
    left_profiles = extract_left_profile_data(file_path)
    print(f"提取到 {len(left_profiles)} 个左齿面齿形数据")
    
    if not left_profiles:
        print("没有找到左齿面数据")
        return
    
    # 初始化Klingelnberg算法
    settings = RippleSpectrumSettings()
    analyzer = KlingelnbergRippleSpectrumReport(settings)
    
    # 计算平均左齿形曲线
    print("\n计算平均左齿形曲线...")
    average_curve = analyzer._calculate_average_curve(left_profiles)
    
    if average_curve is None:
        print("无法计算平均曲线")
        return
    
    print(f"平均曲线长度: {len(average_curve)}")
    
    # 应用Klingelnberg正弦拟合算法
    print("\n应用Klingelnberg正弦拟合算法...")
    sine_fit_params = SineFitParams(
        curve_data=average_curve,
        ze=Ze,
        max_order=500,
        max_components=50
    )
    
    spectrum_results = analyzer._sine_fit_spectrum_analysis(sine_fit_params)
    
    if not spectrum_results:
        print("无法提取频谱结果")
        return
    
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
    
    # 查找261阶次的结果
    if 261 in spectrum_results:
        print("\n" + "=" * 60)
        print("261阶次结果:")
        print("阶次\t\t幅值 (μm)")
        print("-" * 40)
        print(f"261\t\t{spectrum_results[261]:.6f}")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
