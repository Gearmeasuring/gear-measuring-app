import re
import numpy as np

class MKADataExtractor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.gear_params = {}
        self.measurement_data = []
        self._extract_data()
    
    def _extract_data(self):
        with open(self.file_path, 'r', encoding='latin-1') as f:
            lines = f.readlines()
        
        # 提取齿轮参数
        for line in lines:
            if 'Z�hnezahl z' in line:
                match = re.search(r':\s*(\d+)', line)
                if match:
                    self.gear_params['z'] = int(match.group(1))
            elif 'Normalmodul mn' in line:
                match = re.search(r':\s*(\d+\.\d+)', line)
                if match:
                    self.gear_params['mn'] = float(match.group(1))
            elif 'Schr�gungswinkel' in line:
                match = re.search(r':\s*(\d+\.\d+)', line)
                if match:
                    self.gear_params['beta'] = float(match.group(1))
            elif 'Zahnbreite' in line:
                match = re.search(r':\s*(\d+)', line)
                if match:
                    self.gear_params['b'] = int(match.group(1))
            elif 'Auswerteanfang' in line and 'b1' in line:
                match = re.search(r':\s*(\d+\.\d+)', line)
                if match:
                    self.gear_params['profile_start'] = float(match.group(1))
            elif 'Auswerteende' in line and 'b2' in line:
                match = re.search(r':\s*(\d+\.\d+)', line)
                if match:
                    self.gear_params['profile_end'] = float(match.group(1))
            elif 'Start der Auswertestrecke' in line and 'd1' in line:
                match = re.search(r':\s*(\d+\.\d+)', line)
                if match:
                    self.gear_params['flank_start'] = float(match.group(1))
            elif 'Ende der Auswertestrecke' in line and 'd2' in line:
                match = re.search(r':\s*(\d+\.\d+)', line)
                if match:
                    self.gear_params['flank_end'] = float(match.group(1))
        
        # 提取测量数据
        current_tooth = None
        current_data = None
        
        for line in lines:
            line = line.strip()
            
            # 检测新的测量数据段
            if line.startswith('Flankenlinie:') or line.startswith('Profil:'):
                if current_data:
                    self.measurement_data.append(current_data)
                
                # 解析齿号和类型
                match = re.search(r'Zahn-Nr\.:\s*(\d+[a-c]?)\s*(rechts|lefts)', line)
                if match:
                    tooth_number = match.group(1)
                    side = match.group(2)
                else:
                    tooth_number = 'unknown'
                    side = 'rechts'
                
                # 解析类型
                data_type = 'Flankenlinie' if line.startswith('Flankenlinie:') else 'Profil'
                
                # 解析直径或位置
                if data_type == 'Flankenlinie':
                    match = re.search(r'/\s*d=\s*(\d+\.\d+)', line)
                    if match:
                        position = float(match.group(1))
                    else:
                        position = 0
                else:
                    match = re.search(r'/\s*z=\s*(\d+\.\d+)', line)
                    if match:
                        position = float(match.group(1))
                    else:
                        position = 0
                
                current_data = {
                    'type': data_type,
                    'tooth': tooth_number,
                    'side': side,
                    'position': position,
                    'values': []
                }
            
            # 提取数据值
            elif current_data and line:
                # 跳过包含-2147483.648的行（未定义测量点）
                if '-2147483.648' in line:
                    continue
                
                # 提取数值
                values = re.findall(r'[-+]?\d*\.\d+', line)
                if values:
                    current_data['values'].extend([float(v) for v in values])
        
        # 添加最后一组数据
        if current_data:
            self.measurement_data.append(current_data)
    
    def get_gear_params(self):
        return self.gear_params
    
    def get_measurement_data(self):
        return self.measurement_data
    
    def get_data_by_type(self, data_type):
        return [data for data in self.measurement_data if data['type'] == data_type]
    
    def get_data_by_tooth(self, tooth_number):
        return [data for data in self.measurement_data if data['tooth'] == tooth_number]

# 测试代码
if __name__ == "__main__":
    file_path = "263751-018-WAV.mka"
    extractor = MKADataExtractor(file_path)
    
    print("齿轮参数:")
    print(extractor.get_gear_params())
    
    print("\n测量数据数量:")
    print(len(extractor.get_measurement_data()))
    
    print("\nFlankenlinie数据:")
    flank_data = extractor.get_data_by_type('Flankenlinie')
    for data in flank_data:
        print(f"齿号: {data['tooth']}, 位置: {data['position']}, 数据点数量: {len(data['values'])}")
    
    print("\nProfil数据:")
    profil_data = extractor.get_data_by_type('Profil')
    for data in profil_data:
        print(f"齿号: {data['tooth']}, 位置: {data['position']}, 数据点数量: {len(data['values'])}")