"""
================================================================================
齿轮测量报告 Web 应用 - 完整专业报表版
Gear Measurement Report Web App - Full Professional Report
================================================================================

完全仿照 Klingelnberg 标准报告格式
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import sys
import os
from datetime import datetime
import tempfile

rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False

current_dir = os.path.dirname(os.path.abspath(__file__))
web_app_dir = os.path.dirname(current_dir)
project_dir = os.path.dirname(web_app_dir)

if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
if web_app_dir not in sys.path:
    sys.path.insert(0, web_app_dir)

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
        help="支持 Klingelnberg MKA 格式的齿轮测量数据文件"
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
        
        st.markdown("""
        ### 📋 专业报告生成
        
        点击下方按钮生成 Klingelnberg 标准格式 PDF 报告，包含：
        - 齿形/齿向分析图表和数据表
        - 周节分析页面 (fp, Fp, Fr)
        """)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("📄 生成专业 PDF 报告", type="primary", use_container_width=True):
                with st.spinner("正在生成 PDF 报告，请稍候..."):
                    try:
                        from gear_analysis_refactored.models.gear_data import create_gear_data_from_dict
                        from gear_analysis_refactored.utils.file_parser import parse_mka_file
                        from gear_analysis_refactored.reports.klingelnberg_single_page import KlingelnbergSinglePageReport
                        from gear_analysis_refactored.analysis.deviation_analyzer import DeviationAnalyzer
                        
                        data_dict = parse_mka_file(temp_path)
                        measurement_data = create_gear_data_from_dict(data_dict)
                        
                        gear_data = {
                            'module': measurement_data.basic_info.module,
                            'teeth': measurement_data.basic_info.teeth,
                            'width': measurement_data.basic_info.width,
                            'accuracy_grade': measurement_data.basic_info.accuracy_grade
                        }
                        dev_analyzer = DeviationAnalyzer(gear_data)
                        
                        deviation_results = {'profile': {}, 'flank': {}}
                        
                        for side in ['left', 'right']:
                            profile_data = getattr(measurement_data.profile_data, side, {})
                            flank_data = getattr(measurement_data.flank_data, side, {})
                            
                            for tooth_num, tooth_data in profile_data.items():
                                key = f"{'L' if side == 'left' else 'R'}{tooth_num}"
                                F_alpha, fH_alpha, ff_alpha = dev_analyzer.calculate_profile_deviations(tooth_data, side)
                                deviation_results['profile'][key] = {
                                    'F_alpha': F_alpha,
                                    'fH_alpha': fH_alpha,
                                    'ff_alpha': ff_alpha
                                }
                            
                            for tooth_num, tooth_data in flank_data.items():
                                key = f"{'L' if side == 'left' else 'R'}{tooth_num}"
                                F_beta, fH_beta, ff_beta = dev_analyzer.calculate_flank_deviations(tooth_data, side)
                                deviation_results['flank'][key] = {
                                    'F_beta': F_beta,
                                    'fH_beta': fH_beta,
                                    'ff_beta': ff_beta
                                }
                        
                        output_dir = os.path.join(os.path.dirname(__file__), "reports")
                        os.makedirs(output_dir, exist_ok=True)
                        
                        base_name = os.path.splitext(uploaded_file.name)[0]
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_path = os.path.join(output_dir, f"{base_name}_report_{timestamp}.pdf")
                        
                        reporter = KlingelnbergSinglePageReport()
                        success = reporter.generate_report(measurement_data, deviation_results, output_path)
                        
                        if success and os.path.exists(output_path):
                            st.success(f"✅ 报告生成成功！")
                            
                            with open(output_path, "rb") as f:
                                pdf_bytes = f.read()
                            
                            st.download_button(
                                label="📥 下载 PDF 报告",
                                data=pdf_bytes,
                                file_name=f"{base_name}_report.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                            
                            st.info(f"报告已保存至: {output_path}")
                        else:
                            st.error("❌ 报告生成失败，请检查日志")
                            
                    except Exception as e:
                        st.error(f"❌ 生成报告时出错: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
        
        st.markdown("---")
        st.markdown("### 📊 数据预览")
        
        st.markdown("#### 基本信息")
        col1, col2 = st.columns(2)
        
        with col1:
            header_data1 = {
                '参数': ['Prog.No.', 'Type', 'Drawing No.', 'Order No.', 'Cust./Mach. No.', 'Loc. of check', 'Condition:'],
                '值': [uploaded_file.name, 'gear', uploaded_file.name, '263751-018-WAV', '13305', 'VCST CZ', '']
            }
            st.table(header_data1)
        
        with col2:
            if gear_params:
                header_data2 = {
                    '参数': ['Operator', 'No. of teeth', 'Module m', 'Pressure angle', 'Helix angle', 'Base Cir. db', 'Base Helix ang'],
                    '值': ['Jun He', str(gear_params.teeth_count), f"{gear_params.module:.3f}mm",
                           f"{gear_params.pressure_angle}°", f"{gear_params.helix_angle}°",
                           f"{gear_params.base_diameter:.3f}mm", "0.000°"]
                }
            else:
                header_data2 = {
                    '参数': ['Operator', 'No. of teeth', 'Module m', 'Pressure angle', 'Helix angle', 'Base Cir. db', 'Base Helix ang'],
                    '值': ['Jun He', '-', '-', '-', '-', '-', '-']
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
        st.markdown("### 齿到齿周节偏差 fp")
        
        if pitch_left or pitch_right:
            fig, axes = plt.subplots(2, 1, figsize=(14, 10))
            
            if pitch_left:
                teeth = pitch_left.teeth
                fp_values = pitch_left.fp_values
                
                bars = axes[0].bar(teeth, fp_values, color='steelblue', alpha=0.7, edgecolor='black', linewidth=0.5)
                axes[0].axhline(y=0, color='red', linestyle='-', linewidth=1.5)
                
                fp_max_idx = fp_values.index(max(fp_values))
                fp_min_idx = fp_values.index(min(fp_values))
                axes[0].plot(teeth[fp_max_idx], fp_values[fp_max_idx], 'ro', markersize=10, label=f'Max: {fp_values[fp_max_idx]:.2f}')
                axes[0].plot(teeth[fp_min_idx], fp_values[fp_min_idx], 'go', markersize=10, label=f'Min: {fp_values[fp_min_idx]:.2f}')
                
                axes[0].set_title('Tooth to tooth spacing fp left flank', fontsize=14, fontweight='bold')
                axes[0].set_xlabel('Tooth Number', fontsize=12)
                axes[0].set_ylabel('fp (μm)', fontsize=12)
                axes[0].legend()
                axes[0].grid(True, alpha=0.3, axis='y')
            
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
        
        st.markdown("---")
        st.markdown("### 累积周节偏差 Fp")
        
        if pitch_left or pitch_right:
            fig, axes = plt.subplots(2, 1, figsize=(14, 10))
            
            if pitch_left:
                teeth = pitch_left.teeth
                Fp_values = pitch_left.Fp_values
                
                axes[0].plot(teeth, Fp_values, 'b-', linewidth=2, marker='o', markersize=4)
                axes[0].axhline(y=0, color='red', linestyle='--', linewidth=1)
                axes[0].fill_between(teeth, Fp_values, alpha=0.3, color='steelblue')
                
                Fp_max_idx = Fp_values.index(max(Fp_values))
                Fp_min_idx = Fp_values.index(min(Fp_values))
                axes[0].plot(teeth[Fp_max_idx], Fp_values[Fp_max_idx], 'ro', markersize=10, label=f'Max: {Fp_values[Fp_max_idx]:.2f}')
                axes[0].plot(teeth[Fp_min_idx], Fp_values[Fp_min_idx], 'go', markersize=10, label=f'Min: {Fp_values[Fp_min_idx]:.2f}')
                
                axes[0].set_title('Index Fp left flank', fontsize=14, fontweight='bold')
                axes[0].set_xlabel('Tooth Number', fontsize=12)
                axes[0].set_ylabel('Fp (μm)', fontsize=12)
                axes[0].legend()
                axes[0].grid(True, alpha=0.3)
            
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
        
        st.markdown("---")
        st.markdown("### 径向跳动 Fr")
        
        if pitch_left or pitch_right:
            fig, ax = plt.subplots(figsize=(14, 6))
            
            all_teeth = []
            all_Fp = []
            
            if pitch_left:
                all_teeth.extend(pitch_left.teeth)
                all_Fp.extend(pitch_left.Fp_values)
            
            if pitch_right:
                all_teeth.extend(pitch_right.teeth)
                all_Fp.extend(pitch_right.Fp_values)
            
            sorted_data = sorted(zip(all_teeth, all_Fp))
            all_teeth = [x[0] for x in sorted_data]
            all_Fp = [x[1] for x in sorted_data]
            
            ax.bar(all_teeth, all_Fp, color='steelblue', alpha=0.7, edgecolor='black', linewidth=0.5)
            
            if len(all_teeth) > 3:
                x_smooth = np.linspace(min(all_teeth), max(all_teeth), 200)
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
        
        st.markdown("---")
        st.markdown("### 详细数据表")
        
        if pitch_left or pitch_right:
            table_data = []
            
            all_teeth = set()
            if pitch_left:
                all_teeth.update(pitch_left.teeth)
            if pitch_right:
                all_teeth.update(pitch_right.teeth)
            
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
            
            st.markdown("---")
            st.markdown("### 统计汇总")
            
            summary_data = []
            if pitch_left:
                summary_data.append({
                    '参数': 'Worst single pitch deviation fp max',
                    '左齿面 Act.value': f"{pitch_left.fp_max:.2f}",
                    '右齿面 Act.value': f"{pitch_right.fp_max:.2f}" if pitch_right else '-'
                })
                summary_data.append({
                    '参数': 'Worst spacing deviation fu max',
                    '左齿面 Act.value': f"{pitch_left.fp_max:.2f}",
                    '右齿面 Act.value': f"{pitch_right.fp_max:.2f}" if pitch_right else '-'
                })
                summary_data.append({
                    '参数': 'Range of Pitch Error Rp',
                    '左齿面 Act.value': f"{pitch_left.Fp_max - pitch_left.Fp_min:.2f}",
                    '右齿面 Act.value': f"{pitch_right.Fp_max - pitch_right.Fp_min:.2f}" if pitch_right else '-'
                })
                summary_data.append({
                    '参数': 'Total cum. pitch dev. Fp',
                    '左齿面 Act.value': f"{pitch_left.Fp_max:.2f}",
                    '右齿面 Act.value': f"{pitch_right.Fp_max:.2f}" if pitch_right else '-'
                })
                summary_data.append({
                    '参数': 'Runout Fr',
                    '左齿面 Act.value': f"{pitch_left.Fr:.2f}",
                    '右齿面 Act.value': f"{pitch_right.Fr:.2f}" if pitch_right else '-'
                })
            
            st.table(summary_data)
    
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
                    
                    n_points = len(values)
                    idx_start = int(n_points * 0.1)
                    idx_end = int(n_points * 0.9)
                    ax.plot(x_data[idx_start:idx_end], values[idx_start:idx_end], 'r-', linewidth=2.5, label='评价范围')
                    ax.axvline(x=x_data[idx_start], color='green', linestyle='--', alpha=0.7)
                    ax.axvline(x=x_data[idx_end], color='green', linestyle='--', alpha=0.7)
                    
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
                    tooth_helices = helix_data[side][selected_tooth]
                    profile_mid = (profile_eval.eval_start + profile_eval.eval_end) / 2
                    best_d = None
                    best_values = None
                    
                    for d_pos, values in tooth_helices.items():
                        if best_d is None or abs(d_pos - profile_mid) < abs(best_d - profile_mid):
                            best_d = d_pos
                            best_values = values
                    
                    if best_values is not None:
                        fig, ax = plt.subplots(figsize=(8, 6))
                        x_data = np.linspace(helix_eval.meas_start, helix_eval.meas_end, len(best_values))
                        ax.plot(x_data, best_values, 'b-', linewidth=1.5, label='原始数据')
                        
                        n_points = len(best_values)
                        idx_start = int(n_points * 0.1)
                        idx_end = int(n_points * 0.9)
                        ax.plot(x_data[idx_start:idx_end], best_values[idx_start:idx_end], 'r-', linewidth=2.5, label='评价范围')
                        ax.axvline(x=x_data[idx_start], color='green', linestyle='--', alpha=0.7)
                        ax.axvline(x=x_data[idx_end], color='green', linestyle='--', alpha=0.7)
                        
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
                ax.set_xlabel('旋转角度 (deg)')
                ax.set_ylabel('偏差 (μm)')
                ax.set_title(f'{display_name} - 合并曲线 (ZE={ze})')
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, 360)
                st.pyplot(fig)
                
                if result.high_order_waves:
                    st.markdown("**高阶波数列表:**")
                    waves_str = ", ".join([f"{int(w['order'])}({w['amplitude']:.4f})" for w in result.high_order_waves[:10]])
                    if len(result.high_order_waves) > 10:
                        waves_str += " ..."
                    st.write(waves_str)
        
        st.markdown("---")
        st.markdown("### 高阶波纹度重构信号对比")
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        for idx, (name, result) in enumerate([
            ('左齿形', results.get('profile_left')),
            ('右齿形', results.get('profile_right')),
            ('左齿向', results.get('helix_left')),
            ('右齿向', results.get('helix_right'))
        ]):
            ax = axes[idx // 2, idx % 2]
            if result and len(result.angles) > 0:
                ax.plot(result.angles, result.values, 'b-', linewidth=0.3, alpha=0.5, label='原始曲线')
                ax.plot(result.angles, result.reconstructed_signal, 'r-', linewidth=1.5, label='高阶重构')
                ax.set_xlabel('旋转角度 (deg)')
                ax.set_ylabel('偏差 (μm)')
                ax.set_title(f'{name} - 高阶波纹度重构')
                ax.legend(fontsize=8)
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, 360)
            else:
                ax.text(0.5, 0.5, '无数据', ha='center', va='center', transform=ax.transAxes)
        
        plt.tight_layout()
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
            
            st.markdown(f"#### {name} - 前5个齿 (0° - {end_angle:.1f}°)")
            
            mask = result.angles <= end_angle
            if not np.any(mask):
                mask = result.angles < (end_angle + 10)
            
            angles_zoom = result.angles[mask]
            values_zoom = result.values[mask]
            recon_zoom = result.reconstructed_signal[mask]
            
            if len(angles_zoom) > 0:
                fig, ax = plt.subplots(figsize=(14, 5))
                
                # 使用散点图显示数据点，更清楚地看到波纹形状
                ax.scatter(angles_zoom, values_zoom, c='blue', s=2, alpha=0.6, label='原始数据点')
                ax.plot(angles_zoom, values_zoom, 'b-', linewidth=0.5, alpha=0.4)
                ax.plot(angles_zoom, recon_zoom, 'r-', linewidth=2, label='高阶重构')
                
                for i in range(1, 6):
                    ax.axvline(x=i*pitch_angle, color='green', linestyle='--', alpha=0.5, linewidth=1)
                    ax.text(i*pitch_angle - pitch_angle/2, max(values_zoom)*0.9, f'齿{i}', 
                           ha='center', fontsize=10, color='green')
                
                ax.set_xlabel('旋转角度 (deg)')
                ax.set_ylabel('偏差 (μm)')
                ax.set_title(f'{name} - 前5个齿放大 (每齿 {pitch_angle:.2f}°)')
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, end_angle)
                st.pyplot(fig)
                
                st.markdown(f"**数据点数:** {len(angles_zoom)}, **角度范围:** 0° - {max(angles_zoom):.1f}°")
    
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
                    
                    max_order = max(orders) if orders else ze * 4
                    max_amplitude = max(amplitudes) if amplitudes else 1.0
                    
                    ax.axvline(x=ze, color='green', linestyle='--', linewidth=2, label=f'ZE={ze}')
                    ax.text(ze, max_amplitude * 1.05, f'ZE={ze}', ha='center', fontsize=9, color='green')
                    
                    for i in range(2, int(max_order / ze) + 2):
                        ze_multiple = ze * i
                        if ze_multiple <= max_order + ze:
                            ax.axvline(x=ze_multiple, color='green', linestyle=':', alpha=0.5, linewidth=1)
                            ax.text(ze_multiple, max_amplitude * 1.05, f'{i}ZE', 
                                   ha='center', fontsize=8, color='green', alpha=0.7)
                    
                    ax.set_xlim(0, max(orders) + 20)
                else:
                    ax.text(0.5, 0.5, '无频谱数据', ha='center', va='center', transform=ax.transAxes)
                    ax.set_xlim(0, ze * 2)
                
                ax.set_xlabel('阶次 (Order)')
                ax.set_ylabel('振幅 (μm)')
                ax.set_title(f'{display_name} - 频谱图 (ZE={ze})')
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
        
        st.markdown("---")
        st.markdown("### 频谱对比分析")
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        for idx, (name, result) in enumerate([
            ('左齿形', results.get('profile_left')),
            ('右齿形', results.get('profile_right')),
            ('左齿向', results.get('helix_left')),
            ('右齿向', results.get('helix_right'))
        ]):
            ax = axes[idx // 2, idx % 2]
            if result and result.spectrum_components:
                sorted_comps = sorted(result.spectrum_components[:15], key=lambda c: c.order)
                orders = [c.order for c in sorted_comps]
                amplitudes = [c.amplitude for c in sorted_comps]
                
                if orders:
                    colors = ['red' if o >= ze else 'steelblue' for o in orders]
                    ax.bar(orders, amplitudes, color=colors, alpha=0.7, width=4)
                    ax.axvline(x=ze, color='green', linestyle='--', linewidth=2, label=f'ZE={ze}')
                    ax.set_xlabel('阶次')
                    ax.set_ylabel('振幅 (μm)')
                    ax.set_title(f'{name} - 频谱')
                    ax.legend(fontsize=8)
                    ax.grid(True, alpha=0.3)
            else:
                ax.text(0.5, 0.5, '无数据', ha='center', va='center', transform=ax.transAxes)
        
        plt.tight_layout()
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
    | 📄 专业报告 | 生成 PDF 报告（包含齿形/齿向/周节） |
    | 📊 周节详细报表 | 周节偏差 fp/Fp/Fr 分析和详细数据表 |
    | 📈 单齿分析 | 单个齿的齿形/齿向偏差曲线 |
    | 📉 合并曲线 | 0-360°合并曲线、极角计算、高阶波纹度评价 |
    | 📊 频谱分析 | 最小二乘法迭代分解、阶次振幅相位分析 |
    """)

st.markdown("---")
st.caption("齿轮测量报告系统 - 专业版 | 基于 Python + Streamlit 构建")
