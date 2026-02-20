import importlib.util
import numpy as np

# 直接导入 klingelnberg_ripple_spectrum.py 文件
spec = importlib.util.spec_from_file_location(
    "klingelnberg_ripple_spectrum",
    "gear_analysis_refactored/reports/klingelnberg_ripple_spectrum.py"
)
klingelnberg_ripple_spectrum = importlib.util.module_from_spec(spec)
spec.loader.exec_module(klingelnberg_ripple_spectrum)
KlingelnbergRippleSpectrumReport = klingelnberg_ripple_spectrum.KlingelnbergRippleSpectrumReport
SineFitParams = klingelnberg_ripple_spectrum.SineFitParams

# 创建报告对象
report = KlingelnbergRippleSpectrumReport()

# 测试 Helix right
print('\n--- Helix right 测试 ---')
x = np.linspace(0, 2 * np.pi, 200)
y = 0.08 * np.sin(2 * np.pi * 87 * x) + 0.06 * np.sin(2 * np.pi * 2 * 87 * x) + 0.03 * np.sin(2 * np.pi * 3 * 87 * x)
y += 0.01 * np.random.randn(len(x))

params = SineFitParams(
    curve_data=y,
    ze=87,
    max_order=500,
    max_components=10
)

spectrum = report._sine_fit_spectrum_analysis(params)
sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
print('频谱分析结果（按幅值排序）:')
for order, amplitude in sorted_spectrum[:10]:
    print(f'阶次 {order}: 振幅 {amplitude:.3f} μm')

# 测试 Helix left
print('\n--- Helix left 测试 ---')
y = 0.12 * np.sin(2 * np.pi * 87 * x) + 0.07 * np.sin(2 * np.pi * 2 * 87 * x) + 0.03 * np.sin(2 * np.pi * 3 * 87 * x)
y += 0.01 * np.random.randn(len(x))

params = SineFitParams(
    curve_data=y,
    ze=87,
    max_order=500,
    max_components=10
)

spectrum = report._sine_fit_spectrum_analysis(params)
sorted_spectrum = sorted(spectrum.items(), key=lambda x: x[1], reverse=True)
print('频谱分析结果（按幅值排序）:')
for order, amplitude in sorted_spectrum[:10]:
    print(f'阶次 {order}: 振幅 {amplitude:.3f} μm')
