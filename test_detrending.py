#!/usr/bin/env python3
"""
测试修改后的去鼓形和趋势处理代码
验证修改后的代码是否能正确去除鼓形和趋势的影响
"""
import numpy as np
import sys
import os
import matplotlib.pyplot as plt

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 修复模块导入问题
try:
    from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport
except ImportError as e:
    print(f"导入错误: {e}")
    print("尝试直接导入...")
    # 直接导入文件
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "klingelnberg_ripple_spectrum",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "gear_analysis_refactored", "reports", "klingelnberg_ripple_spectrum.py")
    )
    klingelnberg_ripple_spectrum = importlib.util.module_from_spec(spec)
    sys.modules["klingelnberg_ripple_spectrum"] = klingelnberg_ripple_spectrum
    spec.loader.exec_module(klingelnberg_ripple_spectrum)
    KlingelnbergRippleSpectrumReport = klingelnberg_ripple_spectrum.KlingelnbergRippleSpectrumReport
    print("直接导入成功")

class TestInfo:
    """测试用的基本信息类"""
    def __init__(self):
        self.module = 2.0
        self.teeth = 87
        self.pressure_angle = 20.0
        self.helix_angle = 0.0
        self.profile_meas_start = 50.0
        self.profile_meas_end = 60.0

def generate_data_with_crowning_and_trend(n_points=100, crown_amplitude=0.5, linear_slope=0.01, noise=0.1):
    """生成带有鼓形和趋势的数据"""
    x = np.linspace(0, 1, n_points)
    
    # 鼓形（2阶多项式）
    crown = crown_amplitude * 4 * x * (1 - x)
    
    # 线性趋势
    linear_trend = linear_slope * np.arange(n_points)
    
    # 噪声
    noise = noise * np.random.randn(n_points)
    
    # 合成数据
    y = crown + linear_trend + noise
    
    return y.tolist(), crown, linear_trend

def plot_data_comparison(original, crown, linear_trend, detrended, title):
    """绘制数据对比图"""
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.plot(original, 'b-', label='原始数据')
    plt.plot(crown, 'r--', label='鼓形')
    plt.plot(linear_trend, 'g--', label='线性趋势')
    plt.title(f'{title} - 原始数据与趋势成分')
    plt.legend()
    plt.grid(True)
    
    plt.subplot(2, 1, 2)
    plt.plot(original, 'b-', label='原始数据')
    plt.plot(detrended, 'm-', label='去趋势后')
    plt.title(f'{title} - 去趋势前后对比')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig(f"test_result_{title.replace(' ', '_').lower()}.png")
    plt.close()
    print(f"已保存图表: test_result_{title.replace(' ', '_').lower()}.png")

def test_detrending():
    """测试去趋势处理"""
    print("=== 测试修改后的去鼓形和趋势处理代码 ===")
    
    # 创建测试对象
    report = KlingelnbergRippleSpectrumReport()
    info = TestInfo()
    
    # 生成测试数据
    print("\n1. 生成测试数据...")
    
    # 生成带有鼓形和趋势的数据
    data_with_crown, crown, linear_trend = generate_data_with_crowning_and_trend(
        n_points=100, 
        crown_amplitude=0.5, 
        linear_slope=0.01, 
        noise=0.1
    )
    
    print(f"数据长度: {len(data_with_crown)}")
    print(f"原始数据范围: [{min(data_with_crown):.3f}, {max(data_with_crown):.3f}]")
    print(f"鼓形范围: [{min(crown):.3f}, {max(crown):.3f}]")
    print(f"线性趋势范围: [{min(linear_trend):.3f}, {max(linear_trend):.3f}]")
    
    # 测试Profile数据处理
    print("\n2. 测试Profile数据去鼓形和趋势处理...")
    
    detrended_profile = report._process_tooth_data(
        data_with_crown,
        info,
        eval_markers=(50.0, 52.0, 58.0, 60.0),
        data_type='profile',
        side='right',
        preserve_signal=True  # 测试默认情况
    )

    print(f"去趋势后Profile数据范围: [{min(detrended_profile):.3f}, {max(detrended_profile):.3f}]")
    print(f"去趋势后Profile数据均值: {np.mean(detrended_profile):.6f}")
    print(f"去趋势后Profile数据标准差: {np.std(detrended_profile):.6f}")
    
    # 测试Helix数据处理
    print("\n3. 测试Helix数据去趋势处理...")
    detrended_helix = report._process_tooth_data(
        data_with_crown,
        info,
        eval_markers=(0.0, 2.0, 8.0, 10.0),
        data_type='flank',
        side='right',
        preserve_signal=True  # 测试默认情况
    )
    
    print(f"去趋势后Helix数据范围: [{min(detrended_helix):.3f}, {max(detrended_helix):.3f}]")
    print(f"去趋势后Helix数据均值: {np.mean(detrended_helix):.6f}")
    print(f"去趋势后Helix数据标准差: {np.std(detrended_helix):.6f}")
    
    # 绘制对比图
    print("\n4. 生成对比图表...")
    plot_data_comparison(
        data_with_crown, 
        crown, 
        linear_trend, 
        detrended_profile, 
        "Profile数据去鼓形和趋势处理"
    )
    
    plot_data_comparison(
        data_with_crown, 
        crown, 
        linear_trend, 
        detrended_helix, 
        "Helix数据去趋势处理"
    )
    
    # 验证结果
    print("\n5. 验证结果...")
    
    # 检查均值是否接近零
    profile_mean = np.mean(detrended_profile)
    helix_mean = np.mean(detrended_helix)
    
    print(f"Profile数据去趋势后均值: {profile_mean:.6f} (应接近0)")
    print(f"Helix数据去趋势后均值: {helix_mean:.6f} (应接近0)")
    
    # 检查数据范围是否减小（去除了趋势）
    original_range = max(data_with_crown) - min(data_with_crown)
    profile_range = max(detrended_profile) - min(detrended_profile)
    helix_range = max(detrended_helix) - min(detrended_helix)
    
    print(f"原始数据范围: {original_range:.3f}")
    print(f"Profile去趋势后范围: {profile_range:.3f} (应小于原始范围)")
    print(f"Helix去趋势后范围: {helix_range:.3f} (应小于原始范围)")
    
    # 总结
    success = True
    if abs(profile_mean) > 0.1:
        print("❌ Profile数据去均值不完全")
        success = False
    else:
        print("✅ Profile数据去均值成功")
    
    if abs(helix_mean) > 0.1:
        print("❌ Helix数据去均值不完全")
        success = False
    else:
        print("✅ Helix数据去均值成功")
    
    if profile_range >= original_range:
        print("❌ Profile数据去趋势效果不明显")
        success = False
    else:
        print("✅ Profile数据去趋势效果明显")
    
    if helix_range >= original_range:
        print("❌ Helix数据去趋势效果不明显")
        success = False
    else:
        print("✅ Helix数据去趋势效果明显")
    
    if success:
        print("\n✅ 测试通过：去鼓形和趋势处理代码工作正常")
    else:
        print("\n❌ 测试失败：去鼓形和趋势处理代码存在问题")
    
    return success

if __name__ == "__main__":
    success = test_detrending()
    print(f"\n测试结果: {'成功' if success else '失败'}")
