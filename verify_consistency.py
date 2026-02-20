import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import KlingelnbergRippleSpectrumReport, RippleSpectrumSettings
from gear_analysis_refactored.utils.file_parser import MKAFileParser

# 添加当前目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class ConsistencyVerifier:
    def __init__(self):
        self.parser = MKAFileParser()
        self.settings = RippleSpectrumSettings()
        self.report = KlingelnbergRippleSpectrumReport(self.settings)
    
    def analyze_file(self, mka_file_path):
        """分析MKA文件并返回关键参数和频谱数据"""
        try:
            # 读取文件
            content = self.parser.read_file(mka_file_path)
            
            # 提取齿轮基本数据
            gear_data = self.parser.extract_gear_basic_data(content)
            
            # 提取测量数据
            profile_data = self.parser.extract_measurement_data(content, "Profil")
            flank_data = self.parser.extract_measurement_data(content, "Flankenlinie")
            
            # 计算关键参数
            module = gear_data.get('module', 0.0)
            teeth = gear_data.get('teeth', 0)
            pressure_angle = gear_data.get('pressure_angle', 20.0)
            helix_angle = gear_data.get('helix_angle', 0.0)
            
            # 计算基圆直径
            if module and teeth and pressure_angle:
                alpha_n = np.radians(float(pressure_angle))
                beta = np.radians(float(helix_angle)) if helix_angle else 0.0
                alpha_t = np.arctan(np.tan(alpha_n) / np.cos(beta)) if beta != 0 else alpha_n
                d = float(teeth) * float(module) / np.cos(beta) if beta != 0 else float(teeth) * float(module)
                base_diameter = d * np.cos(alpha_t)
            else:
                base_diameter = 0.0
            
            # 计算基节
            base_pitch = np.pi * module * np.cos(np.radians(pressure_angle)) if module else 0.0
            
            # 计算评价范围参数
            eval_start = gear_data.get('profile_eval_start', 0.0)
            eval_end = gear_data.get('profile_eval_end', 0.0)
            
            # 计算lo和lu（使用之前修复的公式）
            if base_diameter and eval_start and eval_end:
                rb = base_diameter / 2.0
                s1 = np.sqrt(max(0.0, (eval_start/2.0)**2 - rb**2)) if eval_start >= base_diameter else abs(eval_start - base_diameter) / 2.0
                s2 = np.sqrt(max(0.0, (eval_end/2.0)**2 - rb**2)) if eval_end >= base_diameter else abs(eval_end - base_diameter) / 2.0
                lo = s2  # 齿顶方向
                lu = s1  # 齿根方向
                ep = abs(s2 - s1) / base_pitch if base_pitch > 0 else 0.0
            else:
                lo = 0.0
                lu = 0.0
                ep = 0.0
            
            # 计算频谱（以右侧齿形为例）
            profile_right_data = profile_data.get('right', {})
            if profile_right_data:
                eval_markers = (gear_data.get('profile_meas_start', 0.0), 
                               gear_data.get('profile_eval_start', 0.0),
                               gear_data.get('profile_eval_end', 0.0),
                               gear_data.get('profile_meas_end', 0.0))
                
                eval_length = self.report._get_eval_length(gear_data, 'profile', 'right', eval_markers)
                
                orders, amplitudes = self.report._calculate_spectrum(
                    profile_right_data,
                    teeth_count=teeth,
                    eval_markers=eval_markers,
                    eval_length=eval_length,
                    base_diameter=base_diameter,
                    info=gear_data
                )
            else:
                orders = []
                amplitudes = []
            
            return {
                'gear_data': gear_data,
                'ep': ep,
                'lo': lo,
                'lu': lu,
                'base_diameter': base_diameter,
                'base_pitch': base_pitch,
                'orders': np.array(orders),
                'amplitudes': np.array(amplitudes)
            }
            
        except Exception as e:
            print(f"分析文件时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def verify_consistency(self, mka_file_path, tolerance=1e-6):
        """验证使用相同MKA文件两次分析的一致性"""
        print(f"验证文件一致性: {mka_file_path}")
        print(f"容差: {tolerance}")
        
        # 第一次分析
        result1 = self.analyze_file(mka_file_path)
        if result1 is None:
            return False
        
        # 第二次分析
        result2 = self.analyze_file(mka_file_path)
        if result2 is None:
            return False
        
        # 比较关键参数
        print("\n=== 比较关键参数 ===")
        all_consistent = True
        
        params_to_compare = ['ep', 'lo', 'lu', 'base_diameter', 'base_pitch']
        for param in params_to_compare:
            val1 = result1[param]
            val2 = result2[param]
            diff = abs(val1 - val2)
            consistent = diff <= tolerance
            all_consistent &= consistent
            
            print(f"{param}: {val1:.6f} vs {val2:.6f} | 差值: {diff:.9f} | {'一致' if consistent else '不一致'}")
        
        # 比较频谱数据
        print("\n=== 比较频谱数据 ===")
        orders1, amps1 = result1['orders'], result1['amplitudes']
        orders2, amps2 = result2['orders'], result2['amplitudes']
        
        # 检查阶次是否相同
        orders_same = len(orders1) == len(orders2) and np.allclose(orders1, orders2, atol=tolerance)
        
        # 检查振幅是否相同
        amps_same = len(amps1) == len(amps2) and np.allclose(amps1, amps2, atol=tolerance)
        
        all_consistent &= orders_same and amps_same
        
        print(f"阶次数量: {len(orders1)} vs {len(orders2)} | {'一致' if orders_same else '不一致'}")
        print(f"振幅数量: {len(amps1)} vs {len(amps2)} | {'一致' if amps_same else '不一致'}")
        
        if not amps_same and len(amps1) == len(amps2):
            max_diff = np.max(np.abs(amps1 - amps2))
            mean_diff = np.mean(np.abs(amps1 - amps2))
            print(f"最大振幅差值: {max_diff:.9f} μm")
            print(f"平均振幅差值: {mean_diff:.9f} μm")
        
        # 显示频谱结果样本
        if len(orders1) > 0 and len(orders2) > 0:
            print("\n=== 频谱数据样本 ===")
            sample_size = min(5, len(orders1))
            for i in range(sample_size):
                print(f"阶次 {int(orders1[i])}: {amps1[i]:.6f} vs {amps2[i]:.6f} μm")
        
        print(f"\n=== 最终结果 ===")
        print(f"两次分析结果{'完全一致' if all_consistent else '不一致'}")
        
        return all_consistent

def main():
    # 检查是否提供了MKA文件路径
    if len(sys.argv) < 2:
        print("用法: python verify_consistency.py <mka_file_path>")
        print("示例: python verify_consistency.py data/test.mka")
        return
    
    mka_file_path = sys.argv[1]
    
    if not os.path.exists(mka_file_path):
        print(f"错误: 文件不存在: {mka_file_path}")
        return
    
    verifier = ConsistencyVerifier()
    
    try:
        consistent = verifier.verify_consistency(mka_file_path)
        if consistent:
            print("✓ 验证通过: 使用相同MKA文件生成的图表数值一致")
            sys.exit(0)
        else:
            print("✗ 验证失败: 使用相同MKA文件生成的图表数值不一致")
            sys.exit(1)
    except Exception as e:
        print(f"验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()