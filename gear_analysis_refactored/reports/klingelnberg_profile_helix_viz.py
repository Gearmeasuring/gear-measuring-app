"""
Klingelnberg Profile/Helix Visualization Report Generator
Generates a landscape A4 report showing Profile and Helix without actual modifications
"""
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as patches
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from config.logging_config import logger

# Check if scipy is available
try:
    from scipy.optimize import curve_fit
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

class KlingelnbergProfileHelixReport:
    """Klingelnberg Profile/Helix Visualization Report - Landscape A4"""
    
    def __init__(self):
        pass
        
    def create_page(self, pdf, measurement_data):
        """
        Create the profile/helix visualization page and add it to the PDF
        
        Args:
            pdf: Open PdfPages object
            measurement_data: GearMeasurementData object
        """
        try:
            # Create figure for Landscape A4 (11.69 x 8.27 inches) with ivory background (Song-style)
            fig = plt.figure(figsize=(11.69, 8.27), dpi=150, facecolor='#F9F6F0')  # 象牙白背景
            
            # Layout: Header, Profile section, Helix section
            gs = gridspec.GridSpec(3, 1, figure=fig, 
                                 height_ratios=[0.10, 0.45, 0.45],
                                 hspace=0.02, left=0.06, right=0.94, top=0.97, bottom=0.03)
            
            # 1. Header
            header_ax = fig.add_subplot(gs[0, 0])
            self._create_header(header_ax, measurement_data)
            
            # 2. Profile Section
            profile_ax = fig.add_subplot(gs[1, 0])
            self._create_section(profile_ax, measurement_data, 'profile')
            
            # 3. Helix Section
            helix_ax = fig.add_subplot(gs[2, 0])
            self._create_section(helix_ax, measurement_data, 'helix')
            
            pdf.savefig(fig, orientation='landscape')
            plt.close(fig)
            logger.info("Added Profile/Helix Visualization Page")
            
        except Exception as e:
            logger.exception(f"Failed to create Profile/Helix Visualization Page: {e}")

    def _create_header(self, ax, measurement_data):
        """Create header with metadata matching Figure 2"""
        ax.axis('off')
        
        # Add border around header
        rect = patches.Rectangle((0.01, 0.05), 0.98, 0.9, linewidth=0.5, edgecolor='#7A8B99', facecolor='none', transform=ax.transAxes)
        ax.add_patch(rect)
        
        # Add second border for the bottom section
        rect_bottom = patches.Rectangle((0.01, 0.15), 0.98, 0.15, linewidth=0.5, edgecolor='#7A8B99', facecolor='none', transform=ax.transAxes)
        ax.add_patch(rect_bottom)
        
        # Add diamond shape and KLINGELNBERG text
        diamond_vertices = np.array([[0.12, 0.75], [0.13, 0.7], [0.12, 0.65], [0.11, 0.7]])
        diamond = patches.Polygon(diamond_vertices, closed=True, edgecolor='#7A8B99', facecolor='none', linewidth=0.5, transform=ax.transAxes)
        ax.add_patch(diamond)
        ax.text(0.16, 0.7, "KLINGELNBERG", ha='left', va='center', fontsize=7, fontweight='bold', transform=ax.transAxes, color='#333333')
        
        # Tool info (moved right)
        ax.text(0.25, 0.85, "Tool:", ha='left', va='center', fontsize=6, fontweight='bold', transform=ax.transAxes, color='#333333')
        ax.text(0.32, 0.85, "CPU-12450-135A-01", ha='left', va='center', fontsize=6, transform=ax.transAxes, color='#333333')
        
        # Serial no. and date
        ax.text(0.50, 0.85, "Serial no.: SHAC-0103-001", ha='left', va='center', fontsize=6, transform=ax.transAxes, color='#333333')
        ax.text(0.88, 0.85, "11.04.25", ha='right', va='center', fontsize=6, transform=ax.transAxes, color='#333333')
        
        # Drawing no. and part name
        ax.text(0.25, 0.70, "Drawing no.: DPUB-125400135-AA", ha='left', va='center', fontsize=6, transform=ax.transAxes, color='#333333')
        ax.text(0.50, 0.70, "Part name: gear", ha='left', va='center', fontsize=6, transform=ax.transAxes, color='#333333')
        ax.text(0.88, 0.70, "16:20", ha='right', va='center', fontsize=6, transform=ax.transAxes, color='#333333')
        
        # Parameters in bottom border
        ax.text(0.25, 0.25, "z= 89 mn= 1.5300 sn= 2.3779", ha='left', va='center', fontsize=5, transform=ax.transAxes, color='#333333')
        ax.text(0.60, 0.25, "αn= 17.0000 β0= 25.0000", ha='left', va='center', fontsize=5, transform=ax.transAxes, color='#333333')

    def _create_section(self, ax, measurement_data, section_type):
        """Create profile or helix section with left and right visualizations matching Figure 2"""
        ax.axis('off')
        
        # Title and labels
        if section_type == 'profile':
            title = "Profile without actual modifications"
            data_left = getattr(measurement_data.profile_data, 'left', {})
            data_right = getattr(measurement_data.profile_data, 'right', {})
            scale_height = "2.000 mm"
            # Use different approach for mu symbol to ensure it displays correctly
            scale_text = "5.0 \u03BCm\n2000:1"
        else:
            title = "Helix without actual modifications"
            data_left = getattr(measurement_data.flank_data, 'left', {})
            data_right = getattr(measurement_data.flank_data, 'right', {})
            scale_height = "3.000 mm"
            scale_text = "5.0 µm\n2000:1"
        
        # Add side labels at top
        ax.text(0.06, 0.95, "+/-", ha='center', va='top', fontsize=7, transform=ax.transAxes, color='#333333')
        ax.text(0.12, 0.95, "left", ha='left', va='top', fontsize=8, transform=ax.transAxes, color='#333333')
        ax.text(0.88, 0.95, "right", ha='right', va='top', fontsize=8, transform=ax.transAxes, color='#333333')
        ax.text(0.94, 0.95, "+/-", ha='center', va='top', fontsize=7, transform=ax.transAxes, color='#333333')
        
        # Add title centered
        ax.text(0.5, 0.95, title, ha='center', va='top', fontsize=9, fontweight='bold', transform=ax.transAxes, color='#333333')
        
        # Removed way of evaluation text
        
        # Create 2-column layout for left and right
        from matplotlib.gridspec import GridSpecFromSubplotSpec
        teeth_gs = GridSpecFromSubplotSpec(1, 2, subplot_spec=ax.get_subplotspec(), 
                                          hspace=0.0, wspace=0.15)
        
        fig = ax.get_figure()
        
        # Left and right panels
        left_ax = fig.add_subplot(teeth_gs[0, 0])
        right_ax = fig.add_subplot(teeth_gs[0, 1])
        
        # Draw teeth profiles
        self._draw_tooth_profiles(left_ax, data_left, "left", scale_height, scale_text, section_type)
        self._draw_tooth_profiles(right_ax, data_right, "right", scale_height, scale_text, section_type)
        
        # Add bottom annotations
        if section_type == 'profile':
            ax.text(0.12, 0.1, "A1\nO(1)", ha='left', va='top', fontsize=6, transform=ax.transAxes, color='#333333')
            ax.text(0.18, 0.1, "0.10\n267", ha='left', va='top', fontsize=6, transform=ax.transAxes, color='#333333')
            
            # 已删除NOK标识及其相关文本
            
            ax.text(0.82, 0.1, "0.24\n89", ha='right', va='top', fontsize=6, transform=ax.transAxes, color='#333333')
            ax.text(0.88, 0.1, "+/-", ha='right', va='top', fontsize=7, transform=ax.transAxes, color='#333333')
            ax.text(0.94, 0.1, "-/+", ha='center', va='top', fontsize=7, transform=ax.transAxes, color='#333333')
        else:
            ax.text(0.12, 0.1, "A1\nO(1)", ha='left', va='top', fontsize=6, transform=ax.transAxes, color='#333333')
            ax.text(0.18, 0.1, "0.08\n89", ha='left', va='top', fontsize=6, transform=ax.transAxes, color='#333333')
            
            ax.text(0.5, 0.05, "■ SHAC-0102-001", ha='center', va='bottom', fontsize=6, 
                   transform=ax.transAxes, color='red')
            
            ax.text(0.08, 0.05, "■ Spectrum", ha='left', va='bottom', fontsize=6, 
                   transform=ax.transAxes, color='blue')
            
            ax.text(0.82, 0.1, "0.09\n89", ha='right', va='top', fontsize=6, transform=ax.transAxes, color='#333333')
            ax.text(0.88, 0.1, "+/-", ha='right', va='top', fontsize=7, transform=ax.transAxes, color='#333333')
            ax.text(0.94, 0.1, "-/+", ha='center', va='top', fontsize=7, transform=ax.transAxes, color='#333333')
        
        # Add diamond marker at bottom right
        if section_type == 'helix':
            diamond_vertices = np.array([[0.975, 0.05], [0.98, 0.03], [0.975, 0.01], [0.97, 0.03]])
            diamond = patches.Polygon(diamond_vertices, closed=True, edgecolor='#7A8B99', facecolor='none', linewidth=0.5, transform=ax.transAxes)
            ax.add_patch(diamond)

    def _fit_sinusoids(self, vals, max_components=2):
        """
        对数据进行正弦拟合，提取主要分量（用于生成红色拟合曲线）
        """
        if len(vals) < 8:
            return None
        
        x = np.arange(len(vals))
        
        # 去趋势
        try:
            p = np.polyfit(x, vals, 1)
            trend = np.polyval(p, x)
            detrended = vals - trend
        except:
            detrended = vals - np.mean(vals)
        
        # 使用FFT找到主要频率分量
        fft_vals = np.fft.rfft(detrended)
        n = len(detrended)
        mag = np.abs(fft_vals) / n
        phases = np.angle(fft_vals)
        
        # 跳过DC分量，找到主要频率
        mag[0] = 0
        top_indices = np.argsort(mag)[::-1][:max_components]
        
        result = {}
        
        # 获取第一个分量
        if len(top_indices) > 0 and top_indices[0] > 0:
            idx1 = top_indices[0]
            A1 = mag[idx1] * 2
            W1 = float(idx1)
            Pw1 = phases[idx1]
            result['A1'] = A1
            result['W1'] = W1
            result['Pw1'] = np.degrees(Pw1)
        else:
            result['A1'] = 0.0
            result['W1'] = 0.0
            result['Pw1'] = 0.0
        
        # 获取第二个分量（如果存在）
        if max_components >= 2 and len(top_indices) > 1 and top_indices[1] > 0:
            idx2 = top_indices[1]
            A2 = mag[idx2] * 2
            W2 = float(idx2)
            Pw2 = phases[idx2]
            result['A2'] = A2
            result['W2'] = W2
            result['Pw2'] = np.degrees(Pw2)
        else:
            result['A2'] = 0.0
            result['W2'] = 0.0
            result['Pw2'] = 0.0
        
        # 计算RMS
        result['rms'] = np.sqrt(np.mean(detrended**2))
        result['sigma'] = np.std(detrended)
        result['6sigma'] = 6 * result['sigma']
        
        return result
    
    def _single_sinusoidal_model(self, x, A, W, Pw, offset):
        """单正弦波模型"""
        L = len(x) if len(x) > 0 else 1
        return A * np.sin(2 * np.pi * W * x / L + Pw) + offset
    
    def _sinusoidal_model(self, x, A1, W1, Pw1, A2, W2, Pw2, offset):
        """双正弦波模型"""
        L = len(x) if len(x) > 0 else 1
        return (A1 * np.sin(2 * np.pi * W1 * x / L + np.radians(Pw1)) + 
                A2 * np.sin(2 * np.pi * W2 * x / L + np.radians(Pw2)) + offset)

    def _draw_tooth_profiles(self, ax, data_dict, side, scale_height, scale_text, section_type):
        """Draw tooth profile visualizations matching Figure 1 exactly - 蓝色和红色叠加曲线"""
        try:
            # Set up axes to match Figure 1 exactly
            ax.set_xlim(0, 500)
            ax.set_ylim(0, 501)  # Slightly extended to accommodate labels
            
            # Get teeth data
            if not data_dict:
                ax.text(250, 250, "No Data", ha='center', va='center', fontsize=8)
                ax.axis('off')
                return
            
            # 获取第一个齿的数据用于绘制
            tooth_nums = sorted(list(data_dict.keys()))
            if len(tooth_nums) == 0:
                ax.text(250, 250, "No Data", ha='center', va='center', fontsize=8)
                ax.axis('off')
                return
            
            # 使用第一个齿的数据
            first_tooth = tooth_nums[0]
            values = data_dict[first_tooth]
            
            if values is None or len(values) == 0:
                ax.text(250, 250, "No Data", ha='center', va='center', fontsize=8)
                ax.axis('off')
                return
            
            # 绘制垂直比例尺（紫色/洋红色）- 左右两侧
            # Left scale (leftmost)
            ax.plot([80, 80], [100, 450], color='magenta', linewidth=0.6, solid_capstyle='butt', zorder=2)
            ax.plot([70, 90], [100, 100], color='magenta', linewidth=0.6, solid_capstyle='butt', zorder=2)
            ax.plot([70, 90], [450, 450], color='magenta', linewidth=0.6, solid_capstyle='butt', zorder=2)
            
            # Right scale (rightmost)
            ax.plot([450, 450], [100, 450], color='magenta', linewidth=0.6, solid_capstyle='butt', zorder=2)
            ax.plot([440, 460], [100, 100], color='magenta', linewidth=0.6, solid_capstyle='butt', zorder=2)
            ax.plot([440, 460], [450, 450], color='magenta', linewidth=0.6, solid_capstyle='butt', zorder=2)
            
            # Add "500" label at top
            ax.text(80, 460, "500", ha='center', va='bottom', fontsize=6, zorder=11, color='#333333')
            ax.text(450, 460, "500", ha='center', va='bottom', fontsize=6, zorder=11, color='#333333')
            
            # 创建垂直方向的曲线（Y轴从下到上，X轴表示偏差）
            # 根据图1，中间两个图表显示垂直的波形线
            y_positions = np.linspace(100, 450, len(values))
            
            # 计算X轴位置（偏差值）
            # 去均值以便显示
            values_array = np.array(values)
            values_mean = np.mean(values_array)
            values_centered = values_array - values_mean
            
            # 缩放因子，使偏差值适合图表宽度
            x_center = 250  # 图表中心
            scale_factor = 100  # 缩放因子
            
            # 蓝色曲线：原始偏差数据（去均值后）
            x_blue = x_center + scale_factor * values_centered
            ax.plot(x_blue, y_positions, color='blue', linewidth=1.5, zorder=5, solid_capstyle='round')
            
            # 红色曲线：正弦拟合曲线（与蓝色曲线叠加显示）
            # 使用正弦拟合提取主要分量
            fit_result = self._fit_sinusoids(values_array, max_components=2)
            if fit_result and fit_result.get('A1', 0) > 0:
                x_fit = np.arange(len(values))
                if fit_result.get('A2', 0) > 0 and fit_result['A2'] > 0.01:
                    # 双正弦波拟合
                    y_fit = self._sinusoidal_model(x_fit, 
                                                  fit_result['A1'], fit_result['W1'], fit_result['Pw1'],
                                                  fit_result['A2'], fit_result['W2'], fit_result['Pw2'],
                                                  values_mean)
                else:
                    # 单正弦波拟合
                    y_fit = self._single_sinusoidal_model(x_fit,
                                                         fit_result['A1'], fit_result['W1'], 
                                                         np.radians(fit_result['Pw1']), values_mean)
                
                # 去均值并缩放（与蓝色曲线使用相同的处理方式）
                y_fit_centered = y_fit - values_mean
                x_red = x_center + scale_factor * y_fit_centered
                ax.plot(x_red, y_positions, color='red', linewidth=1.5, zorder=6, solid_capstyle='round')
            
            # Draw magenta vertical scale bars with correct annotations
            # Middle (near x=250)
            ax.plot([270, 270], [200, 300], color='magenta', linewidth=2.5, solid_capstyle='butt', zorder=10)
            ax.text(270, 305, scale_height, ha='center', va='bottom', fontsize=6, zorder=11, color='#333333')
            ax.text(280, 300, scale_text.split('\n')[0], ha='left', va='top', fontsize=6, zorder=11, color='#333333')
            ax.text(280, 290, scale_text.split('\n')[1], ha='left', va='top', fontsize=6, zorder=11, color='#333333')
            
            # Add "0" and "1" labels at bottom
            ax.text(80, 0, "1", ha='center', va='bottom', fontsize=6, color='#333333', fontweight='bold')
            ax.text(450, 0, "1", ha='center', va='bottom', fontsize=6, color='#333333', fontweight='bold')
            
            # Clean up axes
            ax.axis('off')
            
        except Exception as e:
            logger.error(f"Error drawing tooth profiles: {e}")
            ax.text(250, 250, "Error", ha='center', va='center')
            ax.axis('off')