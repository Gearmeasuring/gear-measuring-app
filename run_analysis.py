from ripple_waviness_analyzer import RippleWavinessAnalyzer
import numpy as np

file_path = r'e:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka'
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

print('='*80)
print('Gear Waviness Analysis Report')
print('='*80)

print()
print('[Gear Parameters]')
print(f'  Teeth Count ZE = {analyzer.gear_params.teeth_count}')
print(f'  Module m = {analyzer.gear_params.module} mm')
print(f'  Pressure Angle alpha = {analyzer.gear_params.pressure_angle} deg')
print(f'  Helix Angle beta = {analyzer.gear_params.helix_angle} deg')
print(f'  Pitch Diameter D0 = {analyzer.gear_params.pitch_diameter:.3f} mm')
print(f'  Base Diameter db = {analyzer.gear_params.base_diameter:.3f} mm')
print(f'  Pitch Angle = {analyzer.gear_params.pitch_angle:.4f} deg')

analyzer.analyze_all()

for name, result in analyzer.results.items():
    print()
    print('='*80)
    print(f'[{name}]')
    print('='*80)
    
    print(f'  Data Points: {len(result.angles)}')
    print(f'  Angle Range: [{result.angles.min():.2f}, {result.angles.max():.2f}] deg')
    print(f'  Deviation Range: [{result.values.min():.4f}, {result.values.max():.4f}] um')
    
    print()
    print('  Spectrum Components (Top 10 Orders):')
    print('  '+'-'*60)
    print(f'  {"Rank":>4} {"Order":>6} {"Amplitude(um)":>14} {"Phase(deg)":>12} {"Type":>12}')
    print('  '+'-'*60)
    
    for i, comp in enumerate(result.spectrum_components):
        high_order = 'High-Order' if comp.order >= analyzer.gear_params.teeth_count else 'Low-Order'
        print(f'  {i+1:>4} {comp.order:>6} {comp.amplitude:>14.4f} {np.degrees(comp.phase):>12.1f} {high_order:>12}')
    
    print()
    print(f'  High-Order Waviness Evaluation (order >= {analyzer.gear_params.teeth_count}):')
    print(f'    High-Order Wave Numbers: {result.high_order_waves}')
    print(f'    Total Amplitude W = {result.high_order_amplitude:.4f} um')
    print(f'    RMS = {result.high_order_rms:.4f} um')

print()
print('='*80)
print('Chart saved to: waviness_analysis_result.png')
print('='*80)
