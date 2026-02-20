"""
Klingelnberg Pitch Ripple/Spectrum Report Generator
Generates a landscape A4 report showing Ripple pitch and Spectrum pitch analysis
"""
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from config.logging_config import logger

class KlingelnbergPitchRippleReport:
    """Klingelnberg Pitch Ripple/Spectrum Report - Landscape A4"""
    
    def __init__(self):
        pass
        
    def create_page(self, pdf, measurement_data):
        """
        Create the pitch ripple/spectrum page and add it to the PDF
        
        Args:
            pdf: Open PdfPages object
            measurement_data: GearMeasurementData object
        """
        try:
            # Create figure for Landscape A4 (11.69 x 8.27 inches)
            fig = plt.figure(figsize=(11.69, 8.27), dpi=150)
            
            # Layout: Header, 4 Stacked Charts (Ripple R, Spectrum R, Ripple L, Spectrum L)
            # GridSpec: 
            # Row 0: Header (12%)
            # Row 1: Ripple Right (22%)
            # Row 2: Spectrum Right (22%)
            # Row 3: Ripple Left (22%)
            # Row 4: Spectrum Left (22%)
            
            # The reference image (Figure 2 right panel) shows a layout that takes up the right half 
            # of the page or a specific full page. 
            # Let's assume full page vertical stack for now as it's a dedicated page.
            
            gs = gridspec.GridSpec(5, 1, figure=fig, 
                                 height_ratios=[0.12, 0.22, 0.22, 0.22, 0.22],
                                 hspace=0.3, left=0.1, right=0.95, top=0.95, bottom=0.05)

            # 1. Header
            header_ax = fig.add_subplot(gs[0, 0])
            self._create_header(header_ax, measurement_data)
            
            # 2. Charts in order
            ripple_right_ax = fig.add_subplot(gs[1, 0])
            spectrum_right_ax = fig.add_subplot(gs[2, 0])
            ripple_left_ax = fig.add_subplot(gs[3, 0])
            spectrum_left_ax = fig.add_subplot(gs[4, 0])
            
            self._create_ripple_chart(ripple_right_ax, "right", measurement_data)
            self._create_spectrum_chart(spectrum_right_ax, "right", measurement_data)
            self._create_ripple_chart(ripple_left_ax, "left", measurement_data)
            self._create_spectrum_chart(spectrum_left_ax, "left", measurement_data)
            
            pdf.savefig(fig, orientation='landscape')
            plt.close(fig)
            logger.info("Added Pitch Ripple/Spectrum Page")
            
        except Exception as e:
            logger.exception(f"Failed to create Pitch Ripple/Spectrum Page: {e}")

    def _create_header(self, ax, measurement_data):
        """Create header with metadata matching Klingelnberg Profile/Helix style"""
        ax.axis('off')
        
        info = measurement_data.basic_info
        
        # Logo and Title similar to profile page
        # Klingelnberg logo box
        
        # Logo text
        ax.text(0.0, 0.7, "Analysis of deviations", ha='left', va='top', fontsize=10, fontweight='bold', 
               transform=ax.transAxes)
        
        # Let's stick to a clean header
        ax.text(0.01, 0.8, f"Drawing no.: {getattr(info, 'drawing_no', '')}", transform=ax.transAxes, fontsize=8)
        ax.text(0.01, 0.5, f"Customer: {getattr(info, 'customer', '')}", transform=ax.transAxes, fontsize=8)
        
        ax.text(0.5, 0.9, "Analysis of deviations", transform=ax.transAxes, ha='center', fontsize=10, fontweight='bold')
        ax.text(0.5, 0.6, f"Part name: {getattr(info, 'type', 'gear')}", transform=ax.transAxes, ha='center', fontsize=8)
        ax.text(0.5, 0.3, f"File: {getattr(info, 'file_name', '')}", transform=ax.transAxes, ha='center', fontsize=8)

        ax.text(0.99, 0.8, f"Serial no.: {getattr(info, 'order_no', '')}", transform=ax.transAxes, ha='right', fontsize=8)
        ax.text(0.99, 0.5, f"{getattr(info, 'date', '')}", transform=ax.transAxes, ha='right', fontsize=8)
        ax.text(0.99, 0.2, f"z= {getattr(info, 'teeth', '')}", transform=ax.transAxes, ha='right', fontsize=8)
        
        # 获取公差参数并在右上角显示
        tolerance = getattr(measurement_data, 'tolerance', None)
        R = None
        N0 = None
        K = None
        
        if tolerance:
            R = getattr(tolerance, 'ripple_tolerance_R', None)
            N0 = getattr(tolerance, 'ripple_tolerance_N0', None)
            K = getattr(tolerance, 'ripple_tolerance_K', None)
        
        # 如果参数不存在，使用默认值
        if R is None:
            R = 2.0
        if N0 is None:
            N0 = 1.0
        if K is None:
            K = 0.0
        
        # 在右上角显示公差参数（在Date下方）
        tolerance_text = f"Limiting curve parameters: R = {R:.2f}, n0 = {N0:.2f}, K = {K:.2f}"
        ax.text(0.99, 0.35, tolerance_text, transform=ax.transAxes, ha='right', fontsize=8)

    def _get_pitch_deviations(self, measurement_data, side):
        """Helper to extract pitch deviations - 获取原始周节偏差数据"""
        pitch_data = getattr(measurement_data, 'pitch_data', None)
        if not pitch_data: 
            return []
        
        side_data = getattr(pitch_data, side, {})
        if not side_data: 
            return []
        
        # 按齿号排序，确保顺序正确
        tooth_nums = sorted(list(side_data.keys()))
        deviations = []
        for tooth_num in tooth_nums:
            tooth_data = side_data[tooth_num]
            if isinstance(tooth_data, dict):
                # 使用fp值（单个周节偏差）作为原始周节偏差
                fp_value = tooth_data.get('fp', 0)
                deviations.append(fp_value)
            else:
                deviations.append(0)
        return deviations

    def _create_ripple_chart(self, ax, side, measurement_data):
        """Create ripple pitch waveform chart with sine wave overlay"""
        try:
            # Title
            title = f"Ripple pitch {side}"
            # Centered title, plain text
            ax.set_title(title, fontsize=10, pad=15)
            
            deviations = self._get_pitch_deviations(measurement_data, side)
            if not deviations:
                ax.text(0.5, 0.5, "No Data", ha='center', va='center', transform=ax.transAxes)
                ax.axis('off')
                return
            
            x = np.arange(len(deviations))
            y = np.array(deviations)
            
            # 直接绘制原始周节偏差曲线（不进行去均值处理，不使用样条插值）
            # Plot raw pitch deviation curve (Blue) - 原始周节偏差曲线
            ax.plot(x, y, 'b-', linewidth=1.0, zorder=2)
            
            # Calculate 1st Order Sine Wave (Red) - 一阶正弦波
            # 从原始周节偏差中提取一阶分量
            # 先去除均值以便FFT分析
            y_mean = np.mean(y)
            y_centered = y - y_mean
            
            # FFT
            n = len(y_centered)
            fft_vals = np.fft.rfft(y_centered)
            orders = np.arange(len(fft_vals))
            
            # Get 1st order (index 1) - 获取一阶分量
            if len(fft_vals) > 1:
                # easier way: zero out all other components and inverse FFT
                fft_1st = np.zeros_like(fft_vals)
                fft_1st[1] = fft_vals[1] # Keep 1st order only
                                          
                y_sine = np.fft.irfft(fft_1st, n=n)
                    
                # Plot 1st Order Sine Wave (Red) - 一阶正弦波（直接绘制，不插值）
                ax.plot(x, y_sine, 'r-', linewidth=1.0, zorder=3)
                
                # Calculate Amplitude A1 - 计算一阶分量的幅值
                A1 = np.max(np.abs(y_sine))
            else:
                A1 = 0
            
            # 绘制黑色零线
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5, zorder=1)
            
            # Axis formatting
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_visible(False) # Maybe? Figure 2 has no left spine visible in crop
            # Actually Figure 2 has a box around it. Let's keep box but make it thin.
            # "Figure 2" provided by user shows a box.
            
            for spine in ax.spines.values():
                spine.set_linewidth(0.5)
                spine.set_edgecolor('black')
                
            # No ticks on axes in Figure 2 inner plots?
            # It seems to have a baseline but no grid or ticks clearly visible in the crop
            # But "Figure 1" (current) has grids. User said "according to figure 2".
            # Figure 2 Right Panel:
            # - No grid lines? Hard to see.
            # - No numeric ticks labels on axes?
            # - Just the curve and the text.
            
            ax.set_xticks([])
            ax.set_yticks([])
            
            # Annotations
            # "A1 = 11.13"
            # "O(1) = 1"
            # Located at left center
            text_str = f"A1 = {A1:.2f}\nO(1) = 1"
            ax.text(0.02, 0.5, text_str, transform=ax.transAxes, 
                   fontsize=9, va='center', ha='left')
            
            # Scale limits - 使用原始数据范围
            y_max = max(np.max(np.abs(y)), A1) * 1.5
            if y_max == 0: y_max = 1
            ax.set_ylim(-y_max, y_max)
            ax.set_xlim(0, len(deviations)-1)
            
        except Exception as e:
            logger.error(f"Error creating ripple chart: {e}")

    def _calculate_tolerance_curve(self, orders, R, N0, K):
        """
        计算公差曲线
        
        公式：公差 = R / (O-1)^N
        其中 N = N0 + K / O
        O = 阶次
        
        Args:
            orders: 阶次数组
            R: 允许波深（当 R<0 没有公差曲线）
            N0: 用于描述公差曲线的常数
            K: 修正值
            
        Returns:
            tolerance_values: 公差值数组，如果R<0则返回None
        """
        if R < 0:
            return None
        
        # 避免除零错误：当O=1时，(O-1)=0，需要特殊处理
        tolerance_values = np.zeros_like(orders, dtype=float)
        
        for i, O in enumerate(orders):
            if O <= 1:
                # 当阶次<=1时，公差值设为无穷大或一个很大的值
                tolerance_values[i] = np.inf
            else:
                # 计算 N = N0 + K / O
                N = N0 + K / O
                # 计算 公差 = R / (O-1)^N
                tolerance_values[i] = R / ((O - 1) ** N)
        
        return tolerance_values

    def _create_spectrum_chart(self, ax, side, measurement_data):
        """Create spectrum bar chart"""
        try:
            title = f"Spectrum pitch {side}"
            ax.set_title(title, fontsize=10, pad=15)
            
            deviations = self._get_pitch_deviations(measurement_data, side)
            if not deviations:
                ax.axis('off')
                return

            y = np.array(deviations) - np.mean(deviations)
            n = len(y)
            fft_vals = np.fft.rfft(y)
            magnitudes = np.abs(fft_vals) / n * 2
            
            # Bar chart
            # Figure 2: Blue bars. 1st order is tall.
            orders = np.arange(len(magnitudes))
            max_order_plot = min(30, len(orders))
            
            # 获取公差参数
            tolerance = getattr(measurement_data, 'tolerance', None)
            R = None
            N0 = None
            K = None
            enabled = True
            
            if tolerance:
                # 优先使用pitch_ripple_tolerance参数，如果没有则使用ripple_tolerance参数
                R = getattr(tolerance, 'pitch_ripple_tolerance_R', None)
                N0 = getattr(tolerance, 'pitch_ripple_tolerance_N0', None)
                K = getattr(tolerance, 'pitch_ripple_tolerance_K', None)
                enabled = getattr(tolerance, 'pitch_ripple_tolerance_enabled', True)
                
                # 如果没有pitch_ripple参数，使用ripple参数
                if R is None:
                    R = getattr(tolerance, 'ripple_tolerance_R', None)
                if N0 is None:
                    N0 = getattr(tolerance, 'ripple_tolerance_N0', None)
                if K is None:
                    K = getattr(tolerance, 'ripple_tolerance_K', None)
                if not enabled:
                    enabled = getattr(tolerance, 'ripple_tolerance_enabled', True)
            
            # 如果参数不存在，使用默认值
            if R is None:
                R = 2.0
            if N0 is None:
                N0 = 1.0
            if K is None:
                K = 0.0
            
            # 绘制柱状图
            ax.bar(orders[:max_order_plot], magnitudes[:max_order_plot], 
                  color='blue', width=0.8, align='center')
            
            # 计算并绘制限制曲线（如果启用且R >= 0）
            # 根据参考图片，Spectrum pitch图表中有一条粉红色/洋红色曲线覆盖在柱状图上
            if enabled and R >= 0:
                # 为限制曲线生成完整的阶次范围（从2开始，因为O=1时公式分母为0）
                # 更密集的点以便绘制平滑曲线
                tolerance_orders = np.arange(2, max_order_plot + 1, 0.1)  # 每0.1阶一个点，使曲线更平滑
                tolerance_values = self._calculate_tolerance_curve(tolerance_orders, R, N0, K)
                
                if tolerance_values is not None:
                    # 过滤掉无效值（无穷大或NaN）
                    valid_mask = np.isfinite(tolerance_values) & (tolerance_values > 0)
                    tolerance_orders_valid = tolerance_orders[valid_mask]
                    tolerance_values_valid = tolerance_values[valid_mask]
                    
                    if len(tolerance_values_valid) > 0:
                        # 绘制粉红色/洋红色限制曲线（覆盖在柱状图上）
                        # 使用magenta或pink颜色，参考图片显示为粉红色/洋红色
                        ax.plot(tolerance_orders_valid, tolerance_values_valid, color='magenta', 
                               linewidth=1.5, linestyle='-', zorder=3, alpha=0.9)
            
            # Annotation A1/O(1)
            A1 = magnitudes[1] if len(magnitudes) > 1 else 0
            text_str = f"A1 = {A1:.2f}\nO(1) = 1"
            
            # Figure 2 puts this text on the left as well
            # But be careful not to overlap bars if bar 1 is huge.
            # Figure 2 shows text is to the LEFT of the main high bar? 
            # Or maybe the first bar IS index 1.
            # Index 0 is DC (usually 0 after detrend).
            
            # Let's put text on left, assume bars start a bit to the right or scale handles it
            ax.text(0.02, 0.5, text_str, transform=ax.transAxes, 
                   fontsize=9, va='center', ha='left')
            
            ax.axhline(y=0, color='black', linewidth=0.5)
            
            # Clean axes
            for spine in ax.spines.values():
                spine.set_linewidth(0.5)
                spine.set_edgecolor('black')
                
            ax.set_xticks([])
            ax.set_yticks([])
            
            # Add scale on the LAST chart (Spectrum Left) if matches Figure 2
            if side == "left":
                 # Red Scale Marker: "I 5.0 µm 2000:1"
                 # Bottom Right
                 self._draw_scale_marker(ax)

            ax.set_xlim(-0.5, max_order_plot)
            
            # 调整Y轴范围，确保限制曲线可见
            top_val = np.max(magnitudes[:max_order_plot]) if len(magnitudes) > 0 else 1
            if enabled and R >= 0:
                # 如果有限制曲线，确保Y轴范围包含限制曲线的最大值
                tolerance_max = np.max(tolerance_values_valid) if len(tolerance_values_valid) > 0 else 0
                top_val = max(top_val, tolerance_max)
            ax.set_ylim(0, top_val * 1.2)
            
        except Exception as e:
            logger.error(f"Error creating spectrum chart: {e}")

    def _draw_scale_marker(self, ax):
        """Draw the red scale marker on the bottom right"""
        # "I" bar
        # 5.0 um
        # 2000:1
        
        x_pos = 0.95
        y_pos = 0.2
        
        # Vertical red line
        ax.plot([x_pos, x_pos], [y_pos, y_pos + 0.2], transform=ax.transAxes, 
               color='red', linewidth=1.5, clip_on=False)
        # Caps
        d = 0.005
        ax.plot([x_pos-d, x_pos+d], [y_pos, y_pos], transform=ax.transAxes, color='red', linewidth=1)
        ax.plot([x_pos-d, x_pos+d], [y_pos+0.2, y_pos+0.2], transform=ax.transAxes, color='red', linewidth=1)
        
        # Text
        ax.text(x_pos - 0.01, y_pos + 0.1, "5.0 µm\n2000:1", transform=ax.transAxes,
               color='red', fontsize=8, va='center', ha='right')
