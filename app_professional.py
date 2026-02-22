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
    st.error(f"无法导入 gear_analysis_refactored 模块: {e}")
    GEAR_ANALYSIS_AVAILABLE = False

# 导入本地分析器作为备用
from ripple_waviness_analyzer import RippleWavinessAnalyzer

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

# 主界面
if uploaded_file is not None:
    # 保存上传的文件
    temp_path = os.path.join(os.path.dirname(__file__), "temp.mka")
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    # 使用 gear_analysis_refactored 解析文件
    if GEAR_ANALYSIS_AVAILABLE:
        try:
            gear_data = parse_mka_file(temp_path)
            st.success("✅ 使用 gear_analysis_refactored 解析文件成功")
            use_gear_analysis = True
        except Exception as e:
            st.warning(f"gear_analysis_refactored 解析失败: {e}，使用备用解析器")
            use_gear_analysis = False
    else:
        use_gear_analysis = False
    
    # 使用备用解析器
    if not use_gear_analysis:
        analyzer = RippleWavinessAnalyzer(temp_path)
        if analyzer.load_file():
            st.success("✅ 使用备用解析器解析文件成功")
        else:
            st.error("❌ 文件解析失败")
            gear_data = None
            analyzer = None
    else:
        analyzer = None
    
    # 显示齿轮参数
    if page == '📄 专业报告':
        st.header("📊 齿轮参数")
        
        if use_gear_analysis and gear_data:
            # parse_mka_file 返回的是字典，不是 GearMeasurementData 对象
            gear_basic = gear_data.get('gear_data', {})
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("模数 (mn)", f"{gear_basic.get('module', 0):.3f}")
            with col2:
                st.metric("齿数 (z)", gear_basic.get('teeth', 0))
            with col3:
                st.metric("压力角 (α)", f"{gear_basic.get('pressure_angle', 0):.1f}°")
            with col4:
                st.metric("螺旋角 (β)", f"{gear_basic.get('helix_angle', 0):.1f}°")
            
            st.subheader("详细信息")
            info_col1, info_col2 = st.columns(2)
            with info_col1:
                st.write(f"**程序:** {gear_basic.get('program', '')}")
                st.write(f"**日期:** {gear_basic.get('date', '')}")
                st.write(f"**操作员:** {gear_basic.get('operator', '')}")
            with info_col2:
                st.write(f"**图号:** {gear_basic.get('drawing_no', '')}")
                st.write(f"**订单号:** {gear_basic.get('order_no', '')}")
                st.write(f"**客户:** {gear_basic.get('customer', '')}")
        elif analyzer and analyzer.gear_params:
            params = analyzer.gear_params
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("模数 (mn)", f"{params.module:.3f}")
            with col2:
                st.metric("齿数 (z)", params.teeth_count)
            with col3:
                st.metric("压力角 (α)", f"{params.pressure_angle:.1f}°")
            with col4:
                st.metric("螺旋角 (β)", f"{params.helix_angle:.1f}°")
        else:
            st.info("暂无齿轮参数信息")
            
    elif page == '📊 周节详细报表':
        st.header("📊 周节详细报表")
        
        if use_gear_analysis and gear_data:
            import pandas as pd
            pitch_data = gear_data.get('pitch_data', {})
            
            # 左齿面周节
            if pitch_data.get('left'):
                st.subheader("左齿面周节")
                pitch_left_data = []
                for tooth_num in sorted(pitch_data['left'].keys()):
                    data = pitch_data['left'][tooth_num]
                    pitch_left_data.append({
                        '齿号': tooth_num,
                        'fp (μm)': data.get('fp', 0),
                        'Fp (μm)': data.get('Fp', 0),
                        'Fr (μm)': data.get('Fr', 0)
                    })
                df_left = pd.DataFrame(pitch_left_data)
                st.dataframe(df_left, use_container_width=True)
            
            # 右齿面周节
            if pitch_data.get('right'):
                st.subheader("右齿面周节")
                pitch_right_data = []
                for tooth_num in sorted(pitch_data['right'].keys()):
                    data = pitch_data['right'][tooth_num]
                    pitch_right_data.append({
                        '齿号': tooth_num,
                        'fp (μm)': data.get('fp', 0),
                        'Fp (μm)': data.get('Fp', 0),
                        'Fr (μm)': data.get('Fr', 0)
                    })
                df_right = pd.DataFrame(pitch_right_data)
                st.dataframe(df_right, use_container_width=True)
        elif analyzer:
            # 使用备用解析器
            pitch_left = analyzer.analyze_pitch('left')
            if pitch_left.teeth:
                st.subheader("左齿面周节")
                import pandas as pd
                df_left = pd.DataFrame({
                    '齿号': pitch_left.teeth,
                    'fp (μm)': pitch_left.fp_values,
                    'Fp (μm)': pitch_left.Fp_values
                })
                st.dataframe(df_left, use_container_width=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("fp_max", f"{pitch_left.fp_max:.2f} μm")
                with col2:
                    st.metric("Fp_max", f"{pitch_left.Fp_max:.2f} μm")
                with col3:
                    st.metric("Fr", f"{pitch_left.Fr:.2f} μm")
            
            pitch_right = analyzer.analyze_pitch('right')
            if pitch_right.teeth:
                st.subheader("右齿面周节")
                df_right = pd.DataFrame({
                    '齿号': pitch_right.teeth,
                    'fp (μm)': pitch_right.fp_values,
                    'Fp (μm)': pitch_right.Fp_values
                })
                st.dataframe(df_right, use_container_width=True)
        else:
            st.info("暂无周节数据")
                    
    elif page == '📈 单齿分析':
        st.header("📈 单齿分析")
        
        if use_gear_analysis and gear_data:
            profile_data = gear_data.get('profile_data', {})
            flank_data = gear_data.get('flank_data', {})
            profile_left_count = len(profile_data.get('left', {}))
            profile_right_count = len(profile_data.get('right', {}))
            flank_left_count = len(flank_data.get('left', {}))
            flank_right_count = len(flank_data.get('right', {}))
            st.info(f"齿形数据: 左齿面 {profile_left_count} 齿, 右齿面 {profile_right_count} 齿")
            st.info(f"齿向数据: 左齿面 {flank_left_count} 齿, 右齿面 {flank_right_count} 齿")
        elif analyzer:
            st.info(f"齿形数据: {len(analyzer.reader.profile_data.get('left', {}))} 齿")
            st.info(f"齿向数据: {len(analyzer.reader.helix_data.get('left', {}))} 齿")
        else:
            st.info("暂无单齿分析数据")
            
    elif page == '📉 合并曲线':
        st.header("📉 合并曲线")
        
        if analyzer:
            # 齿形合并曲线
            result_profile = analyzer.analyze_profile('left')
            if len(result_profile.angles) > 0:
                fig, ax = plt.subplots(figsize=(12, 4))
                ax.plot(result_profile.angles, result_profile.values, 'b-', linewidth=0.5, label='原始曲线')
                ax.plot(result_profile.angles, result_profile.reconstructed_signal, 'r-', linewidth=1, label='高阶重构')
                ax.set_xlabel('旋转角度 (°)')
                ax.set_ylabel('偏差 (μm)')
                ax.set_title('齿形合并曲线 (0-360°) - 左齿面')
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, 360)
                st.pyplot(fig)
            
            # 齿向合并曲线
            result_helix = analyzer.analyze_helix('left')
            if len(result_helix.angles) > 0:
                fig, ax = plt.subplots(figsize=(12, 4))
                ax.plot(result_helix.angles, result_helix.values, 'b-', linewidth=0.5, label='原始曲线')
                ax.plot(result_helix.angles, result_helix.reconstructed_signal, 'r-', linewidth=1, label='高阶重构')
                ax.set_xlabel('旋转角度 (°)')
                ax.set_ylabel('偏差 (μm)')
                ax.set_title('齿向合并曲线 (0-360°) - 左齿面')
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, 360)
                st.pyplot(fig)
        else:
            st.info("暂无合并曲线数据")
                    
    elif page == '📊 频谱分析':
        st.header("📊 频谱分析")
        
        if analyzer:
            result = analyzer.analyze_profile('left')
            if result.spectrum_components:
                fig, ax = plt.subplots(figsize=(12, 5))
                
                orders = [c.order for c in result.spectrum_components]
                amplitudes = [c.amplitude for c in result.spectrum_components]
                
                ax.bar(orders, amplitudes, color='steelblue', edgecolor='navy', alpha=0.7)
                ax.set_xlabel('阶次')
                ax.set_ylabel('振幅 (μm)')
                ax.set_title('频谱分析 - 齿形左齿面')
                ax.grid(True, alpha=0.3, axis='y')
                
                ze = analyzer.gear_params.teeth_count if analyzer.gear_params else 87
                ax.axvline(x=ze, color='r', linestyle='--', label=f'ZE = {ze}')
                ax.axvline(x=2*ze, color='orange', linestyle='--', label=f'2ZE = {2*ze}')
                ax.legend()
                
                st.pyplot(fig)
                
                # 显示频谱数据表
                st.subheader("频谱数据")
                spectrum_data = {
                    '阶次': [f"{c.order:.1f}" for c in result.spectrum_components[:10]],
                    '振幅 (μm)': [f"{c.amplitude:.4f}" for c in result.spectrum_components[:10]]
                }
                import pandas as pd
                st.dataframe(pd.DataFrame(spectrum_data), use_container_width=True)
        else:
            st.info("暂无频谱分析数据")
    
    # 清理临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)
else:
    st.info("👆 请在左侧上传 MKA 文件开始分析")
