#!/usr/bin/env python3
"""
测试修改后的频谱分析代码
验证不同输入数据是否产生不同的频谱结果
"""
import numpy as np
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 修复模块导入问题
try:
    from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, SpectrumParams
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
    SpectrumParams = klingelnberg_ripple_spectrum.SpectrumParams
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

def generate_test_data(frequency1=1, frequency2=2, amplitude1=0.5, amplitude2=0.2, noise=0.05, n_points=100):
    """生成测试数据"""
    x = np.linspace(0, 2*np.pi, n_points)
    y = amplitude1 * np.sin(frequency1 * x) + amplitude2 * np.sin(frequency2 * x)
    y += noise * np.random.randn(n_points)
    return y.tolist()

def test_spectrum_analysis():
    """测试频谱分析"""
    print("=== 测试修改后的频谱分析代码 ===")
    
    # 创建测试对象
    report = KlingelnbergRippleSpectrumReport()
    info = TestInfo()
    
    # 生成不同的测试数据
    print("\n1. 生成测试数据...")
    
    # 数据1：主要频率为1和2
    data1 = generate_test_data(frequency1=1, frequency2=2, amplitude1=0.5, amplitude2=0.2)
    
    # 数据2：主要频率为3和4
    data2 = generate_test_data(frequency1=3, frequency2=4, amplitude1=0.4, amplitude2=0.3)
    
    # 数据3：主要频率为5和6
    data3 = generate_test_data(frequency1=5, frequency2=6, amplitude1=0.6, amplitude2=0.1)
    
    print(f"数据1长度: {len(data1)}, 范围: [{min(data1):.3f}, {max(data1):.3f}]")
    print(f"数据2长度: {len(data2)}, 范围: [{min(data2):.3f}, {max(data2):.3f}]")
    print(f"数据3长度: {len(data3)}, 范围: [{min(data3):.3f}, {max(data3):.3f}]")
    
    # 创建数据字典
    data_dict1 = {1: data1, 2: data1, 3: data1}  # 3个齿，数据相同
    data_dict2 = {1: data2, 2: data2, 3: data2}  # 3个齿，数据相同
    data_dict3 = {1: data3, 2: data3, 3: data3}  # 3个齿，数据相同
    
    # 测试参数
    teeth_count = 87
    eval_markers = (50.0, 52.0, 58.0, 60.0)  # 模拟评价范围标记
    max_components = 5
    
    print("\n2. 测试数据1的频谱分析...")
    params1 = SpectrumParams(
        data_dict=data_dict1,
        teeth_count=teeth_count,
        eval_markers=eval_markers,
        max_components=max_components,
        side='right',
        data_type='profile',
        info=info
    )
    
    orders1, amps1 = report._calculate_spectrum(params1)
    print(f"数据1结果 - 阶次: {orders1}, 幅值: {amps1}")
    
    print("\n3. 测试数据2的频谱分析...")
    params2 = SpectrumParams(
        data_dict=data_dict2,
        teeth_count=teeth_count,
        eval_markers=eval_markers,
        max_components=max_components,
        side='right',
        data_type='profile',
        info=info
    )
    
    orders2, amps2 = report._calculate_spectrum(params2)
    print(f"数据2结果 - 阶次: {orders2}, 幅值: {amps2}")
    
    print("\n4. 测试数据3的频谱分析...")
    params3 = SpectrumParams(
        data_dict=data_dict3,
        teeth_count=teeth_count,
        eval_markers=eval_markers,
        max_components=max_components,
        side='right',
        data_type='profile',
        info=info
    )
    
    orders3, amps3 = report._calculate_spectrum(params3)
    print(f"数据3结果 - 阶次: {orders3}, 幅值: {amps3}")
    
    # 验证结果是否不同
    print("\n5. 验证结果是否不同...")
    
    # 检查阶次是否不同
    orders_equal12 = np.array_equal(orders1, orders2)
    orders_equal13 = np.array_equal(orders1, orders3)
    orders_equal23 = np.array_equal(orders2, orders3)
    
    # 检查幅值是否不同
    amps_equal12 = np.allclose(amps1, amps2, atol=0.1)
    amps_equal13 = np.allclose(amps1, amps3, atol=0.1)
    amps_equal23 = np.allclose(amps2, amps3, atol=0.1)
    
    print(f"数据1和数据2阶次相同: {orders_equal12}")
    print(f"数据1和数据3阶次相同: {orders_equal13}")
    print(f"数据2和数据3阶次相同: {orders_equal23}")
    
    print(f"数据1和数据2幅值相同: {amps_equal12}")
    print(f"数据1和数据3幅值相同: {amps_equal13}")
    print(f"数据2和数据3幅值相同: {amps_equal23}")
    
    # 总结
    if not (orders_equal12 and orders_equal13 and orders_equal23) or not (amps_equal12 and amps_equal13 and amps_equal23):
        print("\n✅ 测试通过：不同数据产生不同的频谱结果")
        return True
    else:
        print("\n❌ 测试失败：不同数据产生相同的频谱结果")
        return False

if __name__ == "__main__":
    success = test_spectrum_analysis()
    print(f"\n测试结果: {'成功' if success else '失败'}")
