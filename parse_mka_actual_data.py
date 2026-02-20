#!/usr/bin/env python
"""
从MKA文件中提取实际测量数据，生成以齿数为X轴的旋转角度曲线
"""
import os
import re
import numpy as np
import matplotlib.pyplot as plt

class MKAActualDataParser:
    """MKA文件实际数据解析器"""
    
    def __init__(self, mka_file):
        """
        初始化解析器
        
        Args:
            mka_file: MKA文件路径
        """
        self.mka_file = mka_file
        self.num_teeth = 87
        self.measured_teeth = 12
        self.data = {
            'profile_left': {'teeth': [], 'values': []},
            'profile_right': {'teeth': [], 'values': []},
            'helix_left': {'teeth': [], 'values': []},
            'helix_right': {'teeth': [], 'values': []}
        }
    
    def parse_mka_file(self):
        """
        解析MKA文件，提取实际测量数据
        """
        print(f"解析MKA文件: {self.mka_file}")
        
        # 读取文件内容
        with open(self.mka_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # 解析文件头部信息
        self._parse_header(lines)
        
        # 解析实际测量数据
        self._parse_measurement_data(lines)
    
    def _parse_header(self, lines):
        """
        解析文件头部信息
        
        Args:
            lines: 文件行列表
        """
        content = ''.join(lines)
        
        # 提取齿数
        teeth_match = re.search(r'Z\u00e4hnezahl z.*?:\s*(\d+)', content)
        if teeth_match:
            self.num_teeth = int(teeth_match.group(1))
            print(f"提取到齿数: {self.num_teeth}")
        
        # 提取测量齿数
        measured_teeth_match = re.search(r'Messz\u00e4hnezahl=.*?:\s*(\d+)', content)
        if measured_teeth_match:
            self.measured_teeth = int(measured_teeth_match.group(1))
            print(f"提取到测量齿数: {self.measured_teeth}")
    
    def _parse_measurement_data(self, lines):
        """
        解析实际测量数据
        
        Args:
            lines: 文件行列表
        """
        print("提取实际测量数据...")
        
        current_section = None
        current_tooth = None
        current_side = None
        values = []
        
        for line in lines:
            line = line.strip()
            
            # 检测数据段开始
            if 'Flankenlinie:' in line:
                current_section = 'helix'
                # 提取齿号和方向
                tooth_match = re.search(r'Zahn-Nr.:\s*(\d+[a-zA-Z]*)\s*(links|rechts)', line)
                if tooth_match:
                    tooth_id = tooth_match.group(1)
                    side = tooth_match.group(2)
                    current_tooth = tooth_id
                    current_side = side
                    values = []
                    print(f"找到齿向数据: {tooth_id} {side}")
            
            elif 'Profil:' in line:
                current_section = 'profile'
                # 提取齿号和方向
                tooth_match = re.search(r'Zahn-Nr.:\s*(\d+[a-zA-Z]*)\s*(links|rechts)', line)
                if tooth_match:
                    tooth_id = tooth_match.group(1)
                    side = tooth_match.group(2)
                    current_tooth = tooth_id
                    current_side = side
                    values = []
                    print(f"找到齿形数据: {tooth_id} {side}")
            
            # 解析数据行
            elif current_section and current_tooth:
                # 跳过非数据行
                if ':' in line or line == '' or 'Zahn-Nr.' in line:
                    continue
                
                # 提取数值
                try:
                    # 分割行中的数值
                    nums = line.split()
                    for num in nums:
                        # 跳过无效值
                        if num == '-2147483.648':
                            continue
                        # 转换为浮点数
                        value = float(num)
                        values.append(value)
                except ValueError:
                    continue
            
            # 检测数据段结束
            if current_section and current_tooth and len(values) > 0:
                # 当遇到新的数据段或文件结束时保存数据
                if ('Flankenlinie:' in line or 'Profil:' in line) and len(values) > 10:
                    self._save_measurement_data(current_section, current_side, current_tooth, values)
                    values = []
        
        # 保存最后一组数据
        if current_section and current_tooth and len(values) > 10:
            self._save_measurement_data(current_section, current_side, current_tooth, values)
    
    def _save_measurement_data(self, section, side, tooth_id, values):
        """
        保存测量数据
        
        Args:
            section: 数据类型 (profile 或 helix)
            side: 方向 (links 或 rechts)
            tooth_id: 齿号
            values: 测量值列表
        """
        # 确定数据键
        if side == 'links':
            key = f'{section}_left'
        else:
            key = f'{section}_right'
        
        # 提取齿序号（去除字母）
        tooth_num = re.search(r'(\d+)', tooth_id)
        if tooth_num:
            tooth_idx = int(tooth_num.group(1)) - 1  # 转换为0-based索引
            
            # 生成齿位置数据
            num_points = len(values)
            tooth_positions = np.linspace(tooth_idx, tooth_idx + 1, num_points)
            
            # 保存数据
            self.data[key]['teeth'].extend(tooth_positions.tolist())
            self.data[key]['values'].extend(values)
            
            print(f"保存 {section} {side} 齿 {tooth_id} 的数据，共 {num_points} 个点")
    
    def display_rotation_curves(self):
        """
        显示以齿数为X轴的旋转角度曲线
        """
        print("显示旋转角度曲线...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 左齿形
        if self.data['profile_left']['teeth']:
            ax1.plot(self.data['profile_left']['teeth'], self.data['profile_left']['values'], 'b-', linewidth=1.0)
            ax1.set_title('Left Profile - Actual MKA Data')
            ax1.set_xlabel('Tooth Number')
            ax1.set_ylabel('Deviation (μm)')
            ax1.set_xlim(0, self.num_teeth)
            ax1.grid(True)
            ax1.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax1.transAxes, fontsize=10, fontweight='bold')
        
        # 右齿形
        if self.data['profile_right']['teeth']:
            ax2.plot(self.data['profile_right']['teeth'], self.data['profile_right']['values'], 'r-', linewidth=1.0)
            ax2.set_title('Right Profile - Actual MKA Data')
            ax2.set_xlabel('Tooth Number')
            ax2.set_ylabel('Deviation (μm)')
            ax2.set_xlim(0, self.num_teeth)
            ax2.grid(True)
            ax2.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax2.transAxes, fontsize=10, fontweight='bold')
        
        # 左齿向
        if self.data['helix_left']['teeth']:
            ax3.plot(self.data['helix_left']['teeth'], self.data['helix_left']['values'], 'g-', linewidth=1.0)
            ax3.set_title('Left Helix - Actual MKA Data')
            ax3.set_xlabel('Tooth Number')
            ax3.set_ylabel('Deviation (μm)')
            ax3.set_xlim(0, self.num_teeth)
            ax3.grid(True)
            ax3.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax3.transAxes, fontsize=10, fontweight='bold')
        
        # 右齿向
        if self.data['helix_right']['teeth']:
            ax4.plot(self.data['helix_right']['teeth'], self.data['helix_right']['values'], 'y-', linewidth=1.0)
            ax4.set_title('Right Helix - Actual MKA Data')
            ax4.set_xlabel('Tooth Number')
            ax4.set_ylabel('Deviation (μm)')
            ax4.set_xlim(0, self.num_teeth)
            ax4.grid(True)
            ax4.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax4.transAxes, fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('mka_actual_rotation_curves.png')
        print("实际MKA数据旋转角度曲线已保存到 mka_actual_rotation_curves.png")
        
        # 显示组合图
        plt.show()
    
    def run(self):
        """
        运行解析流程
        """
        print("=== 从MKA文件提取实际测量数据 ===")
        
        # 解析MKA文件
        self.parse_mka_file()
        
        # 显示曲线
        self.display_rotation_curves()
        
        print("=== MKA文件实际数据解析完成 ===")

if __name__ == "__main__":
    mka_file = "263751-018-WAV.mka"
    parser = MKAActualDataParser(mka_file)
    parser.run()
