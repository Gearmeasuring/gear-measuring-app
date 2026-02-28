"""
齿轮测量报告 Web 应用
Gear Measurement Report Web App
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.colors import LinearSegmentedColormap
import sys
import os
from datetime import datetime
import tempfile
import re

rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False

current_dir = os.path.dirname(os.path.abspath(__file__))

from ripple_waviness_analyzer import RippleWavinessAnalyzer


def parse_topografie_data(file_path):
    with open(file_path, 'r', encoding='latin-1') as f:
        lines = f.readlines()
    
    topografie_data = {
        'rechts': {'profiles': [], 'flank': None},
        'links': {'profiles': [], 'flank': None}
    }
    
    current_section = None
    current_values = []
    current_meta = {}
    undefined_value = -2147483.648
    
    for line in lines:
        line_stripped = line.strip()
        
        if line_stripped.startswith('TOPOGRAFIE:'):
            if current_section and current_values:
                if current_meta.get('type') == 'Profil':
                    side = current_meta.get('side', 'rechts')
                    topografie_data[side]['profiles'].append({
                        'position': current_meta.get('position', 0),
                        'values': np.array(current_values)
                    })
                elif current_meta.get('type') == 'Flankenlinie':
                    side = current_meta.get('side', 'rechts')
                    topografie_data[side]['flank'] = {
                        'diameter': current_meta.get('diameter', 0),
                        'values': np.array(current_values)
                    }
            
            current_values = []
            current_meta = {}
            
            if '/Profil:' in line_stripped:
                current_meta['type'] = 'Profil'
                match = re.search(r'Profil:(\d+)\s+(rechts|links)', line_stripped)
                if match:
                    current_meta['profile_num'] = int(match.group(1))
                    current_meta['side'] = match.group(2)
                match_z = re.search(r'z=\s*(\d+\.\d+)', line_stripped)
                if match_z:
                    current_meta['position'] = float(match_z.group(1))
                    
            elif '/Flankenlinie:' in line_stripped:
                current_meta['type'] = 'Flankenlinie'
                match = re.search(r'Flankenlinie:\d+\s+(rechts|links)', line_stripped)
                if match:
                    current_meta['side'] = match.group(1)
                match_d = re.search(r'd=\s*(\d+\.\d+)', line_stripped)
                if match_d:
                    current_meta['diameter'] = float(match_d.group(1))
            
            current_section = 'data'
            
        elif current_section == 'data' and line_stripped:
            values = re.findall(r'[-+]?\d*\.\d+', line_stripped)
            for v in values:
                val = float(v)
                if val != undefined_value:
                    current_values.append(val)
    
    if current_section and current_values:
        if current_meta.get('type') == 'Profil':
            side = current_meta.get('side', 'rechts')
            topografie_data[side]['profiles'].append({
                'position': current_meta.get('position', 0),
                'values': np.array(current_values)
            })
        elif current_meta.get('type') == 'Flankenlinie':
            side = current_meta.get('side', 'rechts')
            topografie_data[side]['flank'] = {
                'diameter': current_meta.get('diameter', 0),
                'values': np.array(current_values)
            }
    
    for side in ['rechts', 'links']:
        topografie_data[side]['profiles'].sort(key=lambda x: x['position'])
    
    return topografie_data


def create_topography_map(topografie_data, side='rechts'):
    profiles = topografie_data[side]['profiles']
    
    if not profiles:
        return None, None, None
    
    n_profiles = len(profiles)
    n_points = min(len(p['values']) for p in profiles)
    
    z_positions = [p['position'] for p in profiles]
    
    data_matrix = np.zeros((n_profiles, n_points))
    for i, profile in enumerate(profiles):
        values = profile['values'][:n_points]
        data_matrix[i, :] = values
    
    return data_matrix, z_positions, n_points


def plot_topography(data_matrix, z_positions, n_points, side='rechts', title_suffix=''):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = ['#0000FF', '#00FFFF', '#00FF00', '#FFFF00', '#FF0000']
    cmap = LinearSegmentedColormap.from_list('gear_topo', colors, N=256)
    
    im = ax.imshow(data_matrix, aspect='auto', cmap=cmap, origin='lower',
                   extent=[0, n_points-1, z_positions[0], z_positions[-1]])
    
    cbar = plt.colorbar(im, ax=ax, label='偏差 (µm)')
    
    ax.set_xlabel('齿高方向 (测量点)', fontsize=11)
    ax.set_ylabel('齿宽方向 z (mm)', fontsize=11)
    ax.set_title(f'齿面TOPOGRAFIE拓普图 - {side}侧{title_suffix}', fontsize=13)
    
    return fig, ax

st.set_page_config(
    page_title="齿轮测量报告系统",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        ['📄 专业报告', '📊 周节详细报表', '🗺️ 齿面拓普图', '📈 单齿分析', '📉 合并曲线', '📊 频谱分析'],
        index=0
    )

if uploaded_file is not None:
    temp_path = os.path.join(os.path.dirname(__file__), "temp.mka")
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    with st.spinner("正在分析数据..."):
        analyzer = RippleWavinessAnalyzer(temp_path)
        analyzer.load_file()
        
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
    
    if page == '📄 专业报告':
        st.markdown("## Gear Profile/Lead Report")
        
        st.markdown("### 📋 专业报告生成")
        
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
                           f"{gear_params.base_diameter:.3f}mm"]
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
                        f"{gear_params.pitch_diameter:.3f}mm"
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
    
    elif page == '🗺️ 齿面拓普图':
        st.markdown("## 齿面TOPOGRAFIE拓普图")
        
        with st.spinner("正在解析TOPOGRAFIE数据..."):
            topografie_data = parse_topografie_data(temp_path)
        
        col1, col2 = st.columns(2)
        
        for idx, side in enumerate(['rechts', 'links']):
            side_name = '右齿面' if side == 'rechts' else '左齿面'
            profiles = topografie_data[side]['profiles']
            flank = topografie_data[side]['flank']
            
            with [col1, col2][idx]:
                st.markdown(f"### {side_name}")
                
                if profiles:
                    st.markdown(f"**数据统计:** Profil数量: {len(profiles)}, z范围: {profiles[0]['position']:.1f}-{profiles[-1]['position']:.1f} mm")
                    
                    data_matrix, z_positions, n_points = create_topography_map(topografie_data, side)
                    
                    if data_matrix is not None:
                        fig, ax = plot_topography(data_matrix, z_positions, n_points, side_name, f" ({uploaded_file.name})")
                        st.pyplot(fig)
                        
                        st.markdown(f"**偏差范围:**")
                        col_a, col_b, col_c, col_d = st.columns(4)
                        with col_a:
                            st.metric("最小值", f"{np.min(data_matrix):.2f} µm")
                        with col_b:
                            st.metric("最大值", f"{np.max(data_matrix):.2f} µm")
                        with col_c:
                            st.metric("平均值", f"{np.mean(data_matrix):.2f} µm")
                        with col_d:
                            st.metric("标准差", f"{np.std(data_matrix):.2f} µm")
                else:
                    st.warning(f"未找到{side_name}的TOPOGRAFIE数据")
        
        st.markdown("---")
        st.markdown("### 拓普图说明")
        st.info("""
        **齿面TOPOGRAFIE拓普图** 显示整个齿面的偏差分布情况：
        - **X轴**: 齿高方向（从齿根到齿顶）
        - **Y轴**: 齿宽方向（从一端到另一端）
        - **颜色**: 偏差值（蓝色=负偏差，红色=正偏差）
        
        通过拓普图可以直观地看到齿面的加工误差分布，识别系统性偏差和局部缺陷。
        """)
    
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
                    order_type = '高阶 ★' if comp.order >= ze else '低阶'
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
    
    if os.path.exists(temp_path):
        os.remove(temp_path)

else:
    st.info("👆 请在左侧上传 MKA 文件开始分析")
    
    st.markdown("""
    ### 📋 功能说明
    
    本系统提供齿轮测量报告：
    
    | 功能 | 说明 |
    |------|------|
    | 📄 专业报告 | 齿形/齿向分析图表和数据表 |
    | 📊 周节详细报表 | 周节偏差 fp/Fp/Fr 分析 |
    | 🗺️ 齿面拓普图 | 齿面TOPOGRAFIE偏差热力图 |
    | 📈 单齿分析 | 单个齿的齿形/齿向偏差曲线 |
    | 📉 合并曲线 | 0-360°合并曲线、高阶波纹度评价 |
    | 📊 频谱分析 | 阶次振幅相位分析 |
    """)

st.markdown("---")
st.caption("齿轮测量报告系统 | 基于 Python + Streamlit 构建")
