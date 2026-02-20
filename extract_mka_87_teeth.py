#!/usr/bin/env python
"""
从MKA文件中提取87个齿的实际测量数据，生成以齿数为X轴的旋转角度曲线
利用齿轮波纹度软件2_修改版_simplified.py中的解析逻辑
"""
import sys
import re
import os
import numpy as np
import matplotlib.pyplot as plt
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MKAFullDataExtractor:
    """MKA文件完整数据提取器"""
    
    def __init__(self, mka_file):
        """
        初始化提取器
        
        Args:
            mka_file: MKA文件路径
        """
        self.mka_file = mka_file
        self.num_teeth = 87
        self.measured_teeth = 87
        self.data = {
            'profile_left': {'teeth': [], 'values': []},
            'profile_right': {'teeth': [], 'values': []},
            'helix_left': {'teeth': [], 'values': []},
            'helix_right': {'teeth': [], 'values': []}
        }
    
    def parse_mka_file(self):
        """
        解析MKA文件，提取所有87个齿的测量数据
        """
        logger.info(f"解析MKA文件: {self.mka_file}")
        
        # 读取文件内容
        with open(self.mka_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # 提取齿数
        teeth_match = re.search(r'Z\u00e4hnezahl z.*?:\s*(\d+)', content)
        if teeth_match:
            self.num_teeth = int(teeth_match.group(1))
            logger.info(f"提取到齿数: {self.num_teeth}")
        
        # 提取齿形数据
        logger.info("提取齿形数据...")
        self._extract_profile_data(content)
        
        # 提取齿向数据
        logger.info("提取齿向数据...")
        self._extract_helix_data(content)
    
    def _extract_profile_data(self, content):
        """
        提取齿形数据
        """
        # 查找所有齿形数据段
        profile_pattern = re.compile(r'Profil:\s*Zahn-Nr\.:\s*(\d+[a-zA-Z]*)\s*(links|rechts)\s*/\s*\d+\s*Werte.*?\n((?:\s*[-+]?\d*\.?\d+\s*)*)', re.DOTALL)
        profile_matches = profile_pattern.finditer(content)
        
        for match in profile_matches:
            tooth_id = match.group(1)
            side = match.group(2)
            data_text = match.group(3)
            
            # 提取数值
            values = self._extract_values(data_text, 480)  # 齿形数据有480个点
            
            # 转换齿号
            tooth_num = re.search(r'(\d+)', tooth_id)
            if tooth_num:
                tooth_idx = int(tooth_num.group(1)) - 1  # 转换为0-based索引
                
                # 生成齿位置数据
                num_points = len(values)
                tooth_positions = np.linspace(tooth_idx, tooth_idx + 1, num_points)
                
                # 保存数据
                key = f'profile_{"left" if side == "links" else "right"}'
                if key in self.data:
                    self.data[key]['teeth'].extend(tooth_positions.tolist())
                    self.data[key]['values'].extend(values)
                    logger.info(f"保存齿形 {side} 齿 {tooth_id} 的数据，共 {num_points} 个点")
    
    def _extract_helix_data(self, content):
        """
        提取齿向数据
        """
        # 查找所有齿向数据段
        helix_pattern = re.compile(r'Flankenlinie:\s*Zahn-Nr\.:\s*(\d+[a-zA-Z]*)\s*(links|rechts)\s*/\s*\d+\s*Werte.*?\n((?:\s*[-+]?\d*\.?\d+\s*)*)', re.DOTALL)
        helix_matches = helix_pattern.finditer(content)
        
        for match in helix_matches:
            tooth_id = match.group(1)
            side = match.group(2)
            data_text = match.group(3)
            
            # 提取数值
            values = self._extract_values(data_text, 915)  # 齿向数据有915个点
            
            # 转换齿号
            tooth_num = re.search(r'(\d+)', tooth_id)
            if tooth_num:
                tooth_idx = int(tooth_num.group(1)) - 1  # 转换为0-based索引
                
                # 生成齿位置数据
                num_points = len(values)
                tooth_positions = np.linspace(tooth_idx, tooth_idx + 1, num_points)
                
                # 保存数据
                key = f'helix_{"left" if side == "links" else "right"}'
                if key in self.data:
                    self.data[key]['teeth'].extend(tooth_positions.tolist())
                    self.data[key]['values'].extend(values)
                    logger.info(f"保存齿向 {side} 齿 {tooth_id} 的数据，共 {num_points} 个点")
    
    def _extract_values(self, data_text, expected_points):
        """
        从文本中提取数值
        
        Args:
            data_text: 包含数值的文本
            expected_points: 期望的点数
            
        Returns:
            list: 提取的数值列表
        """
        # 提取所有数值
        number_pattern = re.compile(r'[-+]?\d*\.?\d+')
        numbers = number_pattern.findall(data_text)
        
        # 转换为浮点数
        values = []
        for num in numbers:
            try:
                # 处理前导点的情况
                if num.startswith('.'):
                    num = '0' + num
                elif num.startswith('-.'):
                    num = '-0' + num[1:]
                values.append(float(num))
            except ValueError:
                continue
        
        # 确保有足够的点
        if len(values) < expected_points:
            values.extend([0.0] * (expected_points - len(values)))
            logger.warning(f"数据点不足: {len(values)} < {expected_points}，用0填充")
        elif len(values) > expected_points:
            values = values[:expected_points]
            logger.info(f"数据点过多: {len(values)} > {expected_points}，截取前{expected_points}个点")
        
        return values
    
    def display_rotation_curves(self):
        """
        显示以齿数为X轴的旋转角度曲线
        """
        logger.info("显示旋转角度曲线...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 左齿形
        if self.data['profile_left']['teeth']:
            ax1.plot(self.data['profile_left']['teeth'], self.data['profile_left']['values'], 'b-', linewidth=1.0)
            ax1.set_title('Left Profile - 87 Teeth MKA Data')
            ax1.set_xlabel('Tooth Number')
            ax1.set_ylabel('Deviation (μm)')
            ax1.set_xlim(0, self.num_teeth)
            ax1.grid(True)
            ax1.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax1.transAxes, fontsize=10, fontweight='bold')
        
        # 右齿形
        if self.data['profile_right']['teeth']:
            ax2.plot(self.data['profile_right']['teeth'], self.data['profile_right']['values'], 'r-', linewidth=1.0)
            ax2.set_title('Right Profile - 87 Teeth MKA Data')
            ax2.set_xlabel('Tooth Number')
            ax2.set_ylabel('Deviation (μm)')
            ax2.set_xlim(0, self.num_teeth)
            ax2.grid(True)
            ax2.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax2.transAxes, fontsize=10, fontweight='bold')
        
        # 左齿向
        if self.data['helix_left']['teeth']:
            ax3.plot(self.data['helix_left']['teeth'], self.data['helix_left']['values'], 'g-', linewidth=1.0)
            ax3.set_title('Left Helix - 87 Teeth MKA Data')
            ax3.set_xlabel('Tooth Number')
            ax3.set_ylabel('Deviation (μm)')
            ax3.set_xlim(0, self.num_teeth)
            ax3.grid(True)
            ax3.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax3.transAxes, fontsize=10, fontweight='bold')
        
        # 右齿向
        if self.data['helix_right']['teeth']:
            ax4.plot(self.data['helix_right']['teeth'], self.data['helix_right']['values'], 'y-', linewidth=1.0)
            ax4.set_title('Right Helix - 87 Teeth MKA Data')
            ax4.set_xlabel('Tooth Number')
            ax4.set_ylabel('Deviation (μm)')
            ax4.set_xlim(0, self.num_teeth)
            ax4.grid(True)
            ax4.text(0.05, 0.95, f'z={self.num_teeth}', transform=ax4.transAxes, fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('mka_87_teeth_rotation_curves.png')
        logger.info("87个齿的旋转角度曲线已保存到 mka_87_teeth_rotation_curves.png")
        
        # 显示组合图
        plt.show()
    
    def run(self):
        """
        运行提取流程
        """
        logger.info("=== 从MKA文件提取87个齿的实际测量数据 ===")
        
        # 解析MKA文件
        self.parse_mka_file()
        
        # 显示曲线
        self.display_rotation_curves()
        
        logger.info("=== MKA文件87个齿数据提取完成 ===")

if __name__ == "__main__":
    mka_file = "263751-018-WAV.mka"
    extractor = MKAFullDataExtractor(mka_file)
    extractor.run()
