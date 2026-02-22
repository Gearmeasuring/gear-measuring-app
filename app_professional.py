"""
================================================================================
齿轮测量报告 Web 应用 - 完整专业版 (使用 gear_analysis_refactored)
================================================================================

使用 gear_analysis_refactored 模块的完整功能
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.backends.backend_pdf import PdfPages
import sys
import os
from datetime import datetime
from io import BytesIO
import tempfile
import pandas as pd

# 设置中文字体
rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入 gear_analysis_refactored 模块
try:
    from gear_analysis_refactored.models.gear_data import (
        GearMeasurementData, GearBasicInfo, MeasurementData, PitchData
    )
    from gear_analysis_refactored.utils.file_parser import parse_mka_file
    GEAR_ANALYSIS_AVAILABLE = True
except ImportError as e:
    GEAR_ANALYSIS_AVAILABLE = False

# 导入本地分析器作为备用
from ripple_waviness_analyzer import RippleWavinessAnalyzer

# 导入PDF报告生成器
try:
    from klingelnberg_report_generator import KlingelnbergReportGenerator
    PDF_GENERATOR_AVAILABLE = True
except ImportError as e:
    print(f"KlingelnbergReportGenerator import error: {e}")
    PDF_GENERATOR_AVAILABLE = False

st.set_page_config(
    page_title="齿轮测量报告系统 - 专业版",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.header("📁 数据上传")
    uploaded_file = st.file_uploader(
        "上传 MKA 文件",
        type=['mka'],
        help="支持 Klingenberg MKA 格式的齿轮测量数据文件"
    )
    
    if uploaded_file is not None:
        st.success(f"已加载: {uploaded_file.name}")
    
    st.markdown("---")
    st.header("📋 功能导航")
    
    page = st.radio(
        "选择功能",
        ['📄 专业报告', '📊 周节详细报表', '📈 单齿分析', '📉 合并曲线', '📊 频谱分析'],
        index=0
    )

if uploaded_file is not None:
    # 保存上传的文件到临时目录
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, "temp.mka")
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    with st.spinner("正在分析数据..."):
        analyzer = RippleWavinessAnalyzer(temp_path)
        analyzer.load_file()
        
        # 预计算所有结果
        results = {
            'profile_left': analyzer.analyze_profile('left', verbose=False),
            'profile_right': analyzer.analyze_profile('right', verbose=False),
            'helix_left': analyzer.analyze_helix('left', verbose=False),
            'helix_right': analyzer.analyze_helix('right', verbose=False)
        }
        
        pitch_left = analyzer.analyze_pitch('left')
        pitch_right = analyzer.analyze_pitch('right')
    
    profile_eval = analyzer.reader.profile_eval_range
    helix_eval = analyzer.reader.helix_eval_range
    gear_params = analyzer.gear_params
    
    # 同时尝试使用 gear_analysis_refactored 获取额外信息
    if GEAR_ANALYSIS_AVAILABLE:
        try:
            gear_data_dict = parse_mka_file(temp_path)
            use_gear_analysis = True
        except Exception as e:
            gear_data_dict = None
            use_gear_analysis = False
    else:
        gear_data_dict = None
        use_gear_analysis = False
    
    if page == '📄 专业报告':
        st.markdown("## Gear Profile/Lead Report")
        
        st.markdown("### 📋 专业报告生成")
        
        # PDF下载按钮
        if PDF_GENERATOR_AVAILABLE:
            if st.button("📥 生成完整PDF报告"):
                with st.spinner("正在生成PDF报告，请稍候..."):
                    try:
                        generator = KlingelnbergReportGenerator()
                        pdf_buffer = generator.generate_full_report(
                            analyzer,
                            output_filename=f"gear_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        )

                        st.download_button(
                            label="📥 下载PDF报告",
                            data=pdf_buffer,
                            file_name=f"gear_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf"
                        )
                        st.success("✅ PDF报告生成成功！包含2页：齿形/齿向报表、周节报表")
                    except Exception as e:
                        st.error(f"生成PDF失败: {e}")
                        import traceback
                        st.error(traceback.format_exc())
        else:
            st.warning("PDF生成器不可用")
        
        st.markdown("#### 基本信息")
        col1, col2 = st.columns(2)
        
        with col1:
            header_data1 = {
                '参数': ['Prog.No.', 'Type', 'Drawing No.', 'Order No.', 'Cust./Mach. No.', 'Loc. of check'],
                '值': [uploaded_file.name, 'gear', uploaded_file.name, '-', '-', '-']
            }
            st.table(header_data1)
        
        with col2:
            if gear_params:
                header_data2 = {
                    '参数': ['Operator', 'No. of teeth', 'Module m', 'Pressure angle', 'Helix angle', 'Base Cir. db'],
                    '值': ['Operator', str(gear_params.teeth_count), f"{gear_params.module:.3f}mm",
                           f"{gear_params.pressure_angle}°", f"{gear_params.helix_angle}°",
                           f"{gear_params.module * gear_params.teeth_count * np.cos(np.radians(gear_params.pressure_angle)):.3f}mm"]
                }
            else:
                header_data2 = {
                    '参数': ['Operator', 'No. of teeth', 'Module m', 'Pressure angle', 'Helix angle', 'Base Cir. db'],
                    '值': ['Operator', '-', '-', '-', '-', '-']
                }
            st.table(header_data2)
        
        st.markdown("---")
        st.markdown("#### 齿形分析预览 (左齿面)")
        
        profile_data = analyzer.reader.profile_data
        if gear_params:
            teeth_left = [1, 6, 12, 17] if gear_params.teeth_count >= 17 else list(range(1, min(5, gear_params.teeth_count) + 1))
        else:
            teeth_left = [1, 2, 3, 4]
        
        cols = st.columns(min(4, len(teeth_left)))
        
        for i, tooth_id in enumerate(teeth_left[:len(cols)]):
            with cols[i]:
                if tooth_id in profile_data.get('left', {}):
                    tooth_profiles = profile_data['left'][tooth_id]
                    helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                    best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                    values = tooth_profiles[best_z]
                    
                    fig, ax = plt.subplots(figsize=(4, 5))
                    x_positions = np.linspace(0, 8, len(values))
                    n_points = len(values)
                    idx_start = int(n_points * 0.1)
                    idx_end = int(n_points * 0.9)
                    
                    eval_data = values[idx_start:idx_end + 1]
                    eval_x = x_positions[idx_start:idx_end + 1]
                    
                    if len(eval_data) > 1:
                        x = np.arange(len(eval_data))
                        slope, intercept = np.polyfit(x, eval_data, 1)
                        trend = slope * x + intercept
                        
                        ax.plot(eval_data, eval_x, 'k-', linewidth=1.0, label='实际轮廓')
                        ax.plot(trend, eval_x, 'r--', linewidth=1.0, label='评定线')
                    
                    ax.grid(True, linestyle='-', alpha=1.0, color='black', linewidth=0.5)
                    ax.set_xlabel('偏差 (μm)', fontsize=8)
                    ax.set_ylabel('展长 (mm)', fontsize=8)
                    ax.set_title(f'齿号 {tooth_id}', fontsize=10, fontweight='bold')
                    ax.tick_params(axis='both', which='major', labelsize=7)
                    
                    plt.tight_layout()
                    st.pyplot(fig)
                else:
                    st.warning(f"齿号 {tooth_id} 无数据")
            
    elif page == '📊 周节详细报表':
        st.markdown("## Gear Spacing Report - 周节详细报表")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**基本信息**")
            header_data1 = {
                '参数': ['Prog.No.', 'Type', 'Drawing No.', 'Operator', 'Date'],
                '值': [uploaded_file.name, 'gear', uploaded_file.name, 'Operator', datetime.now().strftime('%d.%m.%y')]
            }
            st.table(header_data1)
        
        with col2:
            st.markdown("**齿轮参数**")
            if gear_params:
                header_data2 = {
                    '参数': ['No. of teeth', 'Module m', 'Pressure angle', 'Helix angle', 'Pitch diameter'],
                    '值': [
                        str(gear_params.teeth_count),
                        f"{gear_params.module:.3f}mm",
                        f"{gear_params.pressure_angle}°",
                        f"{gear_params.helix_angle}°",
                        f"{gear_params.module * gear_params.teeth_count:.3f}mm"
                    ]
                }
                st.table(header_data2)
        
        st.markdown("---")
        st.markdown("### 周节偏差统计")
        
        cols = st.columns(4)
        
        if pitch_left:
            with cols[0]:
                st.metric("左齿面 fp max", f"{pitch_left.fp_max:.2f} μm")
            with cols[1]:
                st.metric("左齿面 Fp max", f"{pitch_left.Fp_max:.2f} μm")
            with cols[2]:
                st.metric("左齿面 Fp min", f"{pitch_left.Fp_min:.2f} μm")
            with cols[3]:
                st.metric("左齿面 Fr", f"{pitch_left.Fr:.2f} μm")
        
        if pitch_right:
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
        st.markdown("### 周节偏差数据表")
        
        # 左齿面数据表
        if pitch_left and pitch_left.teeth:
            st.subheader("左齿面周节")
            df_left = pd.DataFrame({
                '齿号': pitch_left.teeth,
                'fp (μm)': pitch_left.fp_values,
                'Fp (μm)': pitch_left.Fp_values
            })
            st.dataframe(df_left, use_container_width=True)
        
        # 右齿面数据表
        if pitch_right and pitch_right.teeth:
            st.subheader("右齿面周节")
            df_right = pd.DataFrame({
                '齿号': pitch_right.teeth,
                'fp (μm)': pitch_right.fp_values,
                'Fp (μm)': pitch_right.Fp_values
            })
            st.dataframe(df_right, use_container_width=True)
    
    elif page == '📈 单齿分析':
        st.markdown("## 单齿详细分析")
        
        selected_tooth = st.number_input("选择齿号", min_value=1, max_value=200, value=1)
        
        profile_data = analyzer.reader.profile_data
        helix_data = analyzer.reader.helix_data
        
        st.markdown("### 齿形偏差曲线")
        cols = st.columns(2)
        
        for idx, side in enumerate(['left', 'right']):
            side_name = '左齿形' if side == 'left' else '右齿形'
            
            if selected_tooth in profile_data.get(side, {}):
                with cols[idx]:
                    tooth_profiles = profile_data[side][selected_tooth]
                    helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                    best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                    values = tooth_profiles[best_z]
                    
                    fig, ax = plt.subplots(figsize=(8, 6))
                    x_data = np.linspace(0, 8, len(values))
                    ax.plot(x_data, values, 'b-', linewidth=1.5, label='原始数据')
                    
                    ax.set_title(f"{side_name} - 齿号 {selected_tooth}", fontsize=12, fontweight='bold')
                    ax.set_xlabel("展长 (mm)")
                    ax.set_ylabel("偏差 (μm)")
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
        
        st.markdown("### 齿向偏差曲线")
        cols = st.columns(2)
        
        for idx, side in enumerate(['left', 'right']):
            side_name = '左齿向' if side == 'left' else '右齿向'
            
            if selected_tooth in helix_data.get(side, {}):
                with cols[idx]:
                    tooth_helix = helix_data[side][selected_tooth]
                    profile_mid = (profile_eval.eval_start + profile_eval.eval_end) / 2
                    best_d = min(tooth_helix.keys(), key=lambda d: abs(d - profile_mid))
                    values = tooth_helix[best_d]
                    
                    fig, ax = plt.subplots(figsize=(8, 6))
                    x_data = np.linspace(0, 40, len(values))
                    ax.plot(x_data, values, 'g-', linewidth=1.5, label='原始数据')
                    
                    ax.set_title(f"{side_name} - 齿号 {selected_tooth}", fontsize=12, fontweight='bold')
                    ax.set_xlabel("齿宽 (mm)")
                    ax.set_ylabel("偏差 (μm)")
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
    
    elif page == '📉 合并曲线':
        st.markdown("## 合并曲线分析 (0-360°)")
        
        ze = gear_params.teeth_count if gear_params else 87
        
        name_mapping = {
            'profile_left': '左齿形',
            'profile_right': '右齿形',
            'helix_left': '左齿向',
            'helix_right': '右齿向'
        }
        
        for name, result in results.items():
            if result is None or len(result.angles) == 0:
                continue
            
            display_name = name_mapping.get(name, name)
            
            with st.expander(f"📈 {display_name}", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("高阶总振幅 W", f"{result.high_order_amplitude:.4f} μm")
                with col2:
                    st.metric("高阶 RMS", f"{result.high_order_rms:.4f} μm")
                with col3:
                    st.metric("高阶波数", len(result.high_order_waves))
                with col4:
                    if result.spectrum_components and len(result.spectrum_components) > 0:
                        max_order = result.spectrum_components[0].order
                        st.metric("主导阶次", int(max_order))
                    else:
                        st.metric("主导阶次", "-")
                
                fig, ax = plt.subplots(figsize=(14, 5))
                ax.plot(result.angles, result.values, 'b-', linewidth=0.5, alpha=0.7, label='原始曲线')
                ax.plot(result.angles, result.reconstructed_signal, 'r-', linewidth=1.5, label='高阶重构')
                ax.set_xlabel('旋转角度 (°)')
                ax.set_ylabel('偏差 (μm)')
                ax.set_title(f'{display_name} - 合并曲线 (ZE={ze})')
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, 360)
                st.pyplot(fig)
        
        st.markdown("---")
        st.markdown("### 前5个齿放大显示")
        
        pitch_angle = 360.0 / ze if ze > 0 else 4.14
        end_angle = 5 * pitch_angle
        
        for name, result in [
            ('左齿形', results.get('profile_left')),
            ('右齿形', results.get('profile_right')),
            ('左齿向', results.get('helix_left')),
            ('右齿向', results.get('helix_right'))
        ]:
            if result is None or len(result.angles) == 0:
                continue
            
            display_name = name
            
            mask = (result.angles >= 0) & (result.angles <= end_angle)
            if np.sum(mask) > 0:
                zoom_angles = result.angles[mask]
                zoom_values = result.values[mask]
                zoom_reconstructed = result.reconstructed_signal[mask]
                
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(zoom_angles, zoom_values, 'b-', linewidth=0.8, alpha=0.7, label='原始曲线')
                ax.plot(zoom_angles, zoom_reconstructed, 'r-', linewidth=1.5, label='高阶重构')
                ax.set_xlabel('旋转角度 (°)')
                ax.set_ylabel('偏差 (μm)')
                ax.set_title(f'{display_name} - 前5个齿 (0° ~ {end_angle:.1f}°)')
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
    
    elif page == '📊 频谱分析':
        st.markdown("## 频谱分析")
        
        ze = gear_params.teeth_count if gear_params else 87
        
        name_mapping = {
            'profile_left': '左齿形',
            'profile_right': '右齿形',
            'helix_left': '左齿向',
            'helix_right': '右齿向'
        }
        
        for name, result in results.items():
            if result is None or len(result.angles) == 0:
                continue
            
            display_name = name_mapping.get(name, name)
            
            with st.expander(f"📈 {display_name}", expanded=True):
                st.markdown("#### 前10个较大阶次")
                
                spectrum_data = []
                for i, comp in enumerate(result.spectrum_components[:10]):
                    order_type = '高阶' if comp.order >= ze else '低阶'
                    spectrum_data.append({
                        '排名': i + 1,
                        '阶次': int(comp.order),
                        '振幅 (μm)': f"{comp.amplitude:.4f}",
                        '相位 (°)': f"{np.degrees(comp.phase):.1f}",
                        '类型': order_type
                    })
                st.table(spectrum_data)
                
                st.markdown("#### 频谱图")
                
                fig, ax = plt.subplots(figsize=(12, 5))
                sorted_components = sorted(result.spectrum_components[:20], key=lambda c: c.order)
                orders = [c.order for c in sorted_components]
                amplitudes = [c.amplitude for c in sorted_components]
                
                if orders and amplitudes:
                    colors_bar = ['red' if o >= ze else 'steelblue' for o in orders]
                    ax.bar(orders, amplitudes, color=colors_bar, alpha=0.7, width=3)
                    
                    ax.axvline(x=ze, color='green', linestyle='--', linewidth=2, label=f'ZE={ze}')
                    ax.set_xlim(0, max(orders) + 20)
                
                ax.set_xlabel('阶次')
                ax.set_ylabel('振幅 (μm)')
                ax.set_title(f'{display_name} - 频谱图 (ZE={ze})')
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
    
    # 清理临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)

else:
    st.info("👆 请在左侧上传 MKA 文件开始分析")
    
    st.markdown("""
    ### 📋 功能说明
    
    本系统提供齿轮测量报告：
    
    | 功能 | 说明 |
    |------|------|
    | 📄 专业报告 | 齿形/齿向分析图表和数据表，支持PDF下载 |
    | 📊 周节详细报表 | 周节偏差 fp/Fp/Fr 分析 |
    | 📈 单齿分析 | 单个齿的齿形/齿向偏差曲线 |
    | 📉 合并曲线 | 0-360°合并曲线、高阶波纹度评价、前5齿放大 |
    | 📊 频谱分析 | 阶次振幅相位分析（全部齿形/齿向） |
    """)

st.markdown("---")
st.caption("齿轮测量报告系统 | 基于 Python + Streamlit 构建")
