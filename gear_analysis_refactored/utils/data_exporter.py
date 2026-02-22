"""
数据导出模块
支持多种格式的数据导出
"""
import csv
import os
from typing import Dict, List, Any
from gear_analysis_refactored.config.logging_config import logger
try:
    from ..models import GearMeasurementData
except ImportError:
    from gear_analysis_refactored.models import GearMeasurementData


class DataExporter:
    """数据导出器"""
    
    @staticmethod
    def export_to_csv(data: Dict[str, Any], output_path: str, 
                     headers: List[str] = None) -> bool:
        """
        导出数据到CSV文件
        
        Args:
            data: 数据字典或列表
            output_path: 输出路径
            headers: 表头列表
            
        Returns:
            bool: 是否成功
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # 写入表头
                if headers:
                    writer.writerow(headers)
                
                # 写入数据
                if isinstance(data, dict):
                    for key, value in data.items():
                        writer.writerow([key, value])
                elif isinstance(data, list):
                    for row in data:
                        if isinstance(row, (list, tuple)):
                            writer.writerow(row)
                        else:
                            writer.writerow([row])
            
            logger.info(f"数据已导出到CSV: {output_path}")
            return True
            
        except Exception as e:
            logger.exception(f"导出CSV失败: {e}")
            return False
    
    @staticmethod
    def export_measurement_data_to_csv(measurement_data: GearMeasurementData,
                                      output_path: str,
                                      data_type: str = 'profile') -> bool:
        """
        导出测量数据到CSV
        
        Args:
            measurement_data: 测量数据对象
            output_path: 输出路径
            data_type: 数据类型 ('profile' 或 'flank')
            
        Returns:
            bool: 是否成功
        """
        try:
            # 选择数据源
            if data_type == 'profile':
                data = measurement_data.profile_data
                data_name = "齿形"
            else:
                data = measurement_data.flank_data
                data_name = "齿向"
            
            if not data.has_data():
                logger.warning(f"无{data_name}数据可导出")
                return False
            
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # 写入基本信息
                writer.writerow([f"{data_name}测量数据导出"])
                writer.writerow([])
                writer.writerow(["文件", measurement_data.file_path])
                writer.writerow(["模数", measurement_data.basic_info.module])
                writer.writerow(["齿数", measurement_data.basic_info.teeth])
                writer.writerow([])
                
                # 导出左侧数据
                if data.left:
                    writer.writerow([f"=== 左侧{data_name}数据 ==="])
                    for tooth_num in sorted(data.left.keys()):
                        values = data.left[tooth_num]
                        writer.writerow([f"齿号 {tooth_num}", f"数据点数: {len(values)}"])
                        
                        # 写入数据（每10个点一行）
                        for i in range(0, len(values), 10):
                            chunk = values[i:i+10]
                            writer.writerow([f"{v:.6f}" for v in chunk])
                        writer.writerow([])
                
                # 导出右侧数据
                if data.right:
                    writer.writerow([f"=== 右侧{data_name}数据 ==="])
                    for tooth_num in sorted(data.right.keys()):
                        values = data.right[tooth_num]
                        writer.writerow([f"齿号 {tooth_num}", f"数据点数: {len(values)}"])
                        
                        # 写入数据（每10个点一行）
                        for i in range(0, len(values), 10):
                            chunk = values[i:i+10]
                            writer.writerow([f"{v:.6f}" for v in chunk])
                        writer.writerow([])
            
            logger.info(f"{data_name}数据已导出到CSV: {output_path}")
            return True
            
        except Exception as e:
            logger.exception(f"导出{data_name}数据失败: {e}")
            return False
    
    @staticmethod
    def export_gear_params_to_csv(measurement_data: GearMeasurementData,
                                  output_path: str) -> bool:
        """
        导出齿轮参数到CSV
        
        Args:
            measurement_data: 测量数据对象
            output_path: 输出路径
            
        Returns:
            bool: 是否成功
        """
        try:
            info = measurement_data.basic_info
            
            data = [
                ["参数项", "值", "单位"],
                ["模数", f"{info.module:.3f}", "mm"],
                ["齿数", str(info.teeth), "-"],
                ["螺旋角", f"{info.helix_angle:.2f}", "°"],
                ["压力角", f"{info.pressure_angle:.2f}", "°"],
                ["变位系数", f"{info.modification_coeff:.4f}", "-"],
                ["齿宽", f"{info.width:.2f}", "mm"],
                ["齿顶圆直径", f"{info.tip_diameter:.3f}", "mm"],
                ["齿根圆直径", f"{info.root_diameter:.3f}", "mm"],
                ["精度等级", f"{info.accuracy_grade}", "级"],
            ]
            
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerows(data)
            
            logger.info(f"齿轮参数已导出到CSV: {output_path}")
            return True
            
        except Exception as e:
            logger.exception(f"导出齿轮参数失败: {e}")
            return False


# 便捷函数
def export_all_data(measurement_data: GearMeasurementData, 
                   base_path: str) -> Dict[str, bool]:
    """
    导出所有数据到多个文件
    
    Args:
        measurement_data: 测量数据
        base_path: 基础路径（不含扩展名）
        
    Returns:
        Dict: 各个导出操作的结果
    """
    results = {}
    exporter = DataExporter()
    
    # 导出齿轮参数
    params_path = f"{base_path}_齿轮参数.csv"
    results['params'] = exporter.export_gear_params_to_csv(
        measurement_data, params_path
    )
    
    # 导出齿形数据
    if measurement_data.has_profile_data():
        profile_path = f"{base_path}_齿形数据.csv"
        results['profile'] = exporter.export_measurement_data_to_csv(
            measurement_data, profile_path, 'profile'
        )
    
    # 导出齿向数据
    if measurement_data.has_flank_data():
        flank_path = f"{base_path}_齿向数据.csv"
        results['flank'] = exporter.export_measurement_data_to_csv(
            measurement_data, flank_path, 'flank'
        )
    
    return results

