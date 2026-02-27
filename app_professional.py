"""
================================================================================
齿轮波纹度软件 - 完整专业版 (使用 gear_analysis_refactored)
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
        help="支持 Klingenberg MKA 格式的齿轮波纹度数据文件"
    )

    if uploaded_file is not None:
        st.success(f"已加载: {uploaded_file.name}")

    st.markdown("---")
    st.header("📋 功能导航")
    page = st.radio(
        "选择功能",
        ['📄 专业报告', '🔍 三截面扭曲数据', '📊 周节详细报表', '📈 单齿分析', '📉 合并曲线', '📊 频谱分析'],
        index=0
    )
    
    # 分页状态管理
    if 'pagination' not in st.session_state:
        st.session_state.pagination = {'profile_page': 1, 'helix_page': 1}

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
        
        # 延迟加载：只在需要时计算分析结果
        # 使用session_state缓存结果避免重复计算
        if 'analyzer' not in st.session_state:
            st.session_state.analyzer = analyzer
        
        # 预计算轻量级结果（齿轮参数等基本信息）
        pitch_left = analyzer.analyze_pitch('left')
        pitch_right = analyzer.analyze_pitch('right')
    
    profile_eval = analyzer.reader.profile_eval_range
    helix_eval = analyzer.reader.helix_eval_range
    gear_params = analyzer.gear_params
    
    # 获取数据 - 所有页面共用
    profile_data = analyzer.reader.profile_data
    helix_data = analyzer.reader.helix_data
    
    # 获取 b1, b2, d1, d2 用于计算范围
    b1 = analyzer.reader.b1 if hasattr(analyzer.reader, 'b1') else 0
    b2 = analyzer.reader.b2 if hasattr(analyzer.reader, 'b2') else 78
    d1 = analyzer.reader.d1 if hasattr(analyzer.reader, 'd1') else 0
    d2 = analyzer.reader.d2 if hasattr(analyzer.reader, 'd2') else 8
    
    # 获取测量范围 da, de, ba, be
    da = analyzer.reader.da if hasattr(analyzer.reader, 'da') else d1
    de = analyzer.reader.de if hasattr(analyzer.reader, 'de') else d2
    ba = analyzer.reader.ba if hasattr(analyzer.reader, 'ba') else b1
    be = analyzer.reader.be if hasattr(analyzer.reader, 'be') else b2
    
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
    
    # 辅助函数：齿号排序（处理数字和带后缀的齿号如 1, 1a, 2, 10）- 所有页面共用
    def tooth_sort_key(tooth_id):
        """将齿号转换为排序键，如 '1a' -> (1, 'a'), '10' -> (10, '')"""
        match = re.match(r'(\d+)([a-z]?)', str(tooth_id))
        if match:
            num = int(match.group(1))
            suffix = match.group(2)
            return (num, suffix)
        return (0, str(tooth_id))
    
    # DIN 3962 公差表 - 所有页面共用
    DIN3962_PROFILE_TOLERANCES = {
        1: {'fHa': 3.0, 'ffa': 4.0, 'Fa': 5.0},
        2: {'fHa': 4.0, 'ffa': 6.0, 'Fa': 7.0},
        3: {'fHa': 5.5, 'ffa': 8.0, 'Fa': 10.0},
        4: {'fHa': 8.0, 'ffa': 12.0, 'Fa': 14.0},
        5: {'fHa': 11.0, 'ffa': 16.0, 'Fa': 20.0},
        6: {'fHa': 16.0, 'ffa': 22.0, 'Fa': 28.0},
        7: {'fHa': 22.0, 'ffa': 32.0, 'Fa': 40.0},
        8: {'fHa': 28.0, 'ffa': 45.0, 'Fa': 56.0},
        9: {'fHa': 40.0, 'ffa': 63.0, 'Fa': 80.0},
        10: {'fHa': 71.0, 'ffa': 110.0, 'Fa': 125.0},
        11: {'fHa': 110.0, 'ffa': 160.0, 'Fa': 200.0},
        12: {'fHa': 180.0, 'ffa': 250.0, 'Fa': 320.0}
    }
    
    DIN3962_LEAD_TOLERANCES = {
        1: {'fHb': 2.5, 'ffb': 2.0, 'Fb': 3.0},
        2: {'fHb': 3.5, 'ffb': 5.0, 'Fb': 6.0},
        3: {'fHb': 4.5, 'ffb': 7.0, 'Fb': 8.0},
        4: {'fHb': 6.0, 'ffb': 8.0, 'Fb': 10.0},
        5: {'fHb': 8.0, 'ffb': 9.0, 'Fb': 12.0},
        6: {'fHb': 11.0, 'ffb': 12.0, 'Fb': 16.0},
        7: {'fHb': 16.0, 'ffb': 16.0, 'Fb': 22.0},
        8: {'fHb': 22.0, 'ffb': 25.0, 'Fb': 32.0},
        9: {'fHb': 32.0, 'ffb': 40.0, 'Fb': 50.0},
        10: {'fHb': 50.0, 'ffb': 63.0, 'Fb': 80.0},
        11: {'fHb': 80.0, 'ffb': 100.0, 'Fb': 125.0},
        12: {'fHb': 125.0, 'ffb': 160.0, 'Fb': 200.0}
    }
    
    DEFAULT_QUALITY = 5  # 默认质量等级
    
    def get_tolerance(param_type, param_code, quality=DEFAULT_QUALITY):
        """获取公差值"""
        if param_type == 'profile':
            table = DIN3962_PROFILE_TOLERANCES
        elif param_type == 'lead':
            table = DIN3962_LEAD_TOLERANCES
        else:
            return None
        if quality in table and param_code in table[quality]:
            return table[quality][param_code]
        return None
    
    def calculate_quality_grade(measured_value, param_type, param_code):
        """根据测量值计算质量等级"""
        if measured_value is None:
            return None
        abs_value = abs(measured_value)
        if param_type == 'profile':
            table = DIN3962_PROFILE_TOLERANCES
        elif param_type == 'lead':
            table = DIN3962_LEAD_TOLERANCES
        else:
            return None
        for quality in range(1, 13):
            if quality in table and param_code in table[quality]:
                if abs_value <= table[quality][param_code]:
                    return quality
        return 12
    
    # 辅助函数：计算偏差参数（与PDF报告完全一致）- 所有页面共用
    def calc_profile_deviations(values):
        """计算齿形偏差参数 - 与PDF报告算法一致"""
        if values is None or len(values) < 10:
            return None, None, None, None
        
        data = np.array(values)
        n = len(data)
        idx_start = int(n * 0.15)
        idx_end = int(n * 0.85)
        eval_values = data[idx_start:idx_end]
        
        if len(eval_values) < 2:
            return None, None, None, None
        
        # 总偏差 F_alpha（峰峰值）
        F_alpha = np.max(eval_values) - np.min(eval_values)
        
        # 拟合直线（最小二乘法）
        x = np.arange(len(eval_values))
        coeffs = np.polyfit(x, eval_values, 1)
        trend = coeffs[0] * x + coeffs[1]
        
        # fH_alpha - 齿形倾斜偏差（趋势线的差值）
        fH_alpha = trend[-1] - trend[0]
        
        # ff_alpha - 齿形形状偏差（去除趋势后的残余分量峰峰值）
        residual = eval_values - trend
        ff_alpha = np.max(residual) - np.min(residual)
        
        # Ca - 鼓形量（抛物线拟合）
        if len(eval_values) >= 3:
            x2 = np.arange(len(eval_values))
            coeffs2 = np.polyfit(x2, eval_values, 2)
            a = coeffs2[0]
            L = len(eval_values)
            Ca = -a * (L ** 2) / 4
        else:
            Ca = 0.0
        
        return F_alpha, fH_alpha, ff_alpha, Ca
    
    def calc_lead_deviations(values):
        """计算齿向偏差参数 - 与PDF报告算法一致"""
        if values is None or len(values) < 10:
            return None, None, None, None
        
        data = np.array(values)
        n = len(data)
        idx_start = int(n * 0.15)
        idx_end = int(n * 0.85)
        eval_values = data[idx_start:idx_end]
        
        if len(eval_values) < 2:
            return None, None, None, None
        
        # 总偏差 F_beta（峰峰值）
        F_beta = np.max(eval_values) - np.min(eval_values)
        
        # 拟合直线（最小二乘法）
        x = np.arange(len(eval_values))
        coeffs = np.polyfit(x, eval_values, 1)
        trend = coeffs[0] * x + coeffs[1]
        
        # fH_beta - 齿向倾斜偏差（趋势线的差值）
        fH_beta = trend[-1] - trend[0]
        
        # ff_beta - 齿向形状偏差（去除趋势后的残余分量峰峰值）
        residual = eval_values - trend
        ff_beta = np.max(residual) - np.min(residual)
        
        # Cb - 鼓形量（抛物线拟合）
        if len(eval_values) >= 3:
            x2 = np.arange(len(eval_values))
            coeffs2 = np.polyfit(x2, eval_values, 2)
            a = coeffs2[0]
            L = len(eval_values)
            Cb = -a * (L ** 2) / 4
        else:
            Cb = 0.0
        
        return F_beta, fH_beta, ff_beta, Cb
    
    if page == '📄 专业报告':
        st.markdown("## Gear Profile/Lead Report")
        
        # ========== 头部参数表格 ==========
        info = analyzer.reader.info if hasattr(analyzer.reader, 'info') else {}
        
        col1, col2 = st.columns(2)
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
        
        # ========== 获取齿号数据 ==========
        profile_teeth_left = sorted(list(profile_data.get('left', {}).keys()), key=tooth_sort_key)
        profile_teeth_right = sorted(list(profile_data.get('right', {}).keys()), key=tooth_sort_key)
        helix_teeth_left = sorted(list(helix_data.get('left', {}).keys()), key=tooth_sort_key)
        helix_teeth_right = sorted(list(helix_data.get('right', {}).keys()), key=tooth_sort_key)
        
        TEETH_PER_PAGE = 6  # 每页显示6个齿
        
        # 计算总页数
        profile_max_teeth = max(len(profile_teeth_left), len(profile_teeth_right))
        profile_total_pages = max(1, (profile_max_teeth + TEETH_PER_PAGE - 1) // TEETH_PER_PAGE)
        
        helix_max_teeth = max(len(helix_teeth_left), len(helix_teeth_right))
        helix_total_pages = max(1, (helix_max_teeth + TEETH_PER_PAGE - 1) // TEETH_PER_PAGE)
        
        # ========== Profile 齿形分析 ==========
        st.markdown("### Profile 齿形分析")
        
        # 齿形分页控制
        profile_page = st.session_state.pagination.get('profile_page', 1)
        
        col_prev, col_info, col_next = st.columns([1, 3, 1])
        with col_prev:
            if st.button("⬅️ 上一页", key="profile_prev") and profile_page > 1:
                st.session_state.pagination['profile_page'] = profile_page - 1
                st.rerun()
        with col_info:
            st.markdown(f"**第 {profile_page} / {profile_total_pages} 页**")
        with col_next:
            if st.button("➡️ 下一页", key="profile_next") and profile_page < profile_total_pages:
                st.session_state.pagination['profile_page'] = profile_page + 1
                st.rerun()
        
        # 计算当前页的齿号范围
        profile_start_idx = (profile_page - 1) * TEETH_PER_PAGE
        profile_end_idx = profile_start_idx + TEETH_PER_PAGE
        
        current_profile_left = profile_teeth_left[profile_start_idx:profile_end_idx]
        current_profile_right = profile_teeth_right[profile_start_idx:profile_end_idx]
        
        # ========== 左右齿形图表并排显示 ==========
        left_profile_results = []
        right_profile_results = []
        
        # 创建12列：左6个 + 右6个
        profile_cols = st.columns(12)
        
        # 左齿面图表（前6列）
        for i, tooth_id in enumerate(current_profile_left):
            with profile_cols[i]:
                if tooth_id in profile_data.get('left', {}):
                    tooth_profiles = profile_data['left'][tooth_id]
                    if tooth_profiles:
                        helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                        best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                        values = np.array(tooth_profiles[best_z])
                        
                        fig, ax = plt.subplots(figsize=(1.8, 4.5))
                        y_positions = np.linspace(da, de, len(values))
                        ax.plot(values / 50.0 + 1, y_positions, 'r-', linewidth=1.0)
                        ax.axvline(x=1, color='black', linestyle='-', linewidth=0.5)
                        
                        n = len(values)
                        meas_length = de - da
                        idx_eval_start = int((d1 - da) / meas_length * (n - 1))
                        idx_eval_end = int((d2 - da) / meas_length * (n - 1))
                        
                        ax.plot(1, y_positions[0], 'v', markersize=6, color='blue')
                        ax.plot(1, y_positions[idx_eval_start], 'v', markersize=6, color='green')
                        ax.plot(1, y_positions[idx_eval_end], '^', markersize=6, color='orange')
                        ax.plot(1, y_positions[-1], '^', markersize=6, color='red')
                        
                        ax.set_ylim(da - 1, de + 1)
                        ax.set_yticks([da, d1, d2, de])
                        ax.set_yticklabels([f'{da:.1f}', f'{d1:.1f}', f'{d2:.1f}', f'{de:.1f}'], fontsize=7)
                        ax.set_xlim(0.3, 1.7)
                        ax.set_xticks([0.5, 1.0, 1.5])
                        ax.set_xticklabels(['-25', '0', '+25'], fontsize=7)
                        ax.grid(True, linestyle=':', linewidth=0.3, color='gray')
                        ax.set_xlabel(f'{tooth_id}', fontsize=9, fontweight='bold')
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
                        
                        F_a, fH_a, ff_a, Ca = calc_profile_deviations(values)
                        if F_a is not None:
                            left_profile_results.append({
                                'Tooth': tooth_id,
                                'fHα': fH_a,
                                'ffα': ff_a,
                                'Fα': F_a,
                                'Ca': Ca
                            })
        
        # 右齿面图表（后6列）
        for i, tooth_id in enumerate(current_profile_right):
            with profile_cols[i + 6]:
                if tooth_id in profile_data.get('right', {}):
                    tooth_profiles = profile_data['right'][tooth_id]
                    if tooth_profiles:
                        helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                        best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                        values = np.array(tooth_profiles[best_z])
                        
                        fig, ax = plt.subplots(figsize=(1.8, 4.5))
                        y_positions = np.linspace(da, de, len(values))
                        ax.plot(values / 50.0 + 1, y_positions, 'r-', linewidth=1.0)
                        ax.axvline(x=1, color='black', linestyle='-', linewidth=0.5)
                        
                        n = len(values)
                        meas_length = de - da
                        idx_eval_start = int((d1 - da) / meas_length * (n - 1))
                        idx_eval_end = int((d2 - da) / meas_length * (n - 1))
                        
                        ax.plot(1, y_positions[0], 'v', markersize=6, color='blue')
                        ax.plot(1, y_positions[idx_eval_start], 'v', markersize=6, color='green')
                        ax.plot(1, y_positions[idx_eval_end], '^', markersize=6, color='orange')
                        ax.plot(1, y_positions[-1], '^', markersize=6, color='red')
                        
                        ax.set_ylim(da - 1, de + 1)
                        ax.set_yticks([da, d1, d2, de])
                        ax.set_yticklabels([f'{da:.1f}', f'{d1:.1f}', f'{d2:.1f}', f'{de:.1f}'], fontsize=7)
                        ax.set_xlim(0.3, 1.7)
                        ax.set_xticks([0.5, 1.0, 1.5])
                        ax.set_xticklabels(['-25', '0', '+25'], fontsize=7)
                        ax.grid(True, linestyle=':', linewidth=0.3, color='gray')
                        ax.set_xlabel(f'{tooth_id}', fontsize=9, fontweight='bold')
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
                        
                        F_a, fH_a, ff_a, Ca = calc_profile_deviations(values)
                        if F_a is not None:
                            right_profile_results.append({
                                'Tooth': tooth_id,
                                'fHα': fH_a,
                                'ffα': ff_a,
                                'Fα': F_a,
                                'Ca': Ca
                            })
        
        # ========== 齿形偏差数据表 ==========
        st.markdown("#### 齿形偏差数据表")
        
        # 左齿面数据表
        if left_profile_results:
            st.markdown("**Left Flank 左齿面**")
            df_left = pd.DataFrame(left_profile_results)
            
            mean_row = {'Tooth': 'Mean'}
            max_row = {'Tooth': 'Max'}
            for col in ['fHα', 'ffα', 'Fα', 'Ca']:
                mean_row[col] = df_left[col].mean()
                max_row[col] = df_left[col].max()
            mean_row['fHαm'] = df_left['fHα'].mean()
            max_row['fHαm'] = np.nan
            df_left['fHαm'] = np.nan
            
            tol_row = {'Tooth': f'Lim.{DEFAULT_QUALITY}'}
            for col, tol_code in [('fHα', 'fHa'), ('ffα', 'ffa'), ('Fα', 'Fa')]:
                tol_val = get_tolerance('profile', tol_code, DEFAULT_QUALITY)
                tol_row[col] = f'±{int(tol_val)}' if tol_val else ''
            tol_row['Ca'] = ''
            tol_row['fHαm'] = ''
            
            for col, tol_code in [('fHα', 'fHa'), ('ffα', 'ffa'), ('Fα', 'Fa')]:
                max_val = max_row[col]
                if max_val is not None and not np.isnan(max_val):
                    quality = calculate_quality_grade(max_val, 'profile', tol_code)
                    if quality:
                        max_row[col] = f"{max_val:.2f} Q{quality}"
            
            df_left = pd.concat([df_left, pd.DataFrame([mean_row]), pd.DataFrame([max_row]), pd.DataFrame([tol_row])], ignore_index=True)
            
            def format_value(x):
                if pd.isna(x):
                    return ''
                if isinstance(x, str):
                    return x
                if isinstance(x, (int, float)):
                    return f'{x:.2f}'
                return str(x)
            
            df_display = df_left[['Tooth', 'fHα', 'fHαm', 'ffα', 'Fα', 'Ca']].copy()
            for col in ['fHα', 'fHαm', 'ffα', 'Fα', 'Ca']:
                df_display[col] = df_display[col].apply(format_value)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # 右齿面数据表
        if right_profile_results:
            st.markdown("**Right Flank 右齿面**")
            df_right = pd.DataFrame(right_profile_results)
            
            mean_row = {'Tooth': 'Mean'}
            max_row = {'Tooth': 'Max'}
            for col in ['fHα', 'ffα', 'Fα', 'Ca']:
                mean_row[col] = df_right[col].mean()
                max_row[col] = df_right[col].max()
            mean_row['fHαm'] = df_right['fHα'].mean()
            max_row['fHαm'] = np.nan
            df_right['fHαm'] = np.nan
            
            tol_row = {'Tooth': f'Lim.{DEFAULT_QUALITY}'}
            for col, tol_code in [('fHα', 'fHa'), ('ffα', 'ffa'), ('Fα', 'Fa')]:
                tol_val = get_tolerance('profile', tol_code, DEFAULT_QUALITY)
                tol_row[col] = f'±{int(tol_val)}' if tol_val else ''
            tol_row['Ca'] = ''
            tol_row['fHαm'] = ''
            
            for col, tol_code in [('fHα', 'fHa'), ('ffα', 'ffa'), ('Fα', 'Fa')]:
                max_val = max_row[col]
                if max_val is not None and not np.isnan(max_val):
                    quality = calculate_quality_grade(max_val, 'profile', tol_code)
                    if quality:
                        max_row[col] = f"{max_val:.2f} Q{quality}"
            
            df_right = pd.concat([df_right, pd.DataFrame([mean_row]), pd.DataFrame([max_row]), pd.DataFrame([tol_row])], ignore_index=True)
            
            df_display = df_right[['Tooth', 'fHα', 'fHαm', 'ffα', 'Fα', 'Ca']].copy()
            for col in ['fHα', 'fHαm', 'ffα', 'Fα', 'Ca']:
                df_display[col] = df_display[col].apply(format_value)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # ========== Helix 齿向分析 ==========
        st.markdown("### Helix 齿向分析")
        
        # 齿向分页控制
        helix_page = st.session_state.pagination.get('helix_page', 1)
        
        col_prev, col_info, col_next = st.columns([1, 3, 1])
        with col_prev:
            if st.button("⬅️ 上一页", key="helix_prev") and helix_page > 1:
                st.session_state.pagination['helix_page'] = helix_page - 1
                st.rerun()
        with col_info:
            st.markdown(f"**第 {helix_page} / {helix_total_pages} 页**")
        with col_next:
            if st.button("➡️ 下一页", key="helix_next") and helix_page < helix_total_pages:
                st.session_state.pagination['helix_page'] = helix_page + 1
                st.rerun()
        
        # 计算当前页的齿号范围
        helix_start_idx = (helix_page - 1) * TEETH_PER_PAGE
        helix_end_idx = helix_start_idx + TEETH_PER_PAGE
        
        current_helix_left = helix_teeth_left[helix_start_idx:helix_end_idx]
        current_helix_right = helix_teeth_right[helix_start_idx:helix_end_idx]
        
        # ========== 左右齿向图表并排显示 ==========
        left_helix_results = []
        right_helix_results = []
        
        # 创建12列：左6个 + 右6个
        helix_cols = st.columns(12)
        
        # 左齿面图表（前6列）
        for i, tooth_id in enumerate(current_helix_left):
            with helix_cols[i]:
                if tooth_id in helix_data.get('left', {}):
                    tooth_helix = helix_data['left'][tooth_id]
                    if tooth_helix:
                        profile_mid = (profile_eval.eval_start + profile_eval.eval_end) / 2
                        best_d = min(tooth_helix.keys(), key=lambda d: abs(d - profile_mid))
                        values = np.array(tooth_helix[best_d])
                        
                        fig, ax = plt.subplots(figsize=(1.8, 4.5))
                        y_positions = np.linspace(ba, be, len(values))
                        ax.plot(values / 50.0 + 1, y_positions, 'k-', linewidth=1.0)
                        ax.axvline(x=1, color='black', linestyle='-', linewidth=0.5)
                        
                        n = len(values)
                        meas_length = be - ba
                        idx_eval_start = int((b1 - ba) / meas_length * (n - 1))
                        idx_eval_end = int((b2 - ba) / meas_length * (n - 1))
                        
                        ax.plot(1, y_positions[0], 'v', markersize=6, color='blue')
                        ax.plot(1, y_positions[idx_eval_start], 'v', markersize=6, color='green')
                        ax.plot(1, y_positions[idx_eval_end], '^', markersize=6, color='orange')
                        ax.plot(1, y_positions[-1], '^', markersize=6, color='red')
                        
                        ax.set_ylim(ba - 1, be + 1)
                        ax.set_yticks([ba, b1, b2, be])
                        ax.set_yticklabels([f'{ba:.1f}', f'{b1:.1f}', f'{b2:.1f}', f'{be:.1f}'], fontsize=7)
                        ax.set_xlim(0.3, 1.7)
                        ax.set_xticks([0.5, 1.0, 1.5])
                        ax.set_xticklabels(['-25', '0', '+25'], fontsize=7)
                        ax.grid(True, linestyle=':', linewidth=0.3, color='gray')
                        ax.set_xlabel(f'{tooth_id}', fontsize=9, fontweight='bold')
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
                        
                        F_b, fH_b, ff_b, Cb = calc_lead_deviations(values)
                        if F_b is not None:
                            left_helix_results.append({
                                'Tooth': tooth_id,
                                'fHβ': fH_b,
                                'ffβ': ff_b,
                                'Fβ': F_b,
                                'Cb': Cb
                            })
        
        # 右齿面图表（后6列）
        for i, tooth_id in enumerate(current_helix_right):
            with helix_cols[i + 6]:
                if tooth_id in helix_data.get('right', {}):
                    tooth_helix = helix_data['right'][tooth_id]
                    if tooth_helix:
                        profile_mid = (profile_eval.eval_start + profile_eval.eval_end) / 2
                        best_d = min(tooth_helix.keys(), key=lambda d: abs(d - profile_mid))
                        values = np.array(tooth_helix[best_d])
                        
                        fig, ax = plt.subplots(figsize=(1.8, 4.5))
                        y_positions = np.linspace(ba, be, len(values))
                        ax.plot(values / 50.0 + 1, y_positions, 'k-', linewidth=1.0)
                        ax.axvline(x=1, color='black', linestyle='-', linewidth=0.5)
                        
                        n = len(values)
                        meas_length = be - ba
                        idx_eval_start = int((b1 - ba) / meas_length * (n - 1))
                        idx_eval_end = int((b2 - ba) / meas_length * (n - 1))
                        
                        ax.plot(1, y_positions[0], 'v', markersize=6, color='blue')
                        ax.plot(1, y_positions[idx_eval_start], 'v', markersize=6, color='green')
                        ax.plot(1, y_positions[idx_eval_end], '^', markersize=6, color='orange')
                        ax.plot(1, y_positions[-1], '^', markersize=6, color='red')
                        
                        ax.set_ylim(ba - 1, be + 1)
                        ax.set_yticks([ba, b1, b2, be])
                        ax.set_yticklabels([f'{ba:.1f}', f'{b1:.1f}', f'{b2:.1f}', f'{be:.1f}'], fontsize=7)
                        ax.set_xlim(0.3, 1.7)
                        ax.set_xticks([0.5, 1.0, 1.5])
                        ax.set_xticklabels(['-25', '0', '+25'], fontsize=7)
                        ax.grid(True, linestyle=':', linewidth=0.3, color='gray')
                        ax.set_xlabel(f'{tooth_id}', fontsize=9, fontweight='bold')
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
                        
                        F_b, fH_b, ff_b, Cb = calc_lead_deviations(values)
                        if F_b is not None:
                            right_helix_results.append({
                                'Tooth': tooth_id,
                                'fHβ': fH_b,
                                'ffβ': ff_b,
                                'Fβ': F_b,
                                'Cb': Cb
                            })
        
        # ========== 齿向偏差数据表 ==========
        st.markdown("#### 齿向偏差数据表")
        
        # 左齿面数据表
        if left_helix_results:
            st.markdown("**Left Flank 左齿面**")
            df_left_h = pd.DataFrame(left_helix_results)
            
            mean_row = {'Tooth': 'Mean'}
            max_row = {'Tooth': 'Max'}
            for col in ['fHβ', 'ffβ', 'Fβ', 'Cb']:
                mean_row[col] = df_left_h[col].mean()
                max_row[col] = df_left_h[col].max()
            mean_row['fHβm'] = df_left_h['fHβ'].mean()
            max_row['fHβm'] = np.nan
            df_left_h['fHβm'] = np.nan
            
            tol_row = {'Tooth': f'Lim.{DEFAULT_QUALITY}'}
            for col, tol_code in [('fHβ', 'fHb'), ('ffβ', 'ffb'), ('Fβ', 'Fb')]:
                tol_val = get_tolerance('lead', tol_code, DEFAULT_QUALITY)
                tol_row[col] = f'±{int(tol_val)}' if tol_val else ''
            tol_row['Cb'] = ''
            tol_row['fHβm'] = ''
            
            for col, tol_code in [('fHβ', 'fHb'), ('ffβ', 'ffb'), ('Fβ', 'Fb')]:
                max_val = max_row[col]
                if max_val is not None and not np.isnan(max_val):
                    quality = calculate_quality_grade(max_val, 'lead', tol_code)
                    if quality:
                        max_row[col] = f"{max_val:.2f} Q{quality}"
            
            df_left_h = pd.concat([df_left_h, pd.DataFrame([mean_row]), pd.DataFrame([max_row]), pd.DataFrame([tol_row])], ignore_index=True)
            
            df_display = df_left_h[['Tooth', 'fHβ', 'fHβm', 'ffβ', 'Fβ', 'Cb']].copy()
            for col in ['fHβ', 'fHβm', 'ffβ', 'Fβ', 'Cb']:
                df_display[col] = df_display[col].apply(format_value)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # 右齿面数据表
        if right_helix_results:
            st.markdown("**Right Flank 右齿面**")
            df_right_h = pd.DataFrame(right_helix_results)
            
            mean_row = {'Tooth': 'Mean'}
            max_row = {'Tooth': 'Max'}
            for col in ['fHβ', 'ffβ', 'Fβ', 'Cb']:
                mean_row[col] = df_right_h[col].mean()
                max_row[col] = df_right_h[col].max()
            mean_row['fHβm'] = df_right_h['fHβ'].mean()
            max_row['fHβm'] = np.nan
            df_right_h['fHβm'] = np.nan
            
            tol_row = {'Tooth': f'Lim.{DEFAULT_QUALITY}'}
            for col, tol_code in [('fHβ', 'fHb'), ('ffβ', 'ffb'), ('Fβ', 'Fb')]:
                tol_val = get_tolerance('lead', tol_code, DEFAULT_QUALITY)
                tol_row[col] = f'±{int(tol_val)}' if tol_val else ''
            tol_row['Cb'] = ''
            tol_row['fHβm'] = ''
            
            for col, tol_code in [('fHβ', 'fHb'), ('ffβ', 'ffb'), ('Fβ', 'Fb')]:
                max_val = max_row[col]
                if max_val is not None and not np.isnan(max_val):
                    quality = calculate_quality_grade(max_val, 'lead', tol_code)
                    if quality:
                        max_row[col] = f"{max_val:.2f} Q{quality}"
            
            df_right_h = pd.concat([df_right_h, pd.DataFrame([mean_row]), pd.DataFrame([max_row]), pd.DataFrame([tol_row])], ignore_index=True)
            
            df_display = df_right_h[['Tooth', 'fHβ', 'fHβm', 'ffβ', 'Fβ', 'Cb']].copy()
            for col in ['fHβ', 'fHβm', 'ffβ', 'Fβ', 'Cb']:
                df_display[col] = df_display[col].apply(format_value)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # PDF下载按钮
        st.markdown("---")
        st.markdown("### 📋 PDF报告生成")
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
                        st.success("✅ PDF报告生成成功！")
                    except Exception as e:
                        st.error(f"生成PDF失败: {e}")
        else:
            st.warning("PDF生成器不可用")
    
    elif page == '📊 周节详细报表':
                
                for i, tooth_id in enumerate(profile_teeth_left):
                    if i % n_cols == 0:
                        cols = st.columns(n_cols)
                    
                    with cols[i % n_cols]:
                        tooth_profiles = profile_data['left'][tooth_id]
                        helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                        best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                        values = np.array(tooth_profiles[best_z])
                        
                        fig, ax = plt.subplots(figsize=(2.2, 5.5))
                        # 数据点是从 da 到 de 均匀分布的
                        y_positions = np.linspace(da, de, len(values))
                        
                        # 绘制曲线（红色）
                        ax.plot(values / 50.0 + 1, y_positions, 'r-', linewidth=1.0)
                        
                        # 零点垂直线
                        ax.axvline(x=1, color='black', linestyle='-', linewidth=0.5)
                        
                        # 根据实际评价范围计算索引
                        n = len(values)
                        meas_length = de - da  # 测量范围
                        
                        # 起测点索引 (da)
                        idx_meas_start = 0
                        # 起评点索引 (d1) - 根据实际评价范围计算
                        idx_eval_start = int((d1 - da) / meas_length * (n - 1))
                        idx_eval_start = max(0, min(idx_eval_start, n - 1))
                        # 终评点索引 (d2)
                        idx_eval_end = int((d2 - da) / meas_length * (n - 1))
                        idx_eval_end = max(0, min(idx_eval_end, n - 1))
                        # 终测点索引 (de)
                        idx_meas_end = n - 1
                        
                        # 起测点（蓝色三角形向下）
                        ax.plot(1, y_positions[idx_meas_start], 'v', markersize=8, color='blue', markerfacecolor='blue')
                        ax.annotate(f'da={da:.1f}', xy=(1.05, y_positions[idx_meas_start]), fontsize=9, color='blue')
                        # 起评点（绿色三角形向下）
                        ax.plot(1, y_positions[idx_eval_start], 'v', markersize=8, color='green', markerfacecolor='green')
                        ax.annotate(f'd1={d1:.1f}', xy=(1.05, y_positions[idx_eval_start]), fontsize=9, color='green')
                        # 终评点（橙色三角形向上）
                        ax.plot(1, y_positions[idx_eval_end], '^', markersize=8, color='orange', markerfacecolor='orange')
                        ax.annotate(f'd2={d2:.1f}', xy=(1.05, y_positions[idx_eval_end]), fontsize=9, color='orange')
                        # 终测点（红色三角形向上）
                        ax.plot(1, y_positions[idx_meas_end], '^', markersize=8, color='red', markerfacecolor='red')
                        ax.annotate(f'de={de:.1f}', xy=(1.05, y_positions[idx_meas_end]), fontsize=9, color='red')
                        
                        # 设置Y轴刻度和网格
                        ax.set_ylim(da - 1, de + 1)
                        ax.set_yticks([da, d1, d2, de])
                        ax.set_yticklabels([f'{da:.1f}', f'{d1:.1f}', f'{d2:.1f}', f'{de:.1f}'], fontsize=10)
                        
                        # 设置X轴刻度和网格
                        ax.set_xlim(0.3, 1.7)
                        ax.set_xticks([0.5, 1.0, 1.5])
                        ax.set_xticklabels(['-25', '0', '+25'], fontsize=10)
                        
                        # 添加网格线
                        ax.grid(True, linestyle=':', linewidth=0.5, color='gray')
                        
                        ax.set_xlabel(f'{tooth_id}', fontsize=11, fontweight='bold')
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
                        
                        F_a, fH_a, ff_a, Ca = calc_profile_deviations(values)
                        if F_a is not None:
                            left_profile_results.append({
                                'Tooth': tooth_id,
                                'fHα': fH_a,
                                'ffα': ff_a,
                                'Fα': F_a,
                                'Ca': Ca
                            })
                
                # 左齿面偏差表格 - 带公差和质量等级
                if left_profile_results:
                    df_left = pd.DataFrame(left_profile_results)
                    
                    # 计算平均值和最大值
                    mean_row = {'Tooth': 'Mean'}
                    max_row = {'Tooth': 'Max'}
                    for col in ['fHα', 'ffα', 'Fα', 'Ca']:
                        mean_row[col] = df_left[col].mean()
                        max_row[col] = df_left[col].max()
                    mean_row['fHαm'] = df_left['fHα'].mean()
                    max_row['fHαm'] = np.nan
                    df_left['fHαm'] = np.nan
                    
                    # 添加公差和质量等级列
                    tol_row = {'Tooth': f'Lim.{DEFAULT_QUALITY}'}
                    for col, tol_code in [('fHα', 'fHa'), ('ffα', 'ffa'), ('Fα', 'Fa')]:
                        tol_val = get_tolerance('profile', tol_code, DEFAULT_QUALITY)
                        tol_row[col] = f'±{int(tol_val)}' if tol_val else ''
                    tol_row['Ca'] = ''
                    tol_row['fHαm'] = ''
                    
                    # 在最大值行添加质量等级标注
                    for col, tol_code in [('fHα', 'fHa'), ('ffα', 'ffa'), ('Fα', 'Fa')]:
                        max_val = max_row[col]
                        if max_val is not None and not np.isnan(max_val):
                            quality = calculate_quality_grade(max_val, 'profile', tol_code)
                            if quality:
                                max_row[col] = f"{max_val:.2f} Q{quality}"
                    
                    df_left = pd.concat([df_left, pd.DataFrame([mean_row]), pd.DataFrame([max_row]), pd.DataFrame([tol_row])], ignore_index=True)
                    
                    # 自定义格式化函数
                    def format_value(x):
                        if pd.isna(x):
                            return ''
                        if isinstance(x, str):
                            return x
                        if isinstance(x, (int, float)):
                            return f'{x:.2f}'
                        return str(x)
                    
                    df_display = df_left[['Tooth', 'fHα', 'fHαm', 'ffα', 'Fα', 'Ca']].copy()
                    for col in ['fHα', 'fHαm', 'ffα', 'Fα', 'Ca']:
                        df_display[col] = df_display[col].apply(format_value)
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # 右齿面曲线图
            if profile_teeth_right:
                st.markdown("**Right Flank**")
                n_cols = min(8, len(profile_teeth_right))
                right_profile_results = []
                
                for i, tooth_id in enumerate(profile_teeth_right):
                    if i % n_cols == 0:
                        cols = st.columns(n_cols)
                    
                    with cols[i % n_cols]:
                        tooth_profiles = profile_data['right'][tooth_id]
                        helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                        best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                        values = np.array(tooth_profiles[best_z])
                        
                        fig, ax = plt.subplots(figsize=(2.2, 5.5))
                        # 数据点是从 da 到 de 均匀分布的
                        y_positions = np.linspace(da, de, len(values))
                        
                        # 绘制曲线（红色）
                        ax.plot(values / 50.0 + 1, y_positions, 'r-', linewidth=1.0)
                        
                        # 零点垂直线
                        ax.axvline(x=1, color='black', linestyle='-', linewidth=0.5)
                        
                        # 根据实际评价范围计算索引
                        n = len(values)
                        meas_length = de - da  # 测量范围
                        
                        # 起测点索引 (da)
                        idx_meas_start = 0
                        # 起评点索引 (d1) - 根据实际评价范围计算
                        idx_eval_start = int((d1 - da) / meas_length * (n - 1))
                        idx_eval_start = max(0, min(idx_eval_start, n - 1))
                        # 终评点索引 (d2)
                        idx_eval_end = int((d2 - da) / meas_length * (n - 1))
                        idx_eval_end = max(0, min(idx_eval_end, n - 1))
                        # 终测点索引 (de)
                        idx_meas_end = n - 1
                        
                        # 起测点（蓝色三角形向下）
                        ax.plot(1, y_positions[idx_meas_start], 'v', markersize=8, color='blue', markerfacecolor='blue')
                        ax.annotate(f'da={da:.1f}', xy=(1.05, y_positions[idx_meas_start]), fontsize=9, color='blue')
                        # 起评点（绿色三角形向下）
                        ax.plot(1, y_positions[idx_eval_start], 'v', markersize=8, color='green', markerfacecolor='green')
                        ax.annotate(f'd1={d1:.1f}', xy=(1.05, y_positions[idx_eval_start]), fontsize=9, color='green')
                        # 终评点（橙色三角形向上）
                        ax.plot(1, y_positions[idx_eval_end], '^', markersize=8, color='orange', markerfacecolor='orange')
                        ax.annotate(f'd2={d2:.1f}', xy=(1.05, y_positions[idx_eval_end]), fontsize=9, color='orange')
                        # 终测点（红色三角形向上）
                        ax.plot(1, y_positions[idx_meas_end], '^', markersize=8, color='red', markerfacecolor='red')
                        ax.annotate(f'de={de:.1f}', xy=(1.05, y_positions[idx_meas_end]), fontsize=9, color='red')
                        
                        # 设置Y轴刻度和网格
                        ax.set_ylim(da - 1, de + 1)
                        ax.set_yticks([da, d1, d2, de])
                        ax.set_yticklabels([f'{da:.1f}', f'{d1:.1f}', f'{d2:.1f}', f'{de:.1f}'], fontsize=10)
                        
                        # 设置X轴刻度和网格
                        ax.set_xlim(0.3, 1.7)
                        ax.set_xticks([0.5, 1.0, 1.5])
                        ax.set_xticklabels(['-25', '0', '+25'], fontsize=10)
                        
                        # 添加网格线
                        ax.grid(True, linestyle=':', linewidth=0.5, color='gray')
                        
                        ax.set_xlabel(f'{tooth_id}', fontsize=11, fontweight='bold')
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
                        
                        F_a, fH_a, ff_a, Ca = calc_profile_deviations(values)
                        if F_a is not None:
                            right_profile_results.append({
                                'Tooth': tooth_id,
                                'fHα': fH_a,
                                'ffα': ff_a,
                                'Fα': F_a,
                                'Ca': Ca
                            })
                
                # 右齿面偏差表格 - 带公差和质量等级
                if right_profile_results:
                    df_right = pd.DataFrame(right_profile_results)
                    
                    # 计算平均值和最大值
                    mean_row = {'Tooth': 'Mean'}
                    max_row = {'Tooth': 'Max'}
                    for col in ['fHα', 'ffα', 'Fα', 'Ca']:
                        mean_row[col] = df_right[col].mean()
                        max_row[col] = df_right[col].max()
                    mean_row['fHαm'] = df_right['fHα'].mean()
                    max_row['fHαm'] = np.nan
                    df_right['fHαm'] = np.nan
                    
                    # 添加公差和质量等级列
                    tol_row = {'Tooth': f'Lim.{DEFAULT_QUALITY}'}
                    for col, tol_code in [('fHα', 'fHa'), ('ffα', 'ffa'), ('Fα', 'Fa')]:
                        tol_val = get_tolerance('profile', tol_code, DEFAULT_QUALITY)
                        tol_row[col] = f'±{int(tol_val)}' if tol_val else ''
                    tol_row['Ca'] = ''
                    tol_row['fHαm'] = ''
                    
                    # 在最大值行添加质量等级标注
                    for col, tol_code in [('fHα', 'fHa'), ('ffα', 'ffa'), ('Fα', 'Fa')]:
                        max_val = max_row[col]
                        if max_val is not None and not np.isnan(max_val):
                            quality = calculate_quality_grade(max_val, 'profile', tol_code)
                            if quality:
                                max_row[col] = f"{max_val:.2f} Q{quality}"
                    
                    df_right = pd.concat([df_right, pd.DataFrame([mean_row]), pd.DataFrame([max_row]), pd.DataFrame([tol_row])], ignore_index=True)
                    
                    # 自定义格式化函数
                    def format_value(x):
                        if pd.isna(x):
                            return ''
                        if isinstance(x, str):
                            return x
                        if isinstance(x, (int, float)):
                            return f'{x:.2f}'
                        return str(x)
                    
                    df_display = df_right[['Tooth', 'fHα', 'fHαm', 'ffα', 'Fα', 'Ca']].copy()
                    for col in ['fHα', 'fHαm', 'ffα', 'Fα', 'Ca']:
                        df_display[col] = df_display[col].apply(format_value)
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # ========== Helix 齿向分析 ==========
        st.markdown("#### Helix")
        
        # 获取所有有齿向数据的齿
        helix_teeth_left = sorted(list(helix_data.get('left', {}).keys()), key=tooth_sort_key, reverse=True)
        helix_teeth_right = sorted(list(helix_data.get('right', {}).keys()), key=tooth_sort_key)
        
        if helix_teeth_left or helix_teeth_right:
            # 左齿面曲线图
            if helix_teeth_left:
                st.markdown("**Left Flank**")
                n_cols = min(8, len(helix_teeth_left))
                left_helix_results = []
                
                for i, tooth_id in enumerate(helix_teeth_left):
                    if i % n_cols == 0:
                        cols = st.columns(n_cols)
                    
                    with cols[i % n_cols]:
                        tooth_helix = helix_data['left'][tooth_id]
                        profile_mid = (profile_eval.eval_start + profile_eval.eval_end) / 2
                        best_d = min(tooth_helix.keys(), key=lambda d: abs(d - profile_mid))
                        values = np.array(tooth_helix[best_d])
                        
                        fig, ax = plt.subplots(figsize=(2.2, 5.5))
                        # 数据点是从 ba 到 be 均匀分布的
                        y_positions = np.linspace(ba, be, len(values))
                        
                        # 绘制曲线（黑色）
                        ax.plot(values / 50.0 + 1, y_positions, 'k-', linewidth=1.0)
                        
                        # 零点垂直线
                        ax.axvline(x=1, color='black', linestyle='-', linewidth=0.5)
                        
                        # 根据实际评价范围计算索引
                        n = len(values)
                        meas_length = be - ba  # 测量范围
                        
                        # 起测点索引 (ba)
                        idx_meas_start = 0
                        # 起评点索引 (b1) - 根据实际评价范围计算
                        idx_eval_start = int((b1 - ba) / meas_length * (n - 1))
                        idx_eval_start = max(0, min(idx_eval_start, n - 1))
                        # 终评点索引 (b2)
                        idx_eval_end = int((b2 - ba) / meas_length * (n - 1))
                        idx_eval_end = max(0, min(idx_eval_end, n - 1))
                        # 终测点索引 (be)
                        idx_meas_end = n - 1
                        
                        # 起测点（蓝色三角形向下）
                        ax.plot(1, y_positions[idx_meas_start], 'v', markersize=8, color='blue', markerfacecolor='blue')
                        ax.annotate(f'ba={ba:.1f}', xy=(1.05, y_positions[idx_meas_start]), fontsize=9, color='blue')
                        # 起评点（绿色三角形向下）
                        ax.plot(1, y_positions[idx_eval_start], 'v', markersize=8, color='green', markerfacecolor='green')
                        ax.annotate(f'b1={b1:.1f}', xy=(1.05, y_positions[idx_eval_start]), fontsize=9, color='green')
                        # 终评点（橙色三角形向上）
                        ax.plot(1, y_positions[idx_eval_end], '^', markersize=8, color='orange', markerfacecolor='orange')
                        ax.annotate(f'b2={b2:.1f}', xy=(1.05, y_positions[idx_eval_end]), fontsize=9, color='orange')
                        # 终测点（红色三角形向上）
                        ax.plot(1, y_positions[idx_meas_end], '^', markersize=8, color='red', markerfacecolor='red')
                        ax.annotate(f'be={be:.1f}', xy=(1.05, y_positions[idx_meas_end]), fontsize=9, color='red')
                        
                        # 设置Y轴刻度和网格
                        ax.set_ylim(ba - 1, be + 1)
                        ax.set_yticks([ba, b1, b2, be])
                        ax.set_yticklabels([f'{ba:.1f}', f'{b1:.1f}', f'{b2:.1f}', f'{be:.1f}'], fontsize=10)
                        
                        # 设置X轴刻度和网格
                        ax.set_xlim(0.3, 1.7)
                        ax.set_xticks([0.5, 1.0, 1.5])
                        ax.set_xticklabels(['-25', '0', '+25'], fontsize=10)
                        
                        # 添加网格线
                        ax.grid(True, linestyle=':', linewidth=0.5, color='gray')
                        
                        ax.set_xlabel(f'{tooth_id}', fontsize=11, fontweight='bold')
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
                        
                        F_b, fH_b, ff_b, Cb = calc_lead_deviations(values)
                        if F_b is not None:
                            left_helix_results.append({
                                'Tooth': tooth_id,
                                'fHβ': fH_b,
                                'ffβ': ff_b,
                                'Fβ': F_b,
                                'Cb': Cb
                            })
                
                # 左齿面齿向偏差表格 - 带公差和质量等级
                if left_helix_results:
                    df_left_h = pd.DataFrame(left_helix_results)
                    
                    # 计算平均值和最大值
                    mean_row = {'Tooth': 'Mean'}
                    max_row = {'Tooth': 'Max'}
                    for col in ['fHβ', 'ffβ', 'Fβ', 'Cb']:
                        mean_row[col] = df_left_h[col].mean()
                        max_row[col] = df_left_h[col].max()
                    mean_row['fHβm'] = df_left_h['fHβ'].mean()
                    max_row['fHβm'] = np.nan
                    df_left_h['fHβm'] = np.nan
                    
                    # 添加公差和质量等级列
                    tol_row = {'Tooth': f'Lim.{DEFAULT_QUALITY}'}
                    for col, tol_code in [('fHβ', 'fHb'), ('ffβ', 'ffb'), ('Fβ', 'Fb')]:
                        tol_val = get_tolerance('lead', tol_code, DEFAULT_QUALITY)
                        tol_row[col] = f'±{int(tol_val)}' if tol_val else ''
                    tol_row['Cb'] = ''
                    tol_row['fHβm'] = ''
                    
                    # 在最大值行添加质量等级标注
                    for col, tol_code in [('fHβ', 'fHb'), ('ffβ', 'ffb'), ('Fβ', 'Fb')]:
                        max_val = max_row[col]
                        if max_val is not None and not np.isnan(max_val):
                            quality = calculate_quality_grade(max_val, 'lead', tol_code)
                            if quality:
                                max_row[col] = f"{max_val:.2f} Q{quality}"
                    
                    df_left_h = pd.concat([df_left_h, pd.DataFrame([mean_row]), pd.DataFrame([max_row]), pd.DataFrame([tol_row])], ignore_index=True)
                    
                    # 自定义格式化函数
                    def format_value(x):
                        if pd.isna(x):
                            return ''
                        if isinstance(x, str):
                            return x
                        if isinstance(x, (int, float)):
                            return f'{x:.2f}'
                        return str(x)
                    
                    df_display = df_left_h[['Tooth', 'fHβ', 'fHβm', 'ffβ', 'Fβ', 'Cb']].copy()
                    for col in ['fHβ', 'fHβm', 'ffβ', 'Fβ', 'Cb']:
                        df_display[col] = df_display[col].apply(format_value)
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # 右齿面曲线图
            if helix_teeth_right:
                st.markdown("**Right Flank**")
                n_cols = min(8, len(helix_teeth_right))
                right_helix_results = []
                
                for i, tooth_id in enumerate(helix_teeth_right):
                    if i % n_cols == 0:
                        cols = st.columns(n_cols)
                    
                    with cols[i % n_cols]:
                        tooth_helix = helix_data['right'][tooth_id]
                        profile_mid = (profile_eval.eval_start + profile_eval.eval_end) / 2
                        best_d = min(tooth_helix.keys(), key=lambda d: abs(d - profile_mid))
                        values = np.array(tooth_helix[best_d])
                        
                        fig, ax = plt.subplots(figsize=(2.2, 5.5))
                        # 数据点是从 ba 到 be 均匀分布的
                        y_positions = np.linspace(ba, be, len(values))
                        
                        # 绘制曲线（黑色）
                        ax.plot(values / 50.0 + 1, y_positions, 'k-', linewidth=1.0)
                        
                        # 零点垂直线
                        ax.axvline(x=1, color='black', linestyle='-', linewidth=0.5)
                        
                        # 根据实际评价范围计算索引
                        n = len(values)
                        meas_length = be - ba  # 测量范围
                        
                        # 起测点索引 (ba)
                        idx_meas_start = 0
                        # 起评点索引 (b1) - 根据实际评价范围计算
                        idx_eval_start = int((b1 - ba) / meas_length * (n - 1))
                        idx_eval_start = max(0, min(idx_eval_start, n - 1))
                        # 终评点索引 (b2)
                        idx_eval_end = int((b2 - ba) / meas_length * (n - 1))
                        idx_eval_end = max(0, min(idx_eval_end, n - 1))
                        # 终测点索引 (be)
                        idx_meas_end = n - 1
                        
                        # 起测点（蓝色三角形向下）
                        ax.plot(1, y_positions[idx_meas_start], 'v', markersize=8, color='blue', markerfacecolor='blue')
                        ax.annotate(f'ba={ba:.1f}', xy=(1.05, y_positions[idx_meas_start]), fontsize=9, color='blue')
                        # 起评点（绿色三角形向下）
                        ax.plot(1, y_positions[idx_eval_start], 'v', markersize=8, color='green', markerfacecolor='green')
                        ax.annotate(f'b1={b1:.1f}', xy=(1.05, y_positions[idx_eval_start]), fontsize=9, color='green')
                        # 终评点（橙色三角形向上）
                        ax.plot(1, y_positions[idx_eval_end], '^', markersize=8, color='orange', markerfacecolor='orange')
                        ax.annotate(f'b2={b2:.1f}', xy=(1.05, y_positions[idx_eval_end]), fontsize=9, color='orange')
                        # 终测点（红色三角形向上）
                        ax.plot(1, y_positions[idx_meas_end], '^', markersize=8, color='red', markerfacecolor='red')
                        ax.annotate(f'be={be:.1f}', xy=(1.05, y_positions[idx_meas_end]), fontsize=9, color='red')
                        
                        # 设置Y轴刻度和网格
                        ax.set_ylim(ba - 1, be + 1)
                        ax.set_yticks([ba, b1, b2, be])
                        ax.set_yticklabels([f'{ba:.1f}', f'{b1:.1f}', f'{b2:.1f}', f'{be:.1f}'], fontsize=10)
                        
                        # 设置X轴刻度和网格
                        ax.set_xlim(0.3, 1.7)
                        ax.set_xticks([0.5, 1.0, 1.5])
                        ax.set_xticklabels(['-25', '0', '+25'], fontsize=10)
                        
                        # 添加网格线
                        ax.grid(True, linestyle=':', linewidth=0.5, color='gray')
                        
                        ax.set_xlabel(f'{tooth_id}', fontsize=11, fontweight='bold')
                        
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
                        
                        F_b, fH_b, ff_b, Cb = calc_lead_deviations(values)
                        if F_b is not None:
                            right_helix_results.append({
                                'Tooth': tooth_id,
                                'fHβ': fH_b,
                                'ffβ': ff_b,
                                'Fβ': F_b,
                                'Cb': Cb
                            })
                
                # 右齿面齿向偏差表格 - 带公差和质量等级
                if right_helix_results:
                    df_right_h = pd.DataFrame(right_helix_results)
                    
                    # 计算平均值和最大值
                    mean_row = {'Tooth': 'Mean'}
                    max_row = {'Tooth': 'Max'}
                    for col in ['fHβ', 'ffβ', 'Fβ', 'Cb']:
                        mean_row[col] = df_right_h[col].mean()
                        max_row[col] = df_right_h[col].max()
                    mean_row['fHβm'] = df_right_h['fHβ'].mean()
                    max_row['fHβm'] = np.nan
                    df_right_h['fHβm'] = np.nan
                    
                    # 添加公差和质量等级列
                    tol_row = {'Tooth': f'Lim.{DEFAULT_QUALITY}'}
                    for col, tol_code in [('fHβ', 'fHb'), ('ffβ', 'ffb'), ('Fβ', 'Fb')]:
                        tol_val = get_tolerance('lead', tol_code, DEFAULT_QUALITY)
                        tol_row[col] = f'±{int(tol_val)}' if tol_val else ''
                    tol_row['Cb'] = ''
                    tol_row['fHβm'] = ''
                    
                    # 在最大值行添加质量等级标注
                    for col, tol_code in [('fHβ', 'fHb'), ('ffβ', 'ffb'), ('Fβ', 'Fb')]:
                        max_val = max_row[col]
                        if max_val is not None and not np.isnan(max_val):
                            quality = calculate_quality_grade(max_val, 'lead', tol_code)
                            if quality:
                                max_row[col] = f"{max_val:.2f} Q{quality}"
                    
                    df_right_h = pd.concat([df_right_h, pd.DataFrame([mean_row]), pd.DataFrame([max_row]), pd.DataFrame([tol_row])], ignore_index=True)
                    
                    # 自定义格式化函数
                    def format_value(x):
                        if pd.isna(x):
                            return ''
                        if isinstance(x, str):
                            return x
                        if isinstance(x, (int, float)):
                            return f'{x:.2f}'
                        return str(x)
                    
                    df_display = df_right_h[['Tooth', 'fHβ', 'fHβm', 'ffβ', 'Fβ', 'Cb']].copy()
                    for col in ['fHβ', 'fHβm', 'ffβ', 'Fβ', 'Cb']:
                        df_display[col] = df_display[col].apply(format_value)
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
            
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
                plt.close(fig)

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
                plt.close(fig)

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
                plt.close(fig)

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
                plt.close(fig)

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
                plt.close(fig)

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

        # 获取所有有测量数据的齿
        measured_teeth = set()
        for side in ['left', 'right']:
            if side in profile_data:
                measured_teeth.update(profile_data[side].keys())
            if side in helix_data:
                measured_teeth.update(helix_data[side].keys())
        
        # 按顺序排列有测量数据的齿（使用数字排序）
        measured_teeth_list = sorted(list(measured_teeth), key=tooth_sort_key)
        
        if not measured_teeth_list:
            st.warning("未找到测量数据")
            st.stop()
        
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
                plt.close(fig)
        
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
                plt.close(fig)
        
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
                    plt.close(fig)
                    
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
                            plt.close(fig2)
                    
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
                        plt.close(fig3)
        
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
                    plt.close(fig)
                    
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
                            plt.close(fig2)
                    
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
                        plt.close(fig3)
    
    elif page == '📉 合并曲线':
        st.markdown("## Merged Curve Analysis (0-360°)")

        ze = gear_params.teeth_count if gear_params else 87

        name_mapping = {
            'profile_left': 'Left Profile',
            'profile_right': 'Right Profile',
            'helix_left': 'Left Lead',
            'helix_right': 'Right Lead'
        }

        # 按需计算分析结果
        with st.spinner("正在计算合并曲线..."):
            results = {
                'profile_left': analyzer.analyze_profile('left', verbose=False),
                'profile_right': analyzer.analyze_profile('right', verbose=False),
                'helix_left': analyzer.analyze_helix('left', verbose=False),
                'helix_right': analyzer.analyze_helix('right', verbose=False)
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
                plt.close(fig)

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
                plt.close(fig)
    
    elif page == '📊 频谱分析':
        st.markdown("## Spectrum Analysis")

        ze = gear_params.teeth_count if gear_params else 87

        name_mapping = {
            'profile_left': 'Left Profile',
            'profile_right': 'Right Profile',
            'helix_left': 'Left Lead',
            'helix_right': 'Right Lead'
        }

        # 按需计算分析结果
        with st.spinner("正在计算频谱分析..."):
            results = {
                'profile_left': analyzer.analyze_profile('left', verbose=False),
                'profile_right': analyzer.analyze_profile('right', verbose=False),
                'helix_left': analyzer.analyze_helix('left', verbose=False),
                'helix_right': analyzer.analyze_helix('right', verbose=False)
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
                plt.close(fig)
    
    elif page == '🔍 三截面扭曲数据':
        st.markdown("## 三截面扭曲数据报告")
        
        # 检测数据格式：检查是否有1a,1b,1c这样的三截面数据
        all_teeth = set()
        for side in ['left', 'right']:
            if side in profile_data:
                all_teeth.update(profile_data[side].keys())
            if side in helix_data:
                all_teeth.update(helix_data[side].keys())
        
        # 检查是否有三截面数据（1a, 1b, 1c）
        has_three_section = any(t in all_teeth for t in ['1a', '1b', '1c'])
        
        if has_three_section:
            st.markdown("### 齿号 1a, 1b, 1c 的齿形/齿向偏差分析")
            tooth_sections = ['1a', '1b', '1c']
        else:
            # 如果没有三截面数据，检查是否有齿号1的数据
            if '1' in all_teeth:
                st.markdown("### 齿号 1 的齿形/齿向偏差分析")
                tooth_sections = ['1']
            else:
                # 显示前3个可用的齿
                available_teeth = sorted(list(all_teeth), key=tooth_sort_key)[:3]
                if available_teeth:
                    st.markdown(f"### 齿号 {', '.join(available_teeth)} 的齿形/齿向偏差分析")
                    tooth_sections = available_teeth
                else:
                    st.warning("未找到可用的齿数据")
                    st.stop()
        
        # 先收集所有数据（用于后面的表格显示）
        profile_sections_data = []
        helix_sections_data = []
        
        for section in tooth_sections:
            # 齿形数据
            row_data_profile = {'Tooth': section}
            has_profile_data = False
            
            # 左齿面
            if 'left' in profile_data and section in profile_data['left']:
                tooth_data = profile_data['left'][section]
                if tooth_data:
                    z_positions = list(tooth_data.keys())
                    if z_positions:
                        mid_z = z_positions[len(z_positions) // 2]
                        values = np.array(tooth_data[mid_z])
                        F_a, fH_a, ff_a, Ca = calc_profile_deviations(values)
                        if F_a is not None:
                            row_data_profile['fHα_L'] = fH_a
                            row_data_profile['ffα_L'] = ff_a
                            row_data_profile['Fα_L'] = F_a
                            row_data_profile['Ca_L'] = Ca
                            has_profile_data = True
            
            # 右齿面
            if 'right' in profile_data and section in profile_data['right']:
                tooth_data = profile_data['right'][section]
                if tooth_data:
                    z_positions = list(tooth_data.keys())
                    if z_positions:
                        mid_z = z_positions[len(z_positions) // 2]
                        values = np.array(tooth_data[mid_z])
                        F_a, fH_a, ff_a, Ca = calc_profile_deviations(values)
                        if F_a is not None:
                            row_data_profile['fHα_R'] = fH_a
                            row_data_profile['ffα_R'] = ff_a
                            row_data_profile['Fα_R'] = F_a
                            row_data_profile['Ca_R'] = Ca
                            has_profile_data = True
            
            if has_profile_data:
                profile_sections_data.append(row_data_profile)
            
            # 齿向数据
            row_data_helix = {'Tooth': section}
            has_helix_data = False
            
            # 左齿面
            if 'left' in helix_data and section in helix_data['left']:
                tooth_data = helix_data['left'][section]
                if tooth_data:
                    d_positions = list(tooth_data.keys())
                    if d_positions:
                        mid_d = d_positions[len(d_positions) // 2]
                        values = np.array(tooth_data[mid_d])
                        F_b, fH_b, ff_b, Cb = calc_lead_deviations(values)
                        if F_b is not None:
                            row_data_helix['fHβ_L'] = fH_b
                            row_data_helix['ffβ_L'] = ff_b
                            row_data_helix['Fβ_L'] = F_b
                            row_data_helix['Cb_L'] = Cb
                            has_helix_data = True
            
            # 右齿面
            if 'right' in helix_data and section in helix_data['right']:
                tooth_data = helix_data['right'][section]
                if tooth_data:
                    d_positions = list(tooth_data.keys())
                    if d_positions:
                        mid_d = d_positions[len(d_positions) // 2]
                        values = np.array(tooth_data[mid_d])
                        F_b, fH_b, ff_b, Cb = calc_lead_deviations(values)
                        if F_b is not None:
                            row_data_helix['fHβ_R'] = fH_b
                            row_data_helix['ffβ_R'] = ff_b
                            row_data_helix['Fβ_R'] = F_b
                            row_data_helix['Cb_R'] = Cb
                            has_helix_data = True
            
            if has_helix_data:
                helix_sections_data.append(row_data_helix)
        
        # 显示详细曲线图 - 按类型分组：左齿形、右齿形、左齿向、右齿向
        st.markdown("#### 详细曲线图")
        
        # ===== 左齿面齿形 (Left Profile) =====
        st.markdown("**Left Profile 左齿面齿形**")
        cols = st.columns(3)
        for i, section in enumerate(tooth_sections):
            with cols[i]:
                if 'left' in profile_data and section in profile_data['left']:
                    tooth_profiles = profile_data['left'][section]
                    if tooth_profiles:
                        best_z = list(tooth_profiles.keys())[len(tooth_profiles)//2]
                        values = np.array(tooth_profiles[best_z])
                        
                        fig, ax = plt.subplots(figsize=(3.5, 5))
                        y_positions = np.linspace(da, de, len(values))
                        ax.plot(values / 50.0 + 1, y_positions, 'r-', linewidth=1.0)
                        ax.axvline(x=1, color='black', linestyle='-', linewidth=0.5)
                        
                        n = len(values)
                        meas_length = de - da
                        idx_eval_start = int((d1 - da) / meas_length * (n - 1))
                        idx_eval_end = int((d2 - da) / meas_length * (n - 1))
                        
                        ax.plot(1, y_positions[0], 'v', markersize=8, color='blue')
                        ax.plot(1, y_positions[idx_eval_start], 'v', markersize=8, color='green')
                        ax.plot(1, y_positions[idx_eval_end], '^', markersize=8, color='orange')
                        ax.plot(1, y_positions[-1], '^', markersize=8, color='red')
                        
                        ax.set_ylim(da - 1, de + 1)
                        ax.set_yticks([da, d1, d2, de])
                        ax.set_yticklabels([f'{da:.1f}', f'{d1:.1f}', f'{d2:.1f}', f'{de:.1f}'], fontsize=8)
                        ax.set_xlim(0.3, 1.7)
                        ax.set_xticks([0.5, 1.0, 1.5])
                        ax.set_xticklabels(['-25', '0', '+25'], fontsize=8)
                        ax.grid(True, linestyle=':', linewidth=0.5, color='gray')
                        ax.set_xlabel(f'{section}', fontsize=10, fontweight='bold')
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
        
        # 左齿面齿形数据表
        if profile_sections_data:
            st.markdown("**Left Profile 数据**")
            df_left_profile = pd.DataFrame(profile_sections_data)[['Tooth', 'fHα_L', 'ffα_L', 'Fα_L', 'Ca_L']]
            df_left_profile = df_left_profile.dropna()
            if not df_left_profile.empty:
                st.dataframe(df_left_profile.style.format({
                    'fHα_L': '{:.2f}', 'ffα_L': '{:.2f}', 'Fα_L': '{:.2f}', 'Ca_L': '{:.2f}'
                }), use_container_width=True, hide_index=True)
        
        # ===== 右齿面齿形 (Right Profile) =====
        st.markdown("**Right Profile 右齿面齿形**")
        cols = st.columns(3)
        for i, section in enumerate(tooth_sections):
            with cols[i]:
                if 'right' in profile_data and section in profile_data['right']:
                    tooth_profiles = profile_data['right'][section]
                    if tooth_profiles:
                        best_z = list(tooth_profiles.keys())[len(tooth_profiles)//2]
                        values = np.array(tooth_profiles[best_z])
                        
                        fig, ax = plt.subplots(figsize=(3.5, 5))
                        y_positions = np.linspace(da, de, len(values))
                        ax.plot(values / 50.0 + 1, y_positions, 'r-', linewidth=1.0)
                        ax.axvline(x=1, color='black', linestyle='-', linewidth=0.5)
                        
                        n = len(values)
                        meas_length = de - da
                        idx_eval_start = int((d1 - da) / meas_length * (n - 1))
                        idx_eval_end = int((d2 - da) / meas_length * (n - 1))
                        
                        ax.plot(1, y_positions[0], 'v', markersize=8, color='blue')
                        ax.plot(1, y_positions[idx_eval_start], 'v', markersize=8, color='green')
                        ax.plot(1, y_positions[idx_eval_end], '^', markersize=8, color='orange')
                        ax.plot(1, y_positions[-1], '^', markersize=8, color='red')
                        
                        ax.set_ylim(da - 1, de + 1)
                        ax.set_yticks([da, d1, d2, de])
                        ax.set_yticklabels([f'{da:.1f}', f'{d1:.1f}', f'{d2:.1f}', f'{de:.1f}'], fontsize=8)
                        ax.set_xlim(0.3, 1.7)
                        ax.set_xticks([0.5, 1.0, 1.5])
                        ax.set_xticklabels(['-25', '0', '+25'], fontsize=8)
                        ax.grid(True, linestyle=':', linewidth=0.5, color='gray')
                        ax.set_xlabel(f'{section}', fontsize=10, fontweight='bold')
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
        
        # 右齿面齿形数据表
        if profile_sections_data:
            st.markdown("**Right Profile 数据**")
            df_right_profile = pd.DataFrame(profile_sections_data)[['Tooth', 'fHα_R', 'ffα_R', 'Fα_R', 'Ca_R']]
            df_right_profile = df_right_profile.dropna()
            if not df_right_profile.empty:
                st.dataframe(df_right_profile.style.format({
                    'fHα_R': '{:.2f}', 'ffα_R': '{:.2f}', 'Fα_R': '{:.2f}', 'Ca_R': '{:.2f}'
                }), use_container_width=True, hide_index=True)
        
        # ===== 左齿面齿向 (Left Helix) =====
        st.markdown("**Left Helix 左齿面齿向**")
        cols = st.columns(3)
        for i, section in enumerate(tooth_sections):
            with cols[i]:
                if 'left' in helix_data and section in helix_data['left']:
                    tooth_helix = helix_data['left'][section]
                    if tooth_helix:
                        best_d = list(tooth_helix.keys())[len(tooth_helix)//2]
                        values = np.array(tooth_helix[best_d])
                        
                        fig, ax = plt.subplots(figsize=(3.5, 5))
                        y_positions = np.linspace(ba, be, len(values))
                        ax.plot(values / 50.0 + 1, y_positions, 'k-', linewidth=1.0)
                        ax.axvline(x=1, color='black', linestyle='-', linewidth=0.5)
                        
                        n = len(values)
                        meas_length = be - ba
                        idx_eval_start = int((b1 - ba) / meas_length * (n - 1))
                        idx_eval_end = int((b2 - ba) / meas_length * (n - 1))
                        
                        ax.plot(1, y_positions[0], 'v', markersize=8, color='blue')
                        ax.plot(1, y_positions[idx_eval_start], 'v', markersize=8, color='green')
                        ax.plot(1, y_positions[idx_eval_end], '^', markersize=8, color='orange')
                        ax.plot(1, y_positions[-1], '^', markersize=8, color='red')
                        
                        ax.set_ylim(ba - 1, be + 1)
                        ax.set_yticks([ba, b1, b2, be])
                        ax.set_yticklabels([f'{ba:.1f}', f'{b1:.1f}', f'{b2:.1f}', f'{be:.1f}'], fontsize=8)
                        ax.set_xlim(0.3, 1.7)
                        ax.set_xticks([0.5, 1.0, 1.5])
                        ax.set_xticklabels(['-25', '0', '+25'], fontsize=8)
                        ax.grid(True, linestyle=':', linewidth=0.5, color='gray')
                        ax.set_xlabel(f'{section}', fontsize=10, fontweight='bold')
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
        
        # 左齿面齿向数据表
        if helix_sections_data:
            st.markdown("**Left Helix 数据**")
            df_left_helix = pd.DataFrame(helix_sections_data)[['Tooth', 'fHβ_L', 'ffβ_L', 'Fβ_L', 'Cb_L']]
            df_left_helix = df_left_helix.dropna()
            if not df_left_helix.empty:
                st.dataframe(df_left_helix.style.format({
                    'fHβ_L': '{:.2f}', 'ffβ_L': '{:.2f}', 'Fβ_L': '{:.2f}', 'Cb_L': '{:.2f}'
                }), use_container_width=True, hide_index=True)
        
        # ===== 右齿面齿向 (Right Helix) =====
        st.markdown("**Right Helix 右齿面齿向**")
        cols = st.columns(3)
        for i, section in enumerate(tooth_sections):
            with cols[i]:
                if 'right' in helix_data and section in helix_data['right']:
                    tooth_helix = helix_data['right'][section]
                    if tooth_helix:
                        best_d = list(tooth_helix.keys())[len(tooth_helix)//2]
                        values = np.array(tooth_helix[best_d])
                        
                        fig, ax = plt.subplots(figsize=(3.5, 5))
                        y_positions = np.linspace(ba, be, len(values))
                        ax.plot(values / 50.0 + 1, y_positions, 'k-', linewidth=1.0)
                        ax.axvline(x=1, color='black', linestyle='-', linewidth=0.5)
                        
                        n = len(values)
                        meas_length = be - ba
                        idx_eval_start = int((b1 - ba) / meas_length * (n - 1))
                        idx_eval_end = int((b2 - ba) / meas_length * (n - 1))
                        
                        ax.plot(1, y_positions[0], 'v', markersize=8, color='blue')
                        ax.plot(1, y_positions[idx_eval_start], 'v', markersize=8, color='green')
                        ax.plot(1, y_positions[idx_eval_end], '^', markersize=8, color='orange')
                        ax.plot(1, y_positions[-1], '^', markersize=8, color='red')
                        
                        ax.set_ylim(ba - 1, be + 1)
                        ax.set_yticks([ba, b1, b2, be])
                        ax.set_yticklabels([f'{ba:.1f}', f'{b1:.1f}', f'{b2:.1f}', f'{be:.1f}'], fontsize=8)
                        ax.set_xlim(0.3, 1.7)
                        ax.set_xticks([0.5, 1.0, 1.5])
                        ax.set_xticklabels(['-25', '0', '+25'], fontsize=8)
                        ax.grid(True, linestyle=':', linewidth=0.5, color='gray')
                        ax.set_xlabel(f'{section}', fontsize=10, fontweight='bold')
                        plt.tight_layout()
                        st.pyplot(fig)
                        plt.close(fig)
        
        # 右齿面齿向数据表
        if helix_sections_data:
            st.markdown("**Right Helix 数据**")
            df_right_helix = pd.DataFrame(helix_sections_data)[['Tooth', 'fHβ_R', 'ffβ_R', 'Fβ_R', 'Cb_R']]
            df_right_helix = df_right_helix.dropna()
            if not df_right_helix.empty:
                st.dataframe(df_right_helix.style.format({
                    'fHβ_R': '{:.2f}', 'ffβ_R': '{:.2f}', 'Fβ_R': '{:.2f}', 'Cb_R': '{:.2f}'
                }), use_container_width=True, hide_index=True)
    
    # 清理临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)

else:
    st.info("👆 请在左侧上传 MKA 文件开始分析")
    
    st.markdown("""
    ### 📋 功能说明
    
    本软件提供齿轮波纹度分析：
    
    | 功能 | 说明 |
    |------|------|
    | 📄 专业报告 | 齿形/齿向分析图表和数据表，支持PDF下载 |
    | 🔍 三截面扭曲数据 | 齿号1a/1b/1c的齿形/齿向偏差报表 |
    | 📊 周节详细报表 | 周节偏差 fp/Fp/Fr 分析 |
    | 📈 单齿分析 | 单个齿的齿形/齿向偏差曲线 |
    | 📉 合并曲线 | 0-360°合并曲线、高阶波纹度评价、前5齿放大 |
    | 📊 频谱分析 | 阶次振幅相位分析（全部齿形/齿向） |
    """)

st.markdown("---")
st.caption("齿轮波纹度软件 | 基于 Python + Streamlit 构建")
