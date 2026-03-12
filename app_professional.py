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
from matplotlib.colors import LinearSegmentedColormap
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
    page_title="齿轮测量分析系统 - 专业版",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 自定义CSS样式 ==========
st.markdown("""
<style>
    /* 导入Google字体 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
    
    /* 全局样式 */
    * {
        font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    /* 主色调 */
    :root {
        --primary-color: #2563eb;
        --primary-dark: #1d4ed8;
        --primary-light: #3b82f6;
        --secondary-color: #f59e0b;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --danger-color: #ef4444;
        --info-color: #06b6d4;
        --gray-50: #f9fafb;
        --gray-100: #f3f4f6;
        --gray-200: #e5e7eb;
        --gray-300: #d1d5db;
        --gray-600: #4b5563;
        --gray-700: #374151;
        --gray-800: #1f2937;
        --gray-900: #111827;
    }
    
    /* 主容器 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* 主标题样式 */
    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        text-align: center;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 2px;
    }
    
    .sub-title {
        font-size: 1.2rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* 卡片样式 */
    .card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 0.75rem 0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
        border: 1px solid #e5e7eb;
        transition: all 0.3s ease;
    }
    
    .card:hover {
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        transform: translateY(-2px);
    }
    
    .card-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1f2937;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 0.75rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
    }
    
    .card-header::before {
        content: '';
        width: 4px;
        height: 20px;
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        border-radius: 2px;
        margin-right: 10px;
    }
    
    /* 指标卡片 */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 12px;
        padding: 1.25rem;
        text-align: center;
        margin: 0.25rem;
        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1.2;
    }
    
    .metric-label {
        font-size: 0.85rem;
        opacity: 0.9;
        margin-top: 0.25rem;
    }
    
    /* 状态标签 */
    .status-excellent {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 0.35rem 1rem;
        border-radius: 50px;
        font-weight: 600;
        font-size: 0.9rem;
        box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);
    }
    
    .status-good {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 0.35rem 1rem;
        border-radius: 50px;
        font-weight: 600;
        font-size: 0.9rem;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
    }
    
    .status-warning {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 0.35rem 1rem;
        border-radius: 50px;
        font-weight: 600;
        font-size: 0.9rem;
        box-shadow: 0 2px 4px rgba(245, 158, 11, 0.3);
    }
    
    .status-danger {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
        padding: 0.35rem 1rem;
        border-radius: 50px;
        font-weight: 600;
        font-size: 0.9rem;
        box-shadow: 0 2px 4px rgba(239, 68, 68, 0.3);
    }
    
    /* 数据表格样式 */
    .stDataFrame {
        border: none !important;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .stDataFrame table {
        border-collapse: separate !important;
        border-spacing: 0 !important;
    }
    
    .stDataFrame th {
        background: linear-gradient(135deg, #1f77b4 0%, #2563eb 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.875rem 1rem !important;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.5px;
    }
    
    .stDataFrame td {
        padding: 0.75rem 1rem !important;
        border-bottom: 1px solid #e5e7eb !important;
        font-size: 0.9rem;
    }
    
    .stDataFrame tr:nth-child(even) {
        background-color: #f9fafb !important;
    }
    
    .stDataFrame tr:hover {
        background-color: #f3f4f6 !important;
    }
    
    /* 侧边栏样式 */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%) !important;
    }
    
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] .stRadio > label,
    section[data-testid="stSidebar"] label {
        color: #1e293b !important;
        font-weight: 500 !important;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #1e293b !important;
        font-weight: 600 !important;
    }
    
    section[data-testid="stSidebar"] .stRadio > div {
        background: rgba(255, 255, 255, 0.7);
        border-radius: 12px;
        padding: 0.5rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    section[data-testid="stSidebar"] .stRadio > div > label {
        background: transparent;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        transition: all 0.2s ease;
        color: #334155 !important;
        font-weight: 500 !important;
    }
    
    section[data-testid="stSidebar"] .stRadio > div > label:hover {
        background: rgba(102, 126, 234, 0.1);
        color: #667eea !important;
    }
    
    section[data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(102, 126, 234, 0.3);
    }
    
    section[data-testid="stSidebar"] .stSuccess {
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 8px;
        color: #059669 !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
        border: 1px solid #4b5563;
        color: white;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #4b5563 0%, #374151 100%);
        border-color: #6b7280;
    }
    
    /* 按钮样式 */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* 进度条样式 */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    .stProgress > div > div {
        background: #e5e7eb;
        border-radius: 10px;
        height: 8px;
    }
    
    /* 问题列表样式 */
    .issue-critical {
        border-left: 4px solid #ef4444;
        background: linear-gradient(90deg, rgba(239, 68, 68, 0.1) 0%, transparent 100%);
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .issue-warning {
        border-left: 4px solid #f59e0b;
        background: linear-gradient(90deg, rgba(245, 158, 11, 0.1) 0%, transparent 100%);
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .issue-info {
        border-left: 4px solid #06b6d4;
        background: linear-gradient(90deg, rgba(6, 182, 212, 0.1) 0%, transparent 100%);
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .issue-success {
        border-left: 4px solid #10b981;
        background: linear-gradient(90deg, rgba(16, 185, 129, 0.1) 0%, transparent 100%);
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    /* 图表容器 */
    .chart-container {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        margin: 0.75rem 0;
        border: 1px solid #e5e7eb;
    }
    
    /* 分隔线 */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #d1d5db, transparent);
        margin: 2rem 0;
    }
    
    /* 标题装饰 */
    h1 {
        font-weight: 700;
        color: #111827;
    }
    
    h2 {
        border-left: 4px solid #667eea;
        padding-left: 1rem;
        font-weight: 600;
        color: #1f2937;
    }
    
    h3 {
        border-left: 3px solid #764ba2;
        padding-left: 0.75rem;
        font-weight: 600;
        color: #374151;
    }
    
    h4 {
        font-weight: 600;
        color: #4b5563;
    }
    
    /* Expander样式 */
    .streamlit-expanderHeader {
        background: #f9fafb;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        font-weight: 500;
    }
    
    /* 隐藏Streamlit默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #5a67d8 0%, #6b46c1 100%);
    }
    
    /* 动画效果 */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .card, .stDataFrame, .chart-container {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* 工具提示 */
    .tooltip {
        position: relative;
        display: inline-block;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        background-color: #1f2937;
        color: #fff;
        text-align: center;
        padding: 0.5rem;
        border-radius: 6px;
        position: absolute;
        z-index: 1;
        font-size: 0.8rem;
        white-space: nowrap;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
    }
    
    /* 徽章 */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 50px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-primary {
        background: #dbeafe;
        color: #1d4ed8;
    }
    
    .badge-success {
        background: #d1fae5;
        color: #059669;
    }
    
    .badge-warning {
        background: #fef3c7;
        color: #d97706;
    }
    
    .badge-danger {
        background: #fee2e2;
        color: #dc2626;
    }
    
    /* 文件上传区域中文 */
    .stFileUploader > div:first-child > div:first-child > div:first-child::before {
        content: "拖放文件到此处" !important;
        display: block;
        font-size: 14px;
        color: #666;
        margin-bottom: 4px;
    }
    
    .stFileUploader [data-testid="stFileUploaderDropzone"] div div:first-child {
        visibility: hidden;
    }
    
    .stFileUploader [data-testid="stFileUploaderDropzone"] div div:first-child::after {
        content: "限制 200MB 每个文件";
        visibility: visible;
        display: block;
        font-size: 12px;
        color: #888;
    }
    
    .stFileUploader button {
        font-size: 0px !important;
    }
    
    .stFileUploader button::after {
        content: "浏览文件";
        font-size: 14px !important;
    }
    
    /* 侧边栏紧凑布局 */
    [data-testid="stSidebar"] .block-container {
        padding-top: 0.3rem !important;
        padding-bottom: 0.3rem !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        margin-bottom: 0.2rem !important;
    }
    
    [data-testid="stSidebar"] hr {
        margin: 0.3rem 0 !important;
    }
    
    [data-testid="stSidebar"] .stButton {
        margin-bottom: 0.15rem !important;
    }
    
    [data-testid="stSidebar"] .stSuccess {
        margin-bottom: 0.15rem !important;
        padding: 0.3rem !important;
    }
    
    [data-testid="stSidebar"] .stCaption {
        margin-bottom: 0.15rem !important;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        margin-top: 0.3rem !important;
        margin-bottom: 0.15rem !important;
        font-size: 1rem !important;
    }
    
    [data-testid="stSidebar"] .stRadio > div {
        margin-top: 0.15rem !important;
    }
    
    [data-testid="stSidebar"] .stRadio label {
        margin-bottom: 0.1rem !important;
        padding: 0.1rem 0 !important;
        font-size: 0.9rem !important;
    }
    
    [data-testid="stSidebar"] .stFileUploader {
        margin-bottom: 0.3rem !important;
    }
    
    [data-testid="stSidebar"] .stHeader {
        margin-bottom: 0.2rem !important;
    }
    
    /* 主界面紧凑布局 */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    
    .main h1 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
        font-size: 1.8rem !important;
    }
    
    .main h2 {
        margin-top: 0.4rem !important;
        margin-bottom: 0.4rem !important;
        font-size: 1.4rem !important;
    }
    
    .main h3 {
        margin-top: 0.3rem !important;
        margin-bottom: 0.3rem !important;
        font-size: 1.1rem !important;
    }
    
    .main .stMarkdown {
        margin-bottom: 0.3rem !important;
    }
    
    .main hr {
        margin: 0.4rem 0 !important;
    }
    
    .main .stMetric {
        margin-bottom: 0.3rem !important;
    }
    
    .main .stMetric label {
        font-size: 0.85rem !important;
    }
    
    .main .stMetric [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    
    .main .stDataFrame {
        margin-bottom: 0.3rem !important;
    }
    
    .main .stExpander {
        margin-bottom: 0.3rem !important;
    }
    
    .main .stColumns {
        gap: 0.5rem !important;
    }
    
    .main .stTabs {
        margin-bottom: 0.3rem !important;
    }
    
    .main .element-container {
        margin-bottom: 0.3rem !important;
    }
    
    .main .stAlert {
        margin-bottom: 0.3rem !important;
        padding: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

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
        ['🤖 AI综合分析报告', '📄 专业报告', '🔍 三截面扭曲数据', '🗺️ 齿面拓普图', '📊 周节详细报表', '📈 单齿分析', '📉 合并曲线', '📊 频谱分析'],
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
        
        # 计算总页数（齿形和齿向使用相同的页数）
        profile_max_teeth = max(len(profile_teeth_left), len(profile_teeth_right))
        helix_max_teeth = max(len(helix_teeth_left), len(helix_teeth_right))
        max_teeth = max(profile_max_teeth, helix_max_teeth)
        total_pages = max(1, (max_teeth + TEETH_PER_PAGE - 1) // TEETH_PER_PAGE)
        
        # ========== 统一分页控制 ==========
        current_page = st.session_state.pagination.get('current_page', 1)
        
        col_prev, col_info, col_next = st.columns([1, 3, 1])
        with col_prev:
            if st.button("⬅️ 上一页", key="page_prev") and current_page > 1:
                st.session_state.pagination['current_page'] = current_page - 1
                st.rerun()
        with col_info:
            st.markdown(f"**第 {current_page} / {total_pages} 页**")
        with col_next:
            if st.button("➡️ 下一页", key="page_next") and current_page < total_pages:
                st.session_state.pagination['current_page'] = current_page + 1
                st.rerun()
        
        # 计算当前页的齿号范围
        start_idx = (current_page - 1) * TEETH_PER_PAGE
        end_idx = start_idx + TEETH_PER_PAGE
        
        current_profile_left = profile_teeth_left[start_idx:end_idx]
        current_profile_right = profile_teeth_right[start_idx:end_idx]
        current_helix_left = helix_teeth_left[start_idx:end_idx]
        current_helix_right = helix_teeth_right[start_idx:end_idx]
        
        # ========== Profile 齿形分析 ==========
        st.markdown("### Profile 齿形分析")
        
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

        # ========== 综合AI分析 ==========
        st.markdown("---")
        st.markdown("## 🤖 综合AI分析报告")
        
        # 计算频谱分析结果
        with st.spinner("正在计算频谱分析..."):
            results = {
                'profile_left': analyzer.analyze_profile('left', verbose=False),
                'profile_right': analyzer.analyze_profile('right', verbose=False),
                'helix_left': analyzer.analyze_helix('left', verbose=False),
                'helix_right': analyzer.analyze_helix('right', verbose=False)
            }
        
        name_mapping = {
            'profile_left': 'Left Profile',
            'profile_right': 'Right Profile',
            'helix_left': 'Left Lead',
            'helix_right': 'Right Lead'
        }
        
        # 收集所有分析数据
        def generate_comprehensive_analysis():
            """生成综合分析报告"""
            report = {
                'overall_score': 0,
                'status': '正常',
                'status_color': 'green',
                'profile_analysis': {},
                'helix_analysis': {},
                'pitch_analysis': {},
                'spectrum_analysis': {},
                'issues': [],
                'causes': [],
                'recommendations': [],
                'noise_prediction': '低',
                'quality_grade': 'Q6'
            }
            
            scores = []
            
            # 1. 齿形偏差分析
            profile_score = 100
            profile_issues = []
            if profile_eval:
                # 获取齿形偏差数据
                for side in ['left', 'right']:
                    side_data = profile_data.get(side, {})
                    if side_data:
                        deviations = []
                        for tooth_id, tooth_profiles in side_data.items():
                            helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                            best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                            values = np.array(tooth_profiles[best_z])
                            F_a, fH_a, ff_a, Ca = calc_profile_deviations(values)
                            if F_a is not None:
                                deviations.append({'Fα': F_a, 'fHα': fH_a, 'ffα': ff_a})
                        
                        if deviations:
                            avg_Fa = np.mean([d['Fα'] for d in deviations])
                            avg_fHa = np.mean([d['fHα'] for d in deviations])
                            avg_ffa = np.mean([d['ffα'] for d in deviations])
                            
                            report['profile_analysis'][side] = {
                                'avg_Fα': avg_Fa,
                                'avg_fHα': avg_fHa,
                                'avg_ffα': avg_ffa
                            }
                            
                            # 评分
                            if avg_Fa > 15:
                                profile_score -= 20
                                profile_issues.append(f"{'左' if side == 'left' else '右'}齿面齿形总偏差Fα过大({avg_Fa:.2f}μm)")
                            elif avg_Fa > 10:
                                profile_score -= 10
                                profile_issues.append(f"{'左' if side == 'left' else '右'}齿面齿形总偏差Fα偏大({avg_Fa:.2f}μm)")
                            
                            if avg_fHa > 8:
                                profile_score -= 10
                                profile_issues.append(f"{'左' if side == 'left' else '右'}齿面齿形倾斜偏差fHα过大")
            
            scores.append(profile_score)
            report['profile_analysis']['score'] = profile_score
            report['profile_analysis']['issues'] = profile_issues
            
            # 2. 齿向偏差分析
            helix_score = 100
            helix_issues = []
            if helix_eval:
                for side in ['left', 'right']:
                    side_data = helix_data.get(side, {})
                    if side_data:
                        deviations = []
                        for tooth_id, tooth_helix in side_data.items():
                            profile_mid = (profile_eval.eval_start + profile_eval.eval_end) / 2
                            best_d = min(tooth_helix.keys(), key=lambda d: abs(d - profile_mid))
                            values = np.array(tooth_helix[best_d])
                            F_b, fH_b, ff_b, Cb = calc_lead_deviations(values)
                            if F_b is not None:
                                deviations.append({'Fβ': F_b, 'fHβ': fH_b, 'ffβ': ff_b})
                        
                        if deviations:
                            avg_Fb = np.mean([d['Fβ'] for d in deviations])
                            avg_fHb = np.mean([d['fHβ'] for d in deviations])
                            avg_ffb = np.mean([d['ffβ'] for d in deviations])
                            
                            report['helix_analysis'][side] = {
                                'avg_Fβ': avg_Fb,
                                'avg_fHβ': avg_fHb,
                                'avg_ffβ': avg_ffb
                            }
                            
                            if avg_Fb > 15:
                                helix_score -= 20
                                helix_issues.append(f"{'左' if side == 'left' else '右'}齿面齿向总偏差Fβ过大({avg_Fb:.2f}μm)")
                            elif avg_Fb > 10:
                                helix_score -= 10
                                helix_issues.append(f"{'左' if side == 'left' else '右'}齿面齿向总偏差Fβ偏大({avg_Fb:.2f}μm)")
            
            scores.append(helix_score)
            report['helix_analysis']['score'] = helix_score
            report['helix_analysis']['issues'] = helix_issues
            
            # 3. 周节偏差分析
            pitch_score = 100
            pitch_issues = []
            if pitch_left:
                if pitch_left.fp_max > 10:
                    pitch_score -= 15
                    pitch_issues.append(f"左齿面单个齿距偏差fp过大({pitch_left.fp_max:.2f}μm)")
                if pitch_left.Fp_max > 30:
                    pitch_score -= 15
                    pitch_issues.append(f"左齿面齿距累积偏差Fp过大({pitch_left.Fp_max:.2f}μm)")
                if pitch_left.Fr > 20:
                    pitch_score -= 10
                    pitch_issues.append(f"左齿面径向跳动Fr过大({pitch_left.Fr:.2f}μm)")
                
                report['pitch_analysis']['left'] = {
                    'fp_max': pitch_left.fp_max,
                    'Fp_max': pitch_left.Fp_max,
                    'Fr': pitch_left.Fr
                }
            
            if pitch_right:
                if pitch_right.fp_max > 10:
                    pitch_score -= 15
                    pitch_issues.append(f"右齿面单个齿距偏差fp过大({pitch_right.fp_max:.2f}μm)")
                if pitch_right.Fp_max > 30:
                    pitch_score -= 15
                    pitch_issues.append(f"右齿面齿距累积偏差Fp过大({pitch_right.Fp_max:.2f}μm)")
                if pitch_right.Fr > 20:
                    pitch_score -= 10
                    pitch_issues.append(f"右齿面径向跳动Fr过大({pitch_right.Fr:.2f}μm)")
                
                report['pitch_analysis']['right'] = {
                    'fp_max': pitch_right.fp_max,
                    'Fp_max': pitch_right.Fp_max,
                    'Fr': pitch_right.Fr
                }
            
            scores.append(pitch_score)
            report['pitch_analysis']['score'] = pitch_score
            report['pitch_analysis']['issues'] = pitch_issues
            
            # 4. 频谱分析（简化版）
            spectrum_score = 100
            spectrum_issues = []
            ze = gear_params.teeth_count if gear_params else 87
            
            for name in ['profile_left', 'profile_right', 'helix_left', 'helix_right']:
                if name in results and results[name]:
                    result = results[name]
                    sorted_components = sorted(result.spectrum_components[:10], key=lambda c: c.order)
                    
                    # 检查主导阶次
                    for comp in sorted_components:
                        if abs(comp.order - ze) < 1:
                            if comp.amplitude > 0.1:
                                spectrum_score -= 10
                                spectrum_issues.append(f"{name_mapping.get(name, name)}主导阶次ZE幅值过高({comp.amplitude:.4f}μm)")
                            break
            
            scores.append(spectrum_score)
            report['spectrum_analysis']['score'] = spectrum_score
            report['spectrum_analysis']['issues'] = spectrum_issues
            
            # 计算综合评分
            overall_score = np.mean(scores) if scores else 100
            report['overall_score'] = overall_score
            
            # 确定状态
            if overall_score >= 90:
                report['status'] = '优秀'
                report['status_color'] = 'green'
                report['noise_prediction'] = '很低'
                report['quality_grade'] = 'Q5'
            elif overall_score >= 80:
                report['status'] = '良好'
                report['status_color'] = 'lightgreen'
                report['noise_prediction'] = '低'
                report['quality_grade'] = 'Q6'
            elif overall_score >= 70:
                report['status'] = '合格'
                report['status_color'] = 'yellow'
                report['noise_prediction'] = '中等'
                report['quality_grade'] = 'Q7'
            elif overall_score >= 60:
                report['status'] = '需关注'
                report['status_color'] = 'orange'
                report['noise_prediction'] = '高'
                report['quality_grade'] = 'Q8'
            else:
                report['status'] = '不合格'
                report['status_color'] = 'red'
                report['noise_prediction'] = '很高'
                report['quality_grade'] = 'Q9+'
            
            # 汇总问题
            all_issues = profile_issues + helix_issues + pitch_issues + spectrum_issues
            report['issues'] = all_issues
            
            # 生成原因分析
            if any('Fα' in issue for issue in all_issues):
                report['causes'].append("齿形误差可能由刀具磨损、机床分度误差或加工参数不当引起")
            if any('Fβ' in issue for issue in all_issues):
                report['causes'].append("齿向误差可能由机床导轨误差、工件装夹变形或热变形引起")
            if any('fp' in issue for issue in all_issues):
                report['causes'].append("齿距误差可能由分度机构误差、刀具误差或工件偏心引起")
            if any('Fr' in issue for issue in all_issues):
                report['causes'].append("径向跳动可能由工件安装偏心、轴承间隙或主轴跳动引起")
            if any('ZE' in issue for issue in all_issues):
                report['causes'].append("主导阶次幅值高可能由分度误差、刀具误差或齿轮偏心引起")
            
            if not report['causes']:
                report['causes'].append("齿轮各项指标正常，加工质量良好")
            
            # 生成改进建议
            if overall_score < 80:
                report['recommendations'].append("建议全面检查加工机床精度和刀具状态")
            if any('Fα' in issue for issue in all_issues):
                report['recommendations'].append("优化齿形加工：检查刀具磨损，调整加工参数")
            if any('Fβ' in issue for issue in all_issues):
                report['recommendations'].append("优化齿向加工：检查机床导轨，改善装夹方式")
            if any('fp' in issue or 'Fp' in issue for issue in all_issues):
                report['recommendations'].append("优化齿距精度：检查分度机构，校准刀具")
            if any('Fr' in issue for issue in all_issues):
                report['recommendations'].append("降低径向跳动：改善工件装夹，检查主轴精度")
            
            if not report['recommendations']:
                report['recommendations'].append("继续保持当前加工工艺，定期监测质量")
            
            return report
        
        # 生成报告
        comprehensive_report = generate_comprehensive_analysis()
        
        # 显示综合评分
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("综合评分", f"{comprehensive_report['overall_score']:.0f}分")
        with col2:
            status_color = comprehensive_report['status_color']
            st.markdown(f"**状态: <span style='color:{status_color};font-size:20px;font-weight:bold;'>{comprehensive_report['status']}</span>**", unsafe_allow_html=True)
        with col3:
            st.metric("质量等级", comprehensive_report['quality_grade'])
        with col4:
            noise_color = 'green' if comprehensive_report['noise_prediction'] in ['很低', '低'] else 'orange' if comprehensive_report['noise_prediction'] == '中等' else 'red'
            st.markdown(f"**噪声预测: <span style='color:{noise_color};'>{comprehensive_report['noise_prediction']}</span>**", unsafe_allow_html=True)
        
        # 分项评分
        st.markdown("### 📊 分项评分")
        score_cols = st.columns(4)
        with score_cols[0]:
            profile_score = comprehensive_report['profile_analysis'].get('score', 100)
            st.metric("齿形偏差", f"{profile_score:.0f}分")
            st.progress(profile_score / 100)
        with score_cols[1]:
            helix_score = comprehensive_report['helix_analysis'].get('score', 100)
            st.metric("齿向偏差", f"{helix_score:.0f}分")
            st.progress(helix_score / 100)
        with score_cols[2]:
            pitch_score = comprehensive_report['pitch_analysis'].get('score', 100)
            st.metric("周节偏差", f"{pitch_score:.0f}分")
            st.progress(pitch_score / 100)
        with score_cols[3]:
            spectrum_score = comprehensive_report['spectrum_analysis'].get('score', 100)
            st.metric("频谱分析", f"{spectrum_score:.0f}分")
            st.progress(spectrum_score / 100)
        
        # 问题汇总
        st.markdown("### 📋 问题汇总")
        if comprehensive_report['issues']:
            for issue in comprehensive_report['issues']:
                st.markdown(f"- 🔴 {issue}")
        else:
            st.markdown("- ✅ 未发现明显问题")
        
        # 原因分析
        st.markdown("### 🔍 原因分析")
        for cause in comprehensive_report['causes']:
            st.markdown(f"- {cause}")
        
        # 改进建议
        st.markdown("### 💡 改进建议")
        for rec in comprehensive_report['recommendations']:
            st.markdown(f"- {rec}")
        
        # 详细数据
        with st.expander("📊 详细分析数据", expanded=False):
            # 齿形数据
            if comprehensive_report['profile_analysis']:
                st.markdown("**齿形偏差数据:**")
                profile_df_data = []
                for side, data in comprehensive_report['profile_analysis'].items():
                    if isinstance(data, dict) and 'avg_Fα' in data:
                        profile_df_data.append({
                            '齿面': '左齿面' if side == 'left' else '右齿面',
                            'Fα (μm)': f"{data['avg_Fα']:.2f}",
                            'fHα (μm)': f"{data['avg_fHα']:.2f}",
                            'ffα (μm)': f"{data['avg_ffα']:.2f}"
                        })
                if profile_df_data:
                    st.dataframe(pd.DataFrame(profile_df_data), use_container_width=True, hide_index=True)
            
            # 齿向数据
            if comprehensive_report['helix_analysis']:
                st.markdown("**齿向偏差数据:**")
                helix_df_data = []
                for side, data in comprehensive_report['helix_analysis'].items():
                    if isinstance(data, dict) and 'avg_Fβ' in data:
                        helix_df_data.append({
                            '齿面': '左齿面' if side == 'left' else '右齿面',
                            'Fβ (μm)': f"{data['avg_Fβ']:.2f}",
                            'fHβ (μm)': f"{data['avg_fHβ']:.2f}",
                            'ffβ (μm)': f"{data['avg_ffβ']:.2f}"
                        })
                if helix_df_data:
                    st.dataframe(pd.DataFrame(helix_df_data), use_container_width=True, hide_index=True)
            
            # 周节数据
            if comprehensive_report['pitch_analysis']:
                st.markdown("**周节偏差数据:**")
                pitch_df_data = []
                for side, data in comprehensive_report['pitch_analysis'].items():
                    if isinstance(data, dict) and 'fp_max' in data:
                        pitch_df_data.append({
                            '齿面': '左齿面' if side == 'left' else '右齿面',
                            'fp max (μm)': f"{data['fp_max']:.2f}",
                            'Fp max (μm)': f"{data['Fp_max']:.2f}",
                            'Fr (μm)': f"{data['Fr']:.2f}"
                        })
                if pitch_df_data:
                    st.dataframe(pd.DataFrame(pitch_df_data), use_container_width=True, hide_index=True)

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
                        
                        # 计算极限曲线
                        def calculate_tolerance_curve_single(orders, R, N0, K):
                            tolerances = []
                            for O in orders:
                                if O <= 1:
                                    tolerances.append(R)
                                else:
                                    N = N0 + K / O
                                    tolerance = R / ((O - 1) ** N)
                                    tolerances.append(tolerance)
                            return tolerances

                        # 根据实际数据自动计算极限曲线参数
                        orders_spec = [c.order for c in spectrum_components[:15]]
                        amplitudes_spec = [c.amplitude for c in spectrum_components[:15]]
                        
                        if amplitudes_spec and orders_spec:
                            N0_auto = 0.6
                            K_auto = 2.8
                            
                            # 找到ZE处的幅值
                            ze_amplitude = None
                            for o, amp in zip(orders_spec, amplitudes_spec):
                                if abs(o - ze) < 1:
                                    if ze_amplitude is None or amp > ze_amplitude:
                                        ze_amplitude = amp
                            
                            if ze_amplitude is not None:
                                N_at_ze = N0_auto + K_auto / ze
                                R_auto = ze_amplitude * 1.5 * ((ze - 1) ** N_at_ze)
                            else:
                                max_amp = max(amplitudes_spec)
                                R_auto = max_amp * 2.0 * ((ze - 1) ** (N0_auto + K_auto / ze))
                            
                            R_auto = max(0.0001, min(R_auto, 10.0))
                        else:
                            R_auto = 0.0039
                            N0_auto = 0.6
                            K_auto = 2.8
                        
                        # 显示极限曲线参数并可调节
                        st.markdown("**Limit Curve Parameters**")
                        st.markdown("*Formula: Tolerance = R / (O-1)^(N₀+K/O)*")
                        col_p1, col_p2, col_p3 = st.columns(3)
                        with col_p1:
                            R_input = st.number_input("R (mm)", min_value=0.0001, max_value=10.0, value=float(R_auto), step=0.0001, format="%.4f", key=f"R_single_{side}")
                        with col_p2:
                            N0_input = st.number_input("N₀", min_value=0.0, max_value=5.0, value=float(N0_auto), step=0.1, format="%.1f", key=f"N0_single_{side}")
                        with col_p3:
                            K_input = st.number_input("K", min_value=0.0, max_value=10.0, value=float(K_auto), step=0.1, format="%.1f", key=f"K_single_{side}")
                        
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
                            
                            # 计算每个阶次的极限值
                            tolerance_values = calculate_tolerance_curve_single(orders, R_input, N0_input, K_input)
                            
                            # 根据是否超出极限设置颜色
                            colors = ['red' if amp > tol else 'steelblue' for amp, tol in zip(amplitudes, tolerance_values)]
                            ax2.bar(orders, amplitudes, color=colors, alpha=0.7, width=3, label='Amplitude')
                            
                            # 标记ZE及其倍数
                            ze_multiples = [ze * i for i in range(1, 5) if ze * i <= max(orders)]
                            for i, ze_mult in enumerate(ze_multiples, 1):
                                if i == 1:
                                    ax2.axvline(x=ze_mult, color='green', linestyle='--', linewidth=2, label=f'ZE={ze}')
                                else:
                                    ax2.axvline(x=ze_mult, color='orange', linestyle=':', linewidth=1.5, alpha=0.7)
                            
                            # 绘制极限曲线（橘黄色）
                            order_range = np.linspace(2, max(orders) + 10, 200)
                            tolerance_curve = calculate_tolerance_curve_single(order_range, R_input, N0_input, K_input)
                            ax2.plot(order_range, tolerance_curve, color='darkorange', linewidth=2.5, label='Tolerance Limit', linestyle='-')
                            
                            # 设置Y轴范围
                            max_amplitude = max(amplitudes) if amplitudes else 1
                            max_tolerance = max(tolerance_curve) if len(tolerance_curve) > 0 else 1
                            y_max = max(max_amplitude, max_tolerance) * 1.2
                            ax2.set_ylim(0, y_max)
                            
                            ax2.set_title(f'Single Tooth Expanded Spectrum (ZE={ze})', fontsize=10, fontweight='bold')
                            ax2.set_xlabel('Order')
                            ax2.set_ylabel('Amplitude (μm) / Tolerance (mm)')
                            ax2.legend(loc='upper right')
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

        # ========== PDF报表生成按钮 ==========
        st.markdown("### 📄 生成频谱分析报表")
        
        if st.button("📥 生成频谱分析PDF报表", type="primary"):
            with st.spinner("正在生成PDF报表..."):
                try:
                    from reportlab.lib.pagesizes import A4
                    from reportlab.lib import colors
                    from reportlab.lib.units import mm
                    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
                    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                    from reportlab.pdfbase import pdfmetrics
                    from reportlab.pdfbase.ttfonts import TTFont
                    import io
                    import os
                    
                    # 计算极限曲线函数
                    def calc_tolerance(orders, R, N0, K):
                        tolerances = []
                        for O in orders:
                            if O <= 1:
                                tolerances.append(R)
                            else:
                                N = N0 + K / O
                                tolerance = R / ((O - 1) ** N)
                                tolerances.append(tolerance)
                        return tolerances
                    
                    # 创建PDF
                    pdf_buffer = io.BytesIO()
                    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, 
                                           leftMargin=15*mm, rightMargin=15*mm,
                                           topMargin=15*mm, bottomMargin=15*mm)
                    
                    elements = []
                    styles = getSampleStyleSheet()
                    
                    # 使用英文字体（避免中文显示问题）
                    title_style = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=16, alignment=1, spaceAfter=10)
                    heading_style = ParagraphStyle('Heading', fontName='Helvetica-Bold', fontSize=12, spaceAfter=6)
                    normal_style = ParagraphStyle('Normal', fontName='Helvetica', fontSize=10)
                    
                    # 标题
                    elements.append(Paragraph("Spectrum Analysis Report", title_style))
                    elements.append(Spacer(1, 5*mm))
                    
                    # 为每个分析结果生成报表
                    for name, result in results.items():
                        if result is None or len(result.angles) == 0:
                            continue
                        
                        display_name = name_mapping.get(name, name)
                        
                        # 获取界面实际参数
                        R_key = f"R_{name}"
                        N0_key = f"N0_{name}"
                        K_key = f"K_{name}"
                        
                        # 从session_state获取参数，如果没有则使用默认值
                        if R_key in st.session_state:
                            current_R = st.session_state[R_key]
                        else:
                            current_R = 0.0039
                        
                        if N0_key in st.session_state:
                            current_N0 = st.session_state[N0_key]
                        else:
                            current_N0 = 0.6
                        
                        if K_key in st.session_state:
                            current_K = st.session_state[K_key]
                        else:
                            current_K = 2.8
                        
                        # 小标题
                        elements.append(Paragraph(f"<b>{display_name}</b>", heading_style))
                        
                        # 极限曲线参数（英文）
                        param_text = f"Limit Curve: R = {current_R:.4f} mm, N0 = {current_N0:.1f}, K = {current_K:.1f}"
                        elements.append(Paragraph(param_text, normal_style))
                        elements.append(Paragraph("Formula: Tolerance = R / (O-1)^(N0+K/O)", normal_style))
                        elements.append(Spacer(1, 3*mm))
                        
                        # 生成频谱图
                        sorted_components = sorted(result.spectrum_components[:20], key=lambda c: c.order)
                        orders = [c.order for c in sorted_components]
                        amplitudes = [c.amplitude for c in sorted_components]
                        
                        if orders and amplitudes:
                            # 创建图表
                            fig, ax = plt.subplots(figsize=(7, 3.5))
                            
                            tolerance_values = calc_tolerance(orders, current_R, current_N0, current_K)
                            colors_bar = ['red' if amp > tol else 'steelblue' for amp, tol in zip(amplitudes, tolerance_values)]
                            ax.bar(orders, amplitudes, color=colors_bar, alpha=0.7, width=3, label='Amplitude')
                            
                            ze_multiples = [ze * i for i in range(1, 5) if ze * i <= max(orders) + 20]
                            for i, ze_mult in enumerate(ze_multiples, 1):
                                if i == 1:
                                    ax.axvline(x=ze_mult, color='green', linestyle='--', linewidth=2, label=f'ZE={ze}')
                                else:
                                    ax.axvline(x=ze_mult, color='orange', linestyle=':', linewidth=1.5, alpha=0.7)
                            
                            order_range = np.linspace(2, max(orders) + 20, 200)
                            tolerance_curve = calc_tolerance(order_range, current_R, current_N0, current_K)
                            ax.plot(order_range, tolerance_curve, color='darkorange', linewidth=2.5, label='Tolerance Limit')
                            
                            max_amplitude = max(amplitudes) if amplitudes else 1
                            max_tolerance = max(tolerance_curve) if len(tolerance_curve) > 0 else 1
                            y_max = max(max_amplitude, max_tolerance) * 1.2
                            ax.set_ylim(0, y_max)
                            ax.set_xlim(0, max(orders) + 20)
                            
                            ax.set_xlabel('Order')
                            ax.set_ylabel('Amplitude (μm) / Tolerance (mm)')
                            ax.set_title(f'{display_name} - Spectrum (ZE={ze})')
                            ax.legend(loc='upper right', fontsize=8)
                            ax.grid(True, alpha=0.3)
                            plt.tight_layout()
                            
                            # 保存图表到内存
                            img_buffer = io.BytesIO()
                            fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                            img_buffer.seek(0)
                            plt.close(fig)
                            
                            # 添加图表到PDF
                            img = Image(img_buffer, width=170*mm, height=85*mm)
                            elements.append(img)
                            elements.append(Spacer(1, 3*mm))
                        
                        # 数据表（英文）
                        table_data = [['Rank', 'Order', 'Amplitude (μm)', 'Phase (°)', 'Type', 'Status']]
                        for i, comp in enumerate(result.spectrum_components[:10]):
                            order_type = 'High' if comp.order >= ze else 'Low'
                            # 计算状态
                            tol = calc_tolerance([comp.order], current_R, current_N0, current_K)[0]
                            status = 'FAIL' if comp.amplitude > tol else 'PASS'
                            table_data.append([
                                str(i + 1),
                                str(int(comp.order)),
                                f"{comp.amplitude:.4f}",
                                f"{np.degrees(comp.phase):.1f}",
                                order_type,
                                status
                            ])
                        
                        table = Table(table_data, colWidths=[20*mm, 25*mm, 35*mm, 30*mm, 20*mm, 25*mm])
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                            ('FONTSIZE', (0, 0), (-1, 0), 9),
                            ('FONTSIZE', (0, 1), (-1, -1), 8),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                        ]))
                        elements.append(table)
                        elements.append(Spacer(1, 5*mm))
                        
                        # 每个分析结果后添加分页（除了最后一个）
                        if name != list(results.keys())[-1]:
                            elements.append(PageBreak())
                    
                    # 生成PDF
                    doc.build(elements)
                    pdf_buffer.seek(0)
                    
                    st.success("✅ PDF Report Generated Successfully!")
                    st.download_button(
                        label="📥 Download Spectrum Analysis PDF Report",
                        data=pdf_buffer,
                        file_name=f"spectrum_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                    
                except Exception as e:
                    st.error(f"PDF Generation Failed: {e}")
                    import traceback
                    st.error(traceback.format_exc())
        
        st.markdown("---")

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

                # 显示公差曲线定义和原理
                with st.expander("📖 公差曲线定义与原理", expanded=False):
                    st.markdown("""
                    **公差曲线（Tolerance Limit Curve）**
                    
                    公差曲线以极限曲线的形式描述连续的公差范围，通过三个参数确定：
                    
                    - **R**：允许波深（参考幅值，单位：mm）
                    - **N₀**：用于描述公差曲线的常数（基础指数）
                    - **K**：修正值
                    
                    **计算公式：**
                    
                    ```
                    公差 = R / (O - 1)^N
                    
                    其中：N = N₀ + K / O
                    
                    O = 阶次（Order）
                    ```
                    
                    **物理意义：**
                    - 低阶次（O较小）：公差较大，允许较大的波纹度
                    - 高阶次（O较大）：公差较小，要求更严格的波纹度控制
                    - 随着阶次增加，允许的波纹度幅值呈指数衰减
                    
                    **应用：**
                    - 蓝色柱：幅值在公差范围内（合格）
                    - 红色柱：幅值超出公差范围（不合格，需关注）
                    - 橘黄线：公差极限曲线
                    """)

                # 计算极限曲线
                def calculate_tolerance_curve(orders, R, N0, K):
                    """计算极限曲线公差值"""
                    tolerances = []
                    for O in orders:
                        if O <= 1:
                            tolerances.append(R)
                        else:
                            N = N0 + K / O
                            tolerance = R / ((O - 1) ** N)
                            tolerances.append(tolerance)
                    return tolerances

                fig, ax = plt.subplots(figsize=(12, 5))
                sorted_components = sorted(result.spectrum_components[:20], key=lambda c: c.order)
                orders = [c.order for c in sorted_components]
                amplitudes = [c.amplitude for c in sorted_components]

                # 根据实际数据自动计算极限曲线参数
                # 目标：公差曲线在ZE处高于主导阶次的幅值
                if amplitudes and orders:
                    N0_auto = 0.6
                    K_auto = 2.8
                    
                    # 找到ZE处的幅值或最接近ZE的幅值
                    # 首先尝试找到精确匹配ZE的阶次
                    ze_amplitude = None
                    for o, amp in zip(orders, amplitudes):
                        if abs(o - ze) < 1:  # ZE ± 1范围内
                            if ze_amplitude is None or amp > ze_amplitude:
                                ze_amplitude = amp
                    
                    if ze_amplitude is not None:
                        # 计算R，使得在ZE处的公差为ZE处幅值的1.5倍
                        # tolerance = R / ((ZE-1)^N), 其中 N = N0 + K/ZE
                        N_at_ze = N0_auto + K_auto / ze
                        R_auto = ze_amplitude * 1.5 * ((ze - 1) ** N_at_ze)
                    else:
                        # 如果没有ZE附近的数据，使用全局最大幅值，并乘以更大系数
                        max_amp = max(amplitudes)
                        R_auto = max_amp * 2.0 * ((ze - 1) ** (N0_auto + K_auto / ze))
                    
                    # 放宽R的上限限制
                    R_auto = max(0.0001, min(R_auto, 10.0))
                else:
                    R_auto = 0.0039
                    N0_auto = 0.6
                    K_auto = 2.8

                # 显示极限曲线参数并可调节
                st.markdown("**Limit Curve Parameters**")
                st.markdown("*Formula: Tolerance = R / (O-1)^(N₀+K/O)*")
                col1, col2, col3 = st.columns(3)
                with col1:
                    R_input = st.number_input("R (mm)", min_value=0.0001, max_value=10.0, value=float(R_auto), step=0.0001, format="%.4f", key=f"R_{name}")
                with col2:
                    N0_input = st.number_input("N₀", min_value=0.0, max_value=5.0, value=float(N0_auto), step=0.1, format="%.1f", key=f"N0_{name}")
                with col3:
                    K_input = st.number_input("K", min_value=0.0, max_value=10.0, value=float(K_auto), step=0.1, format="%.1f", key=f"K_{name}")

                # 使用用户输入的参数
                R = R_input
                N0 = N0_input
                K = K_input

                if orders and amplitudes:
                    # 计算每个阶次的极限值
                    tolerance_values = calculate_tolerance_curve(orders, R, N0, K)
                    
                    # 根据是否超出极限设置颜色：蓝色（未超出），红色（超出）
                    colors_bar = ['red' if amp > tol else 'steelblue' for amp, tol in zip(amplitudes, tolerance_values)]
                    ax.bar(orders, amplitudes, color=colors_bar, alpha=0.7, width=3, label='Amplitude')

                    # 标识 ZE 及其倍数
                    ze_multiples = [ze * i for i in range(1, 5) if ze * i <= max(orders) + 20]
                    for i, ze_mult in enumerate(ze_multiples, 1):
                        if i == 1:
                            ax.axvline(x=ze_mult, color='green', linestyle='--', linewidth=2, label=f'ZE={ze}')
                        else:
                            ax.axvline(x=ze_mult, color='orange', linestyle=':', linewidth=1.5, alpha=0.7, label=f'{i}×ZE={ze_mult}')

                    # 绘制极限曲线（橘黄色）
                    order_range = np.linspace(2, max(orders) + 20, 200)
                    tolerance_curve = calculate_tolerance_curve(order_range, R, N0, K)
                    ax.plot(order_range, tolerance_curve, color='darkorange', linewidth=2.5, label='Tolerance Limit', linestyle='-')

                    # 设置Y轴范围
                    max_amplitude = max(amplitudes) if amplitudes else 1
                    max_tolerance = max(tolerance_curve) if tolerance_curve else 1
                    y_max = max(max_amplitude, max_tolerance) * 1.2
                    ax.set_ylim(0, y_max)
                    ax.set_xlim(0, max(orders) + 20)

                ax.set_xlabel('Order')
                ax.set_ylabel('Amplitude (μm) / Tolerance (mm)')
                ax.set_title(f'{display_name} - Spectrum (ZE={ze})')
                ax.legend(loc='upper right')
                ax.grid(True, alpha=0.3)

                st.pyplot(fig)
                plt.close(fig)
                
                # ========== AI智能分析 ==========
                st.markdown("---")
                st.markdown("#### 🤖 AI智能分析")
                
                # 分析频谱数据
                def analyze_spectrum_ai(components, ze, tolerance_func, R, N0, K, display_name):
                    """AI分析频谱数据，返回状态、原因和建议"""
                    
                    # 统计信息
                    high_order_components = [c for c in components if c.order >= ze]
                    low_order_components = [c for c in components if c.order < ze]
                    
                    # 计算超出公差的数量
                    out_of_tolerance = []
                    out_of_tolerance_details = []
                    for comp in components[:20]:
                        tol = tolerance_func([comp.order], R, N0, K)[0]
                        if comp.amplitude > tol:
                            out_of_tolerance.append(comp)
                            out_of_tolerance_details.append({
                                'order': comp.order,
                                'amplitude': comp.amplitude,
                                'tolerance': tol,
                                'excess': comp.amplitude - tol
                            })
                    
                    # ZE及其倍数的幅值
                    ze_multiples_amp = {}
                    for i in range(1, 6):
                        ze_mult = ze * i
                        for comp in components:
                            if abs(comp.order - ze_mult) < 1:
                                ze_multiples_amp[i] = comp.amplitude
                                break
                    
                    # 计算频谱能量分布
                    total_energy = sum(c.amplitude ** 2 for c in components[:20])
                    low_order_energy = sum(c.amplitude ** 2 for c in low_order_components[:10])
                    high_order_energy = sum(c.amplitude ** 2 for c in high_order_components[:10])
                    ze_energy = sum((ze_multiples_amp.get(i, 0) ** 2) for i in range(1, 5))
                    
                    low_order_ratio = low_order_energy / total_energy if total_energy > 0 else 0
                    high_order_ratio = high_order_energy / total_energy if total_energy > 0 else 0
                    ze_ratio = ze_energy / total_energy if total_energy > 0 else 0
                    
                    # 分析结果
                    analysis = {
                        'status': 'normal',
                        'status_text': '正常',
                        'status_color': 'green',
                        'score': 100,
                        'issues': [],
                        'causes': [],
                        'recommendations': [],
                        'noise_prediction': '低',
                        'noise_level': 1,
                        'energy_distribution': {
                            'low_order': low_order_ratio,
                            'high_order': high_order_ratio,
                            'ze_related': ze_ratio
                        },
                        'out_of_tolerance_details': out_of_tolerance_details
                    }
                    
                    # 计算综合评分
                    score = 100
                    score -= len(out_of_tolerance) * 5  # 每个超差扣5分
                    score -= int(ze_multiples_amp.get(1, 0) * 100)  # ZE幅值扣分
                    score -= int(ze_multiples_amp.get(2, 0) * 50)  # 2ZE幅值扣分
                    score -= len([c for c in high_order_components[:10] if c.amplitude > 0.03]) * 3  # 高阶次扣分
                    score = max(0, min(100, score))
                    analysis['score'] = score
                    
                    # 判断状态
                    if score < 50:
                        analysis['status'] = 'critical'
                        analysis['status_text'] = '严重异常'
                        analysis['status_color'] = 'red'
                        analysis['noise_prediction'] = '很高'
                        analysis['noise_level'] = 5
                    elif score < 70:
                        analysis['status'] = 'warning'
                        analysis['status_text'] = '警告'
                        analysis['status_color'] = 'orange'
                        analysis['noise_prediction'] = '高'
                        analysis['noise_level'] = 4
                    elif score < 85:
                        analysis['status'] = 'attention'
                        analysis['status_text'] = '需关注'
                        analysis['status_color'] = 'yellow'
                        analysis['noise_prediction'] = '中等'
                        analysis['noise_level'] = 3
                    elif score < 95:
                        analysis['status'] = 'good'
                        analysis['status_text'] = '良好'
                        analysis['status_color'] = 'lightgreen'
                        analysis['noise_prediction'] = '低'
                        analysis['noise_level'] = 2
                    else:
                        analysis['status'] = 'excellent'
                        analysis['status_text'] = '优秀'
                        analysis['status_color'] = 'green'
                        analysis['noise_prediction'] = '很低'
                        analysis['noise_level'] = 1
                    
                    # 根据分析类型调整阈值
                    is_profile = 'Profile' in display_name
                    is_helix = 'Lead' in display_name
                    
                    # 分析问题 - 主导阶次ZE
                    ze_amp = ze_multiples_amp.get(1, 0)
                    if ze_amp > 0.15:
                        analysis['issues'].append(f"🔴 主导阶次ZE={ze}幅值严重偏高({ze_amp:.4f}μm)")
                        analysis['causes'].append("齿轮加工分度误差严重，或刀具磨损严重")
                        analysis['recommendations'].append("立即检查机床分度精度，更换或重磨刀具")
                    elif ze_amp > 0.08:
                        analysis['issues'].append(f"🟠 主导阶次ZE={ze}幅值较高({ze_amp:.4f}μm)")
                        analysis['causes'].append("齿轮加工时存在分度误差或刀具误差")
                        analysis['recommendations'].append("检查齿轮加工机床的分度精度，检查刀具磨损情况")
                    elif ze_amp > 0.03:
                        analysis['issues'].append(f"🟡 主导阶次ZE={ze}幅值略高({ze_amp:.4f}μm)")
                        analysis['causes'].append("轻微的分度误差或刀具磨损")
                        analysis['recommendations'].append("关注机床分度状态，定期检查刀具")
                    
                    # 2倍频分析
                    ze2_amp = ze_multiples_amp.get(2, 0)
                    if ze2_amp > 0.08:
                        analysis['issues'].append(f"🔴 2倍频(2ZE={2*ze})幅值严重偏高({ze2_amp:.4f}μm)")
                        analysis['causes'].append("齿轮存在严重偏心或椭圆度误差")
                        analysis['recommendations'].append("检查齿轮安装偏心量，检查齿轮内孔精度，必要时重新加工")
                    elif ze2_amp > 0.04:
                        analysis['issues'].append(f"🟠 2倍频(2ZE={2*ze})幅值较高({ze2_amp:.4f}μm)")
                        analysis['causes'].append("齿轮可能存在偏心或椭圆度")
                        analysis['recommendations'].append("检查齿轮安装偏心量，检查齿轮内孔精度")
                    elif ze2_amp > 0.02:
                        analysis['issues'].append(f"🟡 2倍频(2ZE={2*ze})幅值略高({ze2_amp:.4f}μm)")
                        analysis['causes'].append("轻微的偏心或椭圆度")
                        analysis['recommendations'].append("关注齿轮安装精度")
                    
                    # 3倍频分析
                    ze3_amp = ze_multiples_amp.get(3, 0)
                    if ze3_amp > 0.03:
                        analysis['issues'].append(f"🟠 3倍频(3ZE={3*ze})幅值较高({ze3_amp:.4f}μm)")
                        analysis['causes'].append("齿轮存在三棱度误差")
                        analysis['recommendations'].append("检查齿轮的装夹方式，检查机床主轴精度")
                    
                    # 高阶次分析
                    high_order_large = [c for c in high_order_components[:10] if c.amplitude > 0.03]
                    if len(high_order_large) > 5:
                        analysis['issues'].append(f"🔴 高阶次({len(high_order_large)}个)幅值严重偏高")
                        analysis['causes'].append("齿面粗糙度严重超标，存在严重的微观几何误差")
                        analysis['recommendations'].append("优化磨齿或珩齿工艺，检查砂轮状态，降低齿面粗糙度")
                    elif len(high_order_large) > 3:
                        analysis['issues'].append(f"🟠 高阶次({len(high_order_large)}个)幅值较高")
                        analysis['causes'].append("齿面粗糙度较大或存在微观几何误差")
                        analysis['recommendations'].append("优化磨齿或珩齿工艺，降低齿面粗糙度")
                    elif len(high_order_large) > 1:
                        analysis['issues'].append(f"🟡 高阶次({len(high_order_large)}个)幅值略高")
                        analysis['causes'].append("齿面存在轻微粗糙度问题")
                        analysis['recommendations'].append("关注齿面加工质量")
                    
                    # 低阶次分析
                    low_order_large = [c for c in low_order_components[:5] if c.amplitude > 0.05]
                    if len(low_order_large) > 3:
                        analysis['issues'].append(f"🔴 低阶次({len(low_order_large)}个)幅值严重偏高")
                        analysis['causes'].append("齿轮存在严重的宏观几何误差（齿形误差、齿向误差）")
                        analysis['recommendations'].append("全面检查齿轮的齿形和齿向偏差，重新调整加工工艺")
                    elif len(low_order_large) > 2:
                        analysis['issues'].append(f"🟠 低阶次({len(low_order_large)}个)幅值较高")
                        analysis['causes'].append("齿轮存在宏观几何误差，如齿形误差、齿向误差")
                        analysis['recommendations'].append("检查齿轮的齿形和齿向偏差，优化加工工艺")
                    
                    # 能量分布分析
                    if ze_ratio > 0.5:
                        analysis['issues'].append(f"🔴 ZE相关阶次能量占比过高({ze_ratio*100:.1f}%)")
                        analysis['causes'].append("齿轮的主要误差集中在齿频及其倍频")
                        analysis['recommendations'].append("重点解决分度误差和刀具误差问题")
                    
                    if high_order_ratio > 0.6:
                        analysis['issues'].append(f"🟠 高阶次能量占比过高({high_order_ratio*100:.1f}%)")
                        analysis['causes'].append("齿面质量问题突出")
                        analysis['recommendations'].append("重点改善齿面粗糙度")
                    
                    # 连续多阶次异常
                    consecutive_issues = []
                    for i in range(len(components) - 2):
                        if components[i].amplitude > 0.02 and components[i+1].amplitude > 0.02 and components[i+2].amplitude > 0.02:
                            consecutive_issues.append((components[i].order, components[i+2].order))
                    
                    if len(consecutive_issues) > 3:
                        analysis['issues'].append(f"🔴 连续多阶次({len(consecutive_issues)}处)出现异常")
                        analysis['causes'].append("存在系统性的加工误差或周期性误差")
                        analysis['recommendations'].append("全面检查加工机床的周期性误差，检查工件装夹稳定性")
                    elif len(consecutive_issues) > 1:
                        analysis['issues'].append(f"🟡 连续多阶次({len(consecutive_issues)}处)出现异常")
                        analysis['causes'].append("可能存在周期性误差")
                        analysis['recommendations'].append("检查加工机床的周期性误差")
                    
                    # 齿形/齿向特定分析
                    if is_profile:
                        if analysis['score'] < 80:
                            analysis['recommendations'].append("💡 齿形误差会直接影响齿轮的啮合噪声，建议优先优化")
                    elif is_helix:
                        if analysis['score'] < 80:
                            analysis['recommendations'].append("💡 齿向误差会导致齿轮啮合不良，建议检查齿向修形参数")
                    
                    # 如果没有发现问题
                    if not analysis['issues']:
                        analysis['issues'].append("✅ 未发现明显异常")
                        analysis['causes'].append("齿轮波纹度在正常范围内")
                        analysis['recommendations'].append("继续保持当前加工工艺，定期监测")
                    
                    return analysis
                
                # 执行AI分析
                ai_analysis = analyze_spectrum_ai(
                    sorted_components, ze, calculate_tolerance_curve, R, N0, K, display_name
                )
                
                # 显示分析结果
                status_color = ai_analysis['status_color']
                status_text = ai_analysis['status_text']
                score = ai_analysis['score']
                
                # 状态和评分显示
                col_status, col_score = st.columns([2, 1])
                with col_status:
                    st.markdown(f"**齿轮状态: <span style='color:{status_color};font-size:22px;font-weight:bold;'>{status_text}</span>**", unsafe_allow_html=True)
                with col_score:
                    st.metric("综合评分", f"{score}分")
                
                # 噪声预测
                noise_level = ai_analysis['noise_level']
                noise_prediction = ai_analysis['noise_prediction']
                st.markdown(f"**🔊 噪声预测: <span style='color:{'green' if noise_level <= 2 else 'orange' if noise_level <= 3 else 'red'};'>{noise_prediction}</span>** (基于频谱分析)", unsafe_allow_html=True)
                
                # 能量分布
                energy = ai_analysis['energy_distribution']
                st.markdown("**📊 能量分布:**")
                ecol1, ecol2, ecol3 = st.columns(3)
                with ecol1:
                    st.progress(min(energy['low_order'], 1.0))
                    st.caption(f"低阶次: {energy['low_order']*100:.1f}%")
                with ecol2:
                    st.progress(min(energy['ze_related'], 1.0))
                    st.caption(f"ZE相关: {energy['ze_related']*100:.1f}%")
                with ecol3:
                    st.progress(min(energy['high_order'], 1.0))
                    st.caption(f"高阶次: {energy['high_order']*100:.1f}%")
                
                st.markdown("---")
                
                # 问题列表
                if ai_analysis['issues']:
                    st.markdown("**📋 发现问题:**")
                    for issue in ai_analysis['issues']:
                        st.markdown(f"- {issue}")
                
                # 原因分析
                if ai_analysis['causes']:
                    st.markdown("**🔍 原因分析:**")
                    for cause in ai_analysis['causes']:
                        st.markdown(f"- {cause}")
                
                # 改进建议
                if ai_analysis['recommendations']:
                    st.markdown("**💡 改进建议:**")
                    for rec in ai_analysis['recommendations']:
                        st.markdown(f"- {rec}")
                
                # 详细数据摘要
                with st.expander("📊 详细数据摘要", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("总谐波数", len(sorted_components))
                        st.metric("高阶谐波数", len([c for c in sorted_components if c.order >= ze]))
                    with col2:
                        st.metric("最大幅值", f"{max(amplitudes):.4f} μm")
                        st.metric("超差数量", len([c for c in sorted_components[:20] if c.amplitude > calculate_tolerance_curve([c.order], R, N0, K)[0]]))
                    with col3:
                        st.metric("主导阶次幅值", f"{next((c.amplitude for c in sorted_components if abs(c.order - ze) < 1), 0):.4f} μm")
                        st.metric("2倍频幅值", f"{next((c.amplitude for c in sorted_components if abs(c.order - 2*ze) < 1), 0):.4f} μm")
                    
                    # 超差详情
                    if ai_analysis['out_of_tolerance_details']:
                        st.markdown("**超差详情:**")
                        oot_df = pd.DataFrame(ai_analysis['out_of_tolerance_details'])
                        oot_df.columns = ['阶次', '幅值(μm)', '公差(μm)', '超差量(μm)']
                        st.dataframe(oot_df, use_container_width=True, hide_index=True)
    
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
    
    elif page == '🗺️ 齿面拓普图':
        st.markdown("## 🗺️ 齿面TOPOGRAFIE拓普图")
        st.markdown("### 齿面偏差热力图分析")
        
        # 解析TOPOGRAFIE数据
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
        
        def plot_topography(data_matrix, z_positions, n_points, side='rechts', title_suffix='', 
                           waviness_angle=None, contact_angle=None):
            """绘制拓普图，可选添加波纹螺旋角和接触线"""
            fig, ax = plt.subplots(figsize=(10, 8))
            
            colors = ['#0000FF', '#00FFFF', '#00FF00', '#FFFF00', '#FF0000']
            cmap = LinearSegmentedColormap.from_list('gear_topo', colors, N=256)
            
            im = ax.imshow(data_matrix, aspect='auto', cmap=cmap, origin='lower',
                           extent=[0, n_points-1, z_positions[0], z_positions[-1]])
            
            cbar = plt.colorbar(im, ax=ax, label='Deviation (µm)')
            
            # 绘制波纹线（如果提供了波纹角）
            if waviness_angle is not None:
                # 将角度转换为斜率
                # tan(βw) = Δz / Δx
                beta_w_rad = np.radians(waviness_angle)
                slope = np.tan(beta_w_rad)
                
                # 在图上绘制波纹线
                x_center = n_points / 2
                z_center = (z_positions[0] + z_positions[-1]) / 2
                
                # 绘制多条波纹线
                for offset in [-3, -2, -1, 0, 1, 2, 3]:
                    z_start = z_positions[0] + offset * 2
                    if z_positions[0] <= z_start <= z_positions[-1]:
                        x_at_z0 = x_center - (z_center - z_start) / slope
                        x_at_z1 = x_center + (z_positions[-1] - z_center) / slope
                        ax.plot([x_at_z0, x_at_z1], [z_start, z_positions[-1]], 
                               'r-', linewidth=1.5, alpha=0.7)
                
                # 标注波纹角
                ax.annotate('', xy=(x_center + 30, z_center + slope * 30), 
                           xytext=(x_center, z_center),
                           arrowprops=dict(arrowstyle='->', color='red', lw=2))
                ax.text(x_center + 35, z_center + slope * 15, f'βw = {waviness_angle:.1f}°', 
                       fontsize=11, color='red', fontweight='bold')
            
            # 绘制接触线（如果提供了接触角）
            if contact_angle is not None:
                beta_b_rad = np.radians(contact_angle)
                slope_b = np.tan(beta_b_rad)
                
                x_center = n_points / 2
                z_center = (z_positions[0] + z_positions[-1]) / 2
                
                # 绘制接触线
                for offset in [-2, 0, 2]:
                    z_start = z_positions[0] + offset * 3
                    if z_positions[0] <= z_start <= z_positions[-1]:
                        x_at_z0 = x_center - (z_center - z_start) / slope_b
                        x_at_z1 = x_center + (z_positions[-1] - z_center) / slope_b
                        ax.plot([x_at_z0, x_at_z1], [z_start, z_positions[-1]], 
                               'b-', linewidth=2.5, alpha=0.8)
                
                # 标注接触角
                ax.annotate('', xy=(x_center + 20, z_center + slope_b * 20), 
                           xytext=(x_center, z_center),
                           arrowprops=dict(arrowstyle='->', color='blue', lw=2))
                ax.text(x_center + 25, z_center + slope_b * 10, f'βb = {contact_angle:.1f}°', 
                       fontsize=11, color='blue', fontweight='bold')
            
            ax.set_xlabel('Profile Direction (points)', fontsize=11)
            ax.set_ylabel('Lead Direction z (mm)', fontsize=11)
            ax.set_title(f'Tooth Surface TOPOGRAFIE - {side}{title_suffix}', fontsize=13)
            
            # 添加root/tip标注
            ax.text(-0.02, 0.02, 'root', transform=ax.transAxes, fontsize=10, 
                   verticalalignment='bottom', color='black', fontweight='bold')
            ax.text(0.98, 0.02, 'tip', transform=ax.transAxes, fontsize=10, 
                   horizontalalignment='right', verticalalignment='bottom', 
                   color='black', fontweight='bold')
            
            return fig, ax
        
        def plot_waviness_analysis_diagram(data_matrix, z_positions, n_points, 
                                          waviness_angle, contact_angle, Lp, Lh,
                                          side='Right Flank'):
            """绘制波纹分析示意图，类似论文中的图6和图7"""
            fig = plt.figure(figsize=(14, 12))
            
            # 使用GridSpec实现更灵活的布局
            from matplotlib.gridspec import GridSpec
            gs = GridSpec(3, 2, figure=fig, height_ratios=[2, 1, 1], hspace=0.3, wspace=0.2)
            
            # 主图 - 拓普图带波纹线 (占据第一行两列)
            ax_main = fig.add_subplot(gs[0, :])
            
            colors = ['#0000FF', '#00FFFF', '#00FF00', '#FFFF00', '#FF0000']
            cmap = LinearSegmentedColormap.from_list('gear_topo', colors, N=256)
            
            im = ax_main.imshow(data_matrix, aspect='auto', cmap=cmap, origin='lower',
                               extent=[0, n_points-1, z_positions[0], z_positions[-1]])
            
            cbar = plt.colorbar(im, ax=ax_main, label='Deviation (µm)', shrink=0.8)
            
            # 绘制波纹线
            if waviness_angle is not None and waviness_angle > 0:
                beta_w_rad = np.radians(waviness_angle)
                slope_w = np.tan(beta_w_rad)
                
                x_center = n_points / 2
                z_center = (z_positions[0] + z_positions[-1]) / 2
                
                # 绘制多条红色波纹线
                Lh_val = Lh if Lh and Lh > 0 else 1
                for offset in np.linspace(-4, 4, 9):
                    z_start = z_center + offset * Lh_val / 2
                    if z_positions[0] <= z_start <= z_positions[-1]:
                        x_line = np.linspace(0, n_points-1, 100)
                        z_line = z_center + slope_w * (x_line - x_center) + offset * Lh_val / 2
                        mask = (z_line >= z_positions[0]) & (z_line <= z_positions[-1])
                        if np.any(mask):
                            ax_main.plot(x_line[mask], z_line[mask], 'r-', linewidth=1.5, alpha=0.6)
                
                # 绘制波纹角标注
                ax_main.annotate('', xy=(x_center + 50, z_center + slope_w * 50), 
                                xytext=(x_center - 50, z_center - slope_w * 50),
                                arrowprops=dict(arrowstyle='<->', color='darkred', lw=2))
                ax_main.text(x_center, z_center + slope_w * 60 + 1, f'βw = {waviness_angle:.2f}°', 
                            fontsize=12, color='darkred', fontweight='bold',
                            horizontalalignment='center')
            
            # 绘制接触线
            if contact_angle is not None and contact_angle > 0:
                beta_b_rad = np.radians(contact_angle)
                slope_b = np.tan(beta_b_rad)
                
                x_center = n_points / 2
                z_center = (z_positions[0] + z_positions[-1]) / 2
                
                # 绘制蓝色接触线
                Lh_val = Lh if Lh and Lh > 0 else 1
                for offset in [-1, 0, 1]:
                    z_start = z_center + offset * Lh_val
                    if z_positions[0] <= z_start <= z_positions[-1]:
                        x_line = np.linspace(0, n_points-1, 100)
                        z_line = z_center + slope_b * (x_line - x_center) + offset * Lh_val
                        mask = (z_line >= z_positions[0]) & (z_line <= z_positions[-1])
                        if np.any(mask):
                            ax_main.plot(x_line[mask], z_line[mask], 'b-', linewidth=2.5, alpha=0.8)
                
                # 接触线标注
                ax_main.text(n_points * 0.85, z_positions[-1] * 0.85, 
                            f'Contact Line\nβb = {contact_angle:.2f}°', 
                            fontsize=11, color='blue', fontweight='bold',
                            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            # 波长标注
            if Lp is not None and Lh is not None and Lp > 0 and Lh > 0:
                # Lp标注
                x_lp_start = n_points * 0.1
                x_lp_end = min(x_lp_start + Lp, n_points * 0.9)
                z_lp = z_positions[0] + (z_positions[-1] - z_positions[0]) * 0.15
                ax_main.annotate('', xy=(x_lp_end, z_lp), xytext=(x_lp_start, z_lp),
                                arrowprops=dict(arrowstyle='<->', color='green', lw=2))
                ax_main.text((x_lp_start + x_lp_end)/2, z_lp - 0.8, f'Lp = {Lp:.1f}', 
                            fontsize=10, color='green', horizontalalignment='center')
                
                # Lh标注
                x_lh = n_points * 0.05
                z_lh_start = z_positions[0] + (z_positions[-1] - z_positions[0]) * 0.3
                z_lh_end = min(z_lh_start + Lh, z_positions[-1] * 0.95)
                ax_main.annotate('', xy=(x_lh, z_lh_end), xytext=(x_lh, z_lh_start),
                                arrowprops=dict(arrowstyle='<->', color='purple', lw=2))
                ax_main.text(x_lh - 10, (z_lh_start + z_lh_end)/2, f'Lh = {Lh:.1f}mm', 
                            fontsize=10, color='purple', rotation=90, verticalalignment='center')
            
            ax_main.set_xlabel('Profile Direction (points) - from root to tip', fontsize=11)
            ax_main.set_ylabel('Lead Direction z (mm)', fontsize=11)
            ax_main.set_title(f'Tooth Surface Topography with Waviness Pattern - {side}', fontsize=13, fontweight='bold')
            
            # 添加root/tip标注
            ax_main.text(10, z_positions[0] + 0.5, 'root', fontsize=11, 
                        color='black', fontweight='bold')
            ax_main.text(n_points - 30, z_positions[0] + 0.5, 'tip', fontsize=11, 
                        color='black', fontweight='bold')
            
            # 左下图 - 计算过程
            ax_calc = fig.add_subplot(gs[1, 0])
            ax_calc.axis('off')
            ax_calc.set_title('Waviness Helix Angle Calculation', fontsize=12, fontweight='bold')
            
            # 安全格式化数值
            Lp_val = Lp if Lp is not None and Lp > 0 else 0
            Lh_val = Lh if Lh is not None and Lh > 0 else 1
            waviness_val = waviness_angle if waviness_angle is not None else 0
            contact_val = contact_angle if contact_angle is not None else 0
            
            Op_val = n_points / Lp_val if Lp_val > 0 else 0
            Oh_val = len(z_positions) / Lh_val if Lh_val > 0 else 0
            
            calc_text = f"""
Calculation Process:

1. FFT Spectrum Analysis:
   Profile: Find dominant order Op
   Lead: Find dominant order Oh

2. Wavelength Calculation:
   Lp = N_points / Op = {n_points} / {Op_val:.1f} = {Lp_val:.1f}
   Lh = N_profiles / Oh = {len(z_positions)} / {Oh_val:.1f} = {Lh_val:.1f}

3. Waviness Helix Angle:
   tan(βw) = Lp / Lh = {Lp_val:.1f} / {Lh_val:.1f}
   βw = arctan({Lp_val/Lh_val:.3f}) = {waviness_val:.2f}°

4. Contact Angle: βb = {contact_val:.2f}°

5. Angle Difference: Δβ = {abs(waviness_val - contact_val):.2f}°

Noise Risk: {'HIGH' if abs(waviness_val - contact_val) < 5 else 'LOW'}
"""
            ax_calc.text(0.05, 0.95, calc_text, transform=ax_calc.transAxes, fontsize=9,
                        verticalalignment='top', fontfamily='monospace',
                        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
            
            # 右下图 - 公式和参考
            ax_formula = fig.add_subplot(gs[1, 1])
            ax_formula.axis('off')
            ax_formula.set_title('Reference Formulas', fontsize=12, fontweight='bold')
            
            formula_text = """
Key Formulas:

(1) Waviness Helix Angle:
    tan βw = Lp / Lh

(2) Alternative:
    tan βw = (db × π) / (pz × Op)

Where:
    db = base diameter
    pz = pitch
    Op = profile waviness order
    Oh = lead waviness order
    βb = base helix angle

Noise Assessment:
    Low risk:  βw differs from βb
    High risk: βw ≈ βb
    (waviness parallel to contact line)
"""
            ax_formula.text(0.05, 0.95, formula_text, transform=ax_formula.transAxes, fontsize=9,
                           verticalalignment='top', fontfamily='monospace',
                           bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
            
            # 第三行 - 频谱图
            ax_spec1 = fig.add_subplot(gs[2, 0])
            ax_spec2 = fig.add_subplot(gs[2, 1])
            
            # 简单的频谱示意
            from scipy import fft
            
            # Profile方向频谱
            avg_profile = np.mean(data_matrix, axis=0)
            profile_fft = fft.fft(avg_profile)
            profile_magnitude = np.abs(profile_fft[:len(avg_profile)//2])
            orders_p = np.arange(1, min(50, len(profile_magnitude)))
            ax_spec1.bar(orders_p, profile_magnitude[1:min(51, len(profile_magnitude))], color='blue', alpha=0.7)
            ax_spec1.set_xlabel('Order')
            ax_spec1.set_ylabel('Amplitude (µm)')
            ax_spec1.set_title('Profile Direction Spectrum')
            ax_spec1.grid(True, alpha=0.3)
            
            # Lead方向频谱
            avg_lead = np.mean(data_matrix, axis=1)
            lead_fft = fft.fft(avg_lead)
            lead_magnitude = np.abs(lead_fft[:len(avg_lead)//2])
            orders_l = np.arange(1, min(20, len(lead_magnitude)))
            ax_spec2.bar(orders_l, lead_magnitude[1:min(21, len(lead_magnitude))], color='red', alpha=0.7)
            ax_spec2.set_xlabel('Order')
            ax_spec2.set_ylabel('Amplitude (µm)')
            ax_spec2.set_title('Lead Direction Spectrum')
            ax_spec2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            return fig
        
        with st.spinner("正在解析TOPOGRAFIE数据..."):
            topografie_data = parse_topografie_data(temp_path)
        
        col1, col2 = st.columns(2)
        
        for idx, side in enumerate(['rechts', 'links']):
            side_name = 'Right Flank' if side == 'rechts' else 'Left Flank'
            profiles = topografie_data[side]['profiles']
            
            with [col1, col2][idx]:
                st.markdown(f"### {'右齿面' if side == 'rechts' else '左齿面'}")
                
                if profiles:
                    st.markdown(f"**数据统计:** Profil数量: {len(profiles)}, z范围: {profiles[0]['position']:.1f}-{profiles[-1]['position']:.1f} mm")
                    
                    data_matrix, z_positions, n_points = create_topography_map(topografie_data, side)
                    
                    if data_matrix is not None:
                        fig, ax = plot_topography(data_matrix, z_positions, n_points, side_name, f" ({uploaded_file.name})")
                        st.pyplot(fig)
                        plt.close(fig)
                        
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
                    st.warning(f"未找到{'右齿面' if side == 'rechts' else '左齿面'}的TOPOGRAFIE数据")
        
        st.markdown("---")
        st.markdown("### 📊 波纹度分析 (Waviness Analysis)")
        
        # 波纹分析函数
        def analyze_waviness(data_matrix, z_positions, gear_params):
            from scipy import fft
            
            results = {
                'profile_wavelengths': [],
                'lead_wavelengths': [],
                'profile_spectrum': None,
                'lead_spectrum': None,
                'dominant_orders': [],
                'waviness_helix_angle': None
            }
            
            n_profiles, n_points = data_matrix.shape
            
            # Profile方向FFT分析
            avg_profile = np.mean(data_matrix, axis=0)
            profile_fft = fft.fft(avg_profile)
            profile_freq = fft.fftfreq(n_points)
            profile_magnitude = np.abs(profile_fft[:n_points//2])
            
            # Lead方向FFT分析
            avg_lead = np.mean(data_matrix, axis=1)
            lead_fft = fft.fft(avg_lead)
            lead_freq = fft.fftfreq(n_profiles)
            lead_magnitude = np.abs(lead_fft[:n_profiles//2])
            
            results['profile_spectrum'] = (profile_freq[:n_points//2], profile_magnitude)
            results['lead_spectrum'] = (lead_freq[:n_profiles//2], lead_magnitude)
            
            # 找主导阶次
            profile_peaks = np.argsort(profile_magnitude[1:])[::-1][:5] + 1
            lead_peaks = np.argsort(lead_magnitude[1:])[::-1][:5] + 1
            
            results['dominant_orders'] = {
                'profile': profile_peaks.tolist(),
                'lead': lead_peaks.tolist()
            }
            
            # 计算波纹螺旋角
            if gear_params and len(profile_peaks) > 0 and len(lead_peaks) > 0:
                Lp = n_points / profile_peaks[0] if profile_peaks[0] > 0 else n_points
                Lh = n_profiles / lead_peaks[0] if lead_peaks[0] > 0 else n_profiles
                
                if Lh > 0:
                    beta_w = np.arctan(Lp / Lh)
                    results['waviness_helix_angle'] = np.degrees(beta_w)
            
            return results
        
        # 执行波纹分析
        try:
            from scipy import fft
            
            for idx, side in enumerate(['rechts', 'links']):
                profiles = topografie_data[side]['profiles']
                
                if profiles:
                    data_matrix, z_positions, n_points = create_topography_map(topografie_data, side)
                    
                    if data_matrix is not None:
                        side_name = '右齿面' if side == 'rechts' else '左齿面'
                        
                        with [col1, col2][idx]:
                            st.markdown(f"**{side_name}波纹分析:**")
                            
                            waviness_results = analyze_waviness(data_matrix, z_positions, gear_params)
                            
                            # 显示主导阶次
                            if waviness_results['dominant_orders']:
                                st.markdown("**主导阶次 (Dominant Orders):**")
                                col_p, col_l = st.columns(2)
                                with col_p:
                                    st.caption("Profile方向:")
                                    orders_p = waviness_results['dominant_orders']['profile'][:3]
                                    st.write(f"  阶次: {orders_p}")
                                with col_l:
                                    st.caption("Lead方向:")
                                    orders_l = waviness_results['dominant_orders']['lead'][:3]
                                    st.write(f"  阶次: {orders_l}")
                            
                            # 显示波纹螺旋角
                            if waviness_results['waviness_helix_angle']:
                                beta_w = waviness_results['waviness_helix_angle']
                                st.metric("波纹螺旋角 βw", f"{beta_w:.2f}°")
                                
                                # 与齿轮螺旋角比较
                                if gear_params and hasattr(gear_params, 'helix_angle'):
                                    try:
                                        beta_gear = abs(float(str(gear_params.helix_angle).replace(',', '.')))
                                        diff = abs(beta_w - beta_gear)
                                        if diff < 5:
                                            st.success(f"波纹角接近齿轮螺旋角({beta_gear:.1f}°)，可能与加工工艺相关")
                                        else:
                                            st.info(f"波纹角与齿轮螺旋角({beta_gear:.1f}°)差异较大")
                                    except (ValueError, TypeError):
                                        pass
                            
                            # 计算Lp和Lh
                            n_profiles = len(z_positions)
                            orders_p = waviness_results['dominant_orders']['profile']
                            orders_l = waviness_results['dominant_orders']['lead']
                            Lp = n_points / orders_p[0] if orders_p else n_points
                            Lh = (z_positions[-1] - z_positions[0]) / orders_l[0] if orders_l else (z_positions[-1] - z_positions[0])
                            
                            # 获取齿轮螺旋角
                            contact_angle = None
                            if gear_params and hasattr(gear_params, 'helix_angle'):
                                try:
                                    contact_angle = abs(float(str(gear_params.helix_angle).replace(',', '.')))
                                except (ValueError, TypeError):
                                    contact_angle = None
                            
                            # 绘制详细的波纹分析图（类似论文中的图6和图7）
                            st.markdown("**📐 波纹螺旋角分析图:**")
                            
                            fig_analysis = plot_waviness_analysis_diagram(
                                data_matrix, z_positions, n_points,
                                waviness_results['waviness_helix_angle'],
                                contact_angle, Lp, Lh,
                                side='Right Flank' if side == 'rechts' else 'Left Flank'
                            )
                            st.pyplot(fig_analysis)
                            plt.close(fig_analysis)
                            
                            # 波纹频谱图
                            st.markdown("**波纹频谱 (Waviness Spectrum):**")
                            
                            fig_spec, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3))
                            
                            # Profile方向频谱
                            if waviness_results['profile_spectrum']:
                                freq_p, mag_p = waviness_results['profile_spectrum']
                                ax1.plot(freq_p[1:50], mag_p[1:50], 'b-', linewidth=1)
                                ax1.set_xlabel('Order')
                                ax1.set_ylabel('Amplitude (µm)')
                                ax1.set_title('Profile Direction Spectrum')
                                ax1.grid(True, alpha=0.3)
                            
                            # Lead方向频谱
                            if waviness_results['lead_spectrum']:
                                freq_l, mag_l = waviness_results['lead_spectrum']
                                ax2.plot(freq_l[1:min(30, len(freq_l))], mag_l[1:min(30, len(mag_l))], 'r-', linewidth=1)
                                ax2.set_xlabel('Order')
                                ax2.set_ylabel('Amplitude (µm)')
                                ax2.set_title('Lead Direction Spectrum')
                                ax2.grid(True, alpha=0.3)
                            
                            plt.tight_layout()
                            st.pyplot(fig_spec)
                            plt.close(fig_spec)
                            
        except ImportError:
            st.warning("波纹分析需要scipy库支持")
        except Exception as e:
            st.warning(f"波纹分析出错: {str(e)}")
        
        st.markdown("---")
        st.markdown("### 🔧 磨削工艺影响分析 (Grinding Process Analysis)")
        
        # 分析磨削工艺影响
        for idx, side in enumerate(['rechts', 'links']):
            profiles = topografie_data[side]['profiles']
            
            if profiles:
                data_matrix, z_positions, n_points = create_topography_map(topografie_data, side)
                
                if data_matrix is not None:
                    side_name = '右齿面' if side == 'rechts' else '左齿面'
                    
                    with [col1, col2][idx]:
                        st.markdown(f"**{side_name}工艺分析:**")
                        
                        # 计算各区域偏差
                        n_rows, n_cols = data_matrix.shape
                        
                        # 齿根区域 (前1/3)
                        root_region = data_matrix[:, :n_cols//3]
                        # 齿中区域 (中间1/3)
                        mid_region = data_matrix[:, n_cols//3:2*n_cols//3]
                        # 齿顶区域 (后1/3)
                        tip_region = data_matrix[:, 2*n_cols//3:]
                        
                        col_r, col_m, col_t = st.columns(3)
                        with col_r:
                            st.metric("齿根区RMS", f"{np.std(root_region):.2f} µm")
                        with col_m:
                            st.metric("齿中区RMS", f"{np.std(mid_region):.2f} µm")
                        with col_t:
                            st.metric("齿顶区RMS", f"{np.std(tip_region):.2f} µm")
                        
                        # 判断工艺问题
                        issues = []
                        
                        # 检查系统性偏差
                        mean_dev = np.mean(data_matrix)
                        if abs(mean_dev) > 2:
                            issues.append(f"系统性偏差: 平均偏差 {mean_dev:.2f}µm")
                        
                        # 检查齿根/齿顶差异
                        root_mean = np.mean(root_region)
                        tip_mean = np.mean(tip_region)
                        if abs(root_mean - tip_mean) > 3:
                            issues.append(f"齿形倾斜: 齿根{root_mean:.1f}µm vs 齿顶{tip_mean:.1f}µm")
                        
                        # 检查波纹度
                        row_std = np.std(np.mean(data_matrix, axis=1))
                        col_std = np.std(np.mean(data_matrix, axis=0))
                        if row_std > 2 or col_std > 2:
                            issues.append(f"明显波纹: Lead方向{row_std:.1f}µm, Profile方向{col_std:.1f}µm")
                        
                        if issues:
                            st.warning("**检测到的问题:**")
                            for issue in issues:
                                st.write(f"  • {issue}")
                        else:
                            st.success("齿面质量良好，无明显工艺问题")
        
        st.markdown("---")
        st.markdown("### 🔊 噪声影响评估 (Noise Impact Assessment)")
        
        # 噪声影响评估
        for idx, side in enumerate(['rechts', 'links']):
            profiles = topografie_data[side]['profiles']
            
            if profiles:
                data_matrix, z_positions, n_points = create_topography_map(topografie_data, side)
                
                if data_matrix is not None:
                    side_name = '右齿面' if side == 'rechts' else '左齿面'
                    
                    with [col1, col2][idx]:
                        st.markdown(f"**{side_name}噪声评估:**")
                        
                        # 计算噪声相关指标
                        total_rms = np.std(data_matrix)
                        peak_to_valley = np.max(data_matrix) - np.min(data_matrix)
                        
                        # 噪声风险等级
                        if total_rms < 1:
                            noise_level = "低"
                            noise_color = "green"
                        elif total_rms < 3:
                            noise_level = "中等"
                            noise_color = "orange"
                        else:
                            noise_level = "高"
                            noise_color = "red"
                        
                        col_n1, col_n2, col_n3 = st.columns(3)
                        with col_n1:
                            st.metric("总RMS", f"{total_rms:.2f} µm")
                        with col_n2:
                            st.metric("峰谷值", f"{peak_to_valley:.2f} µm")
                        with col_n3:
                            st.metric("噪声风险", noise_level)
                        
                        # 噪声分析说明
                        if total_rms > 2:
                            st.warning("""
                            **噪声风险分析:**
                            - 高波纹度可能导致齿轮啮合噪声
                            - 建议检查磨削工艺参数
                            - 可能需要优化砂轮修整参数
                            """)
                        else:
                            st.success("齿面波纹度较低，噪声风险小")
        
        st.markdown("---")
        st.markdown("### 📖 拓普图说明")
        st.info("""
        **齿面TOPOGRAFIE拓普图** 显示整个齿面的偏差分布情况：
        - **X轴**: 齿高方向（从齿根到齿顶）
        - **Y轴**: 齿宽方向（从一端到另一端）
        - **颜色**: 偏差值（蓝色=负偏差，红色=正偏差）
        
        **波纹分析** 通过FFT频谱分析识别齿面波纹的主要阶次和波长。
        
        **波纹螺旋角 βw** 表示波纹在齿面上的倾斜方向，与加工工艺直接相关。
        
        **噪声影响** 齿面波纹度是齿轮传动噪声的主要来源之一，RMS值越大，噪声风险越高。
        """)
    
    elif page == '🤖 AI综合分析报告':
        st.markdown("## 🤖 AI综合分析报告")
        
        # 计算频谱分析结果
        with st.spinner("正在计算频谱分析..."):
            results = {
                'profile_left': analyzer.analyze_profile('left', verbose=False),
                'profile_right': analyzer.analyze_profile('right', verbose=False),
                'helix_left': analyzer.analyze_helix('left', verbose=False),
                'helix_right': analyzer.analyze_helix('right', verbose=False)
            }
        
        name_mapping = {
            'profile_left': 'Left Profile',
            'profile_right': 'Right Profile',
            'helix_left': 'Left Lead',
            'helix_right': 'Right Lead'
        }
        
        # 收集所有分析数据
        def generate_comprehensive_analysis():
            """生成综合分析报告 - 智能分析齿轮问题"""
            report = {
                'overall_score': 0,
                'status': '正常',
                'status_color': 'green',
                'profile_analysis': {},
                'helix_analysis': {},
                'pitch_analysis': {},
                'spectrum_analysis': {},
                'issues': [],
                'causes': [],
                'recommendations': [],
                'noise_prediction': '低',
                'quality_grade': 'Q6',
                'detailed_diagnosis': {}
            }
            
            scores = []
            
            # ========== 1. 齿形偏差智能分析 ==========
            profile_score = 100
            profile_issues = []
            profile_diagnosis = {}
            
            if profile_eval:
                for side in ['left', 'right']:
                    side_data = profile_data.get(side, {})
                    if side_data:
                        deviations = []
                        all_ffa = []
                        all_fHa = []
                        all_Fa = []
                        
                        for tooth_id, tooth_profiles in side_data.items():
                            helix_mid = (helix_eval.eval_start + helix_eval.eval_end) / 2
                            best_z = min(tooth_profiles.keys(), key=lambda z: abs(z - helix_mid))
                            values = np.array(tooth_profiles[best_z])
                            F_a, fH_a, ff_a, Ca = calc_profile_deviations(values)
                            if F_a is not None:
                                deviations.append({'Fα': F_a, 'fHα': fH_a, 'ffα': ff_a, 'Ca': Ca})
                                all_Fa.append(F_a)
                                all_fHa.append(fH_a)
                                all_ffa.append(ff_a)
                        
                        if deviations:
                            avg_Fa = np.mean(all_Fa)
                            avg_fHa = np.mean(all_fHa)
                            avg_ffa = np.mean(all_ffa)
                            std_Fa = np.std(all_Fa) if len(all_Fa) > 1 else 0
                            
                            report['profile_analysis'][side] = {
                                'avg_Fα': avg_Fa,
                                'avg_fHα': avg_fHa,
                                'avg_ffα': avg_ffa,
                                'std_Fα': std_Fa
                            }
                            
                            # 智能诊断齿形问题
                            side_name = '左' if side == 'left' else '右'
                            
                            # 齿形总偏差分析
                            if avg_Fa > 20:
                                profile_score -= 25
                                profile_issues.append(f"🔴 {side_name}齿面齿形总偏差Fα严重超标({avg_Fa:.2f}μm)")
                                profile_diagnosis[side] = {'severity': 'critical', 'type': 'Fα_excessive'}
                            elif avg_Fa > 15:
                                profile_score -= 15
                                profile_issues.append(f"🟠 {side_name}齿面齿形总偏差Fα过大({avg_Fa:.2f}μm)")
                                profile_diagnosis[side] = {'severity': 'warning', 'type': 'Fα_high'}
                            elif avg_Fa > 10:
                                profile_score -= 8
                                profile_issues.append(f"🟡 {side_name}齿面齿形总偏差Fα偏大({avg_Fa:.2f}μm)")
                            
                            # 齿形倾斜偏差分析 - 压力角误差
                            if abs(avg_fHa) > 10:
                                profile_score -= 15
                                direction = "正" if avg_fHa > 0 else "负"
                                profile_issues.append(f"🔴 {side_name}齿面压力角误差严重({direction}向倾斜{abs(avg_fHa):.2f}μm)")
                                profile_diagnosis.setdefault(side, {})['pressure_angle'] = 'severe'
                            elif abs(avg_fHa) > 6:
                                profile_score -= 8
                                direction = "正" if avg_fHa > 0 else "负"
                                profile_issues.append(f"🟠 {side_name}齿面存在压力角误差({direction}向倾斜{abs(avg_fHa):.2f}μm)")
                                profile_diagnosis.setdefault(side, {})['pressure_angle'] = 'moderate'
                            
                            # 齿形形状偏差分析 - 齿面波纹
                            if avg_ffa > 8:
                                profile_score -= 10
                                profile_issues.append(f"🟠 {side_name}齿面形状偏差ffα过大({avg_ffa:.2f}μm)，存在波纹")
                                profile_diagnosis.setdefault(side, {})['waviness'] = True
                            
                            # 齿形一致性分析
                            if std_Fa > 5:
                                profile_score -= 8
                                profile_issues.append(f"🟡 {side_name}齿面各齿齿形偏差不一致(标准差{std_Fa:.2f}μm)")
                                profile_diagnosis.setdefault(side, {})['inconsistency'] = True
            
            scores.append(max(0, profile_score))
            report['profile_analysis']['score'] = max(0, profile_score)
            report['profile_analysis']['issues'] = profile_issues
            report['detailed_diagnosis']['profile'] = profile_diagnosis
            
            # ========== 2. 齿向偏差智能分析 ==========
            helix_score = 100
            helix_issues = []
            helix_diagnosis = {}
            
            if helix_eval:
                for side in ['left', 'right']:
                    side_data = helix_data.get(side, {})
                    if side_data:
                        deviations = []
                        all_Fb = []
                        all_fHb = []
                        all_ffb = []
                        
                        for tooth_id, tooth_helix in side_data.items():
                            profile_mid = (profile_eval.eval_start + profile_eval.eval_end) / 2
                            best_d = min(tooth_helix.keys(), key=lambda d: abs(d - profile_mid))
                            values = np.array(tooth_helix[best_d])
                            F_b, fH_b, ff_b, Cb = calc_lead_deviations(values)
                            if F_b is not None:
                                deviations.append({'Fβ': F_b, 'fHβ': fH_b, 'ffβ': ff_b, 'Cb': Cb})
                                all_Fb.append(F_b)
                                all_fHb.append(fH_b)
                                all_ffb.append(ff_b)
                        
                        if deviations:
                            avg_Fb = np.mean(all_Fb)
                            avg_fHb = np.mean(all_fHb)
                            avg_ffb = np.mean(all_ffb)
                            std_Fb = np.std(all_Fb) if len(all_Fb) > 1 else 0
                            
                            report['helix_analysis'][side] = {
                                'avg_Fβ': avg_Fb,
                                'avg_fHβ': avg_fHb,
                                'avg_ffβ': avg_ffb,
                                'std_Fβ': std_Fb
                            }
                            
                            side_name = '左' if side == 'left' else '右'
                            
                            # 齿向总偏差分析
                            if avg_Fb > 20:
                                helix_score -= 25
                                helix_issues.append(f"🔴 {side_name}齿面齿向总偏差Fβ严重超标({avg_Fb:.2f}μm)")
                                helix_diagnosis[side] = {'severity': 'critical', 'type': 'Fβ_excessive'}
                            elif avg_Fb > 15:
                                helix_score -= 15
                                helix_issues.append(f"🟠 {side_name}齿面齿向总偏差Fβ过大({avg_Fb:.2f}μm)")
                                helix_diagnosis[side] = {'severity': 'warning', 'type': 'Fβ_high'}
                            elif avg_Fb > 10:
                                helix_score -= 8
                                helix_issues.append(f"🟡 {side_name}齿面齿向总偏差Fβ偏大({avg_Fb:.2f}μm)")
                            
                            # 齿向倾斜偏差分析 - 螺旋角误差
                            if abs(avg_fHb) > 10:
                                helix_score -= 15
                                direction = "正" if avg_fHb > 0 else "负"
                                helix_issues.append(f"🔴 {side_name}齿面螺旋角误差严重({direction}向倾斜{abs(avg_fHb):.2f}μm)")
                                helix_diagnosis.setdefault(side, {})['helix_angle'] = 'severe'
                            elif abs(avg_fHb) > 6:
                                helix_score -= 8
                                direction = "正" if avg_fHb > 0 else "负"
                                helix_issues.append(f"🟠 {side_name}齿面存在螺旋角误差({direction}向倾斜{abs(avg_fHb):.2f}μm)")
                                helix_diagnosis.setdefault(side, {})['helix_angle'] = 'moderate'
                            
                            # 齿向形状偏差分析
                            if avg_ffb > 8:
                                helix_score -= 10
                                helix_issues.append(f"🟠 {side_name}齿面齿向形状偏差ffβ过大({avg_ffb:.2f}μm)")
                                helix_diagnosis.setdefault(side, {})['shape_error'] = True
                            
                            # 齿向一致性分析
                            if std_Fb > 5:
                                helix_score -= 8
                                helix_issues.append(f"🟡 {side_name}齿面各齿齿向偏差不一致(标准差{std_Fb:.2f}μm)")
                                helix_diagnosis.setdefault(side, {})['inconsistency'] = True
            
            scores.append(max(0, helix_score))
            report['helix_analysis']['score'] = max(0, helix_score)
            report['helix_analysis']['issues'] = helix_issues
            report['detailed_diagnosis']['helix'] = helix_diagnosis
            
            # ========== 3. 周节偏差智能分析 ==========
            pitch_score = 100
            pitch_issues = []
            pitch_diagnosis = {}
            
            if pitch_left:
                report['pitch_analysis']['left'] = {
                    'fp_max': pitch_left.fp_max,
                    'Fp_max': pitch_left.Fp_max,
                    'Fr': pitch_left.Fr
                }
                
                # 单个齿距偏差
                if pitch_left.fp_max > 15:
                    pitch_score -= 20
                    pitch_issues.append(f"🔴 左齿面单个齿距偏差fp严重超标({pitch_left.fp_max:.2f}μm)")
                    pitch_diagnosis['left_fp'] = 'critical'
                elif pitch_left.fp_max > 10:
                    pitch_score -= 12
                    pitch_issues.append(f"🟠 左齿面单个齿距偏差fp过大({pitch_left.fp_max:.2f}μm)")
                    pitch_diagnosis['left_fp'] = 'warning'
                elif pitch_left.fp_max > 6:
                    pitch_score -= 5
                    pitch_issues.append(f"🟡 左齿面单个齿距偏差fp偏大({pitch_left.fp_max:.2f}μm)")
                
                # 齿距累积偏差
                if pitch_left.Fp_max > 40:
                    pitch_score -= 20
                    pitch_issues.append(f"🔴 左齿面齿距累积偏差Fp严重超标({pitch_left.Fp_max:.2f}μm)")
                    pitch_diagnosis['left_Fp'] = 'critical'
                elif pitch_left.Fp_max > 30:
                    pitch_score -= 12
                    pitch_issues.append(f"🟠 左齿面齿距累积偏差Fp过大({pitch_left.Fp_max:.2f}μm)")
                    pitch_diagnosis['left_Fp'] = 'warning'
                elif pitch_left.Fp_max > 20:
                    pitch_score -= 5
                    pitch_issues.append(f"🟡 左齿面齿距累积偏差Fp偏大({pitch_left.Fp_max:.2f}μm)")
                
                # 径向跳动
                if pitch_left.Fr > 25:
                    pitch_score -= 15
                    pitch_issues.append(f"🔴 左齿面径向跳动Fr严重超标({pitch_left.Fr:.2f}μm)")
                    pitch_diagnosis['left_Fr'] = 'critical'
                elif pitch_left.Fr > 20:
                    pitch_score -= 10
                    pitch_issues.append(f"🟠 左齿面径向跳动Fr过大({pitch_left.Fr:.2f}μm)")
                    pitch_diagnosis['left_Fr'] = 'warning'
                elif pitch_left.Fr > 15:
                    pitch_score -= 5
                    pitch_issues.append(f"🟡 左齿面径向跳动Fr偏大({pitch_left.Fr:.2f}μm)")
            
            if pitch_right:
                report['pitch_analysis']['right'] = {
                    'fp_max': pitch_right.fp_max,
                    'Fp_max': pitch_right.Fp_max,
                    'Fr': pitch_right.Fr
                }
                
                if pitch_right.fp_max > 15:
                    pitch_score -= 20
                    pitch_issues.append(f"🔴 右齿面单个齿距偏差fp严重超标({pitch_right.fp_max:.2f}μm)")
                elif pitch_right.fp_max > 10:
                    pitch_score -= 12
                    pitch_issues.append(f"🟠 右齿面单个齿距偏差fp过大({pitch_right.fp_max:.2f}μm)")
                elif pitch_right.fp_max > 6:
                    pitch_score -= 5
                    pitch_issues.append(f"🟡 右齿面单个齿距偏差fp偏大({pitch_right.fp_max:.2f}μm)")
                
                if pitch_right.Fp_max > 40:
                    pitch_score -= 20
                    pitch_issues.append(f"🔴 右齿面齿距累积偏差Fp严重超标({pitch_right.Fp_max:.2f}μm)")
                elif pitch_right.Fp_max > 30:
                    pitch_score -= 12
                    pitch_issues.append(f"🟠 右齿面齿距累积偏差Fp过大({pitch_right.Fp_max:.2f}μm)")
                elif pitch_right.Fp_max > 20:
                    pitch_score -= 5
                    pitch_issues.append(f"🟡 右齿面齿距累积偏差Fp偏大({pitch_right.Fp_max:.2f}μm)")
                
                if pitch_right.Fr > 25:
                    pitch_score -= 15
                    pitch_issues.append(f"🔴 右齿面径向跳动Fr严重超标({pitch_right.Fr:.2f}μm)")
                elif pitch_right.Fr > 20:
                    pitch_score -= 10
                    pitch_issues.append(f"🟠 右齿面径向跳动Fr过大({pitch_right.Fr:.2f}μm)")
                elif pitch_right.Fr > 15:
                    pitch_score -= 5
                    pitch_issues.append(f"🟡 右齿面径向跳动Fr偏大({pitch_right.Fr:.2f}μm)")
            
            scores.append(max(0, pitch_score))
            report['pitch_analysis']['score'] = max(0, pitch_score)
            report['pitch_analysis']['issues'] = pitch_issues
            report['detailed_diagnosis']['pitch'] = pitch_diagnosis
            
            # ========== 4. 频谱分析智能诊断 ==========
            spectrum_score = 100
            spectrum_issues = []
            spectrum_diagnosis = {}
            ze = gear_params.teeth_count if gear_params else 87
            
            for name in ['profile_left', 'profile_right', 'helix_left', 'helix_right']:
                if name in results and results[name]:
                    result = results[name]
                    sorted_components = sorted(result.spectrum_components[:15], key=lambda c: c.order)
                    
                    # ZE主导阶次分析
                    ze_amp = 0
                    for comp in sorted_components:
                        if abs(comp.order - ze) < 1:
                            ze_amp = comp.amplitude
                            break
                    
                    if ze_amp > 0.15:
                        spectrum_score -= 15
                        spectrum_issues.append(f"🔴 {name_mapping.get(name, name)}主导阶次ZE幅值严重偏高({ze_amp:.4f}μm)")
                        spectrum_diagnosis[name] = {'ze_severity': 'critical'}
                    elif ze_amp > 0.1:
                        spectrum_score -= 10
                        spectrum_issues.append(f"🟠 {name_mapping.get(name, name)}主导阶次ZE幅值偏高({ze_amp:.4f}μm)")
                        spectrum_diagnosis[name] = {'ze_severity': 'warning'}
                    elif ze_amp > 0.05:
                        spectrum_score -= 5
                        spectrum_issues.append(f"🟡 {name_mapping.get(name, name)}主导阶次ZE幅值略高({ze_amp:.4f}μm)")
                    
                    # 2ZE分析 - 偏心/椭圆度
                    ze2_amp = 0
                    for comp in sorted_components:
                        if abs(comp.order - 2*ze) < 1:
                            ze2_amp = comp.amplitude
                            break
                    
                    if ze2_amp > 0.08:
                        spectrum_score -= 10
                        spectrum_issues.append(f"🟠 {name_mapping.get(name, name)}2倍频幅值偏高({ze2_amp:.4f}μm)，可能存在偏心")
                        spectrum_diagnosis.setdefault(name, {})['eccentricity'] = True
            
            scores.append(max(0, spectrum_score))
            report['spectrum_analysis']['score'] = max(0, spectrum_score)
            report['spectrum_analysis']['issues'] = spectrum_issues
            report['detailed_diagnosis']['spectrum'] = spectrum_diagnosis
            
            # ========== 5. 计算综合评分 ==========
            overall_score = np.mean(scores) if scores else 100
            report['overall_score'] = overall_score
            
            # ========== 6. 智能状态判断 ==========
            if overall_score >= 95:
                report['status'] = '优秀'
                report['status_color'] = 'green'
                report['noise_prediction'] = '很低'
                report['quality_grade'] = 'Q5'
            elif overall_score >= 85:
                report['status'] = '良好'
                report['status_color'] = 'lightgreen'
                report['noise_prediction'] = '低'
                report['quality_grade'] = 'Q6'
            elif overall_score >= 70:
                report['status'] = '合格'
                report['status_color'] = 'yellow'
                report['noise_prediction'] = '中等'
                report['quality_grade'] = 'Q7'
            elif overall_score >= 50:
                report['status'] = '需关注'
                report['status_color'] = 'orange'
                report['noise_prediction'] = '高'
                report['quality_grade'] = 'Q8'
            else:
                report['status'] = '不合格'
                report['status_color'] = 'red'
                report['noise_prediction'] = '很高'
                report['quality_grade'] = 'Q9+'
            
            # ========== 7. 智能原因分析 ==========
            all_issues = profile_issues + helix_issues + pitch_issues + spectrum_issues
            report['issues'] = all_issues
            
            diagnosis = report['detailed_diagnosis']
            
            # 齿形问题原因
            if any('Fα' in issue for issue in all_issues):
                if diagnosis.get('profile', {}).get('left', {}).get('pressure_angle') == 'severe' or \
                   diagnosis.get('profile', {}).get('right', {}).get('pressure_angle') == 'severe':
                    report['causes'].append("🔧 压力角误差严重：刀具齿形角误差大或砂轮修整角度不正确")
                else:
                    report['causes'].append("🔧 齿形误差：可能由刀具磨损、砂轮修整不良或加工参数不当引起")
            
            if any('压力角' in issue for issue in all_issues):
                report['causes'].append("🔧 压力角偏差：检查刀具/砂轮的齿形角，调整加工参数")
            
            if any('ffα' in issue for issue in all_issues) or any('波纹' in issue for issue in all_issues):
                report['causes'].append("🔧 齿面波纹：可能由磨削振动、砂轮不平衡或主轴跳动引起")
            
            # 齿向问题原因
            if any('Fβ' in issue for issue in all_issues):
                report['causes'].append("🔧 齿向误差：可能由机床导轨误差、工件装夹变形或热变形引起")
            
            if any('螺旋角' in issue for issue in all_issues):
                report['causes'].append("🔧 螺旋角偏差：检查差动挂轮计算，调整机床螺旋角设置")
            
            # 周节问题原因
            if any('fp' in issue for issue in all_issues):
                report['causes'].append("🔧 齿距误差：可能由分度机构误差、刀具误差或工件偏心引起")
            
            if any('Fp' in issue for issue in all_issues):
                report['causes'].append("🔧 齿距累积误差：检查分度盘精度，检查工件安装偏心")
            
            if any('Fr' in issue for issue in all_issues):
                report['causes'].append("🔧 径向跳动：可能由工件安装偏心、轴承间隙或主轴跳动引起")
            
            # 频谱问题原因
            if any('ZE' in issue for issue in all_issues):
                report['causes'].append("🔧 主导阶次异常：分度误差或刀具误差导致")
            
            if any('偏心' in issue for issue in all_issues):
                report['causes'].append("🔧 偏心问题：检查工件安装偏心量和内孔精度")
            
            # 一致性问题
            if any('不一致' in issue for issue in all_issues):
                report['causes'].append("🔧 各齿偏差不一致：检查加工过程稳定性，检查夹紧力是否均匀")
            
            if not report['causes']:
                report['causes'].append("✅ 齿轮各项指标正常，加工质量良好")
            
            # ========== 8. 智能改进建议 ==========
            if overall_score < 60:
                report['recommendations'].append("⚠️ 建议立即停机检查，全面排查加工设备精度")
            elif overall_score < 80:
                report['recommendations'].append("📋 建议全面检查加工机床精度和刀具状态")
            
            # 齿形改进
            if any('Fα' in issue or '压力角' in issue for issue in all_issues):
                report['recommendations'].append("📐 齿形优化：检查刀具/砂轮磨损，重新修整砂轮，调整加工参数")
            
            if any('ffα' in issue or '波纹' in issue for issue in all_issues):
                report['recommendations'].append("📐 减少波纹：检查砂轮平衡，检查主轴精度，降低磨削用量")
            
            # 齿向改进
            if any('Fβ' in issue or '螺旋角' in issue for issue in all_issues):
                report['recommendations'].append("📐 齿向优化：检查导轨精度，校准螺旋角设置，改善装夹方式")
            
            # 周节改进
            if any('fp' in issue or 'Fp' in issue for issue in all_issues):
                report['recommendations'].append("📐 齿距优化：检查分度机构精度，校准分度盘，检查蜗轮蜗杆磨损")
            
            if any('Fr' in issue for issue in all_issues):
                report['recommendations'].append("📐 降低跳动：改善工件装夹，检查夹具精度，检查主轴轴承")
            
            # 频谱改进
            if any('ZE' in issue for issue in all_issues):
                report['recommendations'].append("📐 降低主导阶次：优化分度精度，检查刀具/砂轮状态")
            
            if any('偏心' in issue for issue in all_issues):
                report['recommendations'].append("📐 消除偏心：重新安装工件，检查内孔与心轴配合")
            
            # 一致性改进
            if any('不一致' in issue for issue in all_issues):
                report['recommendations'].append("📐 提高一致性：检查夹紧力均匀性，检查加工过程稳定性")
            
            if not report['recommendations']:
                report['recommendations'].append("✅ 继续保持当前加工工艺，定期监测质量")
            
            return report
        
        # 生成报告
        comprehensive_report = generate_comprehensive_analysis()
        
        # ========== 综合评估仪表板 ==========
        st.markdown(f"""
        <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; margin-bottom: 1.5rem;">
            <div style="text-align: center; padding: 1.5rem;">
                <div style="font-size: 3.5rem; font-weight: 700;">{comprehensive_report['overall_score']:.0f}</div>
                <div style="font-size: 1rem; opacity: 0.9;">综合评分</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 状态卡片
        col1, col2, col3 = st.columns(3)
        
        status_color = comprehensive_report['status_color']
        status_text = comprehensive_report['status']
        
        with col1:
            status_class = 'status-excellent' if status_text in ['优秀', '良好'] else 'status-warning' if status_text in ['合格', '需关注'] else 'status-danger'
            st.markdown(f"""
            <div class="card" style="text-align: center;">
                <div style="font-size: 0.9rem; color: #6b7280; margin-bottom: 0.5rem;">齿轮状态</div>
                <div class="{status_class}" style="display: inline-block;">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="card" style="text-align: center;">
                <div style="font-size: 0.9rem; color: #6b7280; margin-bottom: 0.5rem;">质量等级</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #1f2937;">{comprehensive_report['quality_grade']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            noise = comprehensive_report['noise_prediction']
            noise_icon = '🔇' if noise == '很低' else '🔈' if noise == '低' else '🔉' if noise == '中等' else '🔊'
            noise_class = 'status-excellent' if noise in ['很低', '低'] else 'status-warning' if noise == '中等' else 'status-danger'
            st.markdown(f"""
            <div class="card" style="text-align: center;">
                <div style="font-size: 0.9rem; color: #6b7280; margin-bottom: 0.5rem;">噪声预测</div>
                <div class="{noise_class}" style="display: inline-block;">{noise_icon} {noise}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ========== 分项评分仪表板 ==========
        st.markdown("### 📊 分项评分详情")
        
        profile_score = comprehensive_report['profile_analysis'].get('score', 100)
        helix_score = comprehensive_report['helix_analysis'].get('score', 100)
        pitch_score = comprehensive_report['pitch_analysis'].get('score', 100)
        spectrum_score = comprehensive_report['spectrum_analysis'].get('score', 100)
        
        score_cols = st.columns(4)
        
        with score_cols[0]:
            color = '#10b981' if profile_score >= 85 else '#f59e0b' if profile_score >= 70 else '#ef4444'
            st.markdown(f"""
            <div class="card" style="border-left: 4px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 0.85rem; color: #6b7280;">齿形偏差</div>
                        <div style="font-size: 1.8rem; font-weight: 700; color: {color};">{profile_score:.0f}<span style="font-size: 0.9rem; color: #9ca3af;">/100</span></div>
                    </div>
                    <div style="font-size: 2rem;">📊</div>
                </div>
                <div style="margin-top: 0.5rem; background: #e5e7eb; border-radius: 4px; height: 6px;">
                    <div style="background: {color}; border-radius: 4px; height: 100%; width: {profile_score}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with score_cols[1]:
            color = '#10b981' if helix_score >= 85 else '#f59e0b' if helix_score >= 70 else '#ef4444'
            st.markdown(f"""
            <div class="card" style="border-left: 4px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 0.85rem; color: #6b7280;">齿向偏差</div>
                        <div style="font-size: 1.8rem; font-weight: 700; color: {color};">{helix_score:.0f}<span style="font-size: 0.9rem; color: #9ca3af;">/100</span></div>
                    </div>
                    <div style="font-size: 2rem;">📐</div>
                </div>
                <div style="margin-top: 0.5rem; background: #e5e7eb; border-radius: 4px; height: 6px;">
                    <div style="background: {color}; border-radius: 4px; height: 100%; width: {helix_score}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with score_cols[2]:
            color = '#10b981' if pitch_score >= 85 else '#f59e0b' if pitch_score >= 70 else '#ef4444'
            st.markdown(f"""
            <div class="card" style="border-left: 4px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 0.85rem; color: #6b7280;">周节偏差</div>
                        <div style="font-size: 1.8rem; font-weight: 700; color: {color};">{pitch_score:.0f}<span style="font-size: 0.9rem; color: #9ca3af;">/100</span></div>
                    </div>
                    <div style="font-size: 2rem;">⚙️</div>
                </div>
                <div style="margin-top: 0.5rem; background: #e5e7eb; border-radius: 4px; height: 6px;">
                    <div style="background: {color}; border-radius: 4px; height: 100%; width: {pitch_score}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with score_cols[3]:
            color = '#10b981' if spectrum_score >= 85 else '#f59e0b' if spectrum_score >= 70 else '#ef4444'
            st.markdown(f"""
            <div class="card" style="border-left: 4px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 0.85rem; color: #6b7280;">频谱分析</div>
                        <div style="font-size: 1.8rem; font-weight: 700; color: {color};">{spectrum_score:.0f}<span style="font-size: 0.9rem; color: #9ca3af;">/100</span></div>
                    </div>
                    <div style="font-size: 2rem;">📈</div>
                </div>
                <div style="margin-top: 0.5rem; background: #e5e7eb; border-radius: 4px; height: 6px;">
                    <div style="background: {color}; border-radius: 4px; height: 100%; width: {spectrum_score}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ========== 问题诊断 ==========
        st.markdown("### 🔍 问题诊断")
        
        if comprehensive_report['issues']:
            # 分类显示问题
            critical_issues = [i for i in comprehensive_report['issues'] if '🔴' in i]
            warning_issues = [i for i in comprehensive_report['issues'] if '🟠' in i]
            info_issues = [i for i in comprehensive_report['issues'] if '🟡' in i]
            success_issues = [i for i in comprehensive_report['issues'] if '✅' in i]
            
            if critical_issues:
                st.markdown("<div style='font-weight: 600; color: #ef4444; margin-bottom: 0.5rem;'>⚠️ 严重问题</div>", unsafe_allow_html=True)
                for issue in critical_issues:
                    st.markdown(f"<div class='issue-critical'>{issue}</div>", unsafe_allow_html=True)
            
            if warning_issues:
                st.markdown("<div style='font-weight: 600; color: #f59e0b; margin-bottom: 0.5rem; margin-top: 1rem;'>⚡ 警告问题</div>", unsafe_allow_html=True)
                for issue in warning_issues:
                    st.markdown(f"<div class='issue-warning'>{issue}</div>", unsafe_allow_html=True)
            
            if info_issues:
                st.markdown("<div style='font-weight: 600; color: #06b6d4; margin-bottom: 0.5rem; margin-top: 1rem;'>ℹ️ 提示信息</div>", unsafe_allow_html=True)
                for issue in info_issues:
                    st.markdown(f"<div class='issue-info'>{issue}</div>", unsafe_allow_html=True)
            
            if success_issues:
                st.markdown("<div style='font-weight: 600; color: #10b981; margin-bottom: 0.5rem; margin-top: 1rem;'>✅ 正常状态</div>", unsafe_allow_html=True)
                for issue in success_issues:
                    st.markdown(f"<div class='issue-success'>{issue}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='issue-success'>✅ 未发现明显问题，齿轮状态良好</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # ========== 原因分析 ==========
        st.markdown("### 🔬 原因分析")
        
        causes = comprehensive_report['causes']
        for cause in causes:
            st.markdown(f"- {cause}")
        
        st.markdown("---")
        
        # ========== 改进建议 ==========
        st.markdown("### 💡 改进建议")
        
        recommendations = comprehensive_report['recommendations']
        for rec in recommendations:
            st.markdown(f"- {rec}")
        
        # ========== 详细数据 ==========
        with st.expander("📊 详细分析数据", expanded=False):
            # 齿形数据
            if comprehensive_report['profile_analysis']:
                st.markdown("**齿形偏差数据:**")
                profile_df_data = []
                for side, data in comprehensive_report['profile_analysis'].items():
                    if isinstance(data, dict) and 'avg_Fα' in data:
                        profile_df_data.append({
                            '齿面': '左齿面' if side == 'left' else '右齿面',
                            'Fα (μm)': f"{data['avg_Fα']:.2f}",
                            'fHα (μm)': f"{data['avg_fHα']:.2f}",
                            'ffα (μm)': f"{data['avg_ffα']:.2f}"
                        })
                if profile_df_data:
                    st.dataframe(pd.DataFrame(profile_df_data), use_container_width=True, hide_index=True)
            
            # 齿向数据
            if comprehensive_report['helix_analysis']:
                st.markdown("**齿向偏差数据:**")
                helix_df_data = []
                for side, data in comprehensive_report['helix_analysis'].items():
                    if isinstance(data, dict) and 'avg_Fβ' in data:
                        helix_df_data.append({
                            '齿面': '左齿面' if side == 'left' else '右齿面',
                            'Fβ (μm)': f"{data['avg_Fβ']:.2f}",
                            'fHβ (μm)': f"{data['avg_fHβ']:.2f}",
                            'ffβ (μm)': f"{data['avg_ffβ']:.2f}"
                        })
                if helix_df_data:
                    st.dataframe(pd.DataFrame(helix_df_data), use_container_width=True, hide_index=True)
            
            # 周节数据
            if comprehensive_report['pitch_analysis']:
                st.markdown("**周节偏差数据:**")
                pitch_df_data = []
                for side, data in comprehensive_report['pitch_analysis'].items():
                    if isinstance(data, dict) and 'fp_max' in data:
                        pitch_df_data.append({
                            '齿面': '左齿面' if side == 'left' else '右齿面',
                            'fp max (μm)': f"{data['fp_max']:.2f}",
                            'Fp max (μm)': f"{data['Fp_max']:.2f}",
                            'Fr (μm)': f"{data['Fr']:.2f}"
                        })
                if pitch_df_data:
                    st.dataframe(pd.DataFrame(pitch_df_data), use_container_width=True, hide_index=True)
    
    # 清理临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)

else:
    # ========== 欢迎页面 ==========
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1 class="main-title">⚙️ 齿轮测量分析系统</h1>
        <p style="font-size: 1.2rem; color: #666;">专业版 - 齿轮波纹度分析与质量评估</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 功能卡片
    st.markdown("### 🎯 核心功能")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="card">
            <div class="card-header">📊 偏差分析</div>
            <ul style="list-style: none; padding: 0;">
                <li>✅ 齿形偏差 Fα 分析</li>
                <li>✅ 齿向偏差 Fβ 分析</li>
                <li>✅ 周节偏差 fp/Fp 分析</li>
                <li>✅ 径向跳动 Fr 分析</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <div class="card-header">📈 频谱分析</div>
            <ul style="list-style: none; padding: 0;">
                <li>✅ 阶次振幅分析</li>
                <li>✅ 极限曲线评估</li>
                <li>✅ 主导阶次识别</li>
                <li>✅ 波纹度评价</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="card">
            <div class="card-header">🤖 AI智能分析</div>
            <ul style="list-style: none; padding: 0;">
                <li>✅ 综合质量评分</li>
                <li>✅ 问题智能诊断</li>
                <li>✅ 原因深度分析</li>
                <li>✅ 改进建议生成</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 使用说明
    st.markdown("### 📋 使用说明")
    
    st.markdown("""
    <div class="card">
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="background: #1f77b4; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 1rem;">1</div>
            <div><b>上传数据</b> - 在左侧边栏上传 MKA 格式的齿轮测量数据文件</div>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="background: #1f77b4; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 1rem;">2</div>
            <div><b>选择功能</b> - 在左侧导航栏选择需要使用的分析功能</div>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 1rem;">
            <div style="background: #1f77b4; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 1rem;">3</div>
            <div><b>查看报告</b> - 系统自动生成分析报告，支持PDF导出</div>
        </div>
        <div style="display: flex; align-items: center;">
            <div style="background: #1f77b4; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 1rem;">4</div>
            <div><b>AI分析</b> - 查看AI综合分析报告，获取质量评估和改进建议</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 技术规格
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 📐 支持标准
        - GB/T 10095.1-2008
        - ISO 1328-1:2014
        - DIN 3962
        - AGMA 2015-1-A01
        """)
    
    with col2:
        st.markdown("""
        #### 📁 支持格式
        - Klingelnberg MKA 格式
        - 齿轮波纹度数据
        - 齿形/齿向测量数据
        - 周节测量数据
        """)
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>齿轮波纹度分析系统 专业版 | 基于 Python + Streamlit 构建</p>
        <p style="font-size: 0.8rem;">© 2024 Gear Measurement Analysis System</p>
    </div>
    """, unsafe_allow_html=True)
