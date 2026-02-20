"""
================================================================================
齿轮波纹度分析 Web 应用 - 部署版本
Gear Waviness Analysis Web App - Deployment Version
================================================================================

部署到 Streamlit Cloud 的版本
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

# 导入核心算法
# 注意：需要将 ripple_waviness_analyzer.py 放在同一目录
from ripple_waviness_analyzer import RippleWavinessAnalyzer

# 页面配置
st.set_page_config(
    page_title="齿轮波纹度分析系统",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("⚙️ 齿轮波纹度分析系统")
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
    
    num_components = st.slider(
        "频谱分量数量",
        min_value=5,
        max_value=20,
        value=10
    )

# 主界面
if uploaded_file is not None:
    # 保存上传的文件
    temp_path = "/tmp/temp.mka"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    # 分析
    with st.spinner("正在分析数据..."):
        try:
            analyzer = RippleWavinessAnalyzer(temp_path)
            analyzer.load_file()
            
            # 显示齿轮参数
            st.subheader("📊 齿轮参数")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("齿数 ZE", analyzer.gear_params.teeth_count)
            with col2:
                st.metric("模数 m", f"{analyzer.gear_params.module} mm")
            with col3:
                st.metric("压力角 α", f"{analyzer.gear_params.pressure_angle}°")
            with col4:
                st.metric("螺旋角 β", f"{analyzer.gear_params.helix_angle}°")
            
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
            
            # 显示结果
            st.subheader("📈 分析结果")
            
            for name, result in results.items():
                if result is None:
                    continue
                    
                with st.expander(f"📊 {name}", expanded=True):
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
                    
                    # 曲线图
                    st.markdown("**合并曲线**")
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
        
        except Exception as e:
            st.error(f"分析出错: {str(e)}")
    
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
    3. **查看结果**：系统将自动分析并显示频谱数据和曲线图
    
    ### 📊 分析内容
    
    - **高阶波纹度**：阶次 ≥ 齿数 ZE 的波纹度分量
    - **频谱分析**：迭代分解法提取各阶次振幅和相位
    - **曲线重构**：高阶分量的合成信号
    
    ### 🔧 技术参数
    
    - 预处理：去除鼓形（二次多项式）和斜率（线性）
    - 频谱方法：迭代最小二乘分解
    - 评价标准：Klingelnberg P 系列标准
    """)

# 页脚
st.markdown("---")
st.caption("齿轮波纹度分析系统 v1.0 | 基于 Python + Streamlit 构建")
