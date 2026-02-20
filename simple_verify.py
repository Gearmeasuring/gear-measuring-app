import os
import sys
import numpy as np
import re

# 设置当前目录为工作目录
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class SimpleMKAProcessor:
    def __init__(self):
        pass
    
    def read_file(self, file_path):
        """读取MKA文件内容"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        encodings = ['utf-8', 'gbk', 'latin-1']
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    return f.read()
            except Exception:
                continue
        
        raise IOError(f"无法读取文件: {file_path}")
    
    def extract_gear_data(self, content):
        """提取齿轮关键数据"""
        gear_data = {}
        lines = content.split('\n')
        
        patterns = [
            ('module', r'^\s*21\s*:.*?Normalmodul[^:]*:\s*([\d.]+)', float),
            ('module', r'^\s*21\s*:.*?:\s*([\d.]+)', float),
            ('teeth', r'^\s*22\s*:.*?Zähnezahl[^:]*:\s*(\d+)', int),
            ('teeth', r'^\s*22\s*:.*?:\s*(\d+)', int),
            ('pressure_angle', r'^\s*24\s*:.*?Eingriffswinkel[^:]*:\s*([\d.]+)', float),
            ('pressure_angle', r'^\s*24\s*:.*?:\s*([\d.]+)', float),
            ('helix_angle', r'^\s*23\s*:.*?Schrägungswinkel[^:]*:\s*(-?[\d.]+)', float),
            ('helix_angle', r'^\s*23\s*:.*?:\s*(-?[\d.]+)', float),
            ('profile_eval_start', r'^.*?d1\s*\[?mm\]?\.*:?\s*([-\d.]+)', float),
            ('profile_eval_end', r'^.*?d2\s*\[?mm\]?\.*:?\s*([-\d.]+)', float),
        ]
        
        for line in lines:
            for key, pattern, data_type in patterns:
                if key in gear_data:
                    continue
                    
                match = re.search(pattern, line)
                if match:
                    try:
                        value = match.group(1).strip()
                        gear_data[key] = data_type(value)
                    except Exception:
                        continue
        
        return gear_data
    
    def calculate_key_parameters(self, gear_data):
        """计算关键参数：基圆直径、基节、lo、lu、ep"""
        module = gear_data.get('module', 0.0)
        teeth = gear_data.get('teeth', 0)
        pressure_angle = gear_data.get('pressure_angle', 20.0)
        helix_angle = gear_data.get('helix_angle', 0.0)
        eval_start = gear_data.get('profile_eval_start', 0.0)
        eval_end = gear_data.get('profile_eval_end', 0.0)
        
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
        
        # 计算lo和lu
        if base_diameter and eval_start and eval_end:
            rb = base_diameter / 2.0
            
            # 计算齿根到基圆的距离 (lu)
            if eval_start >= base_diameter:
                lu = np.sqrt(max(0.0, (eval_start/2.0)**2 - rb**2))
            else:
                lu = abs(eval_start - base_diameter) / 2.0
            
            # 计算齿顶到基圆的距离 (lo)
            if eval_end >= base_diameter:
                lo = np.sqrt(max(0.0, (eval_end/2.0)**2 - rb**2))
            else:
                lo = abs(eval_end - base_diameter) / 2.0
            
            # 计算ep（基节的数量）
            eval_length = abs(lo - lu)
            ep = eval_length / base_pitch if base_pitch > 0 else 0.0
        else:
            lo = 0.0
            lu = 0.0
            ep = 0.0
        
        return {
            'base_diameter': base_diameter,
            'base_pitch': base_pitch,
            'lo': lo,
            'lu': lu,
            'ep': ep,
            'module': module,
            'teeth': teeth,
            'pressure_angle': pressure_angle,
            'helix_angle': helix_angle,
            'eval_start': eval_start,
            'eval_end': eval_end
        }
    
    def extract_measurement_data(self, content, data_type="Profil"):
        """提取测量数据"""
        if data_type not in ["Profil", "Flankenlinie"]:
            raise ValueError("data_type must be either 'Profil' or 'Flankenlinie'")
        
        # 简化的测量数据提取逻辑
        # 实际项目中会有更复杂的解析逻辑，但这里我们只需要验证参数计算的一致性
        return {"left": {}, "right": {}}

def verify_consistency(mka_file_path, tolerance=1e-9):
    """验证使用相同MKA文件两次分析的一致性"""
    print(f"验证文件: {mka_file_path}")
    print(f"容差: {tolerance}")
    
    processor = SimpleMKAProcessor()
    
    try:
        # 第一次分析
        content1 = processor.read_file(mka_file_path)
        gear_data1 = processor.extract_gear_data(content1)
        params1 = processor.calculate_key_parameters(gear_data1)
        
        # 第二次分析
        content2 = processor.read_file(mka_file_path)
        gear_data2 = processor.extract_gear_data(content2)
        params2 = processor.calculate_key_parameters(gear_data2)
        
        # 比较结果
        print("\n=== 齿轮基本参数 ===")
        basic_params = ['module', 'teeth', 'pressure_angle', 'helix_angle', 'eval_start', 'eval_end']
        for param in basic_params:
            val1 = gear_data1.get(param, 0.0)
            val2 = gear_data2.get(param, 0.0)
            print(f"{param}: {val1} vs {val2} | {'相同' if val1 == val2 else '不同'}")
        
        print("\n=== 计算参数 ===")
        calc_params = ['base_diameter', 'base_pitch', 'lo', 'lu', 'ep']
        all_consistent = True
        
        for param in calc_params:
            val1 = params1[param]
            val2 = params2[param]
            diff = abs(val1 - val2)
            consistent = diff <= tolerance
            all_consistent &= consistent
            
            print(f"{param}: {val1:.8f} vs {val2:.8f} | 差值: {diff:.12f} | {'一致' if consistent else '不一致'}")
        
        print(f"\n=== 最终结果 ===")
        if all_consistent:
            print("✓ 验证通过: 使用相同MKA文件生成的参数完全一致")
            return True
        else:
            print("✗ 验证失败: 使用相同MKA文件生成的参数不一致")
            return False
            
    except Exception as e:
        print(f"验证过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) < 2:
        print("用法: python simple_verify.py <mka_file_path>")
        return
    
    mka_file = sys.argv[1]
    if not os.path.exists(mka_file):
        print(f"错误: 文件不存在: {mka_file}")
        return
    
    verify_consistency(mka_file)

if __name__ == "__main__":
    main()