import os
import sys
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages

sys.path.append(os.path.abspath('gear_analysis_refactored'))

from gear_analysis_refactored.utils import parse_mka_file
from gear_analysis_refactored.models.gear_data import create_gear_data_from_dict
from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport

# 生成报告
mka_file = r'263751-018-WAV.mka'
output_file = r'263751-018-WAV_ripple_FINAL.pdf'

data = parse_mka_file(mka_file)
measurement_data = create_gear_data_from_dict(data)

report = KlingelnbergRippleSpectrumReport()

with PdfPages(output_file) as pdf:
    report.create_page(pdf, measurement_data)

print(f"报告已生成: {output_file}")

# 打印详细数值对比
print("\n=== 详细数值对比 ===")
print("\n参考图2目标：")
print("  Profile left:  261(3ZE)=0.14, 87(1ZE)=0.14, 174(2ZE)=0.05")
print("  Profile right: 87(1ZE)=0.15, 348(4ZE)=0.07, 261(3ZE)=0.06")

print("\n当前生成值（Poly2 + 平均曲线补偿迭代）：")

report_check = KlingelnbergRippleSpectrumReport()
report_check._current_basic_info = measurement_data.basic_info
ze = measurement_data.basic_info.teeth

for name, data_dict, markers, dtype, side in [
    ('  Profile left ', measurement_data.profile_data.left, measurement_data.basic_info.profile_markers_left, 'profile', 'left'),
    ('  Profile right', measurement_data.profile_data.right, measurement_data.basic_info.profile_markers_right, 'profile', 'right'),
    ('  Helix left   ', measurement_data.flank_data.left, measurement_data.basic_info.lead_markers_left, 'helix', 'left'),
    ('  Helix right  ', measurement_data.flank_data.right, measurement_data.basic_info.lead_markers_right, 'helix', 'right')
]:
    orders, amps = report_check._calculate_spectrum(data_dict, ze, markers, side=side, data_type=dtype, info=measurement_data.basic_info)
    print(name, end=': ')
    for k in [1,2,3,4,5]:
        target = k * ze
        idx = np.where(orders == target)[0]
        if len(idx):
            print(f'{target}({k}ZE)={float(amps[idx[0]]):.3f}', end=' ')
    print()
