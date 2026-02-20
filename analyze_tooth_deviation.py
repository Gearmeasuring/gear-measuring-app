#!/usr/bin/env python3
"""
分析单个齿数据与合并数据的差异，找出偏离的具体齿范围并分析原因
"""

import numpy as np
from parse_mka_file import MKAParser


def analyze_tooth_data():
    """
    分析单个齿数据与合并数据的差异
    """
    print("=== 分析单个齿数据与合并数据的差异 ===")
    
    # 读取MKA文件
    file_path = '263751-018-WAV.mka'
    parser = MKAParser(file_path)
    
    # 获取左齿形数据
    left_profile_data = parser.profile_data['left']
    
    print(f"左齿形数量: {len(left_profile_data)}")
    print(f"原始齿号: {list(left_profile_data.keys())[:10]}...{list(left_profile_data.keys())[-10:]}")
    
    # 分析齿号排序问题
    print("\n=== 齿号排序分析 ===")
    tooth_ids = list(left_profile_data.keys())
    
    # 提取纯数字部分进行排序
    def extract_number(tooth_id):
        return int(''.join(filter(str.isdigit, tooth_id)))
    
    sorted_tooth_ids = sorted(tooth_ids, key=extract_number)
    print(f"排序后的齿号: {sorted_tooth_ids[:10]}...{sorted_tooth_ids[-10:]}")
    
    # 分析每个齿的数据点数量
    print("\n=== 每个齿的数据点数量分析 ===")
    data_points_per_tooth = []
    for tooth_id in sorted_tooth_ids:
        num_points = len(left_profile_data[tooth_id])
        data_points_per_tooth.append(num_points)
        if num_points < 400 or num_points > 600:  # 异常值检测
            print(f"齿 {tooth_id}: {num_points} 个数据点 (异常!)")
    
    # 统计数据点数量的分布
    print(f"\n数据点数量统计:")
    print(f"平均值: {np.mean(data_points_per_tooth):.1f}")
    print(f"最小值: {np.min(data_points_per_tooth)}")
    print(f"最大值: {np.max(data_points_per_tooth)}")
    print(f"标准差: {np.std(data_points_per_tooth):.1f}")
    
    # 分析齿之间的数据连续性
    print("\n=== 齿之间的数据连续性分析 ===")
    
    # 合并所有齿的数据
    all_data = []
    tooth_boundaries = []
    for tooth_id in sorted_tooth_ids:
        values = left_profile_data[tooth_id]
        tooth_boundaries.append(len(all_data))
        all_data.extend(values)
    
    all_data = np.array(all_data)
    
    # 计算相邻数据点之间的差异
    data_diffs = np.abs(np.diff(all_data))
    
    # 找出差异较大的位置
    threshold = np.mean(data_diffs) + 3 * np.std(data_diffs)  # 3倍标准差作为阈值
    large_diff_indices = np.where(data_diffs > threshold)[0]
    
    print(f"\n差异分析:")
    print(f"数据点总数: {len(all_data)}")
    print(f"平均差异: {np.mean(data_diffs):.4f}")
    print(f"最大差异: {np.max(data_diffs):.4f}")
    print(f"差异阈值: {threshold:.4f}")
    print(f"超过阈值的差异数量: {len(large_diff_indices)}")
    
    # 分析大差异位置对应的齿
    if len(large_diff_indices) > 0:
        print("\n=== 大差异位置分析 ===")
        
        # 找出大差异位置对应的齿
        for diff_idx in large_diff_indices[:10]:  # 只显示前10个
            # 找到对应的齿
            tooth_idx = 0
            for i, boundary in enumerate(tooth_boundaries):
                if boundary > diff_idx:
                    tooth_idx = i - 1
                    break
            else:
                tooth_idx = len(tooth_boundaries) - 1
            
            if 0 <= tooth_idx < len(sorted_tooth_ids):
                tooth_id = sorted_tooth_ids[tooth_idx]
                next_tooth_id = sorted_tooth_ids[tooth_idx + 1] if tooth_idx + 1 < len(sorted_tooth_ids) else 'END'
                print(f"位置 {diff_idx}: 齿 {tooth_id} -> 齿 {next_tooth_id}, 差异值: {data_diffs[diff_idx]:.4f}")
    
    # 分析特定齿范围的数据
    print("\n=== 特定齿范围分析 ===")
    # 检查齿号为'1a', '1b', '1'的数据
    special_teeth = ['1a', '1b', '1']
    for tooth_id in special_teeth:
        if tooth_id in left_profile_data:
            values = left_profile_data[tooth_id]
            print(f"齿 {tooth_id}: {len(values)} 个数据点")
            print(f"  数据范围: {min(values):.4f} ~ {max(values):.4f}")
            print(f"  平均值: {np.mean(values):.4f}")
            print(f"  标准差: {np.std(values):.4f}")
    
    # 检查从齿1到齿10的数据
    print("\n=== 前10个齿的数据分析 ===")
    for i, tooth_id in enumerate(sorted_tooth_ids[:10]):
        values = left_profile_data[tooth_id]
        print(f"齿 {tooth_id}: {len(values)} 个数据点, 范围: {min(values):.4f} ~ {max(values):.4f}")
    
    # 检查从齿80到齿87的数据
    print("\n=== 最后10个齿的数据分析 ===")
    for i, tooth_id in enumerate(sorted_tooth_ids[-10:]):
        values = left_profile_data[tooth_id]
        print(f"齿 {tooth_id}: {len(values)} 个数据点, 范围: {min(values):.4f} ~ {max(values):.4f}")
    
    return {
        'sorted_tooth_ids': sorted_tooth_ids,
        'data_points_per_tooth': data_points_per_tooth,
        'large_diff_indices': large_diff_indices,
        'tooth_boundaries': tooth_boundaries
    }


def main():
    """
    主函数
    """
    analysis_result = analyze_tooth_data()
    
    # 分析结果总结
    print("\n=== 分析结果总结 ===")
    print(f"1. 左齿形总数: {len(analysis_result['sorted_tooth_ids'])}")
    print(f"2. 数据点数量异常的齿: {sum(1 for n in analysis_result['data_points_per_tooth'] if n < 400 or n > 600)}")
    print(f"3. 齿间大差异数量: {len(analysis_result['large_diff_indices'])}")
    
    # 找出可能的偏离范围
    if len(analysis_result['large_diff_indices']) > 0:
        print("\n4. 可能的偏离范围:")
        # 分析大差异集中的区域
        diff_positions = np.array(analysis_result['large_diff_indices'])
        if len(diff_positions) > 0:
            # 计算差异位置的聚类
            clusters = []
            current_cluster = [diff_positions[0]]
            
            for pos in diff_positions[1:]:
                if pos - current_cluster[-1] < 1000:  # 1000个数据点内视为同一聚类
                    current_cluster.append(pos)
                else:
                    clusters.append(current_cluster)
                    current_cluster = [pos]
            if current_cluster:
                clusters.append(current_cluster)
            
            # 分析每个聚类对应的齿范围
            for i, cluster in enumerate(clusters):
                cluster_start = min(cluster)
                cluster_end = max(cluster)
                
                # 找到对应的齿范围
                start_tooth_idx = 0
                end_tooth_idx = len(analysis_result['tooth_boundaries']) - 1
                
                for j, boundary in enumerate(analysis_result['tooth_boundaries']):
                    if boundary > cluster_start:
                        start_tooth_idx = j - 1
                        break
                
                for j, boundary in enumerate(analysis_result['tooth_boundaries']):
                    if boundary > cluster_end:
                        end_tooth_idx = j - 1
                        break
                
                start_tooth = analysis_result['sorted_tooth_ids'][max(0, start_tooth_idx)]
                end_tooth = analysis_result['sorted_tooth_ids'][min(len(analysis_result['sorted_tooth_ids']) - 1, end_tooth_idx)]
                
                print(f"  聚类 {i+1}: 数据位置 {cluster_start}~{cluster_end}, 对应齿 {start_tooth}~{end_tooth}")


if __name__ == '__main__':
    main()
