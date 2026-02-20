"""
================================================================================
齿轮周节详细报表 Web 应用
Gear Pitch Detailed Report Web App
================================================================================

功能：
- 周节偏差分析 (fp, Fp, Fr)
- 齿到齿周节偏差图表
- 累积周节偏差图表
- 径向跳动图表
- 详细数据表格
- 仿Klingelnberg标准报告格式
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import sys
import os
from datetime import datetime

# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ripple_waviness_analyzer import RippleWavinessAnalyzer

# 页面配置
st.set_page_config(
    page_title="齿轮周节详细报表系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f2f6, #e6e9ef);
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.3rem;
        color: #333;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
        margin-top: 1rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
    .data-table {
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<div class="main-header">📊 齿轮周节详细报表系统</div>', unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.header("📁 数据上传")
    uploaded_file = st.file_uploader(
        "上传 MKA 文件",
        type=['mka'],
        help="支持 Klingelnberg MKA 格式的齿轮测量数据文件"
    )

    if uploaded_file is not None:
        st.success(f"已加载: {uploaded_file.name}")

    st.markdown("---")
    st.header("📋 功能导航")

    page = st.radio(
        "选择功能页面",
        ['📄 周节总览', '📈 齿到齿周节偏差 fp', '📉 累积周节偏差 Fp', '🔴 径向跳动 Fr', '📊 详细数据表'],
        index=0
    )

# 主界面
if uploaded_file is not None:
    # 保存上传的文件
    temp_path = os.path.join(os.path.dirname(__file__), "temp.mka")
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getvalue())

    # 分析
    with st.spinner("正在分析数据..."):
        analyzer = RippleWavinessAnalyzer(temp_path)
        analyzer.load_file()

        # 执行周节分析
        pitch_left = analyzer.analyze_pitch('left')
        pitch_right = analyzer.analyze_pitch('right')

    # 获取齿轮参数
    gear_params = analyzer.gear_params

    # 页面1: 周节总览
    if page == '📄 周节总览':
        st.markdown('<div class="section-header">📄 Gear Spacing Report - 周节偏差总览</div>', unsafe_allow_html=True)

        # 基本信息表格
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**基本信息**")
            header_data1 = {
                '参数': ['Prog.No.', 'Type', 'Drawing No.', 'Order No.', 'Operator', 'Date'],
                '值': [uploaded_file.name, 'gear', uploaded_file.name, '-', 'Operator', datetime.now().strftime('%d.%m.%y')]
            }
            st.table(header_data1)

        with col2:
            st.markdown("**齿轮参数**")
            if gear_params:
                header_data2 = {
                    '参数': ['No. of teeth', 'Module m', 'Pressure angle', 'Helix angle', 'Pitch diameter', 'Base diameter'],
                    '值': [
                        str(gear_params.teeth_count),
                        f"{gear_params.module:.3f}mm",
                        f"{gear_params.pressure_angle}°",
                        f"{gear_params.helix_angle}°",
                        f"{gear_params.pitch_diameter:.3f}mm",
                        f"{gear_params.base_diameter:.3f}mm"
                    ]
                }
                st.table(header_data2)

        st.markdown("---")
        st.markdown('<div class="section-header">📊 周节偏差统计</div>', unsafe_allow_html=True)

        # 统计卡片
        cols = st.columns(4)

        # 左齿面统计
        if pitch_left:
            with cols[0]:
                st.metric("左齿面 fp max", f"{pitch_left.fp_max:.2f} μm")
            with cols[1]:
                st.metric("左齿面 Fp max", f"{pitch_left.Fp_max:.2f} μm")
            with cols[2]:
                st.metric("左齿面 Fp min", f"{pitch_left.Fp_min:.2f} μm")
            with cols[3]:
                st.metric("左齿面 Fr", f"{pitch_left.Fr:.2f} μm")

        # 右齿面统计
        if pitch_right:
            st.markdown("---")
            cols2 = st.columns(4)
            with cols2[0]:
                st.metric("右齿面 fp max", f"{pitch_right.fp_max:.2f} μm")
            with cols2[1]:
                st.metric("右齿面 Fp max", f"{pitch_right.Fp_max:.2f} μm")
            with cols2[2]:
                st.metric("右齿面 Fp min", f"{pitch_right.Fp_min:.2f} μm")
            with cols2[3]:
                st.metric("右齿面 Fr", f"{pitch_right.Fr:.2f} μm")

        st.markdown("---")
        st.markdown('<div class="section-header">📈 快速预览</div>', unsafe_allow_html=True)

        # 快速预览图表
        if pitch_left or pitch_right:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))

            # 左齿面 fp
            if pitch_left:
                axes[0, 0].bar(pitch_left.teeth, pitch_left.fp_values, color='steelblue', alpha=0.7)
                axes[0, 0].axhline(y=0, color='red', linestyle='--', linewidth=1)
                axes[0, 0].set_title('Tooth to tooth spacing fp left flank', fontsize=11, fontweight='bold')
                axes[0, 0].set_xlabel('Tooth Number')
                axes[0, 0].set_ylabel('fp (μm)')
                axes[0, 0].grid(True, alpha=0.3)

                # 左齿面 Fp
                axes[0, 1].plot(pitch_left.teeth, pitch_left.Fp_values, 'b-', linewidth=1.5, marker='o', markersize=3)
                axes[0, 1].axhline(y=0, color='red', linestyle='--', linewidth=1)
                axes[0, 1].set_title('Index Fp left flank', fontsize=11, fontweight='bold')
                axes[0, 1].set_xlabel('Tooth Number')
                axes[0, 1].set_ylabel('Fp (μm)')
                axes[0, 1].grid(True, alpha=0.3)

            # 右齿面 fp
            if pitch_right:
                axes[1, 0].bar(pitch_right.teeth, pitch_right.fp_values, color='coral', alpha=0.7)
                axes[1, 0].axhline(y=0, color='red', linestyle='--', linewidth=1)
                axes[1, 0].set_title('Tooth to tooth spacing fp right flank', fontsize=11, fontweight='bold')
                axes[1, 0].set_xlabel('Tooth Number')
                axes[1, 0].set_ylabel('fp (μm)')
                axes[1, 0].grid(True, alpha=0.3)

                # 右齿面 Fp
                axes[1, 1].plot(pitch_right.teeth, pitch_right.Fp_values, 'r-', linewidth=1.5, marker='o', markersize=3)
                axes[1, 1].axhline(y=0, color='blue', linestyle='--', linewidth=1)
                axes[1, 1].set_title('Index Fp right flank', fontsize=11, fontweight='bold')
                axes[1, 1].set_xlabel('Tooth Number')
                axes[1, 1].set_ylabel('Fp (μm)')
                axes[1, 1].grid(True, alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig)

    # 页面2: 齿到齿周节偏差 fp
    elif page == '📈 齿到齿周节偏差 fp':
        st.markdown('<div class="section-header">📈 Tooth to Tooth Spacing Deviation (fp)</div>', unsafe_allow_html=True)

        if pitch_left or pitch_right:
            fig, axes = plt.subplots(2, 1, figsize=(14, 10))

            # 左齿面
            if pitch_left:
                teeth = pitch_left.teeth
                fp_values = pitch_left.fp_values

                # 绘制柱状图
                bars = axes[0].bar(teeth, fp_values, color='steelblue', alpha=0.7, edgecolor='black', linewidth=0.5)
                axes[0].axhline(y=0, color='red', linestyle='-', linewidth=1.5)

                # 标记最大值和最小值
                fp_max_idx = fp_values.index(max(fp_values))
                fp_min_idx = fp_values.index(min(fp_values))
                axes[0].plot(teeth[fp_max_idx], fp_values[fp_max_idx], 'ro', markersize=10, label=f'Max: {fp_values[fp_max_idx]:.2f}')
                axes[0].plot(teeth[fp_min_idx], fp_values[fp_min_idx], 'go', markersize=10, label=f'Min: {fp_values[fp_min_idx]:.2f}')

                axes[0].set_title('Tooth to tooth spacing fp left flank', fontsize=14, fontweight='bold')
                axes[0].set_xlabel('Tooth Number', fontsize=12)
                axes[0].set_ylabel('fp (μm)', fontsize=12)
                axes[0].legend()
                axes[0].grid(True, alpha=0.3, axis='y')

            # 右齿面
            if pitch_right:
                teeth = pitch_right.teeth
                fp_values = pitch_right.fp_values

                bars = axes[1].bar(teeth, fp_values, color='coral', alpha=0.7, edgecolor='black', linewidth=0.5)
                axes[1].axhline(y=0, color='red', linestyle='-', linewidth=1.5)

                fp_max_idx = fp_values.index(max(fp_values))
                fp_min_idx = fp_values.index(min(fp_values))
                axes[1].plot(teeth[fp_max_idx], fp_values[fp_max_idx], 'ro', markersize=10, label=f'Max: {fp_values[fp_max_idx]:.2f}')
                axes[1].plot(teeth[fp_min_idx], fp_values[fp_min_idx], 'go', markersize=10, label=f'Min: {fp_values[fp_min_idx]:.2f}')

                axes[1].set_title('Tooth to tooth spacing fp right flank', fontsize=14, fontweight='bold')
                axes[1].set_xlabel('Tooth Number', fontsize=12)
                axes[1].set_ylabel('fp (μm)', fontsize=12)
                axes[1].legend()
                axes[1].grid(True, alpha=0.3, axis='y')

            plt.tight_layout()
            st.pyplot(fig)

            # 显示统计信息
            st.markdown("**统计信息**")
            stats_data = []
            if pitch_left:
                stats_data.append({
                    '齿面': '左齿面',
                    'fp max (μm)': f"{pitch_left.fp_max:.2f}",
                    'fp min (μm)': f"{pitch_left.fp_min:.2f}",
                    'fp avg (μm)': f"{pitch_left.fp_avg:.2f}",
                    'fp range (μm)': f"{pitch_left.fp_max - pitch_left.fp_min:.2f}"
                })
            if pitch_right:
                stats_data.append({
                    '齿面': '右齿面',
                    'fp max (μm)': f"{pitch_right.fp_max:.2f}",
                    'fp min (μm)': f"{pitch_right.fp_min:.2f}",
                    'fp avg (μm)': f"{pitch_right.fp_avg:.2f}",
                    'fp range (μm)': f"{pitch_right.fp_max - pitch_right.fp_min:.2f}"
                })
            st.table(stats_data)
        else:
            st.warning("没有可用的周节数据")

    # 页面3: 累积周节偏差 Fp
    elif page == '📉 累积周节偏差 Fp':
        st.markdown('<div class="section-header">📉 Cumulative Pitch Deviation (Fp)</div>', unsafe_allow_html=True)

        if pitch_left or pitch_right:
            fig, axes = plt.subplots(2, 1, figsize=(14, 10))

            # 左齿面
            if pitch_left:
                teeth = pitch_left.teeth
                Fp_values = pitch_left.Fp_values

                axes[0].plot(teeth, Fp_values, 'b-', linewidth=2, marker='o', markersize=4)
                axes[0].axhline(y=0, color='red', linestyle='--', linewidth=1)

                # 填充区域
                axes[0].fill_between(teeth, Fp_values, alpha=0.3, color='steelblue')

                # 标记最大最小值
                Fp_max_idx = Fp_values.index(max(Fp_values))
                Fp_min_idx = Fp_values.index(min(Fp_values))
                axes[0].plot(teeth[Fp_max_idx], Fp_values[Fp_max_idx], 'ro', markersize=10, label=f'Max: {Fp_values[Fp_max_idx]:.2f}')
                axes[0].plot(teeth[Fp_min_idx], Fp_values[Fp_min_idx], 'go', markersize=10, label=f'Min: {Fp_values[Fp_min_idx]:.2f}')

                axes[0].set_title('Index Fp left flank', fontsize=14, fontweight='bold')
                axes[0].set_xlabel('Tooth Number', fontsize=12)
                axes[0].set_ylabel('Fp (μm)', fontsize=12)
                axes[0].legend()
                axes[0].grid(True, alpha=0.3)

            # 右齿面
            if pitch_right:
                teeth = pitch_right.teeth
                Fp_values = pitch_right.Fp_values

                axes[1].plot(teeth, Fp_values, 'r-', linewidth=2, marker='o', markersize=4)
                axes[1].axhline(y=0, color='blue', linestyle='--', linewidth=1)

                axes[1].fill_between(teeth, Fp_values, alpha=0.3, color='coral')

                Fp_max_idx = Fp_values.index(max(Fp_values))
                Fp_min_idx = Fp_values.index(min(Fp_values))
                axes[1].plot(teeth[Fp_max_idx], Fp_values[Fp_max_idx], 'ro', markersize=10, label=f'Max: {Fp_values[Fp_max_idx]:.2f}')
                axes[1].plot(teeth[Fp_min_idx], Fp_values[Fp_min_idx], 'go', markersize=10, label=f'Min: {Fp_values[Fp_min_idx]:.2f}')

                axes[1].set_title('Index Fp right flank', fontsize=14, fontweight='bold')
                axes[1].set_xlabel('Tooth Number', fontsize=12)
                axes[1].set_ylabel('Fp (μm)', fontsize=12)
                axes[1].legend()
                axes[1].grid(True, alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig)

            # 显示统计信息
            st.markdown("**统计信息**")
            stats_data = []
            if pitch_left:
                stats_data.append({
                    '齿面': '左齿面',
                    'Fp max (μm)': f"{pitch_left.Fp_max:.2f}",
                    'Fp min (μm)': f"{pitch_left.Fp_min:.2f}",
                    'Fp avg (μm)': f"{pitch_left.Fp_avg:.2f}",
                    'Fr (μm)': f"{pitch_left.Fr:.2f}"
                })
            if pitch_right:
                stats_data.append({
                    '齿面': '右齿面',
                    'Fp max (μm)': f"{pitch_right.Fp_max:.2f}",
                    'Fp min (μm)': f"{pitch_right.Fp_min:.2f}",
                    'Fp avg (μm)': f"{pitch_right.Fp_avg:.2f}",
                    'Fr (μm)': f"{pitch_right.Fr:.2f}"
                })
            st.table(stats_data)
        else:
            st.warning("没有可用的周节数据")

    # 页面4: 径向跳动 Fr
    elif page == '🔴 径向跳动 Fr':
        st.markdown('<div class="section-header">🔴 Runout (Fr)</div>', unsafe_allow_html=True)

        if pitch_left or pitch_right:
            fig, ax = plt.subplots(figsize=(14, 6))

            # 合并左右齿面的Fr数据
            all_teeth = []
            all_Fp = []
            all_sides = []

            if pitch_left:
                all_teeth.extend(pitch_left.teeth)
                all_Fp.extend(pitch_left.Fp_values)
                all_sides.extend(['Left'] * len(pitch_left.teeth))

            if pitch_right:
                all_teeth.extend(pitch_right.teeth)
                all_Fp.extend(pitch_right.Fp_values)
                all_sides.extend(['Right'] * len(pitch_right.teeth))

            # 按齿号排序
            sorted_data = sorted(zip(all_teeth, all_Fp, all_sides))
            all_teeth = [x[0] for x in sorted_data]
            all_Fp = [x[1] for x in sorted_data]

            # 绘制径向跳动图
            ax.bar(all_teeth, all_Fp, color='steelblue', alpha=0.7, edgecolor='black', linewidth=0.5)

            # 添加拟合曲线（正弦拟合）
            if len(all_teeth) > 3:
                x_smooth = np.linspace(min(all_teeth), max(all_teeth), 200)
                # 使用多项式拟合
                coeffs = np.polyfit(all_teeth, all_Fp, 3)
                y_smooth = np.polyval(coeffs, x_smooth)
                ax.plot(x_smooth, y_smooth, 'r-', linewidth=2, label='Trend Line')

            ax.axhline(y=0, color='green', linestyle='--', linewidth=1.5)
            ax.set_title('Runout Fr (Ball-Ø = 3mm)', fontsize=14, fontweight='bold')
            ax.set_xlabel('Tooth Number', fontsize=12)
            ax.set_ylabel('Fr (μm)', fontsize=12)
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig)

            # 显示Fr统计
            st.markdown("**径向跳动统计**")
            fr_data = []
            if pitch_left:
                fr_data.append({
                    '齿面': '左齿面',
                    'Fr (μm)': f"{pitch_left.Fr:.2f}",
                    'Fp Max (μm)': f"{pitch_left.Fp_max:.2f}",
                    'Fp Min (μm)': f"{pitch_left.Fp_min:.2f}"
                })
            if pitch_right:
                fr_data.append({
                    '齿面': '右齿面',
                    'Fr (μm)': f"{pitch_right.Fr:.2f}",
                    'Fp Max (μm)': f"{pitch_right.Fp_max:.2f}",
                    'Fp Min (μm)': f"{pitch_right.Fp_min:.2f}"
                })
            st.table(fr_data)
        else:
            st.warning("没有可用的周节数据")

    # 页面5: 详细数据表
    elif page == '📊 详细数据表':
        st.markdown('<div class="section-header">📊 Pitch Measuring Circle - 详细数据表</div>', unsafe_allow_html=True)

        # 创建详细数据表格
        if pitch_left or pitch_right:
            # 准备数据
            table_data = []

            # 获取所有齿号
            all_teeth = set()
            if pitch_left:
                all_teeth.update(pitch_left.teeth)
            if pitch_right:
                all_teeth.update(pitch_right.teeth)

            # 为每个齿创建一行数据
            for tooth in sorted(all_teeth):
                row = {'齿号': tooth}

                if pitch_left and tooth in pitch_left.teeth:
                    idx = pitch_left.teeth.index(tooth)
                    row['左 fp (μm)'] = f"{pitch_left.fp_values[idx]:.2f}"
                    row['左 Fp (μm)'] = f"{pitch_left.Fp_values[idx]:.2f}"
                else:
                    row['左 fp (μm)'] = '-'
                    row['左 Fp (μm)'] = '-'

                if pitch_right and tooth in pitch_right.teeth:
                    idx = pitch_right.teeth.index(tooth)
                    row['右 fp (μm)'] = f"{pitch_right.fp_values[idx]:.2f}"
                    row['右 Fp (μm)'] = f"{pitch_right.Fp_values[idx]:.2f}"
                else:
                    row['右 fp (μm)'] = '-'
                    row['右 Fp (μm)'] = '-'

                table_data.append(row)

            st.table(table_data)

            # 统计汇总表
            st.markdown("---")
            st.markdown('<div class="section-header">📋 统计汇总</div>', unsafe_allow_html=True)

            summary_data = []
            if pitch_left:
                summary_data.append({
                    '参数': 'Worst single pitch deviation fp max',
                    '左齿面 Act.value': f"{pitch_left.fp_max:.2f}",
                    '左齿面 Qual.': '-',
                    '右齿面 Act.value': f"{pitch_right.fp_max:.2f}" if pitch_right else '-',
                    '右齿面 Qual.': '-'
                })
                summary_data.append({
                    '参数': 'Worst spacing deviation fu max',
                    '左齿面 Act.value': f"{abs(pitch_left.fp_max - pitch_left.fp_min):.2f}",
                    '左齿面 Qual.': '-',
                    '右齿面 Act.value': f"{abs(pitch_right.fp_max - pitch_right.fp_min):.2f}" if pitch_right else '-',
                    '右齿面 Qual.': '-'
                })
                summary_data.append({
                    '参数': 'Range of Pitch Error Rp',
                    '左齿面 Act.value': f"{pitch_left.Fp_max - pitch_left.Fp_min:.2f}",
                    '左齿面 Qual.': '-',
                    '右齿面 Act.value': f"{pitch_right.Fp_max - pitch_right.Fp_min:.2f}" if pitch_right else '-',
                    '右齿面 Qual.': '-'
                })
                summary_data.append({
                    '参数': 'Total cum. pitch dev. Fp',
                    '左齿面 Act.value': f"{pitch_left.Fp_max:.2f}",
                    '左齿面 Qual.': '-',
                    '右齿面 Act.value': f"{pitch_right.Fp_max:.2f}" if pitch_right else '-',
                    '右齿面 Qual.': '-'
                })
                summary_data.append({
                    '参数': 'Cum. pitch deviation Fp10',
                    '左齿面 Act.value': f"{pitch_left.Fp_avg:.2f}",
                    '左齿面 Qual.': '-',
                    '右齿面 Act.value': f"{pitch_right.Fp_avg:.2f}" if pitch_right else '-',
                    '右齿面 Qual.': '-'
                })

            st.table(summary_data)

            # 导出按钮
            st.markdown("---")
            if st.button("导出数据为 CSV"):
                import pandas as pd
                df = pd.DataFrame(table_data)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="下载 CSV 文件",
                    data=csv,
                    file_name=f"pitch_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        else:
            st.warning("没有可用的周节数据")

    # 清理临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)

else:
    # 显示说明
    st.info("👆 请在左侧上传 MKA 文件开始分析")

    st.markdown("""
    ### 📋 功能说明

    本系统提供完整的齿轮周节偏差分析功能：

    | 功能 | 说明 |
    |------|------|
    | 📄 周节总览 | 显示周节偏差统计信息和快速预览 |
    | 📈 齿到齿周节偏差 fp | 显示每个齿的fp值柱状图 |
    | 📉 累积周节偏差 Fp | 显示累积周节偏差曲线 |
    | 🔴 径向跳动 Fr | 显示径向跳动分析 |
    | 📊 详细数据表 | 显示完整的周节数据表格 |

    ### 🔧 技术参数

    - **fp**: 单齿周节偏差 (Tooth-to-tooth spacing deviation)
    - **Fp**: 累积周节偏差 (Cumulative pitch deviation)
    - **Fr**: 径向跳动 (Runout)
    - **评价标准**: Klingelnberg P 系列标准
    """)

# 页脚
st.markdown("---")
st.caption("齿轮周节详细报表系统 | 基于 Python + Streamlit 构建")
