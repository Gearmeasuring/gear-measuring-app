#!/usr/bin/env python3
"""
测试克林贝格报表生成和图表更新功能
"""
import os
import sys
import tempfile
import shutil

# 设置正确的 Python 路径
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('./gear_analysis_refactored'))

# 导入必要的模块
try:
    # 动态导入模块，绕过 __init__.py 中的 config 导入问题
    import importlib.util
    
    # 导入 klingelnberg_single_page 模块
    single_page_spec = importlib.util.spec_from_file_location(
        'klingelnberg_single_page',
        os.path.join('gear_analysis_refactored', 'reports', 'klingelnberg_single_page.py')
    )
    klingelnberg_single_page = importlib.util.module_from_spec(single_page_spec)
    sys.modules['klingelnberg_single_page'] = klingelnberg_single_page
    single_page_spec.loader.exec_module(klingelnberg_single_page)
    
    print("✓ 成功导入 klingelnberg_single_page 模块")
    
    # 导入 klingelnberg_ripple_spectrum 模块
    ripple_spec = importlib.util.spec_from_file_location(
        'klingelnberg_ripple_spectrum',
        os.path.join('gear_analysis_refactored', 'reports', 'klingelnberg_ripple_spectrum.py')
    )
    klingelnberg_ripple_spectrum = importlib.util.module_from_spec(ripple_spec)
    sys.modules['klingelnberg_ripple_spectrum'] = klingelnberg_ripple_spectrum
    ripple_spec.loader.exec_module(klingelnberg_ripple_spectrum)
    
    print("✓ 成功导入 klingelnberg_ripple_spectrum 模块")
    
    # 检查模块中的类
    if hasattr(klingelnberg_single_page, 'KlingelnbergSinglePageReport'):
        print("✓ klingelnberg_single_page 模块包含 KlingelnbergSinglePageReport 类")
    else:
        print("✗ klingelnberg_single_page 模块不包含 KlingelnbergSinglePageReport 类")
    
    if hasattr(klingelnberg_ripple_spectrum, 'KlingelnbergRippleSpectrumReport'):
        print("✓ klingelnberg_ripple_spectrum 模块包含 KlingelnbergRippleSpectrumReport 类")
    else:
        print("✗ klingelnberg_ripple_spectrum 模块不包含 KlingelnbergRippleSpectrumReport 类")
        
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 创建测试数据结构
class MockMeasurementData:
    """模拟测量数据对象"""
    def __init__(self):
        # 基本信息
        class BasicInfo:
            def __init__(self):
                self.teeth = 87
                self.module = 1.0
                self.pressure_angle = 20.0
                self.helix_angle = 0.0
                self.width = 10.0
                self.order_no = "263751-018-WAV"
                self.drawing_no = "84-T3.2.47.02.76-G-WAV"
                self.date = "14.02.25"
                self.program = "263751-018-WAV"
                
                # 评价范围标记点
                self.profile_markers_left = (91.35, 87.0, 83.0, 81.75)
                self.profile_markers_right = (91.35, 87.0, 83.0, 81.75)
                self.lead_markers_left = (5.0, 2.0, -2.0, -5.0)
                self.lead_markers_right = (5.0, 2.0, -2.0, -5.0)
        
        self.basic_info = BasicInfo()
        
        # 齿形数据
        class ProfileData:
            def __init__(self):
                # 模拟齿形数据
                import numpy as np
                self.left = {}
                self.right = {}
                
                # 生成模拟数据
                for tooth in range(1, 6):
                    # 生成包含多个阶次的模拟数据
                    x = np.linspace(0, 100, 1000)
                    # 主阶次 87
                    y = 0.1 * np.sin(2 * np.pi * 87 * x / 100)
                    # 添加其他阶次
                    y += 0.05 * np.sin(2 * np.pi * 174 * x / 100)
                    y += 0.03 * np.sin(2 * np.pi * 261 * x / 100)
                    # 添加噪声
                    y += 0.01 * np.random.randn(len(x))
                    
                    self.left[tooth] = y.tolist()
                    self.right[tooth] = y.tolist()
        
        self.profile_data = ProfileData()
        
        # 齿向数据
        class FlankData:
            def __init__(self):
                # 模拟齿向数据
                import numpy as np
                self.left = {}
                self.right = {}
                
                # 生成模拟数据
                for tooth in range(1, 6):
                    # 生成包含多个阶次的模拟数据
                    x = np.linspace(0, 10, 1000)
                    # 主阶次 87
                    y = 0.08 * np.sin(2 * np.pi * 87 * x / 10)
                    # 添加其他阶次
                    y += 0.04 * np.sin(2 * np.pi * 174 * x / 10)
                    y += 0.02 * np.sin(2 * np.pi * 261 * x / 10)
                    # 添加噪声
                    y += 0.008 * np.random.randn(len(x))
                    
                    self.left[tooth] = y.tolist()
                    self.right[tooth] = y.tolist()
        
        self.flank_data = FlankData()

# 测试报表生成
def test_report_generation():
    """测试报表生成功能"""
    print("\n=== 测试报表生成 ===")
    
    try:
        # 创建测试数据
        measurement_data = MockMeasurementData()
        deviation_results = {}
        
        # 创建临时输出文件
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            output_path = tmp.name
        
        # 创建报表生成器
        report_generator = klingelnberg_single_page.KlingelnbergSinglePageReport()
        
        # 生成报表
        print(f"生成报表到: {output_path}")
        success = report_generator.generate_report(
            measurement_data,
            deviation_results,
            output_path,
            settings=None
        )
        
        if success:
            print("✓ 报表生成成功")
            print(f"报表文件大小: {os.path.getsize(output_path)} bytes")
            
            # 检查文件是否存在且不为空
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print("✓ 报表文件已创建且包含内容")
            else:
                print("✗ 报表文件创建失败或为空")
        else:
            print("✗ 报表生成失败")
        
        # 清理临时文件
        if os.path.exists(output_path):
            os.unlink(output_path)
            print("✓ 临时文件已清理")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

# 运行测试
if __name__ == "__main__":
    print("开始测试克林贝格报表生成和图表更新功能")
    print("=" * 60)
    
    # 测试报表生成
    test_report_generation()
    
    print("=" * 60)
    print("测试完成")
