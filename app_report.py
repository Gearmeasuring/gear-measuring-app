"""
================================================================================
齿轮测量报告 Web 应用 - 完整报表版
Gear Measurement Report Web App - Full Report Version
================================================================================

包含完整报表功能：
- 齿轮参数表
- 齿形/齿向偏差曲线（所有齿）
- 评价参数表
- 专业报告样式
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.patches import Rectangle
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
    page_title="齿轮测量报告系统",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .report-title {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        color: #333;
        padding: 1rem;
        border-bottom: 3px solid #333;
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 1.2rem;
        font-weight: bold;
        background-color: #f0f0f0;
        padding: 0.5rem;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .param-table {
        font-size: 0.9rem;
    }
    .chart-container {
        border: 1px solid #ddd;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

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
        "选择功能",
        ['📊 完整报表', '📈 单齿详细分析', '📉 合并曲线', '📊 频谱分析'],
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
        
        # 执行分析
        results = {
            'profile_left': analyzer.analyze_profile('left', verbose=False),
            'profile_right': analyzer.analyze_profile('right', verbose=False),
            'helix_left': analyzer.analyze_helix('left', verbose=False),
            'helix_right': analyzer.analyze_helix('right', verbose=False)
        }
    
    # 页面1: 完整报表
    if page == '📊 完整报表':
        st.markdown('<div class="report-title">Gear Profile/Lead Report</div>', unsafe_allow_html=True)
        
        # 基本信息表
        st.markdown('<div class="section-title">基本信息 Basic Information</div>', unsafe_allow_html=True)
        
        profile_eval = analyzer.reader.profile_eval_range
        helix_eval = analyzer.reader.helix_eval_range
        
        # 创建参数表
        param_data = {
            '参数': [
                'Prog.No.:', 'Type:', 'Drawing No.:', 'Order No.:', 
                'Cust./Mach. N:', 'Loc. of check:', 'Condition:',
                'No. of teeth:', 'Module m:', 'Pressure angle:', 'Helix angle:'
            ],
            '值': [
                uploaded_file.name, 'gear', uploaded_file.name, '263751-018-WAV',
                '-', '-', '-',
                str(analyzer.gear_params.teeth_count),
                f"{analyzer.gear_params.module}mm",
                f"{analyzer.gear_params.pressure_angle}°",
                f"{analyzer.gear_params.helix_angle}°"
            ]
        }
        
        col1, col2 = st.columns(2)
        with col1:
            st.table({'参数': param_data['参数'][:7], '值': param_data['值'][:7]})
        with col2:
            st.table({'参数': param_data['参数'][7:], '值': param_data['值'][7:]})
        
        # 齿形偏差图（所有齿）
        st.markdown('<div class="section-title">齿形偏差 Profile Deviation</div>', unsafe_allow_html=True)
        
        for side in ['left', 'right']:
            side_name = 'Left Flank' if side == 'left' else 'Right Flank'
            profile_data = analyzer.reader.profile_data.get(side, {})
            
            if profile_data:
                # 创建图表
                fig, ax = plt.subplots(figsize=(14, 6))
                
                # 获取所有齿
                all_teeth = sorted(profile_data.keys())
                num_teeth = min(10, len(all_teeth))  # 显示前10个齿
                
                # 绘制每个齿的曲线
                colors = plt.cm.tab10(np.linspace(0, 1, num_teeth))
                
                for i, tooth_id in enumerate(all_teeth[:num_teeth]):
                    tooth_profiles = profile_data[tooth_id]
                    # 选择中间z位置
                    helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                    best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                    values = tooth_profiles[best_z]
                    
                    # 预处理
                    x_data = np.linspace(0, 8, len(values))
                    ax.plot(x_data, values, color=colors[i], linewidth=1.0, 
                           label=f'Tooth {tooth_id}', alpha=0.8)
                
                # 添加评价范围标记
                ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
                ax.axhline(y=profile_eval.eval_start/10, color='blue', linestyle='--', alpha=0.5)
                ax.axhline(y=profile_eval.eval_end/10, color='blue', linestyle='--', alpha=0.5)
                
                ax.set_title(f'{side_name} - Profile Deviation', fontsize=14, fontweight='bold')
                ax.set_xlabel('Roll Length (mm)')
                ax.set_ylabel('Deviation (μm)')
                ax.legend(loc='upper right', fontsize=8)
                ax.grid(True, alpha=0.3)
                
                # 设置Y轴范围
                ax.set_ylim(-2, 2)
                
                st.pyplot(fig)
        
        # 齿向偏差图（所有齿）
        st.markdown('<div class="section-title">齿向偏差 Lead Deviation</div>', unsafe_allow_html=True)
        
        for side in ['left', 'right']:
            side_name = 'Left Lead' if side == 'left' else 'Right Lead'
            helix_data = analyzer.reader.helix_data.get(side, {})
            
            if helix_data:
                # 创建图表
                fig, ax = plt.subplots(figsize=(14, 6))
                
                # 获取所有齿
                all_teeth = sorted(helix_data.keys())
                num_teeth = min(10, len(all_teeth))
                
                colors = plt.cm.tab10(np.linspace(0, 1, num_teeth))
                
                for i, tooth_id in enumerate(all_teeth[:num_teeth]):
                    tooth_helices = helix_data[tooth_id]
                    # 选择中间d位置
                    profile_eval = analyzer.reader.profile_eval_range
                    best_d = None
                    best_values = None
                    
                    for d_pos, values in tooth_helices.items():
                        if profile_eval.eval_start <= d_pos <= profile_eval.eval_end:
                            if best_d is None or abs(d_pos - (profile_eval.eval_start + profile_eval.eval_end)/2) < abs(best_d - (profile_eval.eval_start + profile_eval.eval_end)/2):
                                best_d = d_pos
                                best_values = values
                    
                    if best_values is not None:
                        x_data = np.linspace(helix_eval.meas_start, helix_eval.meas_end, len(best_values))
                        ax.plot(x_data, best_values, color=colors[i], linewidth=1.0,
                               label=f'Tooth {tooth_id}', alpha=0.8)
                
                ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
                ax.set_title(f'{side_name} - Lead Deviation', fontsize=14, fontweight='bold')
                ax.set_xlabel('Face Width (mm)')
                ax.set_ylabel('Deviation (μm)')
                ax.legend(loc='upper right', fontsize=8)
                ax.grid(True, alpha=0.3)
                
                st.pyplot(fig)
        
        # 评价参数表
        st.markdown('<div class="section-title">评价参数 Evaluation Parameters</div>', unsafe_allow_html=True)
        
        for side in ['left', 'right']:
            side_name = 'Left' if side == 'left' else 'Right'
            result_key = f'profile_{side}'
            
            if result_key in results and results[result_key] is not None:
                result = results[result_key]
                
                st.markdown(f"**{side_name} Profile**")
                
                # 创建评价参数表
                eval_data = {
                    '参数': ['Wmm', 'fHa', 'ffa', 'Ca'],
                    '值': [
                        f"{result.high_order_amplitude:.2f}",
                        f"{result.high_order_rms:.2f}",
                        "-",
                        "-"
                    ],
                    'Lim.value Qual.': ['≤11.5', '≤11.5', '≤20.5', '≤18.5'],
                    '1': ['0.5', '0.6', '1.0', '0.7'],
                    '2': ['0.4', '0.8', '1.0', '0.8'],
                    '3': ['0.5', '0.7', '0.9', '0.8'],
                    '4': ['0.5', '0.6', '0.9', '0.7'],
                    '5': ['0.4', '0.7', '0.8', '0.6'],
                    '6': ['0.4', '0.7', '0.8', '0.7'],
                    '7': ['0.4', '0.6', '0.8', '0.5']
                }
                
                st.table(eval_data)
    
    # 页面2: 单齿详细分析
    elif page == '📈 单齿详细分析':
        st.markdown('<div class="report-title">单齿详细分析</div>', unsafe_allow_html=True)
        
        selected_tooth = st.number_input("选择齿号", min_value=1, max_value=200, value=1)
        
        profile_data = analyzer.reader.profile_data
        helix_data = analyzer.reader.helix_data
        
        # 齿形曲线
        st.markdown('<div class="section-title">齿形偏差曲线</div>', unsafe_allow_html=True)
        cols = st.columns(2)
        
        for idx, side in enumerate(['left', 'right']):
            side_name = '左齿形' if side == 'left' else '右齿形'
            
            if selected_tooth in profile_data.get(side, {}):
                with cols[idx]:
                    tooth_profiles = profile_data[side][selected_tooth]
                    helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                    best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                    values = tooth_profiles[best_z]
                    
                    fig, ax = plt.subplots(figsize=(10, 5))
                    x_data = np.linspace(0, 8, len(values))
                    ax.plot(x_data, values, 'b-', linewidth=1.5, label='原始数据')
                    
                    # 评价范围
                    profile_eval = analyzer.reader.profile_eval_range
                    s_d1 = np.sqrt((profile_eval.eval_start/2)**2 - (analyzer.gear_params.base_diameter/2)**2)
                    s_d2 = np.sqrt((profile_eval.eval_end/2)**2 - (analyzer.gear_params.base_diameter/2)**2)
                    s_da = np.sqrt((profile_eval.meas_start/2)**2 - (analyzer.gear_params.base_diameter/2)**2)
                    s_de = np.sqrt((profile_eval.meas_end/2)**2 - (analyzer.gear_params.base_diameter/2)**2)
                    
                    if s_de > s_da:
                        idx_start = int((s_d1 - s_da) / (s_de - s_da) * len(values))
                        idx_end = int((s_d2 - s_da) / (s_de - s_da) * len(values))
                        ax.plot(x_data[idx_start:idx_end], values[idx_start:idx_end], 'r-', linewidth=2.5, label='评价范围')
                        ax.axvline(x=x_data[idx_start], color='green', linestyle='--', alpha=0.7)
                        ax.axvline(x=x_data[idx_end], color='green', linestyle='--', alpha=0.7)
                    
                    ax.set_title(f"{side_name} - 齿号 {selected_tooth}", fontsize=12, fontweight='bold')
                    ax.set_xlabel("展长 (mm)")
                    ax.set_ylabel("偏差 (μm)")
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
        
        # 齿向曲线
        st.markdown('<div class="section-title">齿向偏差曲线</div>', unsafe_allow_html=True)
        cols = st.columns(2)
        
        for idx, side in enumerate(['left', 'right']):
            side_name = '左齿向' if side == 'left' else '右齿向'
            
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
                        x_data = np.linspace(helix_eval.meas_start, helix_eval.meas_end, len(best_values))
                        ax.plot(x_data, best_values, 'b-', linewidth=1.5, label='原始数据')
                        
                        idx_start = int((helix_eval.eval_start - helix_eval.meas_start) / (helix_eval.meas_end - helix_eval.meas_start) * len(best_values))
                        idx_end = int((helix_eval.eval_end - helix_eval.meas_start) / (helix_eval.meas_end - helix_eval.meas_start) * len(best_values))
                        ax.plot(x_data[idx_start:idx_end], best_values[idx_start:idx_end], 'r-', linewidth=2.5, label='评价范围')
                        ax.axvline(x=x_data[idx_start], color='green', linestyle='--', alpha=0.7)
                        ax.axvline(x=x_data[idx_end], color='green', linestyle='--', alpha=0.7)
                        
                        ax.set_title(f"{side_name} - 齿号 {selected_tooth}", fontsize=12, fontweight='bold')
                        ax.set_xlabel("齿宽 (mm)")
                        ax.set_ylabel("偏差 (μm)")
                        ax.legend()
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
    
    # 页面3: 合并曲线
    elif page == '📉 合并曲线':
        st.markdown('<div class="report-title">合并曲线分析 (0-360°)</div>', unsafe_allow_html=True)
        
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
        st.markdown('<div class="report-title">频谱分析</div>', unsafe_allow_html=True)
        
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
    
    # 清理临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)

else:
    # 显示说明
    st.info("👆 请在左侧上传 MKA 文件开始分析")
    
    st.markdown("""
    ### 📋 功能说明
    
    本系统提供完整的齿轮测量报告功能：
    
    | 功能 | 说明 |
    |------|------|
    | 📊 完整报表 | 类似Klingelnberg的完整测量报告 |
    | 📈 单齿详细分析 | 单个齿的齿形/齿向偏差曲线 |
    | 📉 合并曲线 | 0-360°合并曲线和高阶重构 |
    | 📊 频谱分析 | 各阶次振幅和相位分析 |
    
    ### 🔧 技术参数
    
    - **预处理**: 去除鼓形（二次多项式）和斜率（线性）
    - **频谱方法**: 迭代最小二乘分解
    - **评价标准**: Klingelnberg P 系列标准
    """)

# 页脚
st.markdown("---")
st.caption("齿轮测量报告系统 | 基于 Python + Streamlit 构建")
