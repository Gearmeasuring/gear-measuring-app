"""
测试齿距数据整合到波纹频谱分析中
"""
import sys
import os
import numpy as np
from dataclasses import dataclass

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 打印当前工作目录和文件路径，用于调试
print(f"当前工作目录: {os.getcwd()}")
print(f"测试脚本路径: {os.path.abspath(__file__)}")

# 构造 klingelnberg_ripple_spectrum.py 文件的绝对路径
ripple_spectrum_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "gear_analysis_refactored",
    "reports",
    "klingelnberg_ripple_spectrum.py"
)
print(f"klingelnberg_ripple_spectrum.py 路径: {ripple_spectrum_path}")
print(f"文件是否存在: {os.path.exists(ripple_spectrum_path)}")

# 直接导入文件，避免导入 html_generator 模块
import importlib.util

# 创建一个临时模块，用于执行 klingelnberg_ripple_spectrum.py 文件
# 这样可以避免导入 config 模块时的错误
module_name = "klingelnberg_ripple_spectrum"
spec = importlib.util.spec_from_file_location(module_name, ripple_spectrum_path)
module = importlib.util.module_from_spec(spec)

# 添加模块到 sys.modules，这样模块可以被正确导入
sys.modules[module_name] = module

# 执行模块代码，捕获导入错误
try:
    spec.loader.exec_module(module)
    print("✓ 成功执行 klingelnberg_ripple_spectrum.py 文件")
except Exception as e:
    print(f"✗ 执行文件时出错: {e}")
    import traceback
    traceback.print_exc()

# 获取需要的类和函数
KlingelnbergRippleSpectrumReport = getattr(module, 'KlingelnbergRippleSpectrumReport', None)
SpectrumParams = getattr(module, 'SpectrumParams', None)

if KlingelnbergRippleSpectrumReport and SpectrumParams:
    print("✓ 成功获取 KlingelnbergRippleSpectrumReport 和 SpectrumParams 类")
else:
    print("✗ 无法获取 KlingelnbergRippleSpectrumReport 或 SpectrumParams 类")
    print(f"KlingelnbergRippleSpectrumReport: {KlingelnbergRippleSpectrumReport}")
    print(f"SpectrumParams: {SpectrumParams}")

@dataclass
class BasicInfo:
    """基本信息类"""
    teeth: int = 87
    module: float = 2.0
    pressure_angle: float = 20.0
    helix_angle: float = 15.0
    profile_eval_start: float = 40.0
    profile_eval_end: float = 50.0
    helix_eval_start: float = 0.0
    helix_eval_end: float = 20.0
    pitch_data: dict = None
    pitch_measurement_diameter: float = 45.0
    pitch_measurement_height: float = 10.0

@dataclass
class ProfileData:
    """齿廓数据类"""
    right: dict = None
    left: dict = None

@dataclass
class FlankData:
    """齿向数据类"""
    right: dict = None
    left: dict = None

@dataclass
class MeasurementData:
    """测量数据类"""
    basic_info: BasicInfo
    profile_data: ProfileData
    flank_data: FlankData
    pitch_data: dict = None

def generate_test_data(teeth_count=87, points_per_tooth=100):
    """生成测试数据"""
    # 生成齿廓数据
    profile_right = {}
    profile_left = {}
    
    # 生成齿向数据
    flank_right = {}
    flank_left = {}
    
    # 生成齿距数据
    pitch_data = {}
    
    for tooth in range(teeth_count):
        # 生成齿廓测试数据（添加一些随机噪声）
        profile_right[tooth] = np.sin(np.linspace(0, 4 * np.pi, points_per_tooth)) * 0.1 + np.random.normal(0, 0.02, points_per_tooth)
        profile_left[tooth] = np.sin(np.linspace(0, 4 * np.pi, points_per_tooth)) * 0.1 + np.random.normal(0, 0.02, points_per_tooth)
        
        # 生成齿向测试数据
        flank_right[tooth] = np.sin(np.linspace(0, 2 * np.pi, points_per_tooth)) * 0.08 + np.random.normal(0, 0.01, points_per_tooth)
        flank_left[tooth] = np.sin(np.linspace(0, 2 * np.pi, points_per_tooth)) * 0.08 + np.random.normal(0, 0.01, points_per_tooth)
        
        # 生成齿距数据（添加一些随机偏差）
        pitch_data[tooth] = np.random.normal(0, 0.005, 1)[0]
    
    return profile_right, profile_left, flank_right, flank_left, pitch_data

def test_pitch_integration():
    """测试齿距数据整合"""
    print("=== 测试齿距数据整合到波纹频谱分析 ===")
    
    # 生成测试数据
    teeth_count = 87
    points_per_tooth = 100
    
    profile_right, profile_left, flank_right, flank_left, pitch_data = generate_test_data(teeth_count, points_per_tooth)
    
    print(f"生成了 {teeth_count} 个齿的数据，每个齿 {points_per_tooth} 个点")
    print(f"齿距数据示例: {dict(list(pitch_data.items())[:5])}")
    
    # 创建测量数据对象
    basic_info = BasicInfo(
        teeth=teeth_count,
        pitch_data=pitch_data,
        pitch_measurement_diameter=45.0,
        pitch_measurement_height=10.0
    )
    
    profile_data = ProfileData(
        right=profile_right,
        left=profile_left
    )
    
    flank_data = FlankData(
        right=flank_right,
        left=flank_left
    )
    
    measurement_data = MeasurementData(
        basic_info=basic_info,
        profile_data=profile_data,
        flank_data=flank_data,
        pitch_data=pitch_data
    )
    
    # 创建波纹频谱报告对象
    report = KlingelnbergRippleSpectrumReport()
    
    # 测试 _calculate_spectrum 方法
    print("\n=== 测试 _calculate_spectrum 方法 ===")
    
    # 创建频谱计算参数
    spectrum_params = SpectrumParams(
        data_dict=profile_right,
        teeth_count=teeth_count,
        eval_markers=(35.0, 40.0, 50.0, 55.0),
        max_order=609,
        eval_length=10.0,
        base_diameter=45.0,
        max_components=11,
        side='right',
        data_type='profile',
        info=basic_info,
        pitch_data=pitch_data
    )
    
    # 计算频谱
    orders, amplitudes = report._calculate_spectrum(spectrum_params)
    
    print(f"计算得到的阶次: {orders}")
    print(f"计算得到的幅值: {amplitudes}")
    
    # 测试闭合曲线构建方法
    print("\n=== 测试闭合曲线构建方法 ===")
    
    # 处理齿数据
    all_tooth_data = []
    for tooth in range(teeth_count):
        values = profile_right[tooth]
        # 处理数据（去均值、端点匹配）
        detrended = values - np.mean(values)
        # 端点匹配
        ramp = np.linspace(detrended[0], detrended[-1], len(detrended))
        detrended = detrended - ramp
        all_tooth_data.append(detrended)
    
    # 构建闭合曲线
    common_curve = report._build_common_closed_curve_angle(
        all_tooth_data,
        eval_length=10.0,
        base_diameter=45.0,
        teeth_count=teeth_count,
        pitch_data=pitch_data
    )
    
    print(f"构建的闭合曲线长度: {len(common_curve)}")
    print(f"闭合曲线数据范围: [{np.min(common_curve):.3f}, {np.max(common_curve):.3f}]")
    
    # 测试测量位置一致性检查
    print("\n=== 测试测量位置一致性检查 ===")
    consistency = report._check_measurement_position_consistency(basic_info)
    print(f"位置一致性检查结果: {consistency}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_pitch_integration()
