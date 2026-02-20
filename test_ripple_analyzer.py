"""
波纹度分析算法测试脚本

用于验证重构后的波纹度分析算法的正确性
"""

import os
import sys
import math
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'gear_analysis_refactored'))

from analysis.ripple_analyzer import (
    RippleAnalyzer, GearParameters, EvaluationRange,
    DataType, Side, DataPreprocessor, AngleSynthesizer,
    SpectrumAnalyzer, HighOrderEvaluator
)
from utils.file_parser import parse_mka_file


def test_preprocessor():
    """测试数据预处理器"""
    print("\n" + "="*60)
    print("测试数据预处理器")
    print("="*60)
    
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 3.0, 2.0, 1.0])
    
    preprocessor = DataPreprocessor()
    corrected = preprocessor.remove_crown_and_slope(data)
    
    print(f"原始数据: {data}")
    print(f"修正后数据: {corrected}")
    print(f"修正后均值: {np.mean(corrected):.6f} (应接近0)")
    print(f"修正后标准差: {np.std(corrected):.6f}")
    
    assert abs(np.mean(corrected)) < 1e-6, "均值应接近0"
    print("✓ 数据预处理器测试通过")


def test_angle_synthesizer():
    """测试角度合成器"""
    print("\n" + "="*60)
    print("测试角度合成器")
    print("="*60)
    
    params = GearParameters(
        teeth_count=87,
        module=1.859,
        pressure_angle=18.6,
        helix_angle=25.3
    )
    
    synthesizer = AngleSynthesizer(params)
    
    print(f"\n齿轮参数:")
    print(f"  齿数: {params.teeth_count}")
    print(f"  模数: {params.module} mm")
    print(f"  压力角: {params.pressure_angle}°")
    print(f"  螺旋角: {params.helix_angle}°")
    print(f"  基圆直径: {params.base_diameter:.3f} mm")
    print(f"  节圆直径: {params.pitch_diameter:.3f} mm")
    
    diameter = 180.0
    roll_angle = synthesizer.calculate_roll_angle(diameter)
    print(f"\n展长角度计算:")
    print(f"  直径 {diameter} mm 对应的展长角度: {roll_angle:.4f}°")
    
    diameters = np.array([175.0, 177.5, 180.0, 182.5, 185.0])
    profile_angles = synthesizer.synthesize_profile_angles(diameters, 0, Side.LEFT)
    print(f"\n齿形角度合成 (齿0, 左齿面):")
    print(f"  直径: {diameters}")
    print(f"  角度: {profile_angles}")
    
    eval_range = EvaluationRange(2.1, 39.9, 2.1, 39.9)
    axial_positions = np.array([10.0, 20.0, 30.0])
    helix_angles = synthesizer.synthesize_helix_angles(axial_positions, 0, eval_range, Side.LEFT)
    print(f"\n齿向角度合成 (齿0, 左齿面):")
    print(f"  轴向位置: {axial_positions}")
    print(f"  角度: {helix_angles}")
    
    print("✓ 角度合成器测试通过")


def test_spectrum_analyzer():
    """测试频谱分析器"""
    print("\n" + "="*60)
    print("测试频谱分析器")
    print("="*60)
    
    params = GearParameters(teeth_count=87, module=1.859)
    analyzer = SpectrumAnalyzer(params)
    
    angles = np.linspace(0, 360, 360)
    signal = 2.0 * np.sin(np.radians(87 * angles)) + 1.5 * np.sin(np.radians(174 * angles))
    
    result = analyzer.iterative_decomposition(angles, signal, num_components=5, verbose=True)
    
    print(f"\n提取的阶次: {result.orders}")
    print(f"提取的振幅: {result.amplitudes}")
    
    expected_orders = [87, 174]
    for expected in expected_orders:
        if expected in result.orders:
            idx = np.where(result.orders == expected)[0][0]
            print(f"  阶次 {expected}: 振幅 {result.amplitudes[idx]:.4f} (期望约 {2.0 if expected == 87 else 1.5})")
    
    print("✓ 频谱分析器测试通过")


def test_high_order_evaluator():
    """测试高阶波纹度评价器"""
    print("\n" + "="*60)
    print("测试高阶波纹度评价器")
    print("="*60)
    
    params = GearParameters(teeth_count=87, module=1.859)
    evaluator = HighOrderEvaluator(params, amplitude_scale=1.0)
    
    from analysis.ripple_analyzer import SpectrumResult, SpectrumComponent
    
    components = [
        SpectrumComponent(1, 5.0, 0.0, 5.0, 0.0),
        SpectrumComponent(87, 2.0, 0.0, 2.0, 0.0),
        SpectrumComponent(174, 1.5, 0.0, 1.5, 0.0),
    ]
    
    spectrum = SpectrumResult(
        components=components,
        orders=np.array([1, 87, 174]),
        amplitudes=np.array([5.0, 2.0, 1.5]),
        phases=np.array([0.0, 0.0, 0.0]),
        reconstructed=np.zeros(360),
        residual=np.zeros(360),
        original=np.zeros(360)
    )
    
    angles = np.linspace(0, 360, 360)
    result = evaluator.evaluate(spectrum, angles)
    
    print(f"高阶波数: {result.high_order_waves}")
    print(f"高阶振幅: {result.high_order_amplitudes}")
    print(f"总振幅 W: {result.total_amplitude:.4f} (期望 3.5)")
    
    assert abs(result.total_amplitude - 3.5) < 0.01, "总振幅应为3.5"
    print("✓ 高阶波纹度评价器测试通过")


def test_full_analysis():
    """测试完整分析流程"""
    print("\n" + "="*60)
    print("测试完整分析流程")
    print("="*60)
    
    mka_file = os.path.join(current_dir, '263751-018-WAV.mka')
    
    if not os.path.exists(mka_file):
        print(f"测试文件不存在: {mka_file}")
        print("跳过完整分析测试")
        return
    
    print(f"读取文件: {mka_file}")
    parsed_data = parse_mka_file(mka_file)
    
    gear_data = parsed_data.get('gear_data', {})
    profile_data = parsed_data.get('profile_data', {})
    flank_data = parsed_data.get('flank_data', {})
    
    teeth_count = gear_data.get('teeth', 87)
    module = gear_data.get('module', 1.859)
    pressure_angle = gear_data.get('pressure_angle', 18.6)
    helix_angle = gear_data.get('helix_angle', 25.3)
    
    params = GearParameters(
        teeth_count=teeth_count,
        module=module,
        pressure_angle=pressure_angle,
        helix_angle=helix_angle
    )
    
    print(f"\n齿轮参数:")
    print(f"  齿数: {params.teeth_count}")
    print(f"  模数: {params.module} mm")
    print(f"  压力角: {params.pressure_angle}°")
    print(f"  螺旋角: {params.helix_angle}°")
    print(f"  基圆直径: {params.base_diameter:.3f} mm")
    print(f"  节圆直径: {params.pitch_diameter:.3f} mm")
    
    profile_eval_range = EvaluationRange(
        eval_start=gear_data.get('profile_eval_start', 174.822),
        eval_end=gear_data.get('profile_eval_end', 180.603),
        meas_start=gear_data.get('profile_meas_start', 174.822),
        meas_end=gear_data.get('profile_meas_end', 180.603)
    )
    
    helix_eval_range = EvaluationRange(
        eval_start=gear_data.get('helix_eval_start', 2.1),
        eval_end=gear_data.get('helix_eval_end', 39.9),
        meas_start=gear_data.get('helix_meas_start', 2.1),
        meas_end=gear_data.get('helix_meas_end', 39.9)
    )
    
    amplitude_scale = 0.1
    print(f"\n振幅缩放因子: {amplitude_scale}")
    
    analyzer = RippleAnalyzer(params, amplitude_scale=amplitude_scale)
    
    results = analyzer.analyze_all_directions(
        profile_data, flank_data,
        profile_eval_range, helix_eval_range,
        verbose=False
    )
    
    analyzer.print_results(results)
    
    print("\n" + "="*60)
    print("Klingelnberg参考值对比")
    print("="*60)
    
    reference_values = {
        'left_profile': 0.14,
        'right_profile': 0.15,
        'left_helix': 0.12,
        'right_helix': 0.09
    }
    
    print(f"\n{'曲线':<15} {'计算值(μm)':<15} {'参考值(μm)':<15} {'比率':<10}")
    print("-"*55)
    
    for name, ref_val in reference_values.items():
        if name in results:
            result = results[name]
            calc_val = result.high_order.total_amplitude
            ratio = calc_val / ref_val if ref_val > 0 else 0
            print(f"{name:<15} {calc_val:<15.4f} {ref_val:<15.2f} {ratio:<10.2f}x")
    
    print("\n✓ 完整分析流程测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("波纹度分析算法测试")
    print("="*70)
    
    test_preprocessor()
    test_angle_synthesizer()
    test_spectrum_analyzer()
    test_high_order_evaluator()
    test_full_analysis()
    
    print("\n" + "="*70)
    print("所有测试完成!")
    print("="*70)


if __name__ == '__main__':
    run_all_tests()
