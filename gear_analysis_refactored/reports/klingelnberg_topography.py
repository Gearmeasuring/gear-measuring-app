"""
Klingelnberg Topography Report Generator
Generates a landscape A4 report showing 3D topography without actual modifications
"""
import os
import logging
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from mpl_toolkits.mplot3d import Axes3D
from typing import Dict, List, Any, Optional

try:
    from config.logging_config import logger
except ModuleNotFoundError:
    # Allow running this file directly without project root on sys.path
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    try:
        from config.logging_config import logger  # type: ignore
    except ModuleNotFoundError:
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

class KlingelnbergTopographyReport:
    """Klingelnberg Topography Report - Landscape A4 with 3D Wireframes"""
    
    def __init__(self):
        pass
        
    def create_page(self, pdf, measurement_data):
        """
        Create the topography page and add it to the PDF
        
        Args:
            pdf: Open PdfPages object
            measurement_data: GearMeasurementData object
        """
        try:
            # Create figure for Portrait A4 (8.27 x 11.69 inches)
            # Use high DPI for better quality
            fig = plt.figure(figsize=(8.27, 11.69), dpi=150, facecolor='white')  # 设置背景为白色
            
            # Layout: Header(8%), Title(5%), Plots(86%), Footer/Legend(1%)
            # 调整标题区域高度，解决与表头的重叠问题
            # 增加页面边距
            gs = gridspec.GridSpec(4, 1, figure=fig, 
                                 height_ratios=[0.08, 0.05, 0.86, 0.01],
                                 hspace=0.02, left=0.05, right=0.95, top=0.95, bottom=0.05)
            
            # 1. Header (Table-like header matching reference)
            header_ax = fig.add_subplot(gs[0, 0])
            self._draw_matplotlib_header(header_ax, measurement_data)
            
            # 2. Title - 模仿参考图样式，在表格区域上方添加标识
            title_ax = fig.add_subplot(gs[1, 0])
            title_ax.axis('off')
            # 主标题：Gear Topography（参考图中是粗体，较大字体）
            title_ax.text(0.5, 0.7, "Gear Topography", ha='center', va='center', 
                         fontsize=18, fontweight='bold', fontname='Arial', color='black')
            
            # 去掉上方的左右/齿顶标识（按需求）
            
            # 3. 3D Visualizations (完整单个齿：可旋转的3D视图)
            # 使用最大面积展示，图表尽量放大
            # 单个图表，显示完整的单个齿（左齿面+齿顶+右齿面），可旋转查看
            plot_gs = gridspec.GridSpecFromSubplotSpec(
                1, 1, subplot_spec=gs[2, 0],
                wspace=0.02
            )
            
            # Get data for the first available tooth
            topo_data = getattr(measurement_data, 'topography_data', None)
            tooth_data = {}
            tooth_num = 1

            def side_has_data(side_payload: Dict) -> bool:
                """检查侧面是否包含有效数据（更宽松的检查）"""
                if not isinstance(side_payload, dict) or not side_payload:
                    return False
                
                # 新格式：检查profiles或flank_lines
                if 'profiles' in side_payload:
                    profiles = side_payload['profiles']
                    if isinstance(profiles, dict) and profiles:
                        return True
                if 'flank_lines' in side_payload:
                    flank_lines = side_payload['flank_lines']
                    if isinstance(flank_lines, dict) and flank_lines:
                        return True
                
                # 旧格式：直接是索引到数组的字典
                if side_payload and not ('profiles' in side_payload or 'flank_lines' in side_payload):
                    # 检查是否有任何非空值
                    for v in side_payload.values():
                        if v and (isinstance(v, (list, tuple, np.ndarray)) and len(v) > 0):
                            return True
                        elif isinstance(v, dict) and v:
                            return True
                
                return False

            def tooth_has_data(payload: Dict) -> bool:
                """检查齿是否有任意侧面数据"""
                return (
                    ('left' in payload and side_has_data(payload['left'])) or
                    ('right' in payload and side_has_data(payload['right']))
                )

            def pick_best_tooth_with_data(data_dict: Dict) -> Optional[tuple]:
                """选择包含数据最多的齿 (profiles+flank_lines 之和最大)"""
                best = None
                best_score = -1
                for t in sorted(data_dict.keys()):
                    td = data_dict[t]
                    if not (isinstance(td, dict) and tooth_has_data(td)):
                        continue
                    def side_count(side_key: str) -> int:
                        if side_key not in td or not isinstance(td[side_key], dict):
                            return 0
                        s = td[side_key]
                        cnt = 0
                        if isinstance(s.get('profiles'), dict):
                            cnt += len(s['profiles'])
                        if isinstance(s.get('flank_lines'), dict):
                            cnt += len(s['flank_lines'])
                        # 旧格式：直接是索引到数组
                        if 'profiles' not in s and 'flank_lines' not in s:
                            cnt += len(s)
                        return cnt
                    score = side_count('left') + side_count('right')
                    if score > best_score:
                        best_score = score
                        best = (t, td)
                return best

            # Handle various data formats more robustly
            tooth_num = 1
            tooth_data = {}
            
            # 1. Handle TopographyData object
            if topo_data and hasattr(topo_data, 'data') and isinstance(topo_data.data, dict) and topo_data.data:
                picked = pick_best_tooth_with_data(topo_data.data)
                if picked:
                    tooth_num, tooth_data = picked
                else:
                    # fallback: 尝试所有齿，找到第一个有数据的
                    for t in sorted(topo_data.data.keys()):
                        td = topo_data.data[t]
                        if isinstance(td, dict) and (td.get('left') or td.get('right')):
                            tooth_num, tooth_data = t, td
                            break
                    else:
                        # 如果都没有数据，取第一个
                        first = sorted(topo_data.data.keys())[0]
                        tooth_num, tooth_data = first, topo_data.data[first]
            # 2. Handle direct dict format
            elif isinstance(topo_data, dict) and topo_data:
                picked = pick_best_tooth_with_data(topo_data)
                if picked:
                    tooth_num, tooth_data = picked
                else:
                    # fallback: 尝试所有齿
                    for t in sorted(topo_data.keys()):
                        td = topo_data[t]
                        if isinstance(td, dict) and (td.get('left') or td.get('right')):
                            tooth_num, tooth_data = t, td
                            break
                    else:
                        # 如果都没有数据，取第一个
                        first = sorted(topo_data.keys())[0]
                        tooth_num, tooth_data = first, topo_data[first]
            # 3. Handle other data formats
            elif topo_data is not None:
                logger.warning(f"Unexpected topography data format: {type(topo_data)}")
                # 尝试创建默认数据用于测试
                tooth_data = {'left': {}, 'right': {}}

            # 标记是否使用真实数据
            is_real_data = bool(tooth_data)

            if not tooth_data:
                # 没有找到任何有效数据，不创建测试数据
                logger.warning("No valid topography data found in MKA file")
                tooth_data = {'left': {}, 'right': {}}
                tooth_num = 1
                is_real_data = False
            
            # 完整单个齿的3D Plot - 可旋转的3D视图
            ax_tooth = fig.add_subplot(plot_gs[0, 0], projection='3d')
            # 移除边距，让图表占据全部空间
            ax_tooth.margins(0)
            left_has_real_data = 'left' in tooth_data and side_has_data(tooth_data['left'])
            right_has_real_data = 'right' in tooth_data and side_has_data(tooth_data['right'])
            
            if left_has_real_data or right_has_real_data:
                # 创建可旋转的3D单齿视图（使用理论数据+Topography偏差）
                try:
                    logger.info(f"Creating 3D tooth plot for tooth {tooth_num}, left={left_has_real_data}, right={right_has_real_data}")
                    self._create_rotatable_3d_tooth(ax_tooth, tooth_data, measurement_data, is_real_data=is_real_data)
                    logger.info("3D tooth plot created successfully")
                except Exception as e:
                    logger.error(f"Error creating 3D tooth plot: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # 即使出错，也显示一个错误消息
                    self._create_empty_3d_plot(ax_tooth, f"Error: {str(e)}")
            else:
                logger.warning("No valid data for left or right flank, showing empty plot")
                self._create_empty_3d_plot(ax_tooth, "No Data")
            
            # 4. Footer / Legend / Scale - 参照参考图2格式
            footer_ax = fig.add_subplot(gs[3, 0])
            footer_ax.axis('off')
            
            # 去掉比例尺标注（按需求）
            
            # 右侧：齿号
            footer_ax.text(0.95, 0.5, f"Tooth no.: {tooth_num}", ha='right', va='center', 
                          fontsize=10, transform=footer_ax.transAxes)
            
            # 去掉版权与公司标注（按需求）
            
            # Save the page
            pdf.savefig(fig, orientation='portrait')
            plt.close(fig)
            logger.info("Added 3D Topography Page")
            
        except Exception as e:
            logger.exception(f"Failed to create Topography Page: {e}")
            # 即使出错，也尝试保存一个错误页面
            try:
                error_fig = plt.figure(figsize=(8.27, 11.69), dpi=150, facecolor='white')
                error_ax = error_fig.add_subplot(111)
                error_ax.axis('off')
                error_ax.text(0.5, 0.5, f"Error generating Topography report:\n{str(e)}", 
                            ha='center', va='center', fontsize=12, color='red',
                            transform=error_ax.transAxes)
                pdf.savefig(error_fig, orientation='portrait')
                plt.close(error_fig)
                logger.info("Saved error page to PDF")
            except Exception as e2:
                logger.error(f"Failed to save error page: {e2}")

    def _create_test_data(self):
        """创建测试数据用于显示图表"""
        import numpy as np
        
        # 创建模拟的齿面数据
        # 模拟10个profile，每个profile有50个点
        num_profiles = 10
        num_points = 50
        
        # 创建模拟的偏差数据（类似真实齿面数据）
        profiles = {}
        for i in range(num_profiles):
            # 创建正弦波形状的偏差数据
            x = np.linspace(0, 2*np.pi, num_points)
            # 模拟齿面偏差：主要偏差在中间，边缘较小
            deviation = np.sin(x) * np.exp(-0.1*(x-np.pi)**2) * 5.0
            profiles[i] = {
                'z': float(i),  # 高度值
                'values': deviation.tolist()
            }
        
        # 创建模拟的flank_lines数据
        flank_lines = {}
        for i in range(5):
            flank_lines[i] = {
                'd': 48.0 + i * 0.5,  # 直径值
                'values': [np.sin(j * 0.2) * 2.0 for j in range(num_profiles)]
            }
        
        return {
            'left': {
                'profiles': profiles,
                'flank_lines': flank_lines
            },
            'right': {
                'profiles': profiles,
                'flank_lines': flank_lines
            }
        }

    def _draw_matplotlib_header(self, ax, data):
        """Draw table-like header using Matplotlib primitives - 参照参考图2格式"""
        ax.axis('off')
        
        info = data.basic_info
        
        # 辅助函数
        def fmt(val, format_str="{}", default=""):
            if val is None or val == "": return default
            try:
                if isinstance(val, str):
                    val = val.strip()
                    if val == "" or val.upper() == "N/A" or val.upper() == "NA":
                        return default
                if isinstance(val, (float, int)):
                    return format_str.format(val)
                return str(val)
            except:
                return str(val) if val else default
        
        # 计算基本参数（参照klingelnberg_single_page.py）
        import math
        db_str = ""
        beta_b_str = ""
        try:
            mn = getattr(info, 'module', None)
            z = getattr(info, 'teeth', None)
            alpha_n_deg = getattr(info, 'pressure_angle', None)
            beta_deg = getattr(info, 'helix_angle', None)
            
            if mn and z and alpha_n_deg:
                alpha_n = math.radians(alpha_n_deg)
                beta = math.radians(beta_deg) if beta_deg else 0
                
                # 端面压力角
                alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta)) if beta != 0 else alpha_n
                # 分度圆直径
                d = z * mn / math.cos(beta) if beta != 0 else z * mn
                # 基圆直径 db = d * cos(alpha_t)
                db = d * math.cos(alpha_t)
                
                # 基圆螺旋角 beta_b = asin(sin(beta) * cos(alpha_n))
                if beta != 0:
                    beta_b_deg = math.degrees(math.asin(math.sin(beta) * math.cos(alpha_n)))
                else:
                    beta_b_deg = 0
                
                db_str = f"{db:.4f}mm"
                beta_b_str = f"{beta_b_deg:.3f}°"
        except Exception as e:
            logger.warning(f"计算基圆参数失败: {e}")
        
        # 计算评估长度和Approach Length
        l_alpha_str = ""
        l_beta_str = ""
        appr_length_str = ""
        l_bv_alpha_str = ""  # Length Bv. la
        
        try:
            # Profile Evaluation Length (L_alpha) = |d2 - d1|
            # Profile Approach Length = |d1 - da|
            if hasattr(info, 'profile_markers_left') and info.profile_markers_left and len(info.profile_markers_left) >= 4:
                da, d1, d2, de = info.profile_markers_left
                l_alpha = abs(d2 - d1)
                appr_len = abs(d1 - da)
                l_bv_alpha = abs(de - da)  # Length Bv. la (total measurement length)
                if l_alpha > 0: l_alpha_str = f"{l_alpha:.2f}mm"
                if appr_len > 0: appr_length_str = f"{appr_len:.2f}mm"
                if l_bv_alpha > 0: l_bv_alpha_str = f"{l_bv_alpha:.2f}mm"
            elif hasattr(info, 'profile_eval_start') and hasattr(info, 'profile_eval_end'):
                profile_start = getattr(info, 'profile_eval_start', 0.0)
                profile_end = getattr(info, 'profile_eval_end', 0.0)
                if profile_end > profile_start:
                    l_alpha = profile_end - profile_start
                    l_alpha_str = f"{l_alpha:.2f}mm"
        except Exception as e:
            logger.warning(f"计算评估长度失败: {e}")
        
        try:
            # Lead Evaluation Length (L_beta) = |b2 - b1|
            if hasattr(info, 'lead_markers_left') and info.lead_markers_left and len(info.lead_markers_left) >= 4:
                ba, b1, b2, be = info.lead_markers_left
                l_beta = abs(b2 - b1)
                if l_beta > 0: l_beta_str = f"{l_beta:.2f}mm"
        except Exception as e:
            logger.warning(f"计算螺旋线评估长度失败: {e}")
        
        # 构建表格数据 - 参照参考图2格式
        # 左列7行，右列14行（但显示为7行，每行两个参数）
        table_data = [
            ['Prog.No.:', fmt(getattr(info, 'program', '')), 'Operator:', fmt(getattr(info, 'operator', '')), 'Date:', fmt(getattr(info, 'date', ''))],
            ['Type:', fmt(getattr(info, 'type_', 'gear'), default='gear'), 'No. of Teeth:', fmt(getattr(info, 'teeth', '')), 'Face Width:', fmt(getattr(info, 'width', ''), "{:.1f}mm")],
            ['Drawing No.:', fmt(getattr(info, 'drawing_no', '')), 'Module m:', fmt(getattr(info, 'module', ''), "{:.2f}mm"), 'Length Bv. la:', l_bv_alpha_str],
            ['Order No.:', fmt(getattr(info, 'order_no', 'N/A')), 'Pressure angle:', fmt(getattr(info, 'pressure_angle', ''), "{:.0f}º"), 'Length Ev. l4:', l_alpha_str],
            ['Cust./Mach. N:', fmt(getattr(info, 'customer', '')), 'Helix angle:', fmt(getattr(info, 'helix_angle', ''), "{:.0f}º"), 'Appr. Length M:', appr_length_str],
            ['Loc. of check:', fmt(getattr(info, 'location', '')), 'Base Cir.- db:', db_str, 'Stylus-Ø:', fmt(getattr(info, 'ball_diameter', ''), "{:.3f}mm")],
            ['Condition:', fmt(getattr(info, 'condition', '')), 'Base Helix ang:', beta_b_str, 'Add.Mod.Coeff x:', fmt(getattr(info, 'modification_coeff', ''), "{:.3f}")]
        ]
        
        # 创建表格
        table = ax.table(cellText=table_data, loc='center', cellLoc='left', bbox=[0.02, 0, 0.98, 1])
        
        # 设置样式
        table.auto_set_font_size(False)
        table.set_fontsize(7)
        table.auto_set_column_width(range(len(table_data[0])))
        
        cells = table.get_celld()
        for (row, col), cell in cells.items():
            cell.set_edgecolor('black')
            cell.set_linewidth(0.5)
            
            # 标签列（0, 2, 4）：左对齐、加粗
            if col in [0, 2, 4]:
                cell.set_text_props(verticalalignment='center', horizontalalignment='left', weight='bold')
            else:  # 数值列（1, 3, 5）：右对齐
                cell.set_text_props(verticalalignment='center', horizontalalignment='right')
            
            cell.set_height(1.0/7)

    def _create_rotatable_3d_tooth(self, ax, tooth_data: Dict, measurement_data, is_real_data: bool = True):
        """
        创建可旋转的3D单齿视图 - 完整重构
        - 显示完整的单齿形状：左齿面、右齿面、齿顶、齿根
        - 使用MKA文件中的理论数据绘制理论齿面（蓝色）
        - Topography偏差叠加在理论齿面上（黑色网格）
        - 支持交互式旋转查看
        
        坐标系统：
        - X轴：齿宽方向（Face Width）
        - Y轴：齿廓方向（Profile，从齿根到齿顶）
        - Z轴：高度方向（从齿根Z=0到齿顶Z=高度）+ Topography偏差
        """
        import numpy as np
        import math
        
        # 获取齿轮参数
        info = measurement_data.basic_info
        module = getattr(info, 'module', 0.0)
        teeth = getattr(info, 'teeth', 0)
        pressure_angle_deg = getattr(info, 'pressure_angle', 20.0)
        helix_angle_deg = getattr(info, 'helix_angle', 0.0)
        face_width = getattr(info, 'width', 0.0)
        tip_diameter = getattr(info, 'tip_diameter', 0.0)
        root_diameter = getattr(info, 'root_diameter', 0.0)
        
        if module == 0 or teeth == 0:
            ax.text(0.5, 0.5, 0.5, "No valid gear parameters", ha='center', va='center')
            return
        
        # 计算理论齿面参数
        alpha_n = math.radians(pressure_angle_deg)
        beta = math.radians(helix_angle_deg) if helix_angle_deg else 0.0
        
        # 端面压力角
        alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta)) if beta != 0 else alpha_n
        # 分度圆直径
        d_pitch = teeth * module / math.cos(beta) if beta != 0 else teeth * module
        # 基圆直径
        base_circle_db = d_pitch * math.cos(alpha_t)
        
        # 计算齿顶和齿根直径（如果没有提供，则估算）
        if tip_diameter == 0:
            tip_diameter = d_pitch + 2 * module  # 估算：分度圆直径 + 2*模数
        if root_diameter == 0:
            root_diameter = d_pitch - 2.5 * module  # 估算：分度圆直径 - 2.5*模数
        
        # 计算齿高（从齿根到齿顶）
        tooth_height = (tip_diameter - root_diameter) / 2.0
        
        # 获取左右齿面数据
        left_data = tooth_data.get('left', {})
        right_data = tooth_data.get('right', {})
        
        logger.info(f"Creating 3D tooth view: module={module}, teeth={teeth}, face_width={face_width}, tooth_height={tooth_height}")
        
        # 绘制左齿面（左侧，从齿根到齿顶）
        if left_data:
            logger.info("Drawing left flank with data")
            self._draw_complete_3d_flank(ax, left_data, "left", measurement_data, 
                                        base_circle_db, face_width, beta, 
                                        root_diameter, tip_diameter, tooth_height, is_real_data)
        else:
            logger.warning("No left data, drawing theoretical left flank only")
            self._draw_theoretical_flank_only(ax, "left", face_width, beta, root_diameter, tip_diameter, tooth_height)
        
        # 绘制右齿面（右侧，从齿根到齿顶）
        if right_data:
            logger.info("Drawing right flank with data")
            self._draw_complete_3d_flank(ax, right_data, "right", measurement_data, 
                                        base_circle_db, face_width, beta, 
                                        root_diameter, tip_diameter, tooth_height, is_real_data)
        else:
            logger.warning("No right data, drawing theoretical right flank only")
            self._draw_theoretical_flank_only(ax, "right", face_width, beta, root_diameter, tip_diameter, tooth_height)
        
        # 不绘制齿顶/齿根板块（按需求去除）
        
        # 设置3D视图参数
        ax.set_xlabel('X (Face Width, mm)', fontsize=10)
        ax.set_ylabel('Y (Profile, mm)', fontsize=10)
        ax.set_zlabel('Z (Height + Deviation, mm)', fontsize=10)
        
        # 设置合适的视角，使单齿形状更清晰
        ax.view_init(elev=30, azim=45)  # 从上方斜视，使单齿形状更明显
        
        # 设置坐标轴比例
        ax.set_box_aspect([1, 0.8, 1])  # 使单齿形状更明显
        
        # 设置背景
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        ax.xaxis.pane.set_edgecolor('lightgray')
        ax.yaxis.pane.set_edgecolor('lightgray')
        ax.zaxis.pane.set_edgecolor('lightgray')
        
        # 添加网格
        ax.grid(True, alpha=0.3)
        
        # 添加标题和标签
        ax.set_title('Single Tooth 3D View', fontsize=12, fontweight='bold', pad=20)
        
        # 添加文本标签
        ax.text(0, 0, tooth_height * 1.1, 'Tip', fontsize=10, color='red', fontweight='bold')
        ax.text(0, 0, -tooth_height * 0.1, 'Root', fontsize=10, color='red', fontweight='bold')
        if left_data:
            ax.text(-face_width * 0.1 if face_width > 0 else -1, 0, tooth_height * 0.5, 
                   'Left Flank', fontsize=9, color='blue', fontweight='bold')
        if right_data:
            ax.text(face_width * 1.1 if face_width > 0 else 1, 0, tooth_height * 0.5, 
                   'Right Flank', fontsize=9, color='blue', fontweight='bold')
    
    def _draw_complete_3d_flank(self, ax, side_data: Dict, side: str, measurement_data, 
                                base_circle_db: float, face_width: float, beta: float,
                                root_diameter: float, tip_diameter: float, tooth_height: float, is_real_data: bool):
        """
        绘制完整的3D齿面（从齿根到齿顶）
        - 理论表面：蓝色
        - Topography偏差：叠加在理论表面上（黑色网格）
        """
        import numpy as np
        import math
        
        # 提取topography数据
        is_new_format = isinstance(side_data, dict) and ('profiles' in side_data or 'flank_lines' in side_data)
        profiles = None
        
        if is_new_format:
            profiles = side_data.get('profiles', {})
            if not profiles or not isinstance(profiles, dict):
                flank_lines = side_data.get('flank_lines', {})
                if flank_lines and isinstance(flank_lines, dict):
                    profiles = {}
                    for idx, flank in flank_lines.items():
                        if isinstance(flank, dict) and 'values' in flank:
                            profiles[idx] = {
                                'z': flank.get('d', float(idx)),
                                'values': flank['values']
                            }
        
        if not profiles or not isinstance(profiles, dict):
            return
        
        profile_indices = sorted(profiles.keys())
        z_values = []
        valid_profiles = {}
        for idx in profile_indices:
            profile = profiles[idx]
            if isinstance(profile, dict) and 'values' in profile:
                z_val = profile.get('z', float(idx))
                z_values.append(z_val)
                valid_profiles[idx] = profile
            
        if not valid_profiles:
            logger.warning(f"No valid profiles found for {side} flank, drawing theoretical surface only")
            # 如果没有数据，创建理论表面
            self._draw_theoretical_flank_only(ax, side, face_width, beta, root_diameter, tip_diameter, tooth_height)
            return
        
        # 检查所有profile的点数，找到最大点数
        all_point_counts = []
        for idx in profile_indices:
            profile = valid_profiles[idx]
            values = profile.get('values', [])
            if values:
                all_point_counts.append(len(values))
        
        if not all_point_counts:
            logger.warning(f"No values in any profile for {side} flank, drawing theoretical surface only")
            # 如果没有数据，创建理论表面
            self._draw_theoretical_flank_only(ax, side, face_width, beta, root_diameter, tip_diameter, tooth_height)
            return
        
        # 使用最小点数作为标准点数，避免插补（只显示实际测量点）
        min_points = min(all_point_counts)
        num_d_points = min_points
        
        if len(set(all_point_counts)) > 1:
            logger.warning(f"Profile point counts vary: min={min_points}, max={max(all_point_counts)}, using min (no interpolation) for {side} flank")
        
        logger.info(f"Drawing {side} flank: {len(valid_profiles)} profiles, {num_d_points} points per profile (max)")
        
        # 计算理论齿面的Y坐标（齿廓方向，从齿根到齿顶）
        info = measurement_data.basic_info
        if side == 'left':
            profile_markers = getattr(info, 'profile_markers_left', None)
        else:
            profile_markers = getattr(info, 'profile_markers_right', None)
        
        # 获取评价范围标记点
        eval_start_idx = None
        eval_end_idx = None
        if profile_markers and len(profile_markers) >= 4:
            da, d1, d2, de = profile_markers
            root_dia = max(da, d1, d2, de)
            tip_dia = min(da, d1, d2, de)
            
            # 计算每个profile点对应的直径值（从root_dia到tip_dia）
            # 注意：Y坐标是从齿根到齿顶，对应直径从root_dia到tip_dia
            diameter_values = np.linspace(root_dia, tip_dia, num_d_points)
            
            # 找到d1和d2在diameter_values中的索引（评价范围）
            # d1是起评点，d2是终评点
            if root_dia > tip_dia:
                # 直径递减（从齿根到齿顶）
                d1_idx = np.argmin(np.abs(diameter_values - d1))
                d2_idx = np.argmin(np.abs(diameter_values - d2))
                # 确保d1_idx < d2_idx（因为d1在齿根侧，d2在齿顶侧）
                if d1_idx > d2_idx:
                    d1_idx, d2_idx = d2_idx, d1_idx
            else:
                # 直径递增
                d1_idx = np.argmin(np.abs(diameter_values - d1))
                d2_idx = np.argmin(np.abs(diameter_values - d2))
                if d1_idx > d2_idx:
                    d1_idx, d2_idx = d2_idx, d1_idx
            
            eval_start_idx = max(0, d1_idx)
            eval_end_idx = min(num_d_points, d2_idx + 1)  # +1因为切片是左闭右开
            
            logger.info(f"Evaluation range for {side} flank: indices {eval_start_idx} to {eval_end_idx} (d1={d1:.3f}, d2={d2:.3f})")
        else:
            root_dia = root_diameter
            tip_dia = tip_diameter
            # 如果没有markers，使用全部数据
            eval_start_idx = 0
            eval_end_idx = num_d_points
        
        # Y坐标：从齿根（Y=0）到齿顶（Y=tooth_height）- 对应每个profile的点数
        # 只使用评价范围内的Y坐标
        if eval_start_idx is not None and eval_end_idx is not None:
            y_values_full = np.linspace(0, tooth_height, num_d_points)
            y_values = y_values_full[eval_start_idx:eval_end_idx]
            num_d_points_eval = len(y_values)
            logger.info(f"Using evaluation range: {num_d_points_eval} points out of {num_d_points} total")
        else:
            y_values = np.linspace(0, tooth_height, num_d_points)
            num_d_points_eval = num_d_points
        
        # X坐标：齿宽方向 - 对应profile的数量
        num_profiles = len(profile_indices)
        if face_width > 0:
            x_values = np.linspace(0, face_width, num_profiles)
        else:
            # 如果没有face_width，使用默认值
            if num_profiles > 0:
                x_values = np.linspace(0, 10.0, num_profiles)
            else:
                x_values = np.linspace(0, 10.0, 20)  # 默认20个点
                logger.warning(f"No profiles for {side} flank, using default")
        
        # 创建网格：X是齿宽方向（profile数量），Y是齿廓方向（评价范围内的点数）
        # meshgrid的参数顺序：先Y（行），后X（列）
        # 结果：X.shape = (num_d_points_eval, num_profiles), Y.shape = (num_d_points_eval, num_profiles)
        X, Y = np.meshgrid(x_values, y_values)
        
        # 根据side调整X位置，使左右齿面形成完整的单齿形状
        # 左齿面：X值在负侧（左侧）
        # 右齿面：X值在正侧（右侧）
        if side == 'left':
            X = X - face_width * 0.6 if face_width > 0 else X - 5.0  # 左齿面在左侧
        else:  # right
            X = X + face_width * 0.6 if face_width > 0 else X + 5.0  # 右齿面在右侧
        
        # 应用螺旋角扭曲
        if abs(beta) > 0.001 and face_width > 0:
            Y_range = Y.max() - Y.min()
            if Y_range > 1e-10:
                Y_norm = (Y - Y.min()) / Y_range
                twist_amount = Y_norm * face_width * np.tan(beta) * 0.1
                X = X + twist_amount
        
        # Z坐标：理论表面高度（从齿根Z=0到齿顶Z=tooth_height）
        # 理论表面是倾斜的，从齿根到齿顶
        Z_theory = Y  # 理论表面高度 = Y坐标（从齿根到齿顶）
        
        # 提取Topography偏差数据
        # Z_deviation的形状必须与X和Y匹配：(num_d_points_eval, num_profiles)
        # 但在赋值时，我们需要转置，因为数据是按profile组织的
        Z_deviation = np.zeros((num_d_points_eval, num_profiles))
        has_deviation_data = False
        
        for i, idx in enumerate(profile_indices):
            if i >= num_profiles:
                logger.warning(f"Profile index {i} exceeds num_profiles ({num_profiles}), skipping")
                continue
                
            profile = valid_profiles[idx]
            values = profile.get('values', [])
            
            if not values:
                continue
            
            values_array = np.array(values)
            values_len = len(values_array)
            
            # 仅使用实际测量点：截断到最小点数，不插补、不填充
            if values_len == num_d_points:
                values_full = values_array
            else:
                logger.debug(f"Profile {idx} has {values_len} points, truncating to {num_d_points} (no interpolation)")
                values_full = values_array[:num_d_points]
            
            # 提取评价范围内的数据（d1到d2之间）
            if eval_start_idx is not None and eval_end_idx is not None:
                processed_values = values_full[eval_start_idx:eval_end_idx] / 1000.0
            else:
                processed_values = values_full / 1000.0
            
            # 赋值：Z_deviation的形状是(num_d_points_eval, num_profiles)
            # 第i个profile的数据应该放在第i列，所有行
            if len(processed_values) == num_d_points_eval and i < num_profiles:
                Z_deviation[:, i] = processed_values
                has_deviation_data = True
            else:
                logger.warning(f"Shape mismatch: processed_values.shape={processed_values.shape}, expected ({num_d_points_eval},), i={i}, num_profiles={num_profiles}")
        
        if not has_deviation_data:
            logger.warning(f"No deviation data for {side} flank, using zero deviation")
        
        # 实际表面 = 理论表面 + 偏差
        # 为了可视化误差，加入自适应夸大系数（当偏差过小难以看出）
        dev_max = float(np.max(np.abs(Z_deviation))) if Z_deviation.size else 0.0
        if dev_max > 1e-9:
            # 目标：偏差高度约占齿高的 1/5，可视化更清晰
            target_ratio = 0.2
            scale = (tooth_height * target_ratio) / dev_max if tooth_height > 0 else 1.0
            scale = max(1.0, min(scale, 50.0))  # 限制夸大倍数，避免过度失真
        else:
            scale = 1.0
        if scale > 1.0:
            logger.info(f"Topography deviation scaled by {scale:.2f}x for visibility")
        Z_actual = Z_theory + Z_deviation * scale
        
        # 仅用线条绘制：理论表面（蓝色）与偏差网格（红色）
        # 使用更稀疏、更细的网格线
        ax.plot_wireframe(X, Y, Z_theory, alpha=0.7, color='blue', linewidth=0.4, rstride=6, cstride=6)
        ax.plot_wireframe(X, Y, Z_actual, alpha=0.95, color='red', linewidth=0.3, rstride=6, cstride=6)
        
        # 不绘制齿面蓝色边界线（按需求去除）
    
    def _draw_theoretical_flank_only(self, ax, side: str, face_width: float, beta: float,
                                     root_diameter: float, tip_diameter: float, tooth_height: float):
        """
        仅绘制理论齿面（当没有topography数据时）
        """
        import numpy as np
        import math
        
        # 创建理论齿面网格
        num_y_points = 30  # 齿廓方向点数
        num_x_points = 20  # 齿宽方向点数
        
        # Y坐标：从齿根到齿顶
        y_values = np.linspace(0, tooth_height, num_y_points)
        
        # X坐标：齿宽方向
        if face_width > 0:
            x_values = np.linspace(0, face_width, num_x_points)
        else:
            x_values = np.linspace(0, 10.0, num_x_points)
        
        # 创建网格
        X, Y = np.meshgrid(x_values, y_values)
        
        # 根据side调整X位置
        if side == 'left':
            X = X - face_width * 0.6 if face_width > 0 else X - 5.0
        else:  # right
            X = X + face_width * 0.6 if face_width > 0 else X + 5.0
        
        # 应用螺旋角扭曲
        if abs(beta) > 0.001 and face_width > 0:
            Y_range = Y.max() - Y.min()
            if Y_range > 1e-10:
                Y_norm = (Y - Y.min()) / Y_range
                twist_amount = Y_norm * face_width * np.tan(beta) * 0.1
                X = X + twist_amount
        
        # Z坐标：理论表面高度
        Z_theory = Y
        
        # 绘制理论表面（蓝色）
        try:
            ax.plot_surface(X, Y, Z_theory, alpha=0.4, color='blue', linewidth=0.1, edgecolor='blue', shade=True)
        except Exception as e:
            logger.error(f"Error plotting theoretical {side} flank: {e}")
    
    def _draw_3d_flank_surface(self, ax, side_data: Dict, side: str, measurement_data, 
                              base_circle_db: float, face_width: float, beta: float, is_real_data: bool):
        """
        绘制3D齿面（理论表面+Topography偏差）
        """
        import numpy as np
        import math
        
        # 提取topography数据
        is_new_format = isinstance(side_data, dict) and ('profiles' in side_data or 'flank_lines' in side_data)
        profiles = None
        
        if is_new_format:
            profiles = side_data.get('profiles', {})
            if not profiles or not isinstance(profiles, dict):
                flank_lines = side_data.get('flank_lines', {})
                if flank_lines and isinstance(flank_lines, dict):
                    profiles = {}
                    for idx, flank in flank_lines.items():
                        if isinstance(flank, dict) and 'values' in flank:
                            profiles[idx] = {
                                'z': flank.get('d', float(idx)),
                                'values': flank['values']
                            }
        
        if not profiles or not isinstance(profiles, dict):
            return
        
        profile_indices = sorted(profiles.keys())
        z_values = []
        valid_profiles = {}
        for idx in profile_indices:
            profile = profiles[idx]
            if isinstance(profile, dict) and 'values' in profile:
                z_val = profile.get('z', float(idx))
                z_values.append(z_val)
                valid_profiles[idx] = profile
        
        if not valid_profiles:
            return
        
        # 检查所有profile的点数，找到最大点数
        all_point_counts = []
        for idx in profile_indices:
            profile = valid_profiles[idx]
            values = profile.get('values', [])
            if values:
                all_point_counts.append(len(values))
        
        if not all_point_counts:
            return
        
        # 使用最大点数作为标准点数
        num_d_points = max(all_point_counts)
        min_points = min(all_point_counts)
        
        if num_d_points != min_points:
            logger.warning(f"Profile point counts vary: min={min_points}, max={num_d_points}, using max for {side} flank")
        
        # 计算理论齿面的X坐标（渐开线）
        # 使用profile markers确定范围
        info = measurement_data.basic_info
        if side == 'left':
            profile_markers = getattr(info, 'profile_markers_left', None)
        else:
            profile_markers = getattr(info, 'profile_markers_right', None)
        
        if profile_markers and len(profile_markers) >= 4:
            da, d1, d2, de = profile_markers
            root_dia = max(da, d1, d2, de)
            tip_dia = min(da, d1, d2, de)
        else:
            root_dia = base_circle_db + 3.0
            tip_dia = base_circle_db - 3.0
        
        # 计算渐开线X坐标
        if base_circle_db > 0 and root_dia > base_circle_db:
            inv_alpha_root = math.sqrt((root_dia / base_circle_db)**2 - 1) if root_dia > base_circle_db else 0
            inv_alpha_tip = math.sqrt((tip_dia / base_circle_db)**2 - 1) if tip_dia > base_circle_db else 0
            if inv_alpha_root > 0 or inv_alpha_tip > 0:
                inv_alpha_values = np.linspace(inv_alpha_root, inv_alpha_tip, num_d_points)
                x_values = base_circle_db * np.sqrt(1 + inv_alpha_values**2)
            else:
                x_values = np.linspace(root_dia, tip_dia, num_d_points)
        else:
            x_values = np.linspace(root_dia, tip_dia, num_d_points)
        
        # 根据side调整X值方向和位置，使左右齿面形成完整的单齿形状
        # 左齿面：X值从负到0（左侧到中间）
        # 右齿面：X值从0到正（中间到右侧）
        # 这样左右齿面会在中间（X=0）汇合，形成齿顶
        
        if side == 'right':
            x_values = x_values[::-1]  # Right: Root to Tip
            # 右齿面：X值从0开始（中间）到正（右侧）
            x_values = x_values - x_values[0]  # 将最小值移到0
            x_values = x_values + 0.1  # 稍微偏移，避免与左齿面重叠
        else:  # left
            # 左齿面：X值从负（左侧）到0（中间）
            x_values = x_values - x_values[-1]  # 将最大值移到0
            x_values = x_values - 0.1  # 稍微偏移，避免与右齿面重叠
        
        # 创建Y坐标（齿宽方向）
        if face_width > 0:
            y_values = np.linspace(0, face_width, len(z_values))
        else:
            y_values = np.array(z_values)
        
        # 创建网格
        X, Y = np.meshgrid(x_values, y_values)
        
        # 应用螺旋角扭曲
        if abs(beta) > 0.001 and face_width > 0:
            Y_range = Y.max() - Y.min()
            if Y_range > 1e-10:
                Y_norm = (Y - Y.min()) / Y_range
                twist_amount = Y_norm * face_width * np.tan(beta) * 0.1
                X = X + twist_amount
        
        # 计算理论表面Z值（理论表面Z=0）
        Z_theory = np.zeros_like(X)
        
        # 提取Topography偏差数据
        Z_deviation = np.zeros_like(X)
        has_deviation_data = False
        
        # 检查是否需要插值
        try:
            from scipy.interpolate import interp1d
            has_scipy = True
        except ImportError:
            has_scipy = False
        
        for i, idx in enumerate(profile_indices):
            if i >= len(Z_deviation):
                logger.warning(f"Profile index {i} exceeds Z_deviation rows ({len(Z_deviation)}), skipping")
                continue
                
            profile = valid_profiles[idx]
            values = profile.get('values', [])
            
            if not values:
                continue
            
            values_array = np.array(values)
            values_len = len(values_array)
            
            if values_len == num_d_points:
                # 长度匹配，直接使用
                Z_deviation[i, :] = values_array / 1000.0
                has_deviation_data = True
            elif values_len > num_d_points:
                # 长度大于标准点数，截断
                logger.debug(f"Profile {idx} has {values_len} points, truncating to {num_d_points}")
                Z_deviation[i, :] = values_array[:num_d_points] / 1000.0
                has_deviation_data = True
            elif values_len < num_d_points:
                # 长度小于标准点数，需要插值或填充
                if has_scipy and values_len > 1:
                    try:
                        x_old = np.linspace(0, 1, values_len)
                        x_new = np.linspace(0, 1, num_d_points)
                        interp_func = interp1d(x_old, values_array, kind='linear', 
                                             bounds_error=False, fill_value='extrapolate')
                        values_interp = interp_func(x_new)
                        Z_deviation[i, :] = values_interp / 1000.0
                        has_deviation_data = True
                        logger.debug(f"Profile {idx} interpolated from {values_len} to {num_d_points} points")
                    except Exception as e:
                        logger.warning(f"Interpolation failed for profile {idx}: {e}, using padding")
                        # 插值失败，使用零填充
                        padded = np.pad(values_array, (0, num_d_points - values_len), mode='constant')
                        Z_deviation[i, :] = padded / 1000.0
                        has_deviation_data = True
                else:
                    # 没有scipy或点数太少，使用零填充
                    padded = np.pad(values_array, (0, num_d_points - values_len), mode='constant')
                    Z_deviation[i, :] = padded / 1000.0
                    has_deviation_data = True
                    logger.debug(f"Profile {idx} padded from {values_len} to {num_d_points} points")
        
        if not has_deviation_data:
            logger.warning(f"No deviation data for {side} flank, using zero deviation")
        
        # 实际表面 = 理论表面 + 偏差
        Z_actual = Z_theory + Z_deviation
        
        # 绘制理论表面（蓝色，半透明）
        ax.plot_surface(X, Y, Z_theory, alpha=0.4, color='blue', linewidth=0.1, edgecolor='blue', shade=True)
        
        # 绘制Topography偏差网格（黑色，叠加在理论表面上）
        ax.plot_wireframe(X, Y, Z_actual, alpha=0.9, color='black', linewidth=0.2, rstride=4, cstride=4)
        
        # 不绘制齿面蓝色边界线（按需求去除）
    
    def _draw_complete_3d_tip(self, ax, measurement_data, face_width: float, beta: float,
                             root_diameter: float, tip_diameter: float, tooth_height: float):
        """
        绘制完整的3D齿顶表面（顶部，连接左右齿面）
        - 齿顶在Z=tooth_height处
        - 连接左右齿面
        """
        import numpy as np
        import math
        
        if tooth_height <= 0:
            logger.warning(f"Invalid tooth_height: {tooth_height}, skipping tip")
            return
        
        info = measurement_data.basic_info
        
        # 创建齿顶网格
        num_tip_points = 20
        num_x_points = 30
        
        # X坐标：齿宽方向，从左侧到右侧
        x_tip = np.linspace(-face_width * 0.6 if face_width > 0 else -5.0, 
                           face_width * 0.6 if face_width > 0 else 5.0, num_x_points)
        # Y坐标：齿顶宽度（较小，在顶部）
        y_tip = np.linspace(tooth_height * 0.95, tooth_height, num_tip_points)
        
        X_tip, Y_tip = np.meshgrid(x_tip, y_tip)
        # Z坐标：齿顶高度（理论表面）
        Z_tip = np.full_like(X_tip, tooth_height)
        
        # 应用螺旋角扭曲
        if abs(beta) > 0.001 and face_width > 0:
            X_range = X_tip.max() - X_tip.min()
            if X_range > 1e-10:
                X_norm = (X_tip - X_tip.min()) / X_range
                twist_amount = X_norm * face_width * np.tan(beta) * 0.1
                Y_tip = Y_tip + twist_amount
        
        # 绘制齿顶线框（不填充底色）
        try:
            ax.plot_wireframe(X_tip, Y_tip, Z_tip, color='blue', linewidth=0.3, rstride=2, cstride=2, alpha=0.9)
            
            # 绘制齿顶轮廓线，突出单齿形状
            ax.plot(X_tip[0, :], Y_tip[0, :], Z_tip[0, :], 'b-', linewidth=0.6, alpha=0.9)  # 前轮廓
            ax.plot(X_tip[-1, :], Y_tip[-1, :], Z_tip[-1, :], 'b-', linewidth=0.6, alpha=0.9)  # 后轮廓
            ax.plot(X_tip[:, 0], Y_tip[:, 0], Z_tip[:, 0], 'b-', linewidth=0.6, alpha=0.9)  # 左轮廓
            ax.plot(X_tip[:, -1], Y_tip[:, -1], Z_tip[:, -1], 'b-', linewidth=0.6, alpha=0.9)  # 右轮廓
        except Exception as e:
            logger.error(f"Error drawing tip surface: {e}")
    
    def _draw_complete_3d_root(self, ax, measurement_data, face_width: float, beta: float,
                              root_diameter: float, tip_diameter: float):
        """
        绘制完整的3D齿根表面（底部，连接左右齿面）
        - 齿根在Z=0处
        - 连接左右齿面
        """
        import numpy as np
        import math
        
        info = measurement_data.basic_info
        
        # 创建齿根网格
        num_root_points = 20
        num_x_points = 30
        
        # X坐标：齿宽方向，从左侧到右侧
        x_root = np.linspace(-face_width * 0.6 if face_width > 0 else -5.0, 
                            face_width * 0.6 if face_width > 0 else 5.0, num_x_points)
        # Y坐标：齿根宽度（较小，在底部）
        root_width = (tip_diameter - root_diameter) / 2.0 * 0.05 if tip_diameter > root_diameter else 0.5
        y_root = np.linspace(0, root_width, num_root_points)
        
        X_root, Y_root = np.meshgrid(x_root, y_root)
        # Z坐标：齿根高度（Z=0）
        Z_root = np.zeros_like(X_root)
        
        # 应用螺旋角扭曲
        if abs(beta) > 0.001 and face_width > 0:
            X_range = X_root.max() - X_root.min()
            if X_range > 1e-10:
                X_norm = (X_root - X_root.min()) / X_range
                twist_amount = X_norm * face_width * np.tan(beta) * 0.1
                Y_root = Y_root + twist_amount
        
        # 绘制齿根线框（不填充底色）
        try:
            ax.plot_wireframe(X_root, Y_root, Z_root, color='blue', linewidth=0.3, rstride=2, cstride=2, alpha=0.9)
            
            # 绘制齿根轮廓线，突出单齿形状
            ax.plot(X_root[0, :], Y_root[0, :], Z_root[0, :], 'b-', linewidth=0.6, alpha=0.9)  # 前轮廓
            ax.plot(X_root[-1, :], Y_root[-1, :], Z_root[-1, :], 'b-', linewidth=0.6, alpha=0.9)  # 后轮廓
            ax.plot(X_root[:, 0], Y_root[:, 0], Z_root[:, 0], 'b-', linewidth=0.6, alpha=0.9)  # 左轮廓
            ax.plot(X_root[:, -1], Y_root[:, -1], Z_root[:, -1], 'b-', linewidth=0.6, alpha=0.9)  # 右轮廓
        except Exception as e:
            logger.error(f"Error drawing root surface: {e}")
    
    def _create_complete_tooth_plot(self, ax, tooth_data: Dict, measurement_data, is_real_data: bool = True):
        """
        创建完整单个齿的3D图（左齿面+右齿面）
        - 理论表面：蓝色
        - Topography网格：黑色，叠加在理论表面上
        - 左齿面的Topography网格附在左齿面上
        - 右齿面的Topography网格附在右齿面上
        """
        import numpy as np
        import math
        
        # 先绘制左齿面，然后绘制右齿面，在同一个图表中
        # 左齿面在左侧，右齿面在右侧，中间是齿顶
        
        # 获取左右齿面数据
        left_data = tooth_data.get('left', {})
        right_data = tooth_data.get('right', {})
        
        # 计算左右齿面的位置偏移
        # 左齿面在左侧，右齿面在右侧，中间留出齿顶空间
        
        # 先绘制左齿面的理论表面和topography网格（左侧，齿顶在右侧）
        if left_data:
            self._create_3d_wireframe_plot(ax, left_data, "left", measurement_data, 
                                          is_real_data=is_real_data, x_offset=-1.0)
        
        # 再绘制右齿面的理论表面和topography网格（右侧，齿顶在左侧）
        if right_data:
            self._create_3d_wireframe_plot(ax, right_data, "right", measurement_data, 
                                          is_real_data=is_real_data, x_offset=1.0)
        
        # 在中间绘制共用的齿顶区域（连接左右齿面）
        self._create_tip_connection(ax, left_data, right_data, measurement_data, is_real_data)
    
    def _create_tip_connection(self, ax, left_data: Dict, right_data: Dict, measurement_data, is_real_data: bool = True):
        """
        创建齿顶连接区域，连接左齿面和右齿面
        - 理论表面：蓝色
        - Topography网格：黑色（如果有数据）
        """
        import numpy as np
        import math
        
        # 获取齿轮参数
        info = measurement_data.basic_info
        face_width = getattr(info, 'width', 0.0)
        helix_angle_deg = getattr(info, 'helix_angle', 0.0)
        helix_angle_rad = np.radians(helix_angle_deg) if helix_angle_deg else 0.0
        
        # 计算齿顶区域的Y轴范围（齿宽方向）
        # 使用左右齿面的Y轴范围
        y_min = 0.0
        y_max = face_width if face_width > 0 else 10.0
        
        # 创建齿顶区域的网格
        # 齿顶在中间，宽度较小
        tip_width = 0.1  # 齿顶宽度（归一化）
        num_tip_points = 10  # 齿顶方向的点数
        num_y_points = 20  # 齿宽方向的点数
        
        y_tip = np.linspace(y_min, y_max, num_y_points)
        x_tip = np.linspace(-tip_width/2, tip_width/2, num_tip_points)
        
        X_tip, Y_tip = np.meshgrid(x_tip, y_tip)
        Z_tip = np.zeros_like(X_tip)  # 理论表面Z=0
        
        # 应用螺旋角扭曲
        if abs(helix_angle_rad) > 0.001 and face_width > 0:
            Y_range = Y_tip.max() - Y_tip.min()
            if Y_range > 1e-10:
                Y_norm = (Y_tip - Y_tip.min()) / Y_range
                twist_amount = Y_norm * face_width * np.tan(helix_angle_rad) * 0.05
                X_tip = X_tip + twist_amount
        
        # 归一化和投影
        x_min, x_max = X_tip.min(), X_tip.max()
        y_min, y_max = Y_tip.min(), Y_tip.max()
        x_range = x_max - x_min if x_max > x_min else 1.0
        y_range = y_max - y_min if y_max > y_min else 1.0
        
        X_tip_norm = (X_tip - x_min) / x_range if x_range > 0 else X_tip
        Y_tip_norm = (Y_tip - y_min) / y_range if y_range > 0 else Y_tip
        Z_tip_norm = Z_tip  # Z=0，不需要归一化
        
        # 等轴测投影
        iso_angle = np.radians(30)
        cos_iso = np.cos(iso_angle)
        sin_iso = np.sin(iso_angle)
        
        X_tip_proj = X_tip_norm * cos_iso - Y_tip_norm * cos_iso
        Y_tip_proj = X_tip_norm * sin_iso + Y_tip_norm * sin_iso - Z_tip_norm * 0.5
        
        # 绘制齿顶的理论表面（蓝色）
        num_rows_tip = len(Y_tip)
        num_cols_tip = len(X_tip[0])
        rstride_tip = max(1, num_rows_tip // 10)
        cstride_tip = max(1, num_cols_tip // 5)
        
        # 绘制理论表面的行线
        for i in range(0, num_rows_tip, rstride_tip):
            if i < len(X_tip_proj):
                ax.plot(X_tip_proj[i, :], Y_tip_proj[i, :], 
                       color='blue', linewidth=0.5, alpha=0.8, zorder=1)
        
        # 绘制理论表面的列线
        for j in range(0, num_cols_tip, cstride_tip):
            if j < len(X_tip_proj[0]):
                ax.plot(X_tip_proj[:, j], Y_tip_proj[:, j], 
                       color='blue', linewidth=0.5, alpha=0.8, zorder=1)
    
    def _create_3d_wireframe_plot(self, ax, side_data: Dict, side: str, data, is_real_data: bool = True, 
                                   x_offset: float = 0.0, connect_to_tip: bool = False, tip_side: str = 'center'):
        """
        创建3D线框图 - 彻底重构版本
        根据参考图要求：
        - Right flank（左图）：Root在左侧，Tip在中间
        - Left flank（右图）：Tip在中间，Root在右侧
        使用等轴测投影（120度角）实现3D效果
        """
        import numpy as np
        import math
        
        # ========== 1. 数据加载和验证 ==========
        is_new_format = isinstance(side_data, dict) and ('profiles' in side_data or 'flank_lines' in side_data)
        profiles = None
        flank_lines = None
        
        if is_new_format:
            profiles = side_data.get('profiles', {})
            flank_lines = side_data.get('flank_lines', {})
            
            if not profiles or not isinstance(profiles, dict):
                if flank_lines and isinstance(flank_lines, dict):
                    profiles = {}
                    for idx, flank in flank_lines.items():
                        if isinstance(flank, dict) and 'values' in flank:
                            profiles[idx] = {
                                'z': flank.get('d', float(idx)),
                                'values': flank['values']
                            }
            
            if not profiles:
                self._create_empty_3d_plot(ax, f"{side.capitalize()} Flank: No Data")
                return
            
            profile_indices = sorted(profiles.keys())
            z_values = []
            valid_profiles = {}
            for idx in profile_indices:
                profile = profiles[idx]
                if isinstance(profile, dict) and 'values' in profile:
                    z_val = profile.get('z', float(idx))
                    z_values.append(z_val)
                    valid_profiles[idx] = profile
            
            if not valid_profiles:
                self._create_empty_3d_plot(ax, f"{side.capitalize()} Flank: No Data")
                return
            
            profile_indices = sorted(valid_profiles.keys())
            profiles = valid_profiles
            
            # 检查所有profile的点数，找到最大点数
            all_point_counts = []
            for idx in profile_indices:
                profile = profiles[idx]
                values = profile.get('values', [])
                if values:
                    all_point_counts.append(len(values))
            
            if not all_point_counts:
                self._create_empty_3d_plot(ax, f"{side.capitalize()} Flank: No Data")
                return
            
            # 使用最大点数作为标准点数
            num_d_points_orig = max(all_point_counts)
            min_points = min(all_point_counts)
            
            if num_d_points_orig != min_points:
                logger.warning(f"Profile point counts vary: min={min_points}, max={num_d_points_orig}, using max for {side} flank in wireframe")
            
        else:
            # 旧格式
            if not isinstance(side_data, dict) or not side_data:
                self._create_empty_3d_plot(ax, f"{side.capitalize()} Flank: No Data")
                return
            
            profile_indices = sorted(side_data.keys())
            if not profile_indices:
                self._create_empty_3d_plot(ax, f"{side.capitalize()} Flank: No Data")
                return
            
            # 检查所有profile的点数，找到最大点数
            all_point_counts = []
            for idx in profile_indices:
                vals = side_data.get(idx, [])
                if isinstance(vals, (list, tuple, np.ndarray)) and len(vals) > 0:
                    all_point_counts.append(len(vals))
            
            if not all_point_counts:
                self._create_empty_3d_plot(ax, f"{side.capitalize()} Flank: Invalid Data Format")
                return
            
            # 使用最大点数作为标准点数
            num_d_points_orig = max(all_point_counts)
            min_points = min(all_point_counts)
            
            if num_d_points_orig != min_points:
                logger.warning(f"Profile point counts vary: min={min_points}, max={num_d_points_orig}, using max for {side} flank in wireframe (old format)")
            
            z_values = [float(idx) for idx in profile_indices]
        
        # ========== 2. 计算X轴（齿廓方向） ==========
        info = data.basic_info
        
        helix_angle_deg = getattr(info, 'helix_angle', 0.0)
        helix_angle_rad = np.radians(helix_angle_deg) if helix_angle_deg else 0.0
        module = getattr(info, 'module', 0.0)
        teeth = getattr(info, 'teeth', 0)
        pressure_angle_deg = getattr(info, 'pressure_angle', 20.0)
        base_circle_db = getattr(info, 'base_circle_db', 0.0)
        
        if base_circle_db == 0.0 and module > 0 and teeth > 0 and pressure_angle_deg > 0:
            try:
                alpha_n = math.radians(pressure_angle_deg)
                beta = helix_angle_rad
                alpha_t = math.atan(math.tan(alpha_n) / math.cos(beta)) if beta != 0 else alpha_n
                d_pitch = teeth * module / math.cos(beta) if beta != 0 else teeth * module
                base_circle_db = d_pitch * math.cos(alpha_t)
            except:
                base_circle_db = 0.0
        
        profile_markers = None
        if side == 'left' and hasattr(info, 'profile_markers_left'):
            profile_markers = info.profile_markers_left
        elif side == 'right' and hasattr(info, 'profile_markers_right'):
            profile_markers = info.profile_markers_right
        
        if profile_markers and len(profile_markers) >= 4:
            da, d1, d2, de = profile_markers
            current_profile_markers = {'da': da, 'd1': d1, 'd2': d2, 'de': de}
            root_dia = max(da, d1, d2, de)
            tip_dia = min(da, d1, d2, de)
        else:
            d_ref = 48.593
            if is_new_format:
                flank_lines = side_data.get('flank_lines', {})
                if flank_lines and isinstance(flank_lines, dict) and len(flank_lines) > 0:
                    first_flank = flank_lines[sorted(flank_lines.keys())[0]]
                    if isinstance(first_flank, dict) and 'd' in first_flank:
                        d_ref = first_flank.get('d', d_ref)
            root_dia = d_ref + 3.0
            tip_dia = d_ref - 3.0
            current_profile_markers = None
        
        if base_circle_db > 0 and root_dia > base_circle_db:
            inv_alpha_root = math.sqrt((root_dia / base_circle_db)**2 - 1) if root_dia > base_circle_db else 0
            inv_alpha_tip = math.sqrt((tip_dia / base_circle_db)**2 - 1) if tip_dia > base_circle_db else 0
            if inv_alpha_root > 0 or inv_alpha_tip > 0:
                inv_alpha_values = np.linspace(inv_alpha_root, inv_alpha_tip, num_d_points_orig)
                x_values_orig = base_circle_db * np.sqrt(1 + inv_alpha_values**2)
            else:
                x_values_orig = np.linspace(root_dia, tip_dia, num_d_points_orig)
        else:
            x_values_orig = np.linspace(root_dia, tip_dia, num_d_points_orig)
        
        # ========== 3. 重构X轴：使Tip在中间 ==========
        if side == 'right':
            x_values_right = x_values_orig[::-1][1:]
            x_values = np.concatenate([x_values_orig, x_values_right])
        else:  # left
            x_values_left = x_values_orig[::-1][1:]
            x_values = np.concatenate([x_values_left, x_values_orig])
        
        num_d_points = len(x_values)
        current_x_values = x_values
        
        # ========== 4. 处理Y轴（齿宽方向） ==========
        if len(z_values) > 1 and z_values[0] > z_values[-1]:
            z_values = z_values[::-1]
            profile_indices = profile_indices[::-1]
            if is_new_format and profiles is not None:
                profiles = {idx: profiles[idx] for idx in profile_indices}
            
        # ========== 5. 构建网格和Z矩阵 ==========
        X_base, Y_base = np.meshgrid(x_values, z_values)
        
        # 应用X轴偏移（用于在完整齿图中定位左右齿面）
        if x_offset != 0.0:
            X_base = X_base + x_offset
        
        if abs(helix_angle_rad) > 0.001:
            face_width = getattr(info, 'width', 0.0)
            if face_width > 0:
                Y_range = Y_base.max() - Y_base.min()
                if Y_range > 1e-10:
                    Y_norm = (Y_base - Y_base.min()) / Y_range
                    twist_amount = Y_norm * face_width * np.tan(helix_angle_rad) * 0.05
                    X = X_base + twist_amount
                else:
                    X = X_base
            else:
                X = X_base
        else:
            X = X_base
        
        Y = Y_base
        
        num_profiles = len(profile_indices)
        Z = np.zeros((num_profiles, num_d_points))
        UNDEFINED = -2147483.648
        has_valid_data = False
        
        for i, idx in enumerate(profile_indices):
            if is_new_format:
                profile = profiles[idx]
                vals = profile.get('values', [])
            else:
                vals = side_data.get(idx, [])
            
            if not vals or not isinstance(vals, (list, tuple, np.ndarray)):
                continue
            
            values_len = len(vals)
            
            # 处理长度不匹配：使用插值或填充
            if values_len == num_d_points_orig:
                # 长度匹配，直接使用
                pass
            elif values_len > num_d_points_orig:
                # 长度大于标准点数，截断
                logger.debug(f"Profile {idx} has {values_len} points, truncating to {num_d_points_orig} in wireframe")
                vals = vals[:num_d_points_orig]
            elif values_len < num_d_points_orig:
                # 长度小于标准点数，需要插值或填充
                try:
                    from scipy.interpolate import interp1d
                    if values_len > 1:
                        # 使用插值扩展到标准点数
                        x_old = np.linspace(0, 1, values_len)
                        x_new = np.linspace(0, 1, num_d_points_orig)
                        interp_func = interp1d(x_old, np.array(vals), kind='linear', 
                                             bounds_error=False, fill_value='extrapolate')
                        vals = interp_func(x_new).tolist()
                        logger.debug(f"Profile {idx} interpolated from {values_len} to {num_d_points_orig} points in wireframe")
                    else:
                        # 点数太少，使用零填充
                        vals = list(vals) + [0.0] * (num_d_points_orig - values_len)
                except ImportError:
                    # 没有scipy，使用零填充
                    vals = list(vals) + [0.0] * (num_d_points_orig - values_len)
                except Exception as e:
                    logger.warning(f"Interpolation failed for profile {idx} in wireframe: {e}, using padding")
                    # 插值失败，使用零填充
                    vals = list(vals) + [0.0] * (num_d_points_orig - values_len)
            
            filtered_vals = []
            for v in vals:
                try:
                    v_float = float(v)
                    if abs(v_float - UNDEFINED) < 1.0:
                        filtered_vals.append(0.0)
                    else:
                        filtered_vals.append(v_float)
                        has_valid_data = True
                except Exception:
                    filtered_vals.append(0.0)
            
            if side == 'right':
                filtered_vals_right = filtered_vals[::-1][1:]
                z_row = np.concatenate([filtered_vals, filtered_vals_right])
            else:  # left
                filtered_vals_left = filtered_vals[::-1][1:]
                z_row = np.concatenate([filtered_vals_left, filtered_vals])
            
            if len(z_row) > num_d_points:
                z_row = z_row[:num_d_points]
            elif len(z_row) < num_d_points:
                z_row = np.concatenate([z_row, [0.0] * (num_d_points - len(z_row))])
            
            Z[i, :] = z_row
        
        if not has_valid_data:
            self._create_empty_3d_plot(ax, f"{side.capitalize()} Flank: No Valid Data")
            return
        
        # 计算Z的范围用于显示 - 增强3D效果
        z_max = np.max(np.abs(Z))
        if z_max == 0: 
            z_max = 1.0
        else:
            # 增加Z轴范围，使3D效果更明显
            z_max = z_max * 1.5  # 增加边距，使偏差更明显
        
        # Plot wireframe - 计算合适的网格步长，避免过于密集
        num_rows = len(Y) if len(Y) > 0 else 1
        num_cols = len(X[0]) if len(X) > 0 and len(X[0]) > 0 else 1
        
        # 计算合适的网格步长，确保网格线密度适中，接近参考图片的样式
        # 参照参考图：使用更密集的网格，显示更多细节
        rstride_val = max(1, num_rows // 20)  # 增加密度，最多显示20行
        cstride_val = max(1, num_cols // 25)  # 增加密度，最多显示25列
        
        # 如果数据点较少，使用更小的步长
        if num_rows < 20:
            rstride_val = 1
        if num_cols < 25:
            cstride_val = 1
        
        # 重构：使用等轴测投影（Isometric Projection）实现3D效果
        # 等轴测投影：X和Y轴夹角为120度，Z轴垂直
        # 投影公式：
        # X_proj = X * cos(30°) - Y * cos(30°)
        # Y_proj = X * sin(30°) + Y * sin(30°) - Z
        
        # 归一化X, Y, Z到合理范围，保持比例
        x_min, x_max = X.min(), X.max()
        y_min, y_max = Y.min(), Y.max()
        x_range = x_max - x_min if x_max > x_min else 1.0
        y_range = y_max - y_min if y_max > y_min else 1.0
        
        # ========== 6. 计算理论3D表面 ==========
        # 理论表面：基于渐开线和螺旋角，Z=0（无偏差）
        # 使用相同的X和Y网格，但Z_theory = 0（理论表面是平的）
        Z_theory = np.zeros_like(Z)
        
        # ========== 7. 等轴测投影 ==========
        # 归一化坐标到[0, 1]范围
        X_norm = (X - x_min) / x_range if x_range > 0 else X
        Y_norm = (Y - y_min) / y_range if y_range > 0 else Y
        Z_norm = Z / z_max if z_max > 0 else Z
        Z_theory_norm = Z_theory / z_max if z_max > 0 else Z_theory
        
        # 等轴测投影角度（30度）
        iso_angle = np.radians(30)
        cos_iso = np.cos(iso_angle)
        sin_iso = np.sin(iso_angle)
        
        # 理论表面的投影（Z=0，无偏差）
        X_theory_proj = X_norm * cos_iso - Y_norm * cos_iso
        Y_theory_proj = X_norm * sin_iso + Y_norm * sin_iso - Z_theory_norm * 0.5
        
        # Topography网格的投影（理论表面 + 偏差）
        X_proj = X_norm * cos_iso - Y_norm * cos_iso
        Y_proj = X_norm * sin_iso + Y_norm * sin_iso - Z_norm * 0.5
        
        # 计算投影范围（合并理论表面和topography网格的范围）
        try:
            x_proj_min = min(X_theory_proj.min(), X_proj.min())
            x_proj_max = max(X_theory_proj.max(), X_proj.max())
            y_proj_min = min(Y_theory_proj.min(), Y_proj.min())
            y_proj_max = max(Y_theory_proj.max(), Y_proj.max())
            x_proj_range = x_proj_max - x_proj_min if x_proj_max > x_proj_min else 1.0
            y_proj_range = y_proj_max - y_proj_min if y_proj_max > y_proj_min else 1.0
        except Exception as e:
            logger.error(f"计算投影范围失败: {e}")
            # 使用默认范围
            x_proj_min, x_proj_max = -1.0, 1.0
            y_proj_min, y_proj_max = -1.0, 1.0
            x_proj_range = 2.0
            y_proj_range = 2.0
        
        # ========== 8. 绘制理论3D表面（单个齿的理论齿面） ==========
        # 先绘制理论表面（蓝色，作为单个齿的理论齿面）
        if num_rows == 0 or num_cols == 0:
            logger.warning(f"Empty data: num_rows={num_rows}, num_cols={num_cols}")
            return
        
        # 绘制理论表面的行线（沿X方向，即齿廓方向）
        for i in range(0, num_rows, rstride_val):
            if i < len(X_theory_proj):
                ax.plot(X_theory_proj[i, :], Y_theory_proj[i, :], 
                       color='blue', linewidth=0.5, alpha=0.8, zorder=1)
        
        # 绘制理论表面的列线（沿Y方向，即齿宽方向）
        for j in range(0, num_cols, cstride_val):
            if j < len(X_theory_proj[0]):
                ax.plot(X_theory_proj[:, j], Y_theory_proj[:, j], 
                       color='blue', linewidth=0.5, alpha=0.8, zorder=1)
        
        # ========== 9. 绘制Topography网格（叠加在理论表面上） ==========
        # 绘制topography网格的行线（沿X方向，即齿廓方向）
        lines_drawn = 0
        for i in range(0, num_rows, rstride_val):
            if i < len(X_proj):
                ax.plot(X_proj[i, :], Y_proj[i, :], 'k-', linewidth=0.2, alpha=1.0, zorder=2)
                lines_drawn += 1
        
        # 绘制topography网格的列线（沿Y方向，即齿宽方向）
        for j in range(0, num_cols, cstride_val):
            if j < len(X_proj[0]):
                ax.plot(X_proj[:, j], Y_proj[:, j], 'k-', linewidth=0.2, alpha=1.0, zorder=2)
                lines_drawn += 1
        
        if lines_drawn == 0:
            logger.warning(f"No lines drawn: num_rows={num_rows}, num_cols={num_cols}, rstride={rstride_val}, cstride={cstride_val}")
        
        # 设置2D坐标轴范围
        
        margin_ratio = 0.05
        ax.set_xlim(x_proj_min - x_proj_range * margin_ratio, x_proj_max + x_proj_range * margin_ratio)
        ax.set_ylim(y_proj_min - y_proj_range * margin_ratio, y_proj_max + y_proj_range * margin_ratio)
        
        # 隐藏3D坐标轴，因为我们现在使用2D投影
        ax.set_axis_off()
        
        # 设置背景为白色
        ax.set_facecolor('white')
        
        # 添加标签 - 准确标出齿顶和齿根
        # 重构后：X轴是对称分布，Tip在中间，Root在两侧
        
        # 找到X轴中间位置（对应齿顶）
        x_mid_idx = num_cols // 2  # X轴中间索引
        if x_mid_idx < num_cols:
            # 获取中间列的投影坐标
            tip_x_proj = X_proj[:, x_mid_idx].mean()  # 中间列的平均X投影
            tip_y_proj = Y_proj.max()  # 顶部
        else:
            tip_x_proj = (X_proj.min() + X_proj.max()) / 2
            tip_y_proj = Y_proj.max()
        
        # Root位置：根据side和参考图确定
        # Right flank（左图）：Root在左侧（第一列），右侧是镜像的Root（但主要显示左侧的Root）
        # Left flank（右图）：左侧是镜像的Tip，Root在右侧（最后一列，主要显示右侧的Root）
        if side == 'right':
            # Right flank：主要显示左侧的Root
            root_left_x_proj = X_proj[:, 0].mean() if num_cols > 0 else X_proj.min()  # 左侧：X轴第一个点（root）
            root_right_x_proj = X_proj[:, -1].mean() if num_cols > 0 else X_proj.max()  # 右侧：镜像的root（不显示标签）
        else:  # side == 'left'
            # Left flank：主要显示右侧的Root
            root_left_x_proj = X_proj[:, 0].mean() if num_cols > 0 else X_proj.min()  # 左侧：镜像的tip（不显示标签）
            root_right_x_proj = X_proj[:, -1].mean() if num_cols > 0 else X_proj.max()  # 右侧：X轴最后一个点（root）
        
        root_y_proj = Y_proj.min()  # 底部
        
        # Bottom位置：X中间，Y最小（底部中央）
        bottom_x_proj = (X_proj.min() + X_proj.max()) / 2
        bottom_y_proj = Y_proj.min()
        
        # 中间位置（用于Profile/Load标签）
        mid_x_proj = X_proj.min()
        mid_y_proj = (Y_proj.min() + Y_proj.max()) / 2
        
        label_offset = x_proj_range * 0.15  # 标签偏移量
        
        if side == 'left':
            # 左齿面数据，显示在右图，标签"left flank"
            # 参照参考图：Tip在中间，Root在右侧
            # Tip: 在中间顶部
            ax.text(tip_x_proj, tip_y_proj + label_offset, "Tip", 
                    ha='center', va='bottom', fontsize=10, color='black', fontweight='bold')
            # Root: 在右侧底部（只显示右侧的Root）
            ax.text(root_right_x_proj + label_offset, root_y_proj, "Root", 
                    ha='left', va='center', fontsize=10, color='black', fontweight='bold')
            # Lead标签：在左侧垂直边缘，垂直显示（参照参考图）
            ax.text(mid_x_proj - label_offset*0.7, mid_y_proj, "Lead:F:S\n21466", 
                    ha='right', va='center', fontsize=8, color='black', rotation=0, fontweight='bold')
            # Bottom: 在底部中央
            ax.text(bottom_x_proj, bottom_y_proj - label_offset, "Bottom", 
                    ha='center', va='top', fontsize=10, color='black', fontweight='bold')
        else:
            # 右齿面数据，显示在左图，标签"right flank"
            # 参照参考图：Root在左侧，Tip在中间
            # Tip: 在中间顶部
            ax.text(tip_x_proj, tip_y_proj + label_offset, "Tip", 
                    ha='center', va='bottom', fontsize=10, color='black', fontweight='bold')
            # Root: 在左侧底部（只显示左侧的Root）
            ax.text(root_left_x_proj - label_offset, root_y_proj, "Root", 
                    ha='right', va='center', fontsize=10, color='black', fontweight='bold')
            # Profile标签：在左侧垂直边缘，垂直显示（参照参考图）
            ax.text(mid_x_proj - label_offset*0.7, mid_y_proj, "Profile:F:S\n21460", 
                    ha='right', va='center', fontsize=8, color='black', rotation=0, fontweight='bold')
            # Bottom: 在底部中央
            ax.text(bottom_x_proj, bottom_y_proj - label_offset, "Bottom", 
                    ha='center', va='top', fontsize=10, color='black', fontweight='bold')
            
            # 标注起测点、起评点、终评点、终测点 - 改进版本，更清晰明显
            if current_profile_markers and current_x_values is not None and len(current_x_values) > 0:
                markers = current_profile_markers
                x_vals = current_x_values
                
                # 找到每个marker在x_values中的索引位置
                def find_marker_index(marker_dia):
                    """找到marker直径在x_values中最接近的索引"""
                    if len(x_vals) == 0:
                        return None
                    # 计算每个x值与marker_dia的距离
                    distances = np.abs(x_vals - marker_dia)
                    idx = np.argmin(distances)
                    # 验证距离是否合理（如果距离太大，可能找不到对应的点）
                    min_distance = distances[idx]
                    if min_distance > (x_vals.max() - x_vals.min()) * 0.1:  # 如果距离超过范围的10%，认为找不到
                        return None
                    return idx
                
                # 找到各个marker的索引
                da_idx = find_marker_index(markers['da'])  # 起测点
                d1_idx = find_marker_index(markers['d1'])  # 起评点
                d2_idx = find_marker_index(markers['d2'])  # 终评点
                de_idx = find_marker_index(markers['de'])  # 终测点
                
                # 计算投影后的位置（使用多个行位置，使标注更明显）
                # 使用底部、中间、顶部三个位置来标注
                bottom_row_idx = 0
                mid_row_idx = num_rows // 2
                top_row_idx = num_rows - 1
                if mid_row_idx >= num_rows:
                    mid_row_idx = max(0, num_rows - 1)
                
                # 标注起测点（da）- 红色，在底部
                if da_idx is not None and da_idx < num_cols:
                    da_x_proj = X_proj[bottom_row_idx, da_idx]
                    da_y_proj = Y_proj[bottom_row_idx, da_idx]
                    # 绘制垂直线贯穿整个Y轴，使标注更明显
                    ax.plot([X_proj[0, da_idx], X_proj[-1, da_idx]], 
                            [Y_proj[0, da_idx], Y_proj[-1, da_idx]], 
                            'r--', linewidth=1.5, alpha=0.5, zorder=9)
                    # 绘制标记点
                    ax.plot(da_x_proj, da_y_proj, 'ro', markersize=8, markeredgecolor='darkred', 
                           markeredgewidth=2, zorder=11, label='起测点(da)')
                    # 添加文本标注，带背景框
                    ax.text(da_x_proj, da_y_proj - label_offset*0.8, "da\n起测点", 
                            ha='center', va='top', fontsize=9, color='red', fontweight='bold',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='red', linewidth=1.5),
                            zorder=12)
                
                # 标注起评点（d1）- 绿色，在中间偏下
                if d1_idx is not None and d1_idx < num_cols:
                    d1_row = max(0, num_rows // 4)  # 使用1/4位置
                    d1_x_proj = X_proj[d1_row, d1_idx]
                    d1_y_proj = Y_proj[d1_row, d1_idx]
                    # 绘制垂直线
                    ax.plot([X_proj[0, d1_idx], X_proj[-1, d1_idx]], 
                            [Y_proj[0, d1_idx], Y_proj[-1, d1_idx]], 
                            'g--', linewidth=1.5, alpha=0.5, zorder=9)
                    # 绘制标记点
                    ax.plot(d1_x_proj, d1_y_proj, 'go', markersize=8, markeredgecolor='darkgreen', 
                           markeredgewidth=2, zorder=11, label='起评点(d1)')
                    # 添加文本标注
                    ax.text(d1_x_proj, d1_y_proj - label_offset*0.8, "d1\n起评点", 
                            ha='center', va='top', fontsize=9, color='green', fontweight='bold',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='green', linewidth=1.5),
                            zorder=12)
                
                # 标注终评点（d2）- 蓝色，在中间偏上
                if d2_idx is not None and d2_idx < num_cols:
                    d2_row = min(num_rows - 1, num_rows * 3 // 4)  # 使用3/4位置
                    d2_x_proj = X_proj[d2_row, d2_idx]
                    d2_y_proj = Y_proj[d2_row, d2_idx]
                    # 绘制垂直线
                    ax.plot([X_proj[0, d2_idx], X_proj[-1, d2_idx]], 
                            [Y_proj[0, d2_idx], Y_proj[-1, d2_idx]], 
                            'b--', linewidth=1.5, alpha=0.5, zorder=9)
                    # 绘制标记点
                    ax.plot(d2_x_proj, d2_y_proj, 'bo', markersize=8, markeredgecolor='darkblue', 
                           markeredgewidth=2, zorder=11, label='终评点(d2)')
                    # 添加文本标注
                    ax.text(d2_x_proj, d2_y_proj - label_offset*0.8, "d2\n终评点", 
                            ha='center', va='top', fontsize=9, color='blue', fontweight='bold',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='blue', linewidth=1.5),
                            zorder=12)
                
                # 标注终测点（de）- 品红色，在顶部
                if de_idx is not None and de_idx < num_cols:
                    de_x_proj = X_proj[top_row_idx, de_idx]
                    de_y_proj = Y_proj[top_row_idx, de_idx]
                    # 绘制垂直线
                    ax.plot([X_proj[0, de_idx], X_proj[-1, de_idx]], 
                            [Y_proj[0, de_idx], Y_proj[-1, de_idx]], 
                            'm--', linewidth=1.5, alpha=0.5, zorder=9)
                    # 绘制标记点
                    ax.plot(de_x_proj, de_y_proj, 'mo', markersize=8, markeredgecolor='darkmagenta', 
                           markeredgewidth=2, zorder=11, label='终测点(de)')
                    # 添加文本标注
                    ax.text(de_x_proj, de_y_proj + label_offset*0.3, "de\n终测点", 
                            ha='center', va='bottom', fontsize=9, color='magenta', fontweight='bold',
                            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='magenta', linewidth=1.5),
                            zorder=12)

    def _create_empty_3d_plot(self, ax, message):
        """创建空的3D图表（显示错误或空数据消息）"""
        try:
            # 检查是否是3D轴
            if hasattr(ax, 'set_zlabel'):
                # 3D轴
                ax.set_xlim(-1, 1)
                ax.set_ylim(-1, 1)
                ax.set_zlim(-1, 1)
                ax.text(0, 0, 0, message, ha='center', va='center', fontsize=12, color='red')
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
                ax.set_zlabel('Z')
            else:
                # 2D轴
                ax.set_axis_off()
                ax.text(0.5, 0.5, message, ha='center', va='center', fontsize=12, transform=ax.transAxes)
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_facecolor('white')
        except Exception as e:
            logger.error(f"Error creating empty 3D plot: {e}")
            # 最后的后备方案
            try:
                ax.text(0.5, 0.5, message, ha='center', va='center', fontsize=12)
            except:
                pass

    def _create_test_3d_plot(self, ax, side):
        """创建测试3D图表"""
        import numpy as np
        
        # 创建测试数据
        x = np.linspace(48.0, 52.0, 50)  # 直径范围
        y = np.linspace(0, 10, 20)       # 高度范围
        X, Y = np.meshgrid(x, y)
        
        # 创建模拟的齿面偏差数据，增加波动幅度
        Z = np.sin(X * 0.5) * np.cos(Y * 0.3) * 10.0
        
        # 绘制3D线框 - 克林贝格标准格式
        ax.plot_wireframe(X, Y, Z, color='#DDDDDD', linewidth=0.1, 
                         rstride=5, cstride=5, alpha=1.0)  # 与主方法保持一致的设置
        
        # 设置视角 - 克林贝格标准格式
        ax.view_init(elev=65, azim=-90)
        
        # 设置坐标轴范围
        ax.set_xlim(47.5, 52.5)
        ax.set_ylim(-1, 11)
        ax.set_zlim(-6, 6)
        
        # 设置显示比例 - 克林贝格标准格式
        ax.set_box_aspect((1, 3, 0.5))
        ax.dist = 10
        
        # 移除坐标轴
        ax.set_axis_off()
        
        # 添加标题
        ax.text2D(0.5, 0.95, f"{side.capitalize()} Flank (Test Data)", 
                  transform=ax.transAxes, ha='center', fontsize=10)
