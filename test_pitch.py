from ripple_waviness_analyzer import RippleWavinessAnalyzer
import os

file_path = r'e:\python\gear measuring software - 20251217\gear measuring software - 20251217backup\263751-018-WAV.mka'
print(f'测试文件: {file_path}')
print(f'文件存在: {os.path.exists(file_path)}')

analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

print(f'\n齿轮参数:')
print(f'  齿数: {analyzer.gear_params.teeth_count}')
print(f'  模数: {analyzer.gear_params.module}')

print(f'\n周节数据:')
print(f'  左齿面: {len(analyzer.reader.pitch_data.get("left", {}))} 个齿')
print(f'  右齿面: {len(analyzer.reader.pitch_data.get("right", {}))} 个齿')

# 分析周节
pitch_left = analyzer.analyze_pitch('left')
pitch_right = analyzer.analyze_pitch('right')

if pitch_left:
    print(f'\n左齿面分析结果:')
    print(f'  fp_max: {pitch_left.fp_max:.2f} μm')
    print(f'  fp_min: {pitch_left.fp_min:.2f} μm')
    print(f'  Fp_max: {pitch_left.Fp_max:.2f} μm')
    print(f'  Fp_min: {pitch_left.Fp_min:.2f} μm')
    print(f'  Fr: {pitch_left.Fr:.2f} μm')

if pitch_right:
    print(f'\n右齿面分析结果:')
    print(f'  fp_max: {pitch_right.fp_max:.2f} μm')
    print(f'  fp_min: {pitch_right.fp_min:.2f} μm')
    print(f'  Fp_max: {pitch_right.Fp_max:.2f} μm')
    print(f'  Fp_min: {pitch_right.Fp_min:.2f} μm')
    print(f'  Fr: {pitch_right.Fr:.2f} μm')

print('\n测试成功!')
