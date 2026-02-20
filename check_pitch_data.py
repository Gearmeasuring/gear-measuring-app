"""检查节距数据提取情况"""

from contact_pattern_chart_mka import extract_data_from_mka
import numpy as np

# 读取MKA文件
mka_file = '263751-018-WAV.mka'
gear_data, profile_data, pitch_data = extract_data_from_mka(mka_file)

print('=== 节距数据示例 ===')
print('左齿面前5个齿的节距数据:')
for i in range(1, 6):
    if i in pitch_data['left']:
        p = pitch_data['left'][i]
        print(f'  齿 {i}: fp={p["fp"]:.3f}μm, Fp={p["Fp"]:.3f}μm, Fr={p["Fr"]:.3f}μm')

print()
print('右齿面前5个齿的节距数据:')
for i in range(1, 6):
    if i in pitch_data['right']:
        p = pitch_data['right'][i]
        print(f'  齿 {i}: fp={p["fp"]:.3f}μm, Fp={p["Fp"]:.3f}μm, Fr={p["Fr"]:.3f}μm')

# 计算节距误差对角度的影响
z = gear_data['teeth']
module = gear_data['module']
pressure_angle = gear_data.get('pressure_angle', 20.0)
pitch_diameter = module * z
base_diameter = pitch_diameter * np.cos(np.radians(pressure_angle))

print()
print(f'齿轮参数: z={z}, m={module}')
print(f'理论齿距角: {360.0/z:.4f}°')
print(f'基圆直径: {base_diameter:.3f}mm')
print()
print('节距误差角度转换示例:')
for fp in [-5, 0, 5]:
    angle_error = (fp / 1000) / (np.pi * base_diameter) * 360
    print(f'  fp={fp:+.1f}μm → 角度误差={angle_error:+.6f}°')
