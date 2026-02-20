"""
================================================================================
齿轮波纹度分析 Web 应用 V2 - 增加专业报告可视化
Gear Waviness Analysis Web App V2 - Professional Report Visualization
================================================================================

使用 Streamlit 构建
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import sys
import os

# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ripple_waviness_analyzer import RippleWavinessAnalyzer

# 页面配置
st.set_page_config(
    page_title="齿轮波纹度分析系统 V2",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("⚙️ 齿轮波纹度分析系统 V2")
st.markdown("---")

# 侧边栏
with st.sidebar:
    st.header("📁 数据上传")
    uploaded_file = st.file_uploader(
        "上传 MKA 文件",
        type=['mka'],
        help="支持 Klingelnberg MKA 格式的齿轮测量数据文件"
    )
    
    st.markdown("---")
    st.header("⚙️ 分析设置")
    
    analysis_type = st.multiselect(
        "选择分析类型",
        ['左齿形', '右齿形', '左齿向', '右齿向'],
        default=['右齿形', '右齿向']
    )
    
    st.markdown("---")
    st.header("📊 可视化选项")
    
    show_single_tooth = st.checkbox("显示单齿曲线", value=True)
    show_merged_curve = st.checkbox("显示合并曲线", value=True)
    show_spectrum = st.checkbox("显示频谱分析", value=True)
    
    selected_tooth = st.number_input(
        "选择齿号",
        min_value=1,
        max_value=87,
        value=1
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
        
        # 显示齿轮参数
        st.subheader("📊 齿轮参数")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("齿数 ZE", analyzer.gear_params.teeth_count)
        with col2:
            st.metric("模数 m", f"{analyzer.gear_params.module} mm")
        with col3:
            st.metric("压力角 α", f"{analyzer.gear_params.pressure_angle}°")
        with col4:
            st.metric("螺旋角 β", f"{analyzer.gear_params.helix_angle}°")
        with col5:
            st.metric("节圆直径", f"{analyzer.gear_params.pitch_diameter:.2f} mm")
        with col6:
            st.metric("节距角", f"{analyzer.gear_params.pitch_angle:.4f}°")
        
        st.markdown("---")
        
        # 执行分析
        results = {}
        if '左齿形' in analysis_type:
            results['profile_left'] = analyzer.analyze_profile('left', verbose=False)
        if '右齿形' in analysis_type:
            results['profile_right'] = analyzer.analyze_profile('right', verbose=False)
        if '左齿向' in analysis_type:
            results['helix_left'] = analyzer.analyze_helix('left', verbose=False)
        if '右齿向' in analysis_type:
            results['helix_right'] = analyzer.analyze_helix('right', verbose=False)
    
    # 显示单齿曲线
    if show_single_tooth:
        st.subheader(f"📈 单齿曲线 - 齿号 {selected_tooth}")
        
        # 获取原始数据
        profile_data = analyzer.reader.profile_data
        helix_data = analyzer.reader.helix_data
        
        cols = st.columns(2)
        col_idx = 0
        
        # 齿形曲线
        for side in ['left', 'right']:
            side_name = '左' if side == 'left' else '右'
            
            if f'profile_{side}' in results and selected_tooth in profile_data.get(side, {}):
                with cols[col_idx % 2]:
                    st.markdown(f"**{side_name}齿形 - 齿号 {selected_tooth}**")
                    
                    # 获取数据
                    tooth_profiles = profile_data[side][selected_tooth]
                    
                    # 选择最接近中间的z位置
                    helix_eval = analyzer.reader.helix_eval_range
                    helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                    best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                    values = tooth_profiles[best_z]
                    
                    # 绘制曲线
                    fig, ax = plt.subplots(figsize=(10, 5))
                    
                    x_data = np.linspace(0, len(values)-1, len(values))
                    ax.plot(x_data, values, 'b-', linewidth=1.0, label='原始数据')
                    
                    # 添加评价范围标记
                    profile_eval = analyzer.reader.profile_eval_range
                    n_points = len(values)
                    
                    # 计算评价范围在数据中的位置
                    s_d1 = np.sqrt((profile_eval.eval_start/2)**2 - (analyzer.gear_params.base_diameter/2)**2)
                    s_d2 = np.sqrt((profile_eval.eval_end/2)**2 - (analyzer.gear_params.base_diameter/2)**2)
                    s_da = np.sqrt((profile_eval.meas_start/2)**2 - (analyzer.gear_params.base_diameter/2)**2)
                    s_de = np.sqrt((profile_eval.meas_end/2)**2 - (analyzer.gear_params.base_diameter/2)**2)
                    
                    if s_de > s_da:
                        idx_start = int((s_d1 - s_da) / (s_de - s_da) * n_points)
                        idx_end = int((s_d2 - s_da) / (s_de - s_da) * n_points)
                        
                        # 绘制评价范围
                        eval_x = x_data[idx_start:idx_end]
                        eval_y = values[idx_start:idx_end]
                        ax.plot(eval_x, eval_y, 'r-', linewidth=2, label='评价范围')
                        
                        # 添加标记线
                        ax.axvline(x=idx_start, color='green', linestyle='--', alpha=0.7, label='起评点')
                        ax.axvline(x=idx_end, color='green', linestyle='--', alpha=0.7, label='终评点')
                    
                    ax.set_title(f"{side_name}齿形偏差 - z={best_z}mm", fontsize=12)
                    ax.set_xlabel("数据点索引")
                    ax.set_ylabel("偏差 (μm)")
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    
                    st.pyplot(fig)
                
                col_idx += 1
        
        # 齿向曲线
        for side in ['left', 'right']:
            side_name = '左' if side == 'left' else '右'
            
            if f'helix_{side}' in results and selected_tooth in helix_data.get(side, {}):
                with cols[col_idx % 2]:
                    st.markdown(f"**{side_name}齿向 - 齿号 {selected_tooth}**")
                    
                    # 获取数据
                    tooth_helices = helix_data[side][selected_tooth]
                    
                    # 选择评价范围内的d位置
                    profile_eval = analyzer.reader.profile_eval_range
                    best_d = None
                    best_values = None
                    
                    for d_pos, values in tooth_helices.items():
                        if profile_eval.eval_start <= d_pos <= profile_eval.eval_end:
                            if best_d is None or abs(d_pos - (profile_eval.eval_start + profile_eval.eval_end)/2) < abs(best_d - (profile_eval.eval_start + profile_eval.eval_end)/2):
                                best_d = d_pos
                                best_values = values
                    
                    if best_values is not None:
                        # 绘制曲线
                        fig, ax = plt.subplots(figsize=(10, 5))
                        
                        x_data = np.linspace(0, len(best_values)-1, len(best_values))
                        ax.plot(x_data, best_values, 'b-', linewidth=1.0, label='原始数据')
                        
                        # 添加评价范围标记
                        helix_eval = analyzer.reader.helix_eval_range
                        n_points = len(best_values)
                        
                        idx_start = int((helix_eval.eval_start - helix_eval.meas_start) / 
                                      (helix_eval.meas_end - helix_eval.meas_start) * n_points)
                        idx_end = int((helix_eval.eval_end - helix_eval.meas_start) / 
                                    (helix_eval.meas_end - helix_eval.meas_start) * n_points)
                        
                        # 绘制评价范围
                        eval_x = x_data[idx_start:idx_end]
                        eval_y = best_values[idx_start:idx_end]
                        ax.plot(eval_x, eval_y, 'r-', linewidth=2, label='评价范围')
                        
                        # 添加标记线
                        ax.axvline(x=idx_start, color='green', linestyle='--', alpha=0.7, label='起评点')
                        ax.axvline(x=idx_end, color='green', linestyle='--', alpha=0.7, label='终评点')
                        
                        ax.set_title(f"{side_name}齿向偏差 - d={best_d:.2f}mm", fontsize=12)
                        ax.set_xlabel("数据点索引")
                        ax.set_ylabel("偏差 (μm)")
                        ax.legend()
                        ax.grid(True, alpha=0.3)
                        
                        st.pyplot(fig)
                
                col_idx += 1
    
    # 显示合并曲线和频谱分析
    if show_merged_curve or show_spectrum:
        st.markdown("---")
        st.subheader("📊 合并曲线与频谱分析")
        
        for name, result in results.items():
            if result is None:
                continue
            
            with st.expander(f"📈 {name}", expanded=True):
                # 统计信息
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("高阶总振幅 W", f"{result.high_order_amplitude:.3f} μm")
                with col2:
                    st.metric("RMS", f"{result.high_order_rms:.3f} μm")
                with col3:
                    st.metric("高阶波数", len(result.high_order_waves))
                with col4:
                    max_order = result.spectrum_components[0].order
                    st.metric("主导阶次", max_order)
                
                # 合并曲线图
                if show_merged_curve:
                    st.markdown("**合并曲线 (0-360°)**")
                    fig, ax = plt.subplots(figsize=(12, 4))
                    ax.plot(result.angles, result.values, 'b-', linewidth=0.5, alpha=0.7, label='原始曲线')
                    ax.plot(result.angles, result.reconstructed_signal, 'r-', linewidth=1.5, label='高阶重构')
                    ax.set_xlabel('旋转角度 (deg)')
                    ax.set_ylabel('偏差 (μm)')
                    ax.set_title(f'{name} - 合并曲线')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    ax.set_xlim(0, 360)
                    st.pyplot(fig)
                
                # 频谱图
                if show_spectrum:
                    st.markdown("**频谱分析**")
                    
                    # 频谱表格
                    spectrum_data = []
                    for i, comp in enumerate(result.spectrum_components[:10]):
                        spectrum_data.append({
                            '排名': i + 1,
                            '阶次': comp.order,
                            '振幅 (μm)': f"{comp.amplitude:.4f}",
                            '相位 (°)': f"{np.degrees(comp.phase):.1f}",
                            '类型': '高阶' if comp.order >= analyzer.gear_params.teeth_count else '低阶'
                        })
                    st.table(spectrum_data)
                    
                    # 频谱柱状图
                    fig2, ax2 = plt.subplots(figsize=(12, 4))
                    orders = [c.order for c in result.spectrum_components[:20]]
                    amplitudes = [c.amplitude for c in result.spectrum_components[:20]]
                    colors_bar = ['red' if o >= analyzer.gear_params.teeth_count else 'blue' for o in orders]
                    ax2.bar(range(len(orders)), amplitudes, color=colors_bar, alpha=0.7)
                    ax2.axvline(x=analyzer.gear_params.teeth_count - 0.5, color='green', linestyle='--', 
                               label=f'ZE={analyzer.gear_params.teeth_count}')
                    ax2.set_xlabel('Order Rank')
                    ax2.set_ylabel('Amplitude (μm)')
                    ax2.set_title(f'{name} - Spectrum')
                    ax2.legend()
                    ax2.grid(True, alpha=0.3)
                    st.pyplot(fig2)
    
    # 清理临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
else:
    # 显示说明
    st.info("👆 请在左侧上传 MKA 文件开始分析")
    
    st.markdown("""
    ### 📋 使用说明
    
    1. **上传文件**：在左侧上传 Klingelnberg MKA 格式的齿轮测量数据文件
    2. **选择分析类型**：选择要分析的齿形/齿向方向
    3. **选择齿号**：输入要查看的齿号（1-87）
    4. **查看结果**：
       - 单齿曲线：显示单个齿的偏差曲线和评价范围
       - 合并曲线：显示0-360°的合并曲线
       - 频谱分析：显示各阶次振幅和相位
    
    ### 📊 分析内容
    
    - **单齿曲线**：包含评价范围标记（红色）和起评/终评点（绿色虚线）
    - **高阶波纹度**：阶次 ≥ 齿数 ZE 的波纹度分量
    - **频谱分析**：迭代分解法提取各阶次振幅和相位
    
    ### 🔧 技术参数
    
    - 预处理：去除鼓形（二次多项式）和斜率（线性）
    - 频谱方法：迭代最小二乘分解
    - 评价标准：Klingelnberg P 系列标准
    """)

# 页脚
st.markdown("---")
st.caption("齿轮波纹度分析系统 V2 | 基于 Python + Streamlit 构建")
