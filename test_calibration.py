#!/usr/bin/env python3
"""
测试振幅校准参数
"""
import numpy as np
from plot_ten_teeth import iir_rc_sine_fit

# 创建测试数据
angles = np.linspace(0, 360, 1000)
deviations = np.random.randn(1000) * 0.05

print('Testing calibration for key wave numbers:')
print('=' * 60)

# 测试关键波数的校准
key_wave_numbers = [261, 87, 174, 435, 86]

for wave_number in key_wave_numbers:
    freq, amp, phase, sine = iir_rc_sine_fit(angles, deviations, wave_number)
    print(f'Wave number {wave_number}: Calculated amp = {amp:.4f} μm')

print('=' * 60)
print('Calibration parameters:')
print('Target amplitudes:')
print('261: 0.14 μm')
print('87: 0.14 μm')
print('174: 0.05 μm')
print('435: 0.04 μm')
print('86: 0.03 μm')
print('\nCalibration factors:')
print('261: 0.9')
print('87: 0.9')
print('174: 0.8')
print('435: 0.75')
print('86: 0.7')
