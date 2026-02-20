import os, sys, numpy as np
sys.path.append(os.path.abspath('gear_analysis_refactored'))

from gear_analysis_refactored.utils import parse_mka_file
from gear_analysis_refactored.models.gear_data import create_gear_data_from_dict
from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport

data = parse_mka_file(r'263751-018-WAV.mka')
m = create_gear_data_from_dict(data)
report = KlingelnbergRippleSpectrumReport()
report._current_basic_info = m.basic_info
ze = m.basic_info.teeth

print('=== Diagnostic: Check actual calculated values ===\n')
print('Reference Fig 2 targets:')
print('  Profile_L: 1ZE=0.14, 2ZE=0.05, 3ZE=0.14')
print('  Profile_R: 1ZE=0.15, 2ZE=0.05, 3ZE=0.06')
print('  Helix_L:   1ZE=0.12, 2ZE=0.04, 3ZE=0.02')
print('  Helix_R:   1ZE=0.09, 2ZE=0.10, 3ZE=0.05')
print('\nCurrent generated values:')

for name, data_dict, markers, dtype, side in [
    ('Profile_L', m.profile_data.left, m.basic_info.profile_markers_left, 'profile', 'left'),
    ('Profile_R', m.profile_data.right, m.basic_info.profile_markers_right, 'profile', 'right'),
    ('Helix_L  ', m.flank_data.left, m.basic_info.lead_markers_left, 'helix', 'left'),
    ('Helix_R  ', m.flank_data.right, m.basic_info.lead_markers_right, 'helix', 'right')
]:
    orders, amps = report._calculate_spectrum(data_dict, ze, markers, side=side, data_type=dtype, info=m.basic_info)
    print(f'  {name}: ', end='')
    if len(orders) > 0:
        for k in [1, 2, 3]:
            idx = np.where(orders == k * ze)[0]
            if len(idx):
                val = float(amps[idx[0]])
                print(f'{k}ZE={val:.4f}', end=' ')
        print()
    else:
        print('NO DATA')
