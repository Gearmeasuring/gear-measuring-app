"""
================================================================================
齿轮测量报告 Web 应用 - 完整专业版 (使用 gear_analysis_refactored)
================================================================================

使用 gear_analysis_refactored 模块的完整功能
支持用户注册和登录
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.backends.backend_pdf import PdfPages
import sys
import os
import re
from datetime import datetime
from io import BytesIO
import tempfile
import pandas as pd

# 设置中文字体 - 使用系统可用字体
import matplotlib.font_manager as fm

# 尝试查找可用的中文字体
def get_chinese_font():
    """获取系统中可用的中文字体"""
    chinese_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun', 'NSimSun', 'FangSong', 'KaiTi',
                     'WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Source Han Sans CN',
                     'AR PL UMing CN', 'Droid Sans Fallback', 'DejaVu Sans']

    available_fonts = [f.name for f in fm.fontManager.ttflist]

    for font in chinese_fonts:
        if font in available_fonts:
            return font

    # 如果没有找到中文字体，返回默认字体
    return 'DejaVu Sans'

chinese_font = get_chinese_font()
rcParams['font.sans-serif'] = [chinese_font, 'DejaVu Sans', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入用户认证模块
from auth import (
    init_session_state, login_page, logout, get_current_user,
    register_user, login_user, change_password, admin_panel, is_admin
)

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

# 初始化用户认证状态
init_session_state()

# 如果用户未登录，显示登录页面
if not st.session_state.authenticated:
    login_page()
    st.stop()

# 用户已登录，显示主应用
st.set_page_config(
    page_title="Gear Measurement Report System - Professional",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    # 显示用户信息
    user = get_current_user()
    if user:
        st.success(f"👤 欢迎, {user['username']}!")
        if user.get('company'):
            st.caption(f"公司: {user['company']}")

    st.markdown("---")

    # 添加管理员面板按钮（仅管理员可见）
    if user and is_admin(user["username"]):
        if st.button("🔧 管理员面板", use_container_width=True):
            st.session_state.show_admin = True
            st.rerun()

    # 添加登出按钮
    if st.button("🚪 退出登录", use_container_width=True):
        logout()

    st.markdown("---")
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

# 检查是否显示管理员面板
if st.session_state.get('show_admin', False):
    admin_panel()
    st.stop()

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
        
        st.markdown("#### Basic Information")
        col1, col2 = st.columns(2)

        # 从解析器获取信息
        info = analyzer.reader.info if hasattr(analyzer.reader, 'info') else {}

        with col1:
            header_data1 = {
                'Parameter': ['Prog.No.', 'Type', 'Drawing No.', 'Order No.', 'Cust./Mach. No.', 'Loc. of check'],
                'Value': [
                    uploaded_file.name,
                    info.get('type_', 'gear'),
                    info.get('drawing_no', uploaded_file.name),
                    info.get('order_no', '-'),
                    info.get('customer', '-'),
                    info.get('location', '-')
                ]
            }
            st.table(header_data1)

        with col2:
            if gear_params:
                # 正确计算基圆直径
                import math
                beta = math.radians(abs(gear_params.helix_angle))
                alpha_n = math.radians(gear_params.pressure_angle)
                alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta)) if abs(beta) > 1e-6 else alpha_n
                pitch_diameter = gear_params.teeth_count * gear_params.module / math.cos(beta)
                base_diameter = pitch_diameter * math.cos(alpha_t)

                header_data2 = {
                    'Parameter': ['Operator', 'No. of teeth', 'Module m', 'Pressure angle', 'Helix angle', 'Base Cir. db'],
                    'Value': [
                        info.get('operator', 'Operator'),
                        str(gear_params.teeth_count),
                        f"{gear_params.module:.3f}mm",
                        f"{gear_params.pressure_angle}°",
                        f"{gear_params.helix_angle}°",
                        f"{base_diameter:.3f}mm"
                    ]
                }
            else:
                header_data2 = {
                    'Parameter': ['Operator', 'No. of teeth', 'Module m', 'Pressure angle', 'Helix angle', 'Base Cir. db'],
                    'Value': ['Operator', '-', '-', '-', '-', '-']
                }
            st.table(header_data2)
        
        st.markdown("---")
        st.markdown("### Gear Profile/Lead Charts")
        
        profile_data = analyzer.reader.profile_data
        helix_data = analyzer.reader.helix_data
        
        # 获取测量的齿号
        measured_teeth_profile = set()
        measured_teeth_helix = set()
        for side in ['left', 'right']:
            if side in profile_data:
                measured_teeth_profile.update(profile_data[side].keys())
            if side in helix_data:
                measured_teeth_helix.update(helix_data[side].keys())
        
        # 选择要显示的齿（最多6个，类似PDF）
        display_teeth = sorted(list(measured_teeth_profile))[:6]
        if not display_teeth and gear_params:
            display_teeth = list(range(1, min(7, gear_params.teeth_count + 1)))
        
        # 左齿形图表
        st.markdown("#### Left Flank - Profile")
        if display_teeth:
            cols = st.columns(min(6, len(display_teeth)))
            for i, tooth_id in enumerate(display_teeth[:len(cols)]):
                with cols[i]:
                    if tooth_id in profile_data.get('left', {}):
                        tooth_profiles = profile_data['left'][tooth_id]
                        helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                        best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                        values = tooth_profiles[best_z]
                        
                        fig, ax = plt.subplots(figsize=(3, 6))
                        x_positions = np.linspace(0, 8, len(values))
                        
                        # 绘制曲线（类似PDF样式）
                        ax.plot(values, x_positions, 'b-', linewidth=1.0, label='Profile')
                        
                        # 添加网格
                        ax.grid(True, linestyle='-', alpha=0.3, color='gray')
                        ax.set_xlabel('Deviation (μm)', fontsize=7)
                        ax.set_ylabel('Length (mm)', fontsize=7)
                        ax.set_title(f'{tooth_id}', fontsize=9, fontweight='bold')
                        ax.tick_params(axis='both', which='major', labelsize=6)
                        
                        plt.tight_layout()
                        st.pyplot(fig)
        
        # 右齿形图表
        st.markdown("#### Right Flank - Profile")
        if display_teeth:
            cols = st.columns(min(6, len(display_teeth)))
            for i, tooth_id in enumerate(display_teeth[:len(cols)]):
                with cols[i]:
                    if tooth_id in profile_data.get('right', {}):
                        tooth_profiles = profile_data['right'][tooth_id]
                        helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                        best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                        values = tooth_profiles[best_z]
                        
                        fig, ax = plt.subplots(figsize=(3, 6))
                        x_positions = np.linspace(0, 8, len(values))
                        
                        ax.plot(values, x_positions, 'b-', linewidth=1.0, label='Profile')
                        ax.grid(True, linestyle='-', alpha=0.3, color='gray')
                        ax.set_xlabel('Deviation (μm)', fontsize=7)
                        ax.set_ylabel('Length (mm)', fontsize=7)
                        ax.set_title(f'{tooth_id}', fontsize=9, fontweight='bold')
                        ax.tick_params(axis='both', which='major', labelsize=6)
                        
                        plt.tight_layout()
                        st.pyplot(fig)
        
        # 左齿向图表
        st.markdown("#### Left Flank - Lead")
        if display_teeth:
            cols = st.columns(min(6, len(display_teeth)))
            for i, tooth_id in enumerate(display_teeth[:len(cols)]):
                with cols[i]:
                    if tooth_id in helix_data.get('left', {}):
                        tooth_helix = helix_data['left'][tooth_id]
                        profile_mid = (profile_eval.eval_start + profile_eval.eval_end) / 2
                        best_d = min(tooth_helix.keys(), key=lambda d: abs(d - profile_mid))
                        values = tooth_helix[best_d]
                        
                        fig, ax = plt.subplots(figsize=(3, 6))
                        # 从 b1 和 b2 计算齿宽
                        face_width = abs(b2 - b1) if b1 is not None and b2 is not None else 78
                        x_positions = np.linspace(0, face_width, len(values))
                        
                        ax.plot(values, x_positions, 'b-', linewidth=1.0, label='Lead')
                        ax.grid(True, linestyle='-', alpha=0.3, color='gray')
                        ax.set_xlabel('Deviation (μm)', fontsize=7)
                        ax.set_ylabel('Face Width (mm)', fontsize=7)
                        ax.set_title(f'{tooth_id}', fontsize=9, fontweight='bold')
                        ax.tick_params(axis='both', which='major', labelsize=6)
                        
                        plt.tight_layout()
                        st.pyplot(fig)
        
        # 右齿向图表
        st.markdown("#### Right Flank - Lead")
        if display_teeth:
            cols = st.columns(min(6, len(display_teeth)))
            for i, tooth_id in enumerate(display_teeth[:len(cols)]):
                with cols[i]:
                    if tooth_id in helix_data.get('right', {}):
                        tooth_helix = helix_data['right'][tooth_id]
                        profile_mid = (profile_eval.eval_start + profile_eval.eval_end) / 2
                        best_d = min(tooth_helix.keys(), key=lambda d: abs(d - profile_mid))
                        values = tooth_helix[best_d]
                        
                        fig, ax = plt.subplots(figsize=(3, 6))
                        # 从 b1 和 b2 计算齿宽
                        face_width = abs(b2 - b1) if b1 is not None and b2 is not None else 78
                        x_positions = np.linspace(0, face_width, len(values))
                        
                        ax.plot(values, x_positions, 'b-', linewidth=1.0, label='Lead')
                        ax.grid(True, linestyle='-', alpha=0.3, color='gray')
                        ax.set_xlabel('Deviation (μm)', fontsize=7)
                        ax.set_ylabel('Face Width (mm)', fontsize=7)
                        ax.set_title(f'{tooth_id}', fontsize=9, fontweight='bold')
                        ax.tick_params(axis='both', which='major', labelsize=6)
                        
                        plt.tight_layout()
                        st.pyplot(fig)
            
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
                import math
                beta = math.radians(abs(gear_params.helix_angle))
                pitch_diameter = gear_params.teeth_count * gear_params.module / math.cos(beta) if gear_params.module > 0 else 0
                header_data2 = {
                    '参数': ['No. of teeth', 'Module m', 'Pressure angle', 'Helix angle', 'Pitch diameter'],
                    '值': [
                        str(gear_params.teeth_count),
                        f"{gear_params.module:.3f}mm",
                        f"{gear_params.pressure_angle}°",
                        f"{gear_params.helix_angle}°",
                        f"{pitch_diameter:.3f}mm"
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
        st.markdown("### Pitch Deviation Charts")

        # 获取pitch数据
        pitch_data_left = analyzer.reader.pitch_data.get('left', {})
        pitch_data_right = analyzer.reader.pitch_data.get('right', {})

        # 左齿面图表
        if pitch_data_left and 'teeth' in pitch_data_left:
            st.subheader("Left Flank Pitch Deviation")
            teeth_left = pitch_data_left['teeth']
            fp_values_left = pitch_data_left['fp_values']
            Fp_values_left = pitch_data_left['Fp_values']

            # 调整Fp值（从0开始）
            if Fp_values_left:
                first_value = Fp_values_left[0]
                Fp_values_adjusted = [fp - first_value for fp in Fp_values_left]
            else:
                Fp_values_adjusted = []

            col1, col2 = st.columns(2)

            with col1:
                # fp柱状图
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.bar(teeth_left, fp_values_left, color='white', edgecolor='black', width=1.0, linewidth=0.5)
                ax.set_title('Tooth to tooth spacing fp left flank', fontsize=10, fontweight='bold')
                ax.set_xlabel('Tooth Number')
                ax.set_ylabel('fp (μm)')
                ax.grid(True, linestyle=':', alpha=0.5)
                ax.set_xlim(0, len(teeth_left)+1)
                st.pyplot(fig)

            with col2:
                # Fp曲线图
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.plot(teeth_left, Fp_values_adjusted, 'k-', linewidth=1.0)
                ax.set_title('Index Fp left flank', fontsize=10, fontweight='bold')
                ax.set_xlabel('Tooth Number')
                ax.set_ylabel('Fp (μm)')
                ax.grid(True, linestyle=':', alpha=0.5)
                ax.set_xlim(0, len(teeth_left)+1)
                st.pyplot(fig)

        # 右齿面图表
        if pitch_data_right and 'teeth' in pitch_data_right:
            st.subheader("Right Flank Pitch Deviation")
            teeth_right = pitch_data_right['teeth']
            fp_values_right = pitch_data_right['fp_values']
            Fp_values_right = pitch_data_right['Fp_values']

            # 调整Fp值（从0开始）
            if Fp_values_right:
                first_value = Fp_values_right[0]
                Fp_values_adjusted = [fp - first_value for fp in Fp_values_right]
            else:
                Fp_values_adjusted = []

            col1, col2 = st.columns(2)

            with col1:
                # fp柱状图
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.bar(teeth_right, fp_values_right, color='white', edgecolor='black', width=1.0, linewidth=0.5)
                ax.set_title('Tooth to tooth spacing fp right flank', fontsize=10, fontweight='bold')
                ax.set_xlabel('Tooth Number')
                ax.set_ylabel('fp (μm)')
                ax.grid(True, linestyle=':', alpha=0.5)
                ax.set_xlim(0, len(teeth_right)+1)
                st.pyplot(fig)

            with col2:
                # Fp曲线图
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.plot(teeth_right, Fp_values_adjusted, 'k-', linewidth=1.0)
                ax.set_title('Index Fp right flank', fontsize=10, fontweight='bold')
                ax.set_xlabel('Tooth Number')
                ax.set_ylabel('Fp (μm)')
                ax.grid(True, linestyle=':', alpha=0.5)
                ax.set_xlim(0, len(teeth_right)+1)
                st.pyplot(fig)

        st.markdown("---")
        st.markdown("### Runout")

        # Runout图表
        if pitch_data_left and 'teeth' in pitch_data_left:
            teeth = pitch_data_left['teeth']
            runout_values = pitch_data_left['Fp_values']

            if teeth and runout_values:
                fig, ax = plt.subplots(figsize=(12, 5))

                # 绘制柱状图
                ax.bar(teeth, runout_values, color='white', edgecolor='black', width=1.0, linewidth=0.5, label='Runout')

                # 绘制正弦拟合曲线
                if len(teeth) > 2:
                    import numpy as np
                    x_smooth = np.linspace(min(teeth), max(teeth), 200)
                    amplitude = (max(runout_values) - min(runout_values)) / 2
                    mid = (max(runout_values) + min(runout_values)) / 2
                    period = len(teeth)
                    y_smooth = mid + amplitude * np.sin(2 * np.pi * (x_smooth - min(teeth)) / period)
                    ax.plot(x_smooth, y_smooth, 'k-', linewidth=1.5, label='Sine fit')

                ax.set_title('Runout Fr (Ball-Ø =3mm)', fontsize=12, fontweight='bold')
                ax.set_xlabel('Tooth Number')
                ax.set_ylabel('Fr (μm)')
                ax.grid(True, linestyle=':', alpha=0.5)
                ax.set_xlim(0, len(teeth)+1)
                ax.legend()
                st.pyplot(fig)

        st.markdown("---")
        st.markdown("### Pitch Deviation Statistics")

        # 计算统计数据
        def calc_pitch_stats(pitch_data):
            """Calculate pitch deviation statistics"""
            if not pitch_data or 'teeth' not in pitch_data:
                return {}

            teeth = pitch_data['teeth']
            fp_vals = pitch_data['fp_values']
            Fp_vals = pitch_data['Fp_values']

            if not fp_vals or not Fp_vals:
                return {}

            # Worst single pitch deviation fp max
            fp_max = max([abs(x) for x in fp_vals]) if fp_vals else 0

            # Worst spacing deviation fu max (相邻齿距偏差的最大差值)
            fu_max = max([abs(fp_vals[i] - fp_vals[i-1]) for i in range(1, len(fp_vals))]) if len(fp_vals) > 1 else 0

            # Range of Pitch Error Rp
            Rp = max(fp_vals) - min(fp_vals) if fp_vals else 0

            # Total cum. pitch dev. Fp
            Fp_total = max(Fp_vals) - min(Fp_vals) if Fp_vals else 0

            # Cum. pitch deviation Fp10 (k=10的累积偏差)
            k = 10
            Fp10_max = 0
            if len(fp_vals) > k:
                extended_fp = fp_vals + fp_vals[:k]
                window_sums = []
                for i in range(len(fp_vals)):
                    window_sum = sum(extended_fp[i:i+k])
                    window_sums.append(window_sum)
                Fp10_max = max([abs(x) for x in window_sums]) if window_sums else 0

            return {
                'fp_max': fp_max,
                'fu_max': fu_max,
                'Rp': Rp,
                'Fp': Fp_total,
                'Fp10': Fp10_max
            }

        left_stats = calc_pitch_stats(pitch_data_left)
        right_stats = calc_pitch_stats(pitch_data_right)

        # 创建统计表格
        if left_stats or right_stats:
            st.subheader("Pitch measuring circle:")

            # 构建表格数据
            table_data = {
                '': [
                    'Worst single pitch deviation fp max',
                    'Worst spacing deviation fu max',
                    'Range of Pitch Error Rp',
                    'Total cum. pitch dev. Fp',
                    'Cum. pitch deviation Fp10'
                ],
                'left flank Act.value': [
                    f"{left_stats.get('fp_max', 0):.1f}" if left_stats else '',
                    f"{left_stats.get('fu_max', 0):.1f}" if left_stats else '',
                    f"{left_stats.get('Rp', 0):.1f}" if left_stats else '',
                    f"{left_stats.get('Fp', 0):.1f}" if left_stats else '',
                    f"{left_stats.get('Fp10', 0):.1f}" if left_stats else ''
                ],
                'left flank Qual.': ['', '', '', '', ''],
                'left flank Lim.value Qual.': ['12 5', '', '', '36 5', ''],
                'right flank Act.value': [
                    f"{right_stats.get('fp_max', 0):.1f}" if right_stats else '',
                    f"{right_stats.get('fu_max', 0):.1f}" if right_stats else '',
                    f"{right_stats.get('Rp', 0):.1f}" if right_stats else '',
                    f"{right_stats.get('Fp', 0):.1f}" if right_stats else '',
                    f"{right_stats.get('Fp10', 0):.1f}" if right_stats else ''
                ],
                'right flank Qual.': ['', '', '', '', ''],
                'right flank Lim.value Qual.': ['12 5', '', '', '36 5', '']
            }

            df_stats = pd.DataFrame(table_data)
            st.dataframe(df_stats, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### Pitch Deviation Detail Data")

        # 左齿面数据表
        if pitch_left and pitch_left.teeth:
            st.subheader("Left Flank Pitch")
            df_left = pd.DataFrame({
                'Tooth Number': pitch_left.teeth,
                'fp (μm)': pitch_left.fp_values,
                'Fp (μm)': pitch_left.Fp_values
            })
            st.dataframe(df_left, use_container_width=True)

        # 右齿面数据表
        if pitch_right and pitch_right.teeth:
            st.subheader("Right Flank Pitch")
            df_right = pd.DataFrame({
                'Tooth Number': pitch_right.teeth,
                'fp (μm)': pitch_right.fp_values,
                'Fp (μm)': pitch_right.Fp_values
            })
            st.dataframe(df_right, use_container_width=True)

    elif page == '📈 单齿分析':
        st.markdown("## Single Tooth Analysis")

        profile_data = analyzer.reader.profile_data
        helix_data = analyzer.reader.helix_data
        
        # 获取所有有测量数据的齿
        measured_teeth = set()
        for side in ['left', 'right']:
            if side in profile_data:
                measured_teeth.update(profile_data[side].keys())
            if side in helix_data:
                measured_teeth.update(helix_data[side].keys())
        
        # 按顺序排列有测量数据的齿
        measured_teeth_list = sorted(list(measured_teeth))
        
        if not measured_teeth_list:
            st.warning("未找到测量数据")
        else:
            # 使用下拉框选择有测量数据的齿
            selected_tooth = st.selectbox("Select Tooth Number", options=measured_teeth_list)
        
        # 获取齿轮参数
        ze = gear_params.teeth_count if gear_params else 87
        
        # 齿形分析
        st.markdown("### Profile Analysis")
        for side in ['left', 'right']:
            side_name = 'Left Profile' if side == 'left' else 'Right Profile'
            
            if selected_tooth in profile_data.get(side, {}):
                st.markdown(f"#### {side_name} - Tooth {selected_tooth}")
                
                # 获取数据
                tooth_profiles = profile_data[side][selected_tooth]
                helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                raw_values = np.array(tooth_profiles[best_z])
                
                # 截取评价范围内的数据
                d1, d2 = analyzer.reader.d1, analyzer.reader.d2
                da, de = d1, d2  # 默认使用评估范围
                
                # 解析测量范围
                da_match = re.search(r'Start\s+Messbereich.*?da\s*\[mm\]\.*:\s*([\d.]+)', analyzer.reader.raw_content or "", re.IGNORECASE)
                if da_match:
                    da = float(da_match.group(1))
                de_match = re.search(r'Ende\s+der\s+Messstrecke.*?de\s*\[mm\]\.*:\s*([\d.]+)', analyzer.reader.raw_content or "", re.IGNORECASE)
                if de_match:
                    de = float(de_match.group(1))
                
                # 计算展长范围
                base_radius = gear_params.base_diameter / 2 if gear_params else 80
                meas_start_radius = da / 2.0
                meas_end_radius = de / 2.0
                eval_start_radius = d1 / 2.0
                eval_end_radius = d2 / 2.0
                
                meas_start_spread = np.sqrt(max(0, meas_start_radius**2 - base_radius**2))
                meas_end_spread = np.sqrt(max(0, meas_end_radius**2 - base_radius**2))
                eval_start_spread = np.sqrt(max(0, eval_start_radius**2 - base_radius**2))
                eval_end_spread = np.sqrt(max(0, eval_end_radius**2 - base_radius**2))
                
                # 截取评价范围内的数据
                total_spread = meas_end_spread - meas_start_spread
                if total_spread > 0:
                    start_ratio = (eval_start_spread - meas_start_spread) / total_spread
                    end_ratio = (eval_end_spread - meas_start_spread) / total_spread
                    
                    n_total = len(raw_values)
                    start_idx = max(0, int(start_ratio * n_total))
                    end_idx = min(n_total, int(end_ratio * n_total))
                    
                    if end_idx - start_idx > 10:
                        raw_values = raw_values[start_idx:end_idx]
                
                # 去除鼓形和斜率
                values = analyzer._remove_crown_and_slope(raw_values)
                
                # 计算频谱
                if len(values) > 8:
                    # 创建角度数组（0-360度）
                    angles = np.linspace(0, 360, len(values))
                    # 计算频谱
                    spectrum_components = analyzer._iterative_sine_decomposition(angles, values, num_components=10, max_order=50)
                    
                    # 显示指标
                    if spectrum_components:
                        col1, col2, col3, col4 = st.columns(4)
                        max_comp = spectrum_components[0]
                        high_order_comps = [c for c in spectrum_components if c.order >= ze]
                        
                        with col1:
                            st.metric("Max Amplitude", f"{max_comp.amplitude:.4f} μm")
                        with col2:
                            st.metric("Max Order", int(max_comp.order))
                        with col3:
                            st.metric("Wave Count", len(spectrum_components))
                        with col4:
                            rms = np.sqrt(np.mean([c.amplitude**2 for c in high_order_comps])) if high_order_comps else 0
                            st.metric("High Order RMS", f"{rms:.4f} μm")
                
                # 创建曲线图
                fig, ax = plt.subplots(figsize=(10, 5))
                
                # 计算展长作为X轴
                d1, d2 = analyzer.reader.d1, analyzer.reader.d2
                
                # 展长计算
                base_radius = gear_params.base_diameter / 2 if gear_params else 80
                eval_start_radius = d1 / 2.0
                eval_end_radius = d2 / 2.0
                eval_start_spread = np.sqrt(max(0, eval_start_radius**2 - base_radius**2))
                eval_end_spread = np.sqrt(max(0, eval_end_radius**2 - base_radius**2))
                
                x_data = np.linspace(eval_start_spread, eval_end_spread, len(values))
                
                ax.plot(x_data, values, 'b-', linewidth=1.0, label='Raw Data')
                
                # 标记评价范围
                ax.axvline(x=eval_start_spread, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label=f'Eval Start')
                ax.axvline(x=eval_end_spread, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label=f'Eval End')
                
                ax.set_title(f"{side_name} - Tooth {selected_tooth}", fontsize=12, fontweight='bold')
                ax.set_xlabel("Spread Length (mm)")
                ax.set_ylabel("Deviation (μm)")
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
        
        # 齿向分析
        st.markdown("### Lead Analysis")
        for side in ['left', 'right']:
            side_name = 'Left Lead' if side == 'left' else 'Right Lead'
            
            if selected_tooth in helix_data.get(side, {}):
                st.markdown(f"#### {side_name} - Tooth {selected_tooth}")
                
                # 获取数据
                tooth_helix = helix_data[side][selected_tooth]
                profile_mid = (profile_eval.eval_start + profile_eval.eval_end) / 2
                best_d = min(tooth_helix.keys(), key=lambda d: abs(d - profile_mid))
                raw_values = np.array(tooth_helix[best_d])
                
                # 截取评价范围内的数据
                b1, b2 = analyzer.reader.b1, analyzer.reader.b2
                ba, be = b1, b2  # 默认使用评估范围
                
                # 解析测量范围
                ba_match = re.search(r'Messanfang.*?ba\s*\[mm\]\.*:\s*([\d.]+)', analyzer.reader.raw_content or "", re.IGNORECASE)
                if ba_match:
                    ba = float(ba_match.group(1))
                be_match = re.search(r'Messende.*?be\s*\[mm\]\.*:\s*([\d.]+)', analyzer.reader.raw_content or "", re.IGNORECASE)
                if be_match:
                    be = float(be_match.group(1))
                
                # 截取评价范围内的数据
                meas_length = be - ba
                if meas_length > 0:
                    start_ratio = (min(b1, b2) - ba) / meas_length
                    end_ratio = (max(b1, b2) - ba) / meas_length
                    
                    n_total = len(raw_values)
                    start_idx = max(0, int(start_ratio * n_total))
                    end_idx = min(n_total, int(end_ratio * n_total))
                    
                    if end_idx - start_idx > 10:
                        raw_values = raw_values[start_idx:end_idx]
                
                # 去除鼓形和斜率
                values = analyzer._remove_crown_and_slope(raw_values)
                
                # 计算频谱
                if len(values) > 8:
                    angles = np.linspace(0, 360, len(values))
                    spectrum_components = analyzer._iterative_sine_decomposition(angles, values, num_components=10, max_order=50)
                    
                    # 显示指标
                    if spectrum_components:
                        col1, col2, col3, col4 = st.columns(4)
                        max_comp = spectrum_components[0]
                        high_order_comps = [c for c in spectrum_components if c.order >= ze]
                        
                        with col1:
                            st.metric("Max Amplitude", f"{max_comp.amplitude:.4f} μm")
                        with col2:
                            st.metric("Max Order", int(max_comp.order))
                        with col3:
                            st.metric("Wave Count", len(spectrum_components))
                        with col4:
                            rms = np.sqrt(np.mean([c.amplitude**2 for c in high_order_comps])) if high_order_comps else 0
                            st.metric("High Order RMS", f"{rms:.4f} μm")
                
                # 创建曲线图
                fig, ax = plt.subplots(figsize=(10, 5))
                
                # 齿向位置作为X轴
                b1, b2 = analyzer.reader.b1, analyzer.reader.b2
                
                x_data = np.linspace(b1, b2, len(values))
                
                ax.plot(x_data, values, 'g-', linewidth=1.0, label='Raw Data')
                
                # 标记评价范围
                ax.axvline(x=b1, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label=f'b1={b1:.2f}')
                ax.axvline(x=b2, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label=f'b2={b2:.2f}')
                
                ax.set_title(f"{side_name} - Tooth {selected_tooth}", fontsize=12, fontweight='bold')
                ax.set_xlabel("Face Width Position (mm)")
                ax.set_ylabel("Deviation (μm)")
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
        
        # 单齿扩展合并曲线
        st.markdown("---")
        st.markdown("### Single Tooth Expanded Merged Curve (0-360°)")
        st.info("将单齿曲线复制到所有齿，形成完整的0-360°合并曲线，用于计算完整频谱")
        
        pitch_angle = 360.0 / ze if ze > 0 else 4.14
        
        for side in ['left', 'right']:
            side_name = 'Left Profile' if side == 'left' else 'Right Profile'
            
            if selected_tooth in profile_data.get(side, {}):
                # 获取单齿数据
                tooth_profiles = profile_data[side][selected_tooth]
                helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                raw_values = np.array(tooth_profiles[best_z])
                
                # 截取评价范围内的数据
                d1, d2 = analyzer.reader.d1, analyzer.reader.d2
                da, de = d1, d2
                
                # 解析测量范围
                da_match = re.search(r'Start\s+Messbereich.*?da\s*\[mm\]\.*:\s*([\d.]+)', analyzer.reader.raw_content or "", re.IGNORECASE)
                if da_match:
                    da = float(da_match.group(1))
                de_match = re.search(r'Ende\s+der\s+Messstrecke.*?de\s*\[mm\]\.*:\s*([\d.]+)', analyzer.reader.raw_content or "", re.IGNORECASE)
                if de_match:
                    de = float(de_match.group(1))
                
                # 计算展长范围
                base_radius = gear_params.base_diameter / 2 if gear_params else 80
                meas_start_radius = da / 2.0
                meas_end_radius = de / 2.0
                eval_start_radius = d1 / 2.0
                eval_end_radius = d2 / 2.0
                
                meas_start_spread = np.sqrt(max(0, meas_start_radius**2 - base_radius**2))
                meas_end_spread = np.sqrt(max(0, meas_end_radius**2 - base_radius**2))
                eval_start_spread = np.sqrt(max(0, eval_start_radius**2 - base_radius**2))
                eval_end_spread = np.sqrt(max(0, eval_end_radius**2 - base_radius**2))
                
                # 截取评价范围内的数据
                total_spread = meas_end_spread - meas_start_spread
                if total_spread > 0:
                    start_ratio = (eval_start_spread - meas_start_spread) / total_spread
                    end_ratio = (eval_end_spread - meas_start_spread) / total_spread
                    
                    n_total = len(raw_values)
                    start_idx = max(0, int(start_ratio * n_total))
                    end_idx = min(n_total, int(end_ratio * n_total))
                    
                    if end_idx - start_idx > 10:
                        raw_values = raw_values[start_idx:end_idx]
                
                # 去除鼓形和斜率
                values = analyzer._remove_crown_and_slope(raw_values)
                
                if len(values) > 5:
                    # 使用展角计算单齿的角度数组
                    # 展角 θ = L / rb (展长 / 基圆半径)
                    n = len(values)
                    spread_lengths = np.linspace(eval_start_spread, eval_end_spread, n)
                    roll_angles = spread_lengths / base_radius  # 展角（弧度）
                    
                    # 起始展角为0
                    start_roll_angle = roll_angles[0]
                    point_angles_deg = np.degrees(roll_angles - start_roll_angle)
                    single_angles = point_angles_deg  # 单齿内的角度变化
                    
                    # 扩展到所有齿
                    expanded_angles = []
                    expanded_values = []
                    
                    for tooth_num in range(ze):
                        tooth_base = tooth_num * pitch_angle
                        for angle, value in zip(single_angles, values):
                            new_angle = tooth_base + angle
                            if new_angle < 360:
                                expanded_angles.append(new_angle)
                                expanded_values.append(value)
                    
                    expanded_angles = np.array(expanded_angles)
                    expanded_values = np.array(expanded_values)
                    
                    # 排序
                    sort_idx = np.argsort(expanded_angles)
                    expanded_angles = expanded_angles[sort_idx]
                    expanded_values = expanded_values[sort_idx]
                    
                    # 计算高阶重建信号
                    angles_rad = np.deg2rad(expanded_angles)
                    reconstructed = np.zeros_like(expanded_values)
                    
                    # 计算频谱
                    if len(expanded_angles) > 8:
                        spectrum_components = analyzer._iterative_sine_decomposition(expanded_angles, expanded_values, num_components=10, max_order=5*ze)
                        high_order_comps = [c for c in spectrum_components if c.order >= ze]
                        
                        for comp in high_order_comps:
                            a = comp.amplitude * np.sin(comp.phase)
                            b = comp.amplitude * np.cos(comp.phase)
                            reconstructed += a * np.cos(comp.order * angles_rad) + b * np.sin(comp.order * angles_rad)
                        
                        # 显示指标
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            high_order_amplitude = sum(c.amplitude for c in high_order_comps) if high_order_comps else 0.0
                            st.metric("High Order Amplitude W", f"{high_order_amplitude:.4f} μm")
                        with col2:
                            high_order_rms = np.sqrt(sum(c.amplitude**2 for c in high_order_comps)) if high_order_comps else 0.0
                            st.metric("High Order RMS", f"{high_order_rms:.4f} μm")
                        with col3:
                            st.metric("High Order Wave Count", len(high_order_comps))
                        with col4:
                            if spectrum_components:
                                st.metric("Dominant Order", int(spectrum_components[0].order))
                    
                    # 绘制合并曲线
                    fig, ax = plt.subplots(figsize=(14, 5))
                    ax.plot(expanded_angles, expanded_values, 'b-', linewidth=0.5, alpha=0.7, label='Raw Curve')
                    ax.plot(expanded_angles, reconstructed, 'r-', linewidth=1.5, label='High Order Reconstruction')
                    
                    # 添加齿数标志
                    for tooth_num in range(ze + 1):
                        tooth_angle = tooth_num * pitch_angle
                        if tooth_angle <= 360:
                            ax.axvline(x=tooth_angle, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
                            if tooth_num % 5 == 0 or tooth_num == ze:
                                ax.text(tooth_angle, ax.get_ylim()[1] * 0.95, str(tooth_num), 
                                       ha='center', va='top', fontsize=7, color='gray', alpha=0.7)
                    
                    ax.set_xlabel('Rotation Angle (°)')
                    ax.set_ylabel('Deviation (μm)')
                    ax.set_title(f'{side_name} - Single Tooth Expanded Merged Curve (ZE={ze})')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    ax.set_xlim(0, 360)
                    st.pyplot(fig)
                    
                    # 显示单齿扩展合并曲线的频谱图
                    if spectrum_components:
                        st.markdown(f"**{side_name} - Single Tooth Expanded Spectrum**")
                        
                        col1, col2 = st.columns([3, 2])
                        
                        with col1:
                            # Top 10 阶次表格
                            st.markdown("**Top 10 Largest Orders:**")
                            top_10_data = []
                            for i, comp in enumerate(spectrum_components[:10], 1):
                                top_10_data.append({
                                    'Rank': i,
                                    'Order': int(comp.order),
                                    'Amplitude (μm)': f"{comp.amplitude:.4f}",
                                    'Phase (°)': f"{np.degrees(comp.phase):.1f}"
                                })
                            st.dataframe(pd.DataFrame(top_10_data), use_container_width=True, hide_index=True)
                        
                        with col2:
                            # 频谱图
                            fig2, ax2 = plt.subplots(figsize=(8, 5))
                            
                            orders = [c.order for c in spectrum_components[:15]]
                            amplitudes = [c.amplitude for c in spectrum_components[:15]]
                            
                            colors = ['red' if o >= ze else 'steelblue' for o in orders]
                            ax2.bar(orders, amplitudes, color=colors, alpha=0.7)
                            
                            # 标记ZE及其倍数
                            ze_multiples = [ze * i for i in range(1, 5) if ze * i <= max(orders)]
                            for i, ze_mult in enumerate(ze_multiples, 1):
                                if i == 1:
                                    ax2.axvline(x=ze_mult, color='green', linestyle='--', linewidth=2, label=f'ZE={ze}')
                                else:
                                    ax2.axvline(x=ze_mult, color='orange', linestyle=':', linewidth=1.5, alpha=0.7)
                            
                            ax2.set_title(f'Single Tooth Expanded Spectrum (ZE={ze})', fontsize=10, fontweight='bold')
                            ax2.set_xlabel('Order')
                            ax2.set_ylabel('Amplitude (μm)')
                            ax2.legend()
                            ax2.grid(True, alpha=0.3)
                            st.pyplot(fig2)
                    
                    # 显示前5个齿的放大视图
                    st.markdown(f"**{side_name} - First 5 Teeth Zoom View**")
                    
                    # 计算前5个齿的角度范围
                    end_angle = 5 * pitch_angle
                    zoom_mask = expanded_angles <= end_angle
                    zoom_angles = expanded_angles[zoom_mask]
                    zoom_values = expanded_values[zoom_mask]
                    zoom_reconstructed = reconstructed[zoom_mask]
                    
                    if len(zoom_angles) > 0:
                        fig3, ax3 = plt.subplots(figsize=(12, 4))
                        
                        # 降采样以改善显示
                        if len(zoom_angles) > 5000:
                            step = len(zoom_angles) // 2000 + 1
                            zoom_angles = zoom_angles[::step]
                            zoom_values = zoom_values[::step]
                            zoom_reconstructed = zoom_reconstructed[::step]
                        
                        ax3.plot(zoom_angles, zoom_values, 'b-', linewidth=1.0, alpha=0.8, label='Raw Curve')
                        ax3.plot(zoom_angles, zoom_reconstructed, 'r-', linewidth=2.0, label='High Order Reconstruction')
                        
                        # 添加齿数标志
                        for tooth_num in range(6):  # 0到5
                            tooth_angle = tooth_num * pitch_angle
                            if tooth_angle <= end_angle:
                                ax3.axvline(x=tooth_angle, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
                                ax3.text(tooth_angle, ax3.get_ylim()[1] * 0.95, str(tooth_num), 
                                        ha='center', va='top', fontsize=8, color='gray', alpha=0.7)
                        
                        ax3.set_xlabel('Rotation Angle (°)')
                        ax3.set_ylabel('Deviation (μm)')
                        ax3.set_title(f'{side_name} - First 5 Teeth (0° ~ {end_angle:.1f}°)')
                        ax3.legend()
                        ax3.grid(True, alpha=0.3)
                        ax3.set_xlim(0, end_angle)
                        st.pyplot(fig3)
        
        # 单齿齿向扩展合并曲线
        st.markdown("---")
        st.markdown("### Single Tooth Lead Expanded Merged Curve (0-360°)")
        st.info("将单齿齿向曲线复制到所有齿，形成完整的0-360°合并曲线，用于计算完整频谱")
        
        for side in ['left', 'right']:
            side_name = 'Left Lead' if side == 'left' else 'Right Lead'
            
            if selected_tooth in helix_data.get(side, {}):
                # 获取单齿数据
                tooth_helix = helix_data[side][selected_tooth]
                profile_mid = (profile_eval.eval_start + profile_eval.eval_end) / 2
                best_d = min(tooth_helix.keys(), key=lambda d: abs(d - profile_mid))
                raw_values = np.array(tooth_helix[best_d])
                
                # 截取评价范围内的数据
                b1, b2 = analyzer.reader.b1, analyzer.reader.b2
                ba, be = b1, b2
                
                # 解析测量范围
                ba_match = re.search(r'Messanfang.*?ba\s*\[mm\]\.*:\s*([\d.]+)', analyzer.reader.raw_content or "", re.IGNORECASE)
                if ba_match:
                    ba = float(ba_match.group(1))
                be_match = re.search(r'Messende.*?be\s*\[mm\]\.*:\s*([\d.]+)', analyzer.reader.raw_content or "", re.IGNORECASE)
                if be_match:
                    be = float(be_match.group(1))
                
                # 评价范围
                eval_start = min(b1, b2)
                eval_end = max(b1, b2)
                
                # 从全部数据中截取评价范围内的数据
                meas_length = be - ba
                if meas_length > 0:
                    start_ratio = (eval_start - ba) / meas_length
                    end_ratio = (eval_end - ba) / meas_length
                    
                    n_total = len(raw_values)
                    start_idx = max(0, int(start_ratio * n_total))
                    end_idx = min(n_total, int(end_ratio * n_total))
                    
                    if end_idx - start_idx > 10:
                        raw_values = raw_values[start_idx:end_idx]
                
                # 去除鼓形和斜率
                values = analyzer._remove_crown_and_slope(raw_values)
                
                if len(values) > 5:
                    # 使用螺旋角公式计算单齿的角度数组
                    # 极角 = 2 * (评价范围内测量点 - 起评点) * tan(螺旋角) / 节圆直径
                    n = len(values)
                    eval_points = np.linspace(0, eval_end - eval_start, n)
                    
                    # 获取螺旋角和节圆直径
                    helix_angle = gear_params.helix_angle if gear_params else 0
                    pitch_diameter = gear_params.pitch_diameter if gear_params else 100
                    
                    # 计算每个测量点的极角变化
                    if pitch_diameter > 0 and abs(helix_angle) > 0.01:
                        point_angle_change = 2.0 * eval_points * np.tan(np.radians(abs(helix_angle))) / pitch_diameter
                        point_angles_deg = np.degrees(point_angle_change)
                    else:
                        # 如果螺旋角为0，使用均匀分布
                        point_angles_deg = np.linspace(0, pitch_angle * 0.95, n)
                    
                    single_angles = point_angles_deg
                    
                    # 扩展到所有齿
                    expanded_angles = []
                    expanded_values = []
                    
                    for tooth_num in range(ze):
                        tooth_base = tooth_num * pitch_angle
                        # 右齿向：加极角，左齿向：减极角
                        if side == 'right':
                            for angle, value in zip(single_angles, values):
                                new_angle = tooth_base + angle
                                if new_angle < 360:
                                    expanded_angles.append(new_angle)
                                    expanded_values.append(value)
                        else:
                            for angle, value in zip(single_angles, values):
                                new_angle = tooth_base - angle
                                if new_angle >= 0:
                                    expanded_angles.append(new_angle)
                                    expanded_values.append(value)
                    
                    expanded_angles = np.array(expanded_angles)
                    expanded_values = np.array(expanded_values)
                    
                    # 排序
                    sort_idx = np.argsort(expanded_angles)
                    expanded_angles = expanded_angles[sort_idx]
                    expanded_values = expanded_values[sort_idx]
                    
                    # 计算高阶重建信号
                    angles_rad = np.deg2rad(expanded_angles)
                    reconstructed = np.zeros_like(expanded_values)
                    
                    # 计算频谱
                    if len(expanded_angles) > 8:
                        spectrum_components = analyzer._iterative_sine_decomposition(expanded_angles, expanded_values, num_components=10, max_order=5*ze)
                        high_order_comps = [c for c in spectrum_components if c.order >= ze]
                        
                        for comp in high_order_comps:
                            a = comp.amplitude * np.sin(comp.phase)
                            b = comp.amplitude * np.cos(comp.phase)
                            reconstructed += a * np.cos(comp.order * angles_rad) + b * np.sin(comp.order * angles_rad)
                        
                        # 显示指标
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            high_order_amplitude = sum(c.amplitude for c in high_order_comps) if high_order_comps else 0.0
                            st.metric("High Order Amplitude W", f"{high_order_amplitude:.4f} μm")
                        with col2:
                            high_order_rms = np.sqrt(sum(c.amplitude**2 for c in high_order_comps)) if high_order_comps else 0.0
                            st.metric("High Order RMS", f"{high_order_rms:.4f} μm")
                        with col3:
                            st.metric("High Order Wave Count", len(high_order_comps))
                        with col4:
                            if spectrum_components:
                                st.metric("Dominant Order", int(spectrum_components[0].order))
                    
                    # 绘制合并曲线
                    fig, ax = plt.subplots(figsize=(14, 5))
                    ax.plot(expanded_angles, expanded_values, 'b-', linewidth=0.5, alpha=0.7, label='Raw Curve')
                    ax.plot(expanded_angles, reconstructed, 'r-', linewidth=1.5, label='High Order Reconstruction')
                    
                    # 添加齿数标志
                    for tooth_num in range(ze + 1):
                        tooth_angle = tooth_num * pitch_angle
                        if tooth_angle <= 360:
                            ax.axvline(x=tooth_angle, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
                            if tooth_num % 5 == 0 or tooth_num == ze:
                                ax.text(tooth_angle, ax.get_ylim()[1] * 0.95, str(tooth_num), 
                                       ha='center', va='top', fontsize=7, color='gray', alpha=0.7)
                    
                    ax.set_xlabel('Rotation Angle (°)')
                    ax.set_ylabel('Deviation (μm)')
                    ax.set_title(f'{side_name} - Single Tooth Expanded Merged Curve (ZE={ze})')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    ax.set_xlim(0, 360)
                    st.pyplot(fig)
                    
                    # 显示频谱图
                    if spectrum_components:
                        st.markdown(f"**{side_name} - Single Tooth Expanded Spectrum**")
                        
                        col1, col2 = st.columns([3, 2])
                        
                        with col1:
                            # Top 10 阶次表格
                            st.markdown("**Top 10 Largest Orders:**")
                            top_10_data = []
                            for i, comp in enumerate(spectrum_components[:10], 1):
                                top_10_data.append({
                                    'Rank': i,
                                    'Order': int(comp.order),
                                    'Amplitude (μm)': f"{comp.amplitude:.4f}",
                                    'Phase (°)': f"{np.degrees(comp.phase):.1f}"
                                })
                            st.dataframe(pd.DataFrame(top_10_data), use_container_width=True, hide_index=True)
                        
                        with col2:
                            # 频谱图
                            fig2, ax2 = plt.subplots(figsize=(8, 5))
                            
                            orders = [c.order for c in spectrum_components[:15]]
                            amplitudes = [c.amplitude for c in spectrum_components[:15]]
                            
                            colors = ['red' if o >= ze else 'steelblue' for o in orders]
                            ax2.bar(orders, amplitudes, color=colors, alpha=0.7)
                            
                            # 标记ZE及其倍数
                            ze_multiples = [ze * i for i in range(1, 5) if ze * i <= max(orders)]
                            for i, ze_mult in enumerate(ze_multiples, 1):
                                if i == 1:
                                    ax2.axvline(x=ze_mult, color='green', linestyle='--', linewidth=2, label=f'ZE={ze}')
                                else:
                                    ax2.axvline(x=ze_mult, color='orange', linestyle=':', linewidth=1.5, alpha=0.7)
                            
                            ax2.set_title(f'Single Tooth Expanded Spectrum (ZE={ze})', fontsize=10, fontweight='bold')
                            ax2.set_xlabel('Order')
                            ax2.set_ylabel('Amplitude (μm)')
                            ax2.legend()
                            ax2.grid(True, alpha=0.3)
                            st.pyplot(fig2)
                    
                    # 显示前5个齿的放大视图
                    st.markdown(f"**{side_name} - First 5 Teeth Zoom View**")
                    
                    # 计算前5个齿的角度范围
                    end_angle = 5 * pitch_angle
                    zoom_mask = expanded_angles <= end_angle
                    zoom_angles = expanded_angles[zoom_mask]
                    zoom_values = expanded_values[zoom_mask]
                    zoom_reconstructed = reconstructed[zoom_mask]
                    
                    if len(zoom_angles) > 0:
                        fig3, ax3 = plt.subplots(figsize=(12, 4))
                        
                        # 降采样以改善显示
                        if len(zoom_angles) > 5000:
                            step = len(zoom_angles) // 2000 + 1
                            zoom_angles = zoom_angles[::step]
                            zoom_values = zoom_values[::step]
                            zoom_reconstructed = zoom_reconstructed[::step]
                        
                        ax3.plot(zoom_angles, zoom_values, 'b-', linewidth=1.0, alpha=0.8, label='Raw Curve')
                        ax3.plot(zoom_angles, zoom_reconstructed, 'r-', linewidth=2.0, label='High Order Reconstruction')
                        
                        # 添加齿数标志
                        for tooth_num in range(6):  # 0到5
                            tooth_angle = tooth_num * pitch_angle
                            if tooth_angle <= end_angle:
                                ax3.axvline(x=tooth_angle, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
                                ax3.text(tooth_angle, ax3.get_ylim()[1] * 0.95, str(tooth_num), 
                                        ha='center', va='top', fontsize=8, color='gray', alpha=0.7)
                        
                        ax3.set_xlabel('Rotation Angle (°)')
                        ax3.set_ylabel('Deviation (μm)')
                        ax3.set_title(f'{side_name} - First 5 Teeth (0° ~ {end_angle:.1f}°)')
                        ax3.legend()
                        ax3.grid(True, alpha=0.3)
                        ax3.set_xlim(0, end_angle)
                        st.pyplot(fig3)
    
    elif page == '📉 合并曲线':
        st.markdown("## Merged Curve Analysis (0-360°)")

        ze = gear_params.teeth_count if gear_params else 87

        name_mapping = {
            'profile_left': 'Left Profile',
            'profile_right': 'Right Profile',
            'helix_left': 'Left Lead',
            'helix_right': 'Right Lead'
        }

        for name, result in results.items():
            if result is None or len(result.angles) == 0:
                continue

            display_name = name_mapping.get(name, name)

            with st.expander(f"📈 {display_name}", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("High Order Amplitude W", f"{result.high_order_amplitude:.4f} μm")
                with col2:
                    st.metric("High Order RMS", f"{result.high_order_rms:.4f} μm")
                with col3:
                    st.metric("High Order Wave Count", len(result.high_order_waves))
                with col4:
                    if result.spectrum_components and len(result.spectrum_components) > 0:
                        max_order = result.spectrum_components[0].order
                        st.metric("Dominant Order", int(max_order))
                    else:
                        st.metric("Dominant Order", "-")

                # 计算节距角
                pitch_angle = 360.0 / ze if ze > 0 else 4.14
                
                # 检查是否为单齿扩展数据
                unique_teeth_in_data = len(set(result.angles // pitch_angle))
                is_single_tooth_expanded = unique_teeth_in_data < ze
                
                fig, ax = plt.subplots(figsize=(14, 5))
                ax.plot(result.angles, result.values, 'b-', linewidth=0.5, alpha=0.7, label='Raw Curve')
                ax.plot(result.angles, result.reconstructed_signal, 'r-', linewidth=1.5, label='High Order Reconstruction')
                
                # 添加齿数标志 - 在每个齿的起始位置添加虚线
                for tooth_num in range(ze + 1):  # 从0到齿数
                    tooth_angle = tooth_num * pitch_angle
                    if tooth_angle <= 360:
                        # 添加虚线标记每个齿的位置
                        ax.axvline(x=tooth_angle, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
                        # 在顶部添加齿号标记（每5个齿或第一个齿显示数字）
                        if tooth_num % 5 == 0 or tooth_num == ze:
                            ax.text(tooth_angle, ax.get_ylim()[1] * 0.95, str(tooth_num), 
                                   ha='center', va='top', fontsize=7, color='gray', alpha=0.7)
                
                ax.set_xlabel('Rotation Angle (°)')
                ax.set_ylabel('Deviation (μm)')
                
                # 如果是单齿扩展，在标题中标识
                if is_single_tooth_expanded:
                    ax.set_title(f'{display_name} - Merged Curve (ZE={ze}, Single Tooth Expanded)')
                else:
                    ax.set_title(f'{display_name} - Merged Curve (ZE={ze})')
                
                ax.legend()
                ax.grid(True, alpha=0.3)
                ax.set_xlim(0, 360)
                st.pyplot(fig)

        st.markdown("---")
        st.markdown("### First 5 Teeth Zoom View")

        pitch_angle = 360.0 / ze if ze > 0 else 4.14
        end_angle = 5 * pitch_angle

        for name, result in [
            ('Left Profile', results.get('profile_left')),
            ('Right Profile', results.get('profile_right')),
            ('Left Lead', results.get('helix_left')),
            ('Right Lead', results.get('helix_right'))
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
                # 如果数据点过多，进行降采样以改善线条显示
                if len(zoom_angles) > 5000:
                    step = len(zoom_angles) // 2000 + 1
                    zoom_angles = zoom_angles[::step]
                    zoom_values = zoom_values[::step]
                    zoom_reconstructed = zoom_reconstructed[::step]
                ax.plot(zoom_angles, zoom_values, 'b-', linewidth=1.0, alpha=0.8, label='Raw Curve')
                ax.plot(zoom_angles, zoom_reconstructed, 'r-', linewidth=2.0, label='High Order Reconstruction')
                
                # 添加齿数标志
                pitch_angle = 360.0 / ze if ze > 0 else 4.14
                for tooth_num in range(ze + 1):  # 从0到齿数
                    tooth_angle = tooth_num * pitch_angle
                    if tooth_angle <= end_angle:
                        # 添加虚线标记每个齿的位置
                        ax.axvline(x=tooth_angle, color='gray', linestyle=':', linewidth=0.5, alpha=0.5)
                        # 在顶部添加齿号标记（每5个齿或第一个齿显示数字）
                        if tooth_num % 5 == 0 or tooth_num == ze:
                            ax.text(tooth_angle, ax.get_ylim()[1] * 0.95, str(tooth_num), 
                                   ha='center', va='top', fontsize=7, color='gray', alpha=0.7)
                
                ax.set_xlabel('Rotation Angle (°)')
                ax.set_ylabel('Deviation (μm)')
                ax.set_title(f'{display_name} - First 5 Teeth (0° ~ {end_angle:.1f}°)')
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
    
    elif page == '📊 频谱分析':
        st.markdown("## Spectrum Analysis")

        ze = gear_params.teeth_count if gear_params else 87

        name_mapping = {
            'profile_left': 'Left Profile',
            'profile_right': 'Right Profile',
            'helix_left': 'Left Lead',
            'helix_right': 'Right Lead'
        }

        for name, result in results.items():
            if result is None or len(result.angles) == 0:
                continue

            display_name = name_mapping.get(name, name)

            with st.expander(f"📈 {display_name}", expanded=True):
                st.markdown("#### Top 10 Largest Orders")

                spectrum_data = []
                for i, comp in enumerate(result.spectrum_components[:10]):
                    order_type = 'High Order' if comp.order >= ze else 'Low Order'
                    spectrum_data.append({
                        'Rank': i + 1,
                        'Order': int(comp.order),
                        'Amplitude (μm)': f"{comp.amplitude:.4f}",
                        'Phase (°)': f"{np.degrees(comp.phase):.1f}",
                        'Type': order_type
                    })
                st.table(spectrum_data)

                st.markdown("#### Spectrum Chart")

                fig, ax = plt.subplots(figsize=(12, 5))
                sorted_components = sorted(result.spectrum_components[:20], key=lambda c: c.order)
                orders = [c.order for c in sorted_components]
                amplitudes = [c.amplitude for c in sorted_components]

                if orders and amplitudes:
                    colors_bar = ['red' if o >= ze else 'steelblue' for o in orders]
                    ax.bar(orders, amplitudes, color=colors_bar, alpha=0.7, width=3)

                    # 标识 ZE 及其倍数
                    ze_multiples = [ze * i for i in range(1, 5) if ze * i <= max(orders) + 20]
                    for i, ze_mult in enumerate(ze_multiples, 1):
                        if i == 1:
                            ax.axvline(x=ze_mult, color='green', linestyle='--', linewidth=2, label=f'ZE={ze}')
                        else:
                            ax.axvline(x=ze_mult, color='orange', linestyle=':', linewidth=1.5, alpha=0.7, label=f'{i}×ZE={ze_mult}')
                    ax.set_xlim(0, max(orders) + 20)

                ax.set_xlabel('Order')
                ax.set_ylabel('Amplitude (μm)')
                ax.set_title(f'{display_name} - Spectrum (ZE={ze})')
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
