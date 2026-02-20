import re
import numpy as np
import math

class MKAParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.basic_info = {}
        self.profile_data = {'left': {}, 'right': {}}
        self.flank_data = {'left': {}, 'right': {}}
        self.pitch_data = {'left': {}, 'right': {}}
        self._parse_file()
    
    def _parse_file(self):
        with open(self.file_path, 'r', encoding='latin-1') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Parse basic info
            if line.startswith(':'):
                match = re.match(r':(.+?):\s*(.*)', line)
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    self.basic_info[key] = value
            
            # Parse profile data
            elif line.startswith('Profil:'):
                # Extract tooth ID and side
                tooth_id_match = re.search(r'Zahn-Nr.:\s*(\d+[ab]?)', line)
                if tooth_id_match:
                    tooth_id = tooth_id_match.group(1)
                    # Determine side
                    side = 'right' if 'rechts' in line else 'left'
                    
                    # Read data lines
                    data_lines = []
                    i += 1
                    while i < len(lines):
                        data_line = lines[i].strip()
                        if not data_line or data_line.startswith('Flankenlinie:') or data_line.startswith('Profil:'):
                            break
                        # Split data values
                        values = re.split(r'\s+', data_line)
                        # Filter out undefined values (-2147483.648)
                        valid_values = [float(v) for v in values if v != '-2147483.648']
                        data_lines.extend(valid_values)
                        i += 1
                    
                    if data_lines:
                        if tooth_id not in self.profile_data[side]:
                            self.profile_data[side][tooth_id] = []
                        self.profile_data[side][tooth_id].extend(data_lines)
                    continue
            
            # Parse flank data
            elif line.startswith('Flankenlinie:'):
                # Extract tooth ID and side
                tooth_id_match = re.search(r'Zahn-Nr.:\s*(\d+[ab]?)', line)
                if tooth_id_match:
                    tooth_id = tooth_id_match.group(1)
                    # Determine side
                    side = 'right' if 'rechts' in line else 'left'
                    
                    # Read data lines
                    data_lines = []
                    i += 1
                    while i < len(lines):
                        data_line = lines[i].strip()
                        if not data_line or data_line.startswith('Flankenlinie:') or data_line.startswith('Profil:'):
                            break
                        # Split data values
                        values = re.split(r'\s+', data_line)
                        # Filter out undefined values (-2147483.648)
                        valid_values = [float(v) for v in values if v != '-2147483.648']
                        data_lines.extend(valid_values)
                        i += 1
                    
                    if data_lines:
                        if tooth_id not in self.flank_data[side]:
                            self.flank_data[side][tooth_id] = []
                        self.flank_data[side][tooth_id].extend(data_lines)
                    continue
            
            # Parse pitch data
            elif line == 'Teilung:':
                i += 1
                # Skip header line
                if i < len(lines) and 'Z-Nr. Seite' in lines[i]:
                    i += 1
                # Read pitch data lines
                while i < len(lines):
                    data_line = lines[i].strip()
                    if not data_line or data_line.startswith('Profil:') or data_line.startswith('Flankenlinie:'):
                        break
                    # Split data values
                    values = re.split(r'\s+', data_line)
                    if len(values) >= 5:
                        try:
                            tooth_id = values[0]
                            side = 'right' if values[1] == 'R' else 'left'
                            phi = float(values[2])
                            x = float(values[3])
                            
                            if tooth_id not in self.pitch_data[side]:
                                self.pitch_data[side][tooth_id] = []
                            # Store pitch deviation (x value)
                            self.pitch_data[side][tooth_id].append(x)
                        except:
                            pass
                    i += 1
                continue
            
            i += 1
    
    def get_teeth_count(self):
        # Extract teeth count from basic info
        # Try to find teeth count from the header section
        try:
            with open(self.file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            # Look for the line with Zähnezahl, Zahnzahl, or similar
            # Use a more flexible regex to match different formats
            match = re.search(r'Z[aä]hnezahl z.*:\s*(\d+)', content)
            if match:
                return int(match.group(1).strip())
        except:
            pass
        return 0
    
    def get_module(self):
        # Extract module from basic info
        try:
            with open(self.file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            # Look for the line with Normalmodul
            match = re.search(r'Normalmodul mn................  \[mm\]....:\s*(\d+\.\d+)', content)
            if match:
                return float(match.group(1).strip())
        except:
            pass
        return 0.0
    
    def get_helix_angle(self):
        # Extract helix angle from basic info
        try:
            with open(self.file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            # Look for the line with Schr�gungswinkel
            match = re.search(r'Schr[�a]gungswinkel �  ..........  \[Grad\]..:\s*(\d+\.\d+)', content)
            if match:
                return float(match.group(1).strip())
        except:
            pass
        return 0.0
    
    def get_pressure_angle(self):
        # Extract pressure angle from basic info
        try:
            with open(self.file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            # Look for the line with Eingriffswinkel
            match = re.search(r'Eingriffswinkel alpha ........  \[Grad\]..:\s*(\d+\.\d+)', content)
            if match:
                return float(match.group(1).strip())
        except:
            pass
        return 0.0
    
    def get_face_width(self):
        # Extract face width from basic info
        try:
            with open(self.file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            # Look for the line with Zahnbreite
            match = re.search(r'Zahnbreite ...................  \[mm\]....:\s*(\d+)', content)
            if match:
                return float(match.group(1).strip())
        except:
            pass
        return 0.0
    
    def calculate_rotation_angles(self):
        """
        Calculate rotation angles for each measurement point
        Returns a dictionary with the same structure as profile_data and flank_data
        but with angles instead of raw values
        
        根据用户提供的公式计算：
        φ = -ξ₁ - Δφ = -ξ₂ - Δφ + τ
        其中：Δφ = 2 * Δz * tan(β₀) / D₀
        - Δz：轴向距离
        - β₀：螺旋角
        - D₀：节圆直径
        """
        teeth_count = self.get_teeth_count()
        if teeth_count == 0:
            teeth_count = 26  # Fallback to 26 based on the data
        
        # 获取螺旋角（β₀）
        helix_angle_deg = self.get_helix_angle()
        helix_angle_rad = math.radians(helix_angle_deg)
        
        # 获取模数
        module = self.get_module() or 1.859
        
        # 计算节圆直径（D₀）
        pitch_circle_diameter = module * teeth_count
        
        # 计算每个齿的节距角（τ）
        pitch_angle_per_tooth = 360.0 / teeth_count
        
        # 获取齿向的评价范围，用于计算参考点
        eval_ranges = self.get_evaluation_ranges()
        flank_eval_start = eval_ranges['flank']['start']
        flank_eval_end = eval_ranges['flank']['end']
        # 计算评价范围的中点作为参考点
        flank_eval_mid = (flank_eval_start + flank_eval_end) / 2
        
        # 计算节距偏差角度
        def get_pitch_angle_deviation(side, tooth_num):
            """Get pitch deviation angle for a specific tooth"""
            tooth_id = str(tooth_num)
            if tooth_id in self.pitch_data[side]:
                pitch_deviations = self.pitch_data[side][tooth_id]
                if pitch_deviations:
                    # Average pitch deviation
                    avg_deviation = sum(pitch_deviations) / len(pitch_deviations)
                    # Convert pitch deviation to angle deviation
                    pitch_circle_circumference = math.pi * pitch_circle_diameter
                    # Angle per mm at pitch circle
                    angle_per_mm = 360.0 / pitch_circle_circumference
                    # Calculate angle deviation
                    angle_deviation = avg_deviation * angle_per_mm
                    return angle_deviation
            return 0.0
        
        # Calculate angles for profile data
        profile_angles = {'left': {}, 'right': {}}
        for side in ['left', 'right']:
            for tooth_id, data in self.profile_data[side].items():
                # Extract tooth number from tooth_id (e.g., '1a' -> 1)
                tooth_num_match = re.search(r'\d+', tooth_id)
                if tooth_num_match:
                    tooth_num = int(tooth_num_match.group(0))
                    # Calculate base pitch angle (τ)
                    base_pitch_angle = (tooth_num - 1) * pitch_angle_per_tooth
                    # Add pitch deviation angle
                    pitch_deviation = get_pitch_angle_deviation(side, tooth_num)
                    total_pitch_angle = base_pitch_angle + pitch_deviation
                    
                    # Calculate angles for each point
                    num_points = len(data)
                    angles = []
                    
                    for i in range(num_points):
                        # 计算滚动角（ξ）- 假设每个点均匀分布在齿面上
                        # 对于齿形数据，滚动角从0到pitch_angle_per_tooth
                        rolling_angle = (i / max(1, num_points - 1)) * pitch_angle_per_tooth
                        
                        # 计算轴向距离（Δz）- 假设齿形数据的轴向位置在中间
                        # 对于齿形数据，轴向距离较小，暂时设为0
                        delta_z = 0.0
                        
                        # 计算轴向位置产生的旋转（Δφ）
                        if pitch_circle_diameter > 0:
                            delta_phi = (2 * delta_z * math.tan(helix_angle_rad)) / pitch_circle_diameter
                            # 转换为角度
                            delta_phi_deg = math.degrees(delta_phi)
                        else:
                            delta_phi_deg = 0.0
                        
                        # 根据公式计算旋转角度：φ = -ξ - Δφ + τ
                        rotation_angle = -rolling_angle - delta_phi_deg + total_pitch_angle
                        
                        # 确保角度在0-360范围内
                        rotation_angle = rotation_angle % 360
                        if rotation_angle < 0:
                            rotation_angle += 360
                        
                        angles.append(rotation_angle)
                    
                    profile_angles[side][tooth_id] = angles
        
        # Calculate angles for flank data
        flank_angles = {'left': {}, 'right': {}}
        for side in ['left', 'right']:
            for tooth_id, data in self.flank_data[side].items():
                # Extract tooth number from tooth_id (e.g., '1a' -> 1)
                tooth_num_match = re.search(r'\d+', tooth_id)
                if tooth_num_match:
                    tooth_num = int(tooth_num_match.group(0))
                    # Calculate base pitch angle (τ)
                    base_pitch_angle = (tooth_num - 1) * pitch_angle_per_tooth
                    # Add pitch deviation angle
                    pitch_deviation = get_pitch_angle_deviation(side, tooth_num)
                    total_pitch_angle = base_pitch_angle + pitch_deviation
                    
                    # 获取齿宽
                    face_width = self.get_face_width()
                    
                    # Calculate angles for each point
                    num_points = len(data)
                    angles = []
                    
                    for i in range(num_points):
                        # 计算滚动角（ξ）- 假设每个点均匀分布在齿面上
                        # 对于齿向数据，滚动角从0到pitch_angle_per_tooth
                        rolling_angle = (i / max(1, num_points - 1)) * pitch_angle_per_tooth
                        
                        # 计算轴向距离（Δz）- 对于齿向数据，轴向距离从0到齿宽
                        # 然后减去评价范围的中点，以中点作为参考点
                        if face_width > 0:
                            # 计算绝对轴向位置
                            absolute_z = (i / max(1, num_points - 1)) * face_width
                            # 以评价范围的中点作为参考点
                            delta_z = absolute_z - flank_eval_mid
                        else:
                            delta_z = 0.0
                        
                        # 计算轴向位置产生的旋转（Δφ）
                        if pitch_circle_diameter > 0:
                            delta_phi = (2 * delta_z * math.tan(helix_angle_rad)) / pitch_circle_diameter
                            # 转换为角度
                            delta_phi_deg = math.degrees(delta_phi)
                        else:
                            delta_phi_deg = 0.0
                        
                        # 根据公式计算旋转角度：φ = -ξ - Δφ + τ
                        rotation_angle = -rolling_angle - delta_phi_deg + total_pitch_angle
                        
                        # 确保角度在0-360范围内
                        rotation_angle = rotation_angle % 360
                        if rotation_angle < 0:
                            rotation_angle += 360
                        
                        angles.append(rotation_angle)
                    
                    flank_angles[side][tooth_id] = angles
        
        return profile_angles, flank_angles
    
    def get_evaluation_ranges(self):
        """
        Get evaluation ranges from MKA file
        """
        try:
            with open(self.file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            
            # Get profile evaluation range
            profile_start_match = re.search(r'Start der Auswertestrecke.........................d1  \[mm\]..:\s*(\d+\.\d+)', content)
            profile_end_match = re.search(r'Ende der Auswertestrecke..........................d2  \[mm\]..:\s*(\d+\.\d+)', content)
            # Get profile measurement range
            profile_start_mess_match = re.search(r'Start Messbereich.................................da  \[mm\]..:\s*(\d+\.\d+)', content)
            profile_end_mess_match = re.search(r'Ende der Messstrecke..............................de  \[mm\]..:\s*(\d+\.\d+)', content)
            
            profile_start = float(profile_start_match.group(1)) if profile_start_match else 0.0
            profile_end = float(profile_end_match.group(1)) if profile_end_match else 0.0
            profile_start_mess = float(profile_start_mess_match.group(1)) if profile_start_mess_match else 0.0
            profile_end_mess = float(profile_end_mess_match.group(1)) if profile_end_mess_match else 0.0
            
            # Get flank evaluation range
            flank_start_match = re.search(r'Auswerteanfang....................................b1  \[mm\]..:\s*(\d+\.\d+)', content)
            flank_end_match = re.search(r'Auswerteende......................................b2  \[mm\]..:\s*(\d+\.\d+)', content)
            # Get flank measurement range
            flank_start_mess_match = re.search(r'Messanfang \(unten\)................................ba  \[mm\]..:\s*(\d+\.\d+)', content)
            flank_end_mess_match = re.search(r'Messende \(oben\)...................................be  \[mm\]..:\s*(\d+\.\d+)', content)
            
            flank_start = float(flank_start_match.group(1)) if flank_start_match else 0.0
            flank_end = float(flank_end_match.group(1)) if flank_end_match else 0.0
            flank_start_mess = float(flank_start_mess_match.group(1)) if flank_start_mess_match else 0.0
            flank_end_mess = float(flank_end_mess_match.group(1)) if flank_end_mess_match else 0.0
            
            return {
                'profile': {
                    'start': profile_start,
                    'end': profile_end,
                    'start_mess': profile_start_mess,
                    'end_mess': profile_end_mess
                },
                'flank': {
                    'start': flank_start,
                    'end': flank_end,
                    'start_mess': flank_start_mess,
                    'end_mess': flank_end_mess
                }
            }
        except:
            return {
                'profile': {'start': 0.0, 'end': 0.0, 'start_mess': 0.0, 'end_mess': 0.0},
                'flank': {'start': 0.0, 'end': 0.0, 'start_mess': 0.0, 'end_mess': 0.0}
            }
    
    def get_combined_data(self, use_evaluation_range=True):
        """
        Combine all teeth data into a single dataset for each side and type
        Returns combined data sorted by angle
        
        Args:
            use_evaluation_range: Whether to only include data within evaluation range
        """
        profile_angles, flank_angles = self.calculate_rotation_angles()
        
        combined_data = {
            'profile_left': [],
            'profile_right': [],
            'flank_left': [],
            'flank_right': []
        }
        
        # Get evaluation ranges if needed
        eval_ranges = self.get_evaluation_ranges() if use_evaluation_range else None
        
        # Combine profile data
        for side in ['left', 'right']:
            key = f'profile_{side}'
            for tooth_id, angles in profile_angles[side].items():
                data = self.profile_data[side].get(tooth_id, [])
                if len(angles) == len(data):
                    if use_evaluation_range and eval_ranges:
                        # Use actual evaluation range from the file
                        profile_start = eval_ranges['profile']['start']
                        profile_end = eval_ranges['profile']['end']
                        profile_start_mess = eval_ranges['profile']['start_mess']
                        profile_end_mess = eval_ranges['profile']['end_mess']
                        
                        if profile_start > 0 and profile_end > profile_start and profile_start_mess >= 0 and profile_end_mess > profile_start_mess:
                            # Calculate the fraction of the total measurement range that the evaluation range covers
                            # This gives us the exact position within the measurement data
                            total_points = len(data)
                            total_mess_range = profile_end_mess - profile_start_mess
                            eval_start_offset = profile_start - profile_start_mess
                            eval_end_offset = profile_end - profile_start_mess
                            
                            # Calculate the indices based on the actual ranges
                            start_idx = int(total_points * (eval_start_offset / total_mess_range))
                            end_idx = int(total_points * (eval_end_offset / total_mess_range))
                            
                            # Ensure we have a valid range
                            start_idx = max(0, min(start_idx, total_points - 1))
                            end_idx = max(start_idx + 1, min(end_idx, total_points))
                        else:
                            # Fallback to middle 40% if no valid evaluation range
                            total_points = len(data)
                            start_idx = int(total_points * 0.3)
                            end_idx = int(total_points * 0.7)
                        
                        if start_idx < end_idx:
                            combined_data[key].extend(list(zip(angles[start_idx:end_idx], data[start_idx:end_idx])))
                    else:
                        combined_data[key].extend(list(zip(angles, data)))
        
        # Combine flank data
        for side in ['left', 'right']:
            key = f'flank_{side}'
            for tooth_id, angles in flank_angles[side].items():
                data = self.flank_data[side].get(tooth_id, [])
                if len(angles) == len(data):
                    if use_evaluation_range and eval_ranges:
                        # Use actual evaluation range from the file
                        flank_start = eval_ranges['flank']['start']
                        flank_end = eval_ranges['flank']['end']
                        flank_start_mess = eval_ranges['flank']['start_mess']
                        flank_end_mess = eval_ranges['flank']['end_mess']
                        
                        if flank_start > 0 and flank_end > flank_start and flank_start_mess >= 0 and flank_end_mess > flank_start_mess:
                            # Calculate the fraction of the total measurement range that the evaluation range covers
                            # This gives us the exact position within the measurement data
                            total_points = len(data)
                            total_mess_range = flank_end_mess - flank_start_mess
                            eval_start_offset = flank_start - flank_start_mess
                            eval_end_offset = flank_end - flank_start_mess
                            
                            # Calculate the indices based on the actual ranges
                            start_idx = int(total_points * (eval_start_offset / total_mess_range))
                            end_idx = int(total_points * (eval_end_offset / total_mess_range))
                            
                            # Ensure we have a valid range
                            start_idx = max(0, min(start_idx, total_points - 1))
                            end_idx = max(start_idx + 1, min(end_idx, total_points))
                        else:
                            # Fallback to middle 40% if no valid evaluation range
                            total_points = len(data)
                            start_idx = int(total_points * 0.3)
                            end_idx = int(total_points * 0.7)
                        
                        if start_idx < end_idx:
                            combined_data[key].extend(list(zip(angles[start_idx:end_idx], data[start_idx:end_idx])))
                    else:
                        combined_data[key].extend(list(zip(angles, data)))
        
        # Sort by angle
        for key in combined_data:
            combined_data[key].sort(key=lambda x: x[0])
        
        return combined_data

if __name__ == '__main__':
    # Test the parser
    file_path = '263751-018-WAV.mka'
    parser = MKAParser(file_path)
    
    print('Basic Info:')
    print(f'Teeth Count: {parser.get_teeth_count()}')
    print(f'Module: {parser.get_module()}')
    print(f'Helix Angle: {parser.get_helix_angle()}')
    print(f'Pressure Angle: {parser.get_pressure_angle()}')
    print(f'Face Width: {parser.get_face_width()}')
    
    print('\nProfile Data:')
    for side in ['left', 'right']:
        print(f'{side}: {len(parser.profile_data[side])} teeth')
        # Show first 5 teeth only
        count = 0
        for tooth_id, data in parser.profile_data[side].items():
            print(f'  Tooth {tooth_id}: {len(data)} points')
            count += 1
            if count >= 5:
                print(f'  ... and {len(parser.profile_data[side]) - 5} more teeth')
                break
    
    print('\nFlank Data:')
    for side in ['left', 'right']:
        print(f'{side}: {len(parser.flank_data[side])} teeth')
        # Show first 5 teeth only
        count = 0
        for tooth_id, data in parser.flank_data[side].items():
            print(f'  Tooth {tooth_id}: {len(data)} points')
            count += 1
            if count >= 5:
                print(f'  ... and {len(parser.flank_data[side]) - 5} more teeth')
                break
    
    # Test rotation angle calculation
    print('\nTesting Rotation Angle Calculation:')
    profile_angles, flank_angles = parser.calculate_rotation_angles()
    
    # Test combined data
    print('\nTesting Combined Data:')
    combined_data = parser.get_combined_data()
    for key, data in combined_data.items():
        if data:
            print(f'{key}: {len(data)} points')
            # Show first and last few points
            print(f'  First point: angle={data[0][0]:.2f}°, value={data[0][1]:.2f}')
            print(f'  Last point: angle={data[-1][0]:.2f}°, value={data[-1][1]:.2f}')
        else:
            print(f'{key}: No data')
