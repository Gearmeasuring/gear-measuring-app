#!/usr/bin/env python
"""
生成四行布局的旋转角度曲线
每个曲线单独一行，显示更清晰
"""
import numpy as np
import matplotlib.pyplot as plt
import re

class FourRowCurveGenerator:
    """
    四行布局的曲线生成器
    """
    
    def __init__(self, mka_file):
        """
        初始化生成器
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
        解析MKA文件
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
        
        # 提取齿形数据
        print("提取齿形数据...")
        self._extract_data(content, 'Profil', 20)
        
        # 提取齿向数据
        print("提取齿向数据...")
        self._extract_data(content, 'Flankenlinie', 30)
    
    def _extract_data(self, content, data_type, points_per_tooth):
        """
        提取数据
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
            
            # 提取数值
            numbers = re.findall(r'[-+]?\d*\.?\d+', data_text)
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
            
            # 减少数据点
            if len(values) > points_per_tooth:
                step = max(1, len(values) // points_per_tooth)
                values = values[::step][:points_per_tooth]
            
            # 转换齿号
            tooth_num = re.search(r'(\d+)', tooth_id)
            if tooth_num:
                tooth_idx = int(tooth_num.group(1)) - 1
                
                # 生成齿位置数据
                num_points = len(values)
                if num_points > 0:
                    tooth_positions = np.linspace(tooth_idx, tooth_idx + 1, num_points)
                    
                    # 保存数据
                    if side in data_keys:
                        key = data_keys[side]
                        self.data[key]['teeth'].extend(tooth_positions.tolist())
                        self.data[key]['values'].extend(values)
    
    def display_four_row_curves(self):
        """
        显示四行布局的曲线
        """
        print("显示四行布局的旋转角度曲线...")
        
        # 创建四行一列的布局
        fig, ((ax1), (ax2), (ax3), (ax4)) = plt.subplots(4, 1, figsize=(16, 16))
        
        # 左齿形
        if self.data['profile_left']['teeth']:
            teeth = self.data['profile_left']['teeth']
            values = self.data['profile_left']['values']
            ax1.plot(teeth, values, 'b-', linewidth=0.8)
            ax1.set_title('Left Profile - 87 Teeth')
            ax1.set_xlabel('Tooth Number')
            ax1.set_ylabel('Deviation (μm)')
            ax1.set_xlim(0, self.num_teeth)
            ax1.grid(True, alpha=0.3)
            ax1.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax1.transAxes, fontsize=10, fontweight='bold')
        
        # 右齿形
        if self.data['profile_right']['teeth']:
            teeth = self.data['profile_right']['teeth']
            values = self.data['profile_right']['values']
            ax2.plot(teeth, values, 'r-', linewidth=0.8)
            ax2.set_title('Right Profile - 87 Teeth')
            ax2.set_xlabel('Tooth Number')
            ax2.set_ylabel('Deviation (μm)')
            ax2.set_xlim(0, self.num_teeth)
            ax2.grid(True, alpha=0.3)
            ax2.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax2.transAxes, fontsize=10, fontweight='bold')
        
        # 左齿向
        if self.data['helix_left']['teeth']:
            teeth = self.data['helix_left']['teeth']
            values = self.data['helix_left']['values']
            ax3.plot(teeth, values, 'g-', linewidth=0.8)
            ax3.set_title('Left Helix - 87 Teeth')
            ax3.set_xlabel('Tooth Number')
            ax3.set_ylabel('Deviation (μm)')
            ax3.set_xlim(0, self.num_teeth)
            ax3.grid(True, alpha=0.3)
            ax3.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax3.transAxes, fontsize=10, fontweight='bold')
        
        # 右齿向
        if self.data['helix_right']['teeth']:
            teeth = self.data['helix_right']['teeth']
            values = self.data['helix_right']['values']
            ax4.plot(teeth, values, 'y-', linewidth=0.8)
            ax4.set_title('Right Helix - 87 Teeth')
            ax4.set_xlabel('Tooth Number')
            ax4.set_ylabel('Deviation (μm)')
            ax4.set_xlim(0, self.num_teeth)
            ax4.grid(True, alpha=0.3)
            ax4.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax4.transAxes, fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('four_row_87_teeth_rotation_curves.png')
        print("四行布局的旋转角度曲线已保存到 four_row_87_teeth_rotation_curves.png")
        
        # 显示组合图
        plt.show()
    
    def run(self):
        """
        运行生成流程
        """
        print("=== 生成四行布局的87个齿旋转角度曲线 ===")
        
        # 解析MKA文件
        self.parse_mka_file()
        
        # 显示曲线
        self.display_four_row_curves()
        
        print("=== 四行布局曲线生成完成 ===")

if __name__ == "__main__":
    mka_file = "263751-018-WAV.mka"
    generator = FourRowCurveGenerator(mka_file)
    generator.run()
