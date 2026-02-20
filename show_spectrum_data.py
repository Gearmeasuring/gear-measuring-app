from ripple_waviness_analyzer import RippleWavinessAnalyzer
import numpy as np

file_path = r'e:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka'
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()
analyzer.analyze_all()

print('='*80)
print('Spectrum Data Report')
print('='*80)

print()
print('[Gear Parameters]')
print(f'  Teeth Count ZE = {analyzer.gear_params.teeth_count}')
print(f'  Module m = {analyzer.gear_params.module} mm')

for name, result in analyzer.results.items():
    print()
    print('='*80)
    print(f'[{name}] Spectrum Data')
    print('='*80)
    
    print()
    print('Curve Data:')
    print(f'  Data Points: {len(result.angles)}')
    print(f'  Angle Range: [0, 360] deg')
    print(f'  Deviation Range: [{result.values.min():.4f}, {result.values.max():.4f}] um')
    
    print()
    print('Spectrum Components (sorted by amplitude):')
    print('-'*70)
    header = "{:>4} {:>6} {:>12} {:>12} {:>12}".format("Rank", "Order", "Amp(um)", "Phase(deg)", "Type")
    print(header)
    print('-'*70)
    
    for i, comp in enumerate(result.spectrum_components):
        order_type = 'High-Order' if comp.order >= analyzer.gear_params.teeth_count else 'Low-Order'
        line = "{:>4} {:>6} {:>12.4f} {:>12.1f} {:>12}".format(
            i+1, comp.order, comp.amplitude, np.degrees(comp.phase), order_type
        )
        print(line)
    
    print()
    print('High-Order Waviness (order >= ZE):')
    print(f'  High-Order Waves: {result.high_order_waves}')
    print(f'  Total Amplitude W = {result.high_order_amplitude:.4f} um')
    print(f'  RMS = {result.high_order_rms:.4f} um')

print()
print('='*80)
print('Chart: waviness_analysis_result.png')
print('='*80)
