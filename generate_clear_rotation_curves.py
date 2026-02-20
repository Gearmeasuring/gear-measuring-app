#!/usr/bin/env python
"""
生成清晰易理解的旋转角度曲线
显示87个齿的测量数据，使曲线更平滑、更易读
"""
import numpy as np
import matplotlib.pyplot as plt
import re

class ClearRotationCurveGenerator:
    """清晰的旋转角度曲线生成器"""
    
    def __init__(self, mka_file):
        """
        初始化生成器
        
        Args:
            mka_file: MKA文件路径
        """
        self.mka_file = mka_file
        self.num_teeth = 87
        self.data = {
            'profile_left': {'teeth': [], 'values': []},
            'profile_right': {'teeth': [], 'values': []},
            'helix_left': {'teeth': [], 'values': []},
            'helix_right': {'teeth': [], 'values': []}
        }
    
    def parse_mka_file(self):
        """
        解析MKA文件，提取关键数据点
        """
        print(f"解析MKA文件: {self.mka_file}")
        
        # 读取文件内容
        with open(self.mka_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 提取齿数
        teeth_match = re.search(r'Z\u00e4hnezahl z.*?:\s*(\d+)', content)
        if teeth_match:
            self.num_teeth = int(teeth_match.group(1))
            print(f"提取到齿数: {self.num_teeth}")
        
        # 提取齿形数据（每齿只取关键点数）
        print("提取齿形数据...")
        self._extract_key_points(content, 'Profil', 480, 50)  # 每齿取50个点
        
        # 提取齿向数据（每齿只取关键点数）
        print("提取齿向数据...")
        self._extract_key_points(content, 'Flankenlinie', 915, 100)  # 每齿取100个点
    
    def _extract_key_points(self, content, data_type, total_points, key_points):
        """
        提取关键数据点
        """
        if data_type == 'Profil':
            pattern = re.compile(r'Profil:\s*Zahn-Nr\.:\s*(\d+[a-zA-Z]*)\s*(links|rechts)\s*/\s*\d+\s*Werte.*?\n((?:\s*[-+]?\d*\.?\d+\s*)*)', re.DOTALL)
            data_keys = {'links': 'profile_left', 'rechts': 'profile_right'}
        else:
            pattern = re.compile(r'Flankenlinie:\s*Zahn-Nr\.:\s*(\d+[a-zA-Z]*)\s*(links|rechts)\s*/\s*\d+\s*Werte.*?\n((?:\s*[-+]?\d*\.?\d+\s*)*)', re.DOTALL)
            data_keys = {'links': 'helix_left', 'rechts': 'helix_right'}
        
        matches = pattern.finditer(content)
        
        for match in matches:
            tooth_id = match.group(1)
            side = match.group(2)
            data_text = match.group(3)
            
            # 提取所有数值
            number_pattern = re.compile(r'[-+]?\d*\.?\d+')
            numbers = number_pattern.findall(data_text)
            values = []
            for num in numbers:
                try:
                    if num.startswith('.'):
                        num = '0' + num
                    elif num.startswith('-.'):
                        num = '-0' + num[1:]
                    values.append(float(num))
                except ValueError:
                    continue
            
            # 只取关键点数
            if len(values) >= key_points:
                # 均匀采样
                step = max(1, len(values) // key_points)
                sampled_values = values[::step][:key_points]
            else:
                sampled_values = values
            
            # 转换齿号
            tooth_num = re.search(r'(\d+)', tooth_id)
            if tooth_num:
                tooth_idx = int(tooth_num.group(1)) - 1  # 转换为0-based索引
                
                # 生成齿位置数据
                num_points = len(sampled_values)
                tooth_positions = np.linspace(tooth_idx, tooth_idx + 1, num_points)
                
                # 保存数据
                if side in data_keys:
                    key = data_keys[side]
                    self.data[key]['teeth'].extend(tooth_positions.tolist())
                    self.data[key]['values'].extend(sampled_values)
                    print(f"保存 {data_type} {side} 齿 {tooth_id} 的数据，共 {num_points} 个点")
    
    def display_clear_curves(self):
        """
        显示清晰易理解的旋转角度曲线
        """
        print("显示清晰的旋转角度曲线...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 左齿形
        if self.data['profile_left']['teeth']:
            ax1.plot(self.data['profile_left']['teeth'], self.data['profile_left']['values'], 'b-', linewidth=0.8)
            ax1.set_title('Left Profile - 87 Teeth')
            ax1.set_xlabel('Tooth Number')
            ax1.set_ylabel('Deviation (μm)')
            ax1.set_xlim(0, self.num_teeth)
            ax1.grid(True, alpha=0.3)
            ax1.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax1.transAxes, fontsize=10, fontweight='bold')
        
        # 右齿形
        if self.data['profile_right']['teeth']:
            ax2.plot(self.data['profile_right']['teeth'], self.data['profile_right']['values'], 'r-', linewidth=0.8)
            ax2.set_title('Right Profile - 87 Teeth')
            ax2.set_xlabel('Tooth Number')
            ax2.set_ylabel('Deviation (μm)')
            ax2.set_xlim(0, self.num_teeth)
            ax2.grid(True, alpha=0.3)
            ax2.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax2.transAxes, fontsize=10, fontweight='bold')
        
        # 左齿向
        if self.data['helix_left']['teeth']:
            ax3.plot(self.data['helix_left']['teeth'], self.data['helix_left']['values'], 'g-', linewidth=0.8)
            ax3.set_title('Left Helix - 87 Teeth')
            ax3.set_xlabel('Tooth Number')
            ax3.set_ylabel('Deviation (μm)')
            ax3.set_xlim(0, self.num_teeth)
            ax3.grid(True, alpha=0.3)
            ax3.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax3.transAxes, fontsize=10, fontweight='bold')
        
        # 右齿向
        if self.data['helix_right']['teeth']:
            ax4.plot(self.data['helix_right']['teeth'], self.data['helix_right']['values'], 'y-', linewidth=0.8)
            ax4.set_title('Right Helix - 87 Teeth')
            ax4.set_xlabel('Tooth Number')
            ax4.set_ylabel('Deviation (μm)')
            ax4.set_xlim(0, self.num_teeth)
            ax4.grid(True, alpha=0.3)
            ax4.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax4.transAxes, fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('clear_87_teeth_rotation_curves.png')
        print("清晰的旋转角度曲线已保存到 clear_87_teeth_rotation_curves.png")
        
        # 显示组合图
        plt.show()
    
    def run(self):
        """
        运行生成流程
        """
        print("=== 生成清晰的87个齿旋转角度曲线 ===")
        
        # 解析MKA文件
        self.parse_mka_file()
        
        # 显示曲线
        self.display_clear_curves()
        
        print("=== 清晰曲线生成完成 ===")

if __name__ == "__main__":
    mka_file = "263751-018-WAV.mka"
    generator = ClearRotationCurveGenerator(mka_file)
    generator.run()
