"""
================================================================================
齿轮测量报告 Web 应用 - 完整版
Gear Measurement Report Web App - Full Version
================================================================================

包含完整功能：
- 齿轮参数显示
- 齿形/齿向偏差分析
- 单齿曲线可视化
- 合并曲线与频谱分析
- 3D表面图
- 报告导出
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from mpl_toolkits.mplot3d import Axes3D
import sys
import os
import io
import base64
from datetime import datetime

# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ripple_waviness_analyzer import RippleWavinessAnalyzer

# 页面配置
st.set_page_config(
    page_title="齿轮测量报告系统",
    page_icon="⚙️",
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
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
    .section-header {
        font-size: 1.3rem;
        color: #333;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<div class="main-header">⚙️ 齿轮测量报告系统</div>', unsafe_allow_html=True)

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
        ['📊 齿轮参数', '📈 单齿分析', '📉 合并曲线', '📊 频谱分析', 
         '🌐 3D表面图', '📄 报告导出'],
        index=0
    )
    
    st.markdown("---")
    st.header("⚙️ 分析设置")
    
    analysis_type = st.multiselect(
        "选择分析类型",
        ['左齿形', '右齿形', '左齿向', '右齿向'],
        default=['右齿形', '右齿向']
    )
    
    selected_tooth = st.number_input(
        "选择齿号",
        min_value=1,
        max_value=200,
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
    
    # 页面1: 齿轮参数
    if page == '📊 齿轮参数':
        st.markdown('<div class="section-header">📊 齿轮参数</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("齿数 ZE", analyzer.gear_params.teeth_count)
            st.metric("模数 m", f"{analyzer.gear_params.module} mm")
        with col2:
            st.metric("压力角 α", f"{analyzer.gear_params.pressure_angle}°")
            st.metric("螺旋角 β", f"{analyzer.gear_params.helix_angle}°")
        with col3:
            st.metric("节圆直径", f"{analyzer.gear_params.pitch_diameter:.2f} mm")
            st.metric("基圆直径", f"{analyzer.gear_params.base_diameter:.2f} mm")
        
        st.markdown("---")
        st.markdown('<div class="section-header">📏 评价范围</div>', unsafe_allow_html=True)
        
        profile_eval = analyzer.reader.profile_eval_range
        helix_eval = analyzer.reader.helix_eval_range
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**齿形评价范围**")
            st.write(f"- 起评点 d1: {profile_eval.eval_start} mm")
            st.write(f"- 终评点 d2: {profile_eval.eval_end} mm")
            st.write(f"- 测量起点 da: {profile_eval.meas_start} mm")
            st.write(f"- 测量终点 de: {profile_eval.meas_end} mm")
        
        with col2:
            st.markdown("**齿向评价范围**")
            st.write(f"- 起评点 b1: {helix_eval.eval_start} mm")
            st.write(f"- 终评点 b2: {helix_eval.eval_end} mm")
            st.write(f"- 测量起点 ba: {helix_eval.meas_start} mm")
            st.write(f"- 测量终点 be: {helix_eval.meas_end} mm")
    
    # 页面2: 单齿分析
    elif page == '📈 单齿分析':
        st.markdown(f'<div class="section-header">📈 单齿分析 - 齿号 {selected_tooth}</div>', unsafe_allow_html=True)
        
        profile_data = analyzer.reader.profile_data
        helix_data = analyzer.reader.helix_data
        
        # 齿形曲线
        st.markdown("**齿形偏差曲线**")
        cols = st.columns(2)
        
        for idx, side in enumerate(['left', 'right']):
            side_name = '左' if side == 'left' else '右'
            
            if selected_tooth in profile_data.get(side, {}):
                with cols[idx]:
                    tooth_profiles = profile_data[side][selected_tooth]
                    helix_eval = analyzer.reader.helix_eval_range
                    helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                    best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                    values = tooth_profiles[best_z]
                    
                    fig, ax = plt.subplots(figsize=(10, 5))
                    x_data = np.linspace(0, len(values)-1, len(values))
                    ax.plot(x_data, values, 'b-', linewidth=1.0, label='原始数据')
                    
                    # 评价范围标记
                    profile_eval = analyzer.reader.profile_eval_range
                    n_points = len(values)
                    s_d1 = np.sqrt((profile_eval.eval_start/2)**2 - (analyzer.gear_params.base_diameter/2)**2)
                    s_d2 = np.sqrt((profile_eval.eval_end/2)**2 - (analyzer.gear_params.base_diameter/2)**2)
                    s_da = np.sqrt((profile_eval.meas_start/2)**2 - (analyzer.gear_params.base_diameter/2)**2)
                    s_de = np.sqrt((profile_eval.meas_end/2)**2 - (analyzer.gear_params.base_diameter/2)**2)
                    
                    if s_de > s_da:
                        idx_start = int((s_d1 - s_da) / (s_de - s_da) * n_points)
                        idx_end = int((s_d2 - s_da) / (s_de - s_da) * n_points)
                        ax.plot(x_data[idx_start:idx_end], values[idx_start:idx_end], 'r-', linewidth=2, label='评价范围')
                        ax.axvline(x=idx_start, color='green', linestyle='--', alpha=0.7, label='起评点')
                        ax.axvline(x=idx_end, color='green', linestyle='--', alpha=0.7, label='终评点')
                    
                    ax.set_title(f"{side_name}齿形偏差 - z={best_z}mm")
                    ax.set_xlabel("数据点索引")
                    ax.set_ylabel("偏差 (μm)")
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
        
        # 齿向曲线
        st.markdown("**齿向偏差曲线**")
        cols = st.columns(2)
        
        for idx, side in enumerate(['left', 'right']):
            side_name = '左' if side == 'left' else '右'
            
            if selected_tooth in helix_data.get(side, {}):
                with cols[idx]:
                    tooth_helices = helix_data[side][selected_tooth]
                    profile_eval = analyzer.reader.profile_eval_range
                    best_d = None
                    best_values = None
                    
                    for d_pos, values in tooth_helices.items():
                        if profile_eval.eval_start <= d_pos <= profile_eval.eval_end:
                            if best_d is None or abs(d_pos - (profile_eval.eval_start + profile_eval.eval_end)/2) < abs(best_d - (profile_eval.eval_start + profile_eval.eval_end)/2):
                                best_d = d_pos
                                best_values = values
                    
                    if best_values is not None:
                        fig, ax = plt.subplots(figsize=(10, 5))
                        x_data = np.linspace(0, len(best_values)-1, len(best_values))
                        ax.plot(x_data, best_values, 'b-', linewidth=1.0, label='原始数据')
                        
                        helix_eval = analyzer.reader.helix_eval_range
                        n_points = len(best_values)
                        idx_start = int((helix_eval.eval_start - helix_eval.meas_start) / (helix_eval.meas_end - helix_eval.meas_start) * n_points)
                        idx_end = int((helix_eval.eval_end - helix_eval.meas_start) / (helix_eval.meas_end - helix_eval.meas_start) * n_points)
                        ax.plot(x_data[idx_start:idx_end], best_values[idx_start:idx_end], 'r-', linewidth=2, label='评价范围')
                        ax.axvline(x=idx_start, color='green', linestyle='--', alpha=0.7, label='起评点')
                        ax.axvline(x=idx_end, color='green', linestyle='--', alpha=0.7, label='终评点')
                        
                        ax.set_title(f"{side_name}齿向偏差 - d={best_d:.2f}mm")
                        ax.set_xlabel("数据点索引")
                        ax.set_ylabel("偏差 (μm)")
                        ax.legend()
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
    
    # 页面3: 合并曲线
    elif page == '📉 合并曲线':
        st.markdown('<div class="section-header">📉 合并曲线 (0-360°)</div>', unsafe_allow_html=True)
        
        for name, result in results.items():
            if result is None:
                continue
            
            with st.expander(f"📈 {name}", expanded=True):
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
                
                fig, ax = plt.subplots(figsize=(14, 5))
                ax.plot(result.angles, result.values, 'b-', linewidth=0.5, alpha=0.7, label='原始曲线')
                ax.plot(result.angles, result.reconstructed_signal, 'r-', linewidth=1.5, label='高阶重构')
                ax.set_xlabel('旋转角度 (deg)')
                ax.set_ylabel('偏差 (μm)')
                ax.set_title(f'{name} - 合并曲线')
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, 360)
                st.pyplot(fig)
    
    # 页面4: 频谱分析
    elif page == '📊 频谱分析':
        st.markdown('<div class="section-header">📊 频谱分析</div>', unsafe_allow_html=True)
        
        for name, result in results.items():
            if result is None:
                continue
            
            with st.expander(f"📈 {name}", expanded=True):
                # 频谱表格
                st.markdown("**频谱分量（前10个）**")
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
                fig, ax = plt.subplots(figsize=(12, 5))
                orders = [c.order for c in result.spectrum_components[:20]]
                amplitudes = [c.amplitude for c in result.spectrum_components[:20]]
                colors_bar = ['red' if o >= analyzer.gear_params.teeth_count else 'blue' for o in orders]
                ax.bar(range(len(orders)), amplitudes, color=colors_bar, alpha=0.7)
                ax.axvline(x=analyzer.gear_params.teeth_count - 0.5, color='green', linestyle='--', 
                           label=f'ZE={analyzer.gear_params.teeth_count}')
                ax.set_xlabel('Order Rank')
                ax.set_ylabel('Amplitude (μm)')
                ax.set_title(f'{name} - Spectrum')
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
    
    # 页面5: 3D表面图
    elif page == '🌐 3D表面图':
        st.markdown('<div class="section-header">🌐 3D表面图</div>', unsafe_allow_html=True)
        
        side = st.selectbox("选择齿面", ['left', 'right'], index=1)
        side_name = '左' if side == 'left' else '右'
        
        profile_data = analyzer.reader.profile_data.get(side, {})
        
        if profile_data:
            # 收集所有齿的数据
            all_teeth = sorted(profile_data.keys())
            num_teeth = min(20, len(all_teeth))  # 限制显示齿数
            
            fig = plt.figure(figsize=(12, 8))
            ax = fig.add_subplot(111, projection='3d')
            
            for i, tooth_id in enumerate(all_teeth[:num_teeth]):
                tooth_profiles = profile_data[tooth_id]
                for z_pos, values in tooth_profiles.items():
                    x = np.full(len(values), tooth_id)
                    y = np.linspace(0, len(values)-1, len(values))
                    z = values
                    ax.plot(x, y, z, alpha=0.7)
            
            ax.set_xlabel('齿号')
            ax.set_ylabel('数据点索引')
            ax.set_zlabel('偏差 (μm)')
            ax.set_title(f'{side_name}齿面 3D 表面图')
            st.pyplot(fig)
        else:
            st.warning("没有可用的数据")
    
    # 页面6: 报告导出
    elif page == '📄 报告导出':
        st.markdown('<div class="section-header">📄 报告导出</div>', unsafe_allow_html=True)
        
        st.markdown("""
        ### 报告内容
        
        报告将包含以下内容：
        - 齿轮基本参数
        - 评价范围信息
        - 齿形/齿向偏差分析结果
        - 频谱分析数据
        - 高阶波纹度评价结果
        """)
        
        if st.button("生成报告", type="primary"):
            # 生成报告内容
            report_content = f"""
# 齿轮测量分析报告

## 基本信息
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **文件名**: {uploaded_file.name}

## 齿轮参数
- **齿数 ZE**: {analyzer.gear_params.teeth_count}
- **模数 m**: {analyzer.gear_params.module} mm
- **压力角 α**: {analyzer.gear_params.pressure_angle}°
- **螺旋角 β**: {analyzer.gear_params.helix_angle}°
- **节圆直径**: {analyzer.gear_params.pitch_diameter:.2f} mm
- **基圆直径**: {analyzer.gear_params.base_diameter:.2f} mm

## 评价范围
### 齿形评价范围
- 起评点 d1: {analyzer.reader.profile_eval_range.eval_start} mm
- 终评点 d2: {analyzer.reader.profile_eval_range.eval_end} mm

### 齿向评价范围
- 起评点 b1: {analyzer.reader.helix_eval_range.eval_start} mm
- 终评点 b2: {analyzer.reader.helix_eval_range.eval_end} mm

## 分析结果
"""
            
            for name, result in results.items():
                if result is not None:
                    report_content += f"""
### {name}
- 高阶总振幅 W: {result.high_order_amplitude:.3f} μm
- RMS: {result.high_order_rms:.3f} μm
- 高阶波数: {len(result.high_order_waves)}
- 主导阶次: {result.spectrum_components[0].order}

#### 频谱分量（前5个）
"""
                    for i, comp in enumerate(result.spectrum_components[:5]):
                        report_content += f"- 阶次 {comp.order}: 振幅 {comp.amplitude:.4f} μm\n"
            
            # 下载按钮
            st.download_button(
                label="下载报告 (Markdown)",
                data=report_content,
                file_name=f"gear_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
            
            st.success("报告已生成！点击上方按钮下载。")
    
    # 清理临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)

else:
    # 显示说明
    st.info("👆 请在左侧上传 MKA 文件开始分析")
    
    st.markdown("""
    ### 📋 功能说明
    
    本系统提供完整的齿轮测量分析功能：
    
    | 功能 | 说明 |
    |------|------|
    | 📊 齿轮参数 | 显示齿轮基本参数和评价范围 |
    | 📈 单齿分析 | 显示单个齿的齿形/齿向偏差曲线 |
    | 📉 合并曲线 | 显示0-360°的合并曲线和高阶重构 |
    | 📊 频谱分析 | 显示各阶次振幅和相位 |
    | 🌐 3D表面图 | 显示齿面3D表面图 |
    | 📄 报告导出 | 生成并下载分析报告 |
    
    ### 🔧 技术参数
    
    - **预处理**: 去除鼓形（二次多项式）和斜率（线性）
    - **频谱方法**: 迭代最小二乘分解
    - **评价标准**: Klingelnberg P 系列标准
    - **高阶定义**: 阶次 ≥ 齿数 ZE
    """)

# 页脚
st.markdown("---")
st.caption("齿轮测量报告系统 | 基于 Python + Streamlit 构建")
