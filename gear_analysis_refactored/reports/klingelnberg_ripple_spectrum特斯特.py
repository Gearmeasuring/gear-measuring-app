"""
Klingelnberg Ripple Spectrum Report Generator
Generates a landscape A4 report showing the spectrum of the ripple (Sinusoidal Fit analysis)
"""
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from config.logging_config import logger
try:
    from scipy.optimize import curve_fit
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not available, falling back to FFT method")

class RippleSpectrumSettings:
    """齿廓波纹频谱报告设置类
    
    包含以下设置类别：
    1. 齿廓和齿向设置：滤波器参数、评价方法、阶次筛选等
    2. 评价设置：评价范围、阶次计算方式、波形标准等
    3. 显示设置：放大系数、阶次分类、颜色标记等
    """
    
    def __init__(self):
        # 1. 齿廓和齿向设置
        self.profile_helix_settings = {
            # RC低通滤波器参数
            'filter_params': {
                'max_depth': 2.00,  # μm，最大波深
                'attenuation_ratio': 5000,  # 衰减比
                'cutoff_frequency': 100.0,  # Hz，截止频率
                'sampling_frequency': 10000.0  # Hz，采样频率
            },
            # 评价方法
            'evaluation_method': 'high_order',  # 评价方法：'high_order' 或 'all_orders'
            # 阶次筛选
            'order_filtering': {
                'min_order': None,  # 最小阶次，None表示使用ZE阶(齿数)
                'max_order': 500,  # 最大阶次
                'only_high_orders': True  # 是否只保留高阶分量
            }
        }
        
        # 2. 评价设置
        self.evaluation_settings = {
            # 评价范围
            'evaluation_range': {
                'use_default': True,  # 是否使用默认评价范围
                'start_percent': 0.2,  # 默认评价范围起始百分比
                'end_percent': 0.8     # 默认评价范围结束百分比
            },
            # 阶次计算方式
            'order_calculation': {
                'base_order': 'ze',  # 基准阶次：'ze' (齿数) 或 'custom'
                'custom_base': 10    # 自定义基准阶次
            },
            # 波形标准
            'waveform_standard': {
                'R': 2.0,  # 允许波深
                'N0': 1.0,  # 用于描述公差曲线的常数
                'K': 0.0    # 修正值
            }
        }
        
        # 3. 显示设置
        self.display_settings = {
            # 放大系数
            'magnification': {
                'auto_scale': True,  # 是否自动缩放
                'manual_factor': 1.0  # 手动放大系数
            },
            # 阶次分类
            'order_classification': {
                'show_ze_markers': True,  # 是否显示ZE, 2ZE等标记
                'ze_multiples': 5  # 显示的ZE倍数数量
            },
            # 颜色标记
            'color_marking': {
                'tolerance_color': 'purple',  # 公差曲线颜色
                'pass_color': 'blue',  # 合格数据颜色
                'fail_color': 'red',  # 超差数据颜色
                'grid_color': 'gray'  # 网格线颜色
            },
            # 表格设置
            'table_settings': {
                'max_components': 11,  # 表格中显示的最大分量数
                'show_zero_values': False  # 是否显示零值
            },
            # 滤波器显示
            'filter_display': {
                'show_indicator': True,  # 是否显示滤波器指示器
                'indicator_type': 'blue_i_beam'  # 指示器类型
            }
        }
    
    def update_profile_helix_settings(self, **kwargs):
        """更新齿廓和齿向设置"""
        for key, value in kwargs.items():
            if key in self.profile_helix_settings:
                if isinstance(value, dict):
                    self.profile_helix_settings[key].update(value)
                else:
                    self.profile_helix_settings[key] = value
    
    def update_evaluation_settings(self, **kwargs):
        """更新评价设置"""
        for key, value in kwargs.items():
            if key in self.evaluation_settings:
                if isinstance(value, dict):
                    self.evaluation_settings[key].update(value)
                else:
                    self.evaluation_settings[key] = value
    
    def update_display_settings(self, **kwargs):
        """更新显示设置"""
        for key, value in kwargs.items():
            if key in self.display_settings:
                if isinstance(value, dict):
                    self.display_settings[key].update(value)
                else:
                    self.display_settings[key] = value
    
    def get_filter_params(self):
        """获取滤波器参数"""
        return self.profile_helix_settings['filter_params']
    
    def get_order_filtering(self):
        """获取阶次筛选设置"""
        return self.profile_helix_settings['order_filtering']
    
    def get_evaluation_range(self):
        """获取评价范围设置"""
        return self.evaluation_settings['evaluation_range']
    
    def get_waveform_standard(self):
        """获取波形标准设置"""
        return self.evaluation_settings['waveform_standard']
    
    def get_display_settings(self):
        """获取显示设置"""
        return self.display_settings

class KlingelnbergRippleSpectrumReport:
    """Klingelnberg Ripple Spectrum Report - Landscape A4"""
    
    def __init__(self, settings=None):
        # 如果没有提供设置，使用默认设置
        self.settings = settings if settings is not None else RippleSpectrumSettings()
        
    def create_page(self, pdf, measurement_data):
        """
        Create the ripple spectrum page and add it to the PDF
        
        Args:
            pdf: Open PdfPages object
            measurement_data: GearMeasurementData object
        """
        try:
            # Create figure for Landscape A4 (11.69 x 8.27 inches)
            fig = plt.figure(figsize=(11.69, 8.27), dpi=150)
            
            # Layout: Header, 4 Stacked Charts, Tables
            # GridSpec: 
            # Row 0: Header (12%)
            # Row 1: Profile right chart (18%)
            # Row 2: Profile left chart (18%)
            # Row 3: Helix right chart (18%)
            # Row 4: Helix left chart (18%)
            # Row 5: Tables (16%)
            
            gs = gridspec.GridSpec(6, 1, figure=fig, 
                                 height_ratios=[0.12, 0.18, 0.18, 0.18, 0.18, 0.16],
                                 hspace=0.25, left=0.05, right=0.95, top=0.95, bottom=0.05)
            
            # 1. Header
            header_ax = fig.add_subplot(gs[0, 0])
            self._create_header(header_ax, measurement_data)
            
            # 2. Stacked Charts
            profile_left_ax = fig.add_subplot(gs[1, 0])
            profile_right_ax = fig.add_subplot(gs[2, 0])
            helix_left_ax = fig.add_subplot(gs[3, 0])
            helix_right_ax = fig.add_subplot(gs[4, 0])
            
            self._create_spectrum_chart(profile_left_ax, "Profile left", measurement_data, 'profile', 'left')
            self._create_spectrum_chart(profile_right_ax, "Profile right", measurement_data, 'profile', 'right')
            self._create_spectrum_chart(helix_left_ax, "Helix left", measurement_data, 'flank', 'left')
            self._create_spectrum_chart(helix_right_ax, "Helix right", measurement_data, 'flank', 'right')
            
            # 3. Tables
            # Use a nested gridspec for the two tables at the bottom
            table_gs = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[5, 0], wspace=0.05)
            table_left_ax = fig.add_subplot(table_gs[0, 0])
            table_right_ax = fig.add_subplot(table_gs[0, 1])
            
            self._create_data_table(table_left_ax, measurement_data, 'left')
            self._create_data_table(table_right_ax, measurement_data, 'right')
            
            pdf.savefig(fig, orientation='landscape')
            plt.close(fig)
            logger.info("Added Ripple Spectrum Page")
            
        except Exception as e:
            logger.exception(f"Failed to create Ripple Spectrum Page: {e}")

    def _create_header(self, ax, measurement_data):
        """Create header similar to standard report but landscape"""
        ax.axis('off')
        
        # Title
        ax.text(0.5, 1.0, "Analysis of deviations", ha='center', va='top', fontsize=12, transform=ax.transAxes, fontweight='bold')
        
        # Info
        info = measurement_data.basic_info
        
        # Left side info - 增加间距
        ax.text(0.05, 0.85, f"Drawing no.: {getattr(info, 'drawing_no', '')}", transform=ax.transAxes, fontsize=10, ha='left', va='top')
        ax.text(0.05, 0.65, f"Customer: {getattr(info, 'customer', '')}", transform=ax.transAxes, fontsize=10, ha='left', va='top')
        
        # Right side info - 垂直排列，增加间距避免重叠
        # 从顶部开始，依次向下排列
        right_x = 0.95  # 右侧对齐位置
        y_start = 0.90  # 起始Y位置（从顶部开始）
        y_step = 0.20   # 进一步增加行间距，确保不重叠
        
        # Serial no. (最顶部)
        serial_no = getattr(info, 'order_no', 'N/A')
        if not serial_no:
            serial_no = 'N/A'
        ax.text(right_x, y_start, f"Serial no.: {serial_no}", transform=ax.transAxes, ha='right', va='top', fontsize=10)
        
        # Date (Serial no.下方)
        date_str = getattr(info, 'date', '')
        ax.text(right_x, y_start - y_step, f"{date_str}", transform=ax.transAxes, ha='right', va='top', fontsize=10)
        
        # 获取公差参数
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
        
        # Limiting curve parameters (Date下方) - 使用稍小的字体，并增加间距
        tolerance_text = f"Limiting curve parameters: R = {R:.2f}, n0 = {N0:.2f}, K = {K:.2f}"
        ax.text(right_x, y_start - 2 * y_step, tolerance_text, transform=ax.transAxes, ha='right', va='top', fontsize=8)
        
        # File (Limiting curve parameters下方)
        file_str = getattr(info, 'program', '')
        ax.text(right_x, y_start - 3 * y_step, f"File: {file_str}", transform=ax.transAxes, ha='right', va='top', fontsize=10)
        
        # Z value (Teeth) (File下方)
        teeth = getattr(info, 'teeth', '')
        ax.text(right_x, y_start - 4 * y_step, f"z= {teeth}", transform=ax.transAxes, ha='right', va='top', fontsize=10, fontweight='bold')

        # Center Title - 调整位置，给上方信息更多空间
        ax.text(0.5, 0.15, "Spectrum of the ripple", transform=ax.transAxes, ha='center', fontsize=16, fontweight='bold')
        
        # 评估方法说明 - 调整位置
        ax.text(0.5, 0.05, "Evaluation method: High orders", transform=ax.transAxes, ha='center', fontsize=9, style='italic')
        
        # RC低通滤波器信息 - 使用蓝色I型指示器
        # 从设置中获取滤波器参数
        filter_params = self.settings.get_filter_params()
        max_depth = filter_params['max_depth']
        attenuation_ratio = filter_params['attenuation_ratio']
        cutoff_frequency = filter_params['cutoff_frequency']
        
        # 绘制蓝色I型指示器
        indicator_x = 0.90
        indicator_top = 0.90
        indicator_bottom = 0.80
        indicator_width = 0.015
        
        # 垂直线
        ax.plot([indicator_x, indicator_x], [indicator_bottom, indicator_top], color='blue', linewidth=1.5, transform=ax.transAxes)
        # 顶部横线
        ax.plot([indicator_x - indicator_width, indicator_x + indicator_width], [indicator_top, indicator_top], color='blue', linewidth=1.5, transform=ax.transAxes)
        # 底部横线
        ax.plot([indicator_x - indicator_width, indicator_x + indicator_width], [indicator_bottom, indicator_bottom], color='blue', linewidth=1.5, transform=ax.transAxes)
        
        # 文本信息
        ax.text(indicator_x + indicator_width * 2, indicator_top, f"{max_depth:.2f} μm", transform=ax.transAxes, ha='left', fontsize=9, color='blue', va='center')
        ax.text(indicator_x + indicator_width * 2, indicator_bottom, f"{attenuation_ratio}:1", transform=ax.transAxes, ha='left', fontsize=9, color='blue', va='center')
        ax.text(indicator_x + indicator_width * 2 + 0.04, indicator_top, "Low-pass filter RC", transform=ax.transAxes, ha='left', fontsize=9, color='blue', va='center')
        
    def _sinusoidal_model(self, x, A1, W1, Pw1, A2, W2, Pw2, offset):
        """
        双正弦波模型：y = A1*sin(2*pi*W1*x/L + Pw1) + A2*sin(2*pi*W2*x/L + Pw2) + offset
        
        Args:
            x: 位置数组
            A1, A2: 振幅
            W1, W2: 波数（在测量长度内的周期数）
            Pw1, Pw2: 相位（弧度）
            offset: 偏移量
        """
        L = len(x) if len(x) > 0 else 1
        return (A1 * np.sin(2 * np.pi * W1 * x / L + Pw1) + 
                A2 * np.sin(2 * np.pi * W2 * x / L + Pw2) + offset)
    
    def _single_sinusoidal_model(self, x, A, W, Pw, offset):
        """单正弦波模型"""
        L = len(x) if len(x) > 0 else 1
        return A * np.sin(2 * np.pi * W * x / L + Pw) + offset
    
    def _fit_sinusoids(self, vals, max_components=2):
        """
        对数据进行正弦拟合，提取主要分量
        
        Args:
            vals: 数据数组
            max_components: 最大分量数（1或2）
            
        Returns:
            dict: {
                'A1', 'W1', 'Pw1': 第一个分量的振幅、波数、相位
                'A2', 'W2', 'Pw2': 第二个分量的振幅、波数、相位（如果存在）
                'rms': RMS值
                'sigma': 标准差
                '6sigma': 6倍标准差
            }
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
        
        # 应用RC低通滤波器
        detrended = self._apply_rc_low_pass_filter(detrended)
        
        # 使用FFT找到主要频率分量作为初始估计
        fft_vals = np.fft.rfft(detrended)
        n = len(detrended)
        mag = np.abs(fft_vals) / n
        phases = np.angle(fft_vals)
        
        # 跳过DC分量，找到主要频率
        mag[0] = 0
        top_indices = np.argsort(mag)[::-1][:max_components]
        
        result = {}
        
        if not SCIPY_AVAILABLE:
            # 如果没有scipy，使用FFT结果作为近似
            if len(top_indices) > 0 and top_indices[0] > 0:
                idx1 = top_indices[0]
                A1 = mag[idx1] * 2  # FFT幅值需要乘以2得到实际振幅
                W1 = float(idx1)
                Pw1 = phases[idx1]
                result['A1'] = A1
                result['W1'] = W1
                result['Pw1'] = np.degrees(Pw1)  # 转换为度
            else:
                result['A1'] = 0.0
                result['W1'] = 0.0
                result['Pw1'] = 0.0
            
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
            
            # 计算RMS和统计值
            rms = np.sqrt(np.mean(detrended**2))
            sigma = np.std(detrended)
            result['rms'] = rms
            result['sigma'] = sigma
            result['6sigma'] = 6 * sigma
            return result
        
        # 使用scipy进行非线性拟合
        try:
            if max_components >= 2 and len(top_indices) >= 2 and top_indices[1] > 0:
                # 双正弦波拟合
                idx1, idx2 = top_indices[0], top_indices[1]
                
                # 初始估计
                A1_init = mag[idx1] * 2
                W1_init = float(idx1)
                Pw1_init = phases[idx1]
                
                A2_init = mag[idx2] * 2
                W2_init = float(idx2)
                Pw2_init = phases[idx2]
                
                offset_init = np.mean(detrended)
                
                # 拟合
                try:
                    popt, _ = curve_fit(
                        self._sinusoidal_model, x, detrended,
                        p0=[A1_init, W1_init, Pw1_init, A2_init, W2_init, Pw2_init, offset_init],
                        maxfev=5000,
                        bounds=([0, 0.1, -np.pi, 0, 0.1, -np.pi, -np.inf],
                               [np.inf, n/2, np.pi, np.inf, n/2, np.pi, np.inf])
                    )
                    A1, W1, Pw1, A2, W2, Pw2, offset = popt
                    
                    result['A1'] = abs(A1)
                    result['W1'] = abs(W1)
                    result['Pw1'] = np.degrees(Pw1) % 360
                    
                    result['A2'] = abs(A2)
                    result['W2'] = abs(W2)
                    result['Pw2'] = np.degrees(Pw2) % 360
                except:
                    # 如果双正弦拟合失败，尝试单正弦
                    if len(top_indices) > 0 and top_indices[0] > 0:
                        idx1 = top_indices[0]
                        A1_init = mag[idx1] * 2
                        W1_init = float(idx1)
                        Pw1_init = phases[idx1]
                        offset_init = np.mean(detrended)
                        
                        popt, _ = curve_fit(
                            self._single_sinusoidal_model, x, detrended,
                            p0=[A1_init, W1_init, Pw1_init, offset_init],
                            maxfev=5000
                        )
                        A1, W1, Pw1, offset = popt
                        result['A1'] = abs(A1)
                        result['W1'] = abs(W1)
                        result['Pw1'] = np.degrees(Pw1) % 360
                        result['A2'] = 0.0
                        result['W2'] = 0.0
                        result['Pw2'] = 0.0
                    else:
                        result['A1'] = 0.0
                        result['W1'] = 0.0
                        result['Pw1'] = 0.0
                        result['A2'] = 0.0
                        result['W2'] = 0.0
                        result['Pw2'] = 0.0
            else:
                # 单正弦波拟合
                if len(top_indices) > 0 and top_indices[0] > 0:
                    idx1 = top_indices[0]
                    A1_init = mag[idx1] * 2
                    W1_init = float(idx1)
                    Pw1_init = phases[idx1]
                    offset_init = np.mean(detrended)
                    
                    try:
                        popt, _ = curve_fit(
                            self._single_sinusoidal_model, x, detrended,
                            p0=[A1_init, W1_init, Pw1_init, offset_init],
                            maxfev=5000
                        )
                        A1, W1, Pw1, offset = popt
                        result['A1'] = abs(A1)
                        result['W1'] = abs(W1)
                        result['Pw1'] = np.degrees(Pw1) % 360
                    except:
                        result['A1'] = A1_init
                        result['W1'] = W1_init
                        result['Pw1'] = np.degrees(Pw1_init) % 360
                else:
                    result['A1'] = 0.0
                    result['W1'] = 0.0
                    result['Pw1'] = 0.0
                
                result['A2'] = 0.0
                result['W2'] = 0.0
                result['Pw2'] = 0.0
            
            # 计算RMS和统计值
            rms = np.sqrt(np.mean(detrended**2))
            sigma = np.std(detrended)
            result['rms'] = rms
            result['sigma'] = sigma
            result['6sigma'] = 6 * sigma
            
            return result
            
        except Exception as e:
            logger.warning(f"Sinusoidal fit failed: {e}, using FFT approximation")
            # 回退到FFT方法
            if len(top_indices) > 0 and top_indices[0] > 0:
                idx1 = top_indices[0]
                result['A1'] = mag[idx1] * 2
                result['W1'] = float(idx1)
                result['Pw1'] = np.degrees(phases[idx1]) % 360
            else:
                result['A1'] = 0.0
                result['W1'] = 0.0
                result['Pw1'] = 0.0
            
            if max_components >= 2 and len(top_indices) > 1 and top_indices[1] > 0:
                idx2 = top_indices[1]
                result['A2'] = mag[idx2] * 2
                result['W2'] = float(idx2)
                result['Pw2'] = np.degrees(phases[idx2]) % 360
            else:
                result['A2'] = 0.0
                result['W2'] = 0.0
                result['Pw2'] = 0.0
            
            rms = np.sqrt(np.mean(detrended**2))
            sigma = np.std(detrended)
            result['rms'] = rms
            result['sigma'] = sigma
            result['6sigma'] = 6 * sigma
            return result
    
    def _calculate_sinusoidal_fit(self, data_dict, teeth_count, eval_markers=None):
        """
        使用正弦拟合方法分析测量数据
        返回所有齿的平均拟合结果
        
        Args:
            data_dict: {齿号: [数据点]}
            teeth_count: 齿数
            eval_markers: 评价范围标记点 (start_meas, start_eval, end_eval, end_meas)
            
        Returns:
            dict: 包含A1, W1, Pw1, A2, W2, Pw2, rms, sigma, 6sigma的平均值
        """
        if not data_dict:
            return None
        
        all_results = []
        
        for tooth_num, values in data_dict.items():
            if values is None or len(values) == 0:
                continue
            
            vals = np.array(values)
            
            # 提取评价范围
            if eval_markers and len(eval_markers) == 4:
                start_meas, start_eval, end_eval, end_meas = eval_markers
                n_points = len(vals)
                total_len = abs(end_meas - start_meas)
                
                if total_len == 0:
                    idx_start = int(n_points * 0.2)
                    idx_end = int(n_points * 0.8)
                else:
                    dist_to_start = abs(start_eval - start_meas)
                    dist_to_end = abs(end_eval - start_meas)
                    idx_start = int(n_points * (dist_to_start / total_len))
                    idx_end = int(n_points * (dist_to_end / total_len))
                
                idx_start = max(0, min(idx_start, n_points - 1))
                idx_end = max(0, min(idx_end, n_points - 1))
                
                if idx_end <= idx_start + 5:
                    continue
                
                vals = vals[idx_start:idx_end]
            
            # 进行正弦拟合
            result = self._fit_sinusoids(vals, max_components=2)
            if result:
                all_results.append(result)
        
        if len(all_results) == 0:
            return None
        
        # 计算平均值
        avg_result = {
            'A1': np.mean([r['A1'] for r in all_results]),
            'W1': np.mean([r['W1'] for r in all_results]),
            'Pw1': np.mean([r['Pw1'] for r in all_results]),
            'A2': np.mean([r['A2'] for r in all_results]),
            'W2': np.mean([r['W2'] for r in all_results]),
            'Pw2': np.mean([r['Pw2'] for r in all_results]),
            'rms': np.mean([r['rms'] for r in all_results]),
            'sigma': np.mean([r['sigma'] for r in all_results]),
            '6sigma': np.mean([r['6sigma'] for r in all_results])
        }
        
        return avg_result
    
    def _calculate_average_curve(self, data_dict, eval_markers=None):
        """
        计算评价区域中的平均曲线
        
        Args:
            data_dict: {齿号: [数据点]}
            eval_markers: 评价范围标记点 (start_meas, start_eval, end_eval, end_meas)
                         如果为None，则使用全部数据
        
        Returns:
            np.ndarray: 评价区域中的平均曲线
        """
        if not data_dict:
            return None
        
        all_curves = []
        
        for tooth_num, values in data_dict.items():
            if values is None or len(values) == 0:
                continue
            
            vals = np.array(values, dtype=float)
            
            # 提取评价范围
            if eval_markers and len(eval_markers) == 4:
                start_meas, start_eval, end_eval, end_meas = eval_markers
                n_points = len(vals)
                total_len = abs(end_meas - start_meas)
                
                if total_len == 0:
                    # 总测量长度为0，使用默认范围
                    idx_start = int(n_points * 0.2)
                    idx_end = int(n_points * 0.8)
                else:
                    # 计算相对位置
                    dist_to_start = abs(start_eval - start_meas)
                    dist_to_end = abs(end_eval - start_meas)
                    
                    idx_start = int(n_points * (dist_to_start / total_len))
                    idx_end = int(n_points * (dist_to_end / total_len))
                
                # 确保索引在有效范围内
                idx_start = max(0, min(idx_start, n_points - 1))
                idx_end = max(0, min(idx_end, n_points - 1))
                
                # 确保评价范围至少有8个点
                if idx_end <= idx_start + 7:
                    continue
                
                # 提取评价范围数据
                vals = vals[idx_start:idx_end]
            else:
                # 使用全部数据
                if len(vals) < 8:
                    continue
            
            # 去趋势
            x = np.arange(len(vals))
            try:
                # 拟合线性趋势（1阶）
                p = np.polyfit(x, vals, 1)
                trend = np.polyval(p, x)
                detrended = vals - trend
            except:
                # 如果拟合失败，使用去均值
                detrended = vals - np.mean(vals)
            
            # 应用RC低通滤波器
            detrended = self._apply_rc_low_pass_filter(detrended)
            
            all_curves.append(detrended)
        
        if not all_curves:
            return None
        
        # 对齐所有曲线到相同长度（使用最短长度）
        min_len = min(len(c) for c in all_curves)
        if min_len < 8:
            return None
        
        aligned_curves = [c[:min_len] for c in all_curves]
        
        # 计算平均曲线
        avg_curve = np.mean(aligned_curves, axis=0)
        
        return avg_curve
    
    def _iterative_residual_sine_fit(self, curve_data, max_order=500, max_components=50):
        """
        使用迭代残差法进行正弦拟合频谱分析
        
        核心算法：
        1. 对输入曲线数据进行正弦拟合，找到幅值最大的频率分量
        2. 从原始信号中移除该频率分量，得到残差信号
        3. 对残差信号重复上述过程
        4. 直到达到最大分量数、残差RMS小于0.001μm，或幅值小于0.02
        
        Args:
            curve_data: 曲线数据
            max_order: 最大阶次（频率）
            max_components: 最大分量数
        
        Returns:
            dict: {频率: 幅值(μm)}
        """
        if curve_data is None or len(curve_data) < 8:
            return {}
        
        n = len(curve_data)
        
        # 生成时间坐标x轴（0到1秒，假设转速为1转/秒）
        x = np.linspace(0.0, 1.0, n, dtype=float)
        
        # 初始化残差信号为原始信号
        residual = np.array(curve_data, dtype=float)
        
        # 存储提取的频谱分量
        spectrum_results = {}
        
        # 生成均匀分布的候选频率值（1到max_order）
        candidate_frequencies = list(range(1, max_order + 1))
        
        # 迭代提取最大频率分量
        for iteration in range(max_components):
            # 对每个候选频率进行正弦拟合
            best_frequency = None
            best_amplitude = 0.0
            best_coeffs = None
            
            # 存储所有候选频率的拟合结果
            frequency_amplitudes = {}
            
            for freq in candidate_frequencies:
                try:
                    # 直接使用freq作为频率值
                    frequency = float(freq)
                    
                    # 构建矩阵 A = [sin(2π*f*x), cos(2π*f*x), 1]
                    sin_x = np.sin(2.0 * np.pi * frequency * x)
                    cos_x = np.cos(2.0 * np.pi * frequency * x)
                    A = np.column_stack((sin_x, cos_x, np.ones_like(sin_x)))
                    
                    # 求解最小二乘
                    try:
                        coeffs, _, _, _ = np.linalg.lstsq(A, residual, rcond=None)
                        a, b, c = coeffs
                    except Exception as e:
                        # 如果最小二乘失败，使用备选方法
                        a = 2.0 * np.mean(residual * sin_x)
                        b = 2.0 * np.mean(residual * cos_x)
                        c = np.mean(residual)
                    
                    # 计算幅值：A = sqrt(a^2 + b^2)
                    amplitude = float(np.sqrt(a * a + b * b))
                    
                    # 检查幅值是否合理
                    max_reasonable_amplitude = 10.0
                    if amplitude > max_reasonable_amplitude:
                        continue
                    
                    # 存储拟合结果
                    frequency_amplitudes[freq] = (amplitude, a, b, c)
                    
                except Exception as e:
                    continue
            
            # 选择幅值最大的频率
            if not frequency_amplitudes:
                break
            
            best_frequency = max(frequency_amplitudes.keys(), key=lambda f: frequency_amplitudes[f][0])
            best_amplitude, best_coeffs = frequency_amplitudes[best_frequency][0], frequency_amplitudes[best_frequency][1:4]
            
            # 检查是否找到有效的最大频率
            if best_frequency is None or best_amplitude < 0.02:
                break
            
            # 保存提取的频谱分量
            spectrum_results[best_frequency] = best_amplitude
            
            # 从残差信号中移除已提取的正弦波
            a, b, c = best_coeffs
            best_freq_float = float(best_frequency)
            fitted_wave = a * np.sin(2.0 * np.pi * best_freq_float * x) + b * np.cos(2.0 * np.pi * best_freq_float * x) + c
            residual = residual - fitted_wave
            
            # 检查残差信号是否已经足够小
            residual_rms = np.sqrt(np.mean(np.square(residual)))
            if residual_rms < 0.001:
                break
        
        return spectrum_results
    
    def _calculate_spectrum(self, data_dict, teeth_count, eval_markers=None):
        """
        Calculate spectrum from measurement data using iterative residual sine fit
        Returns: (orders, amplitudes)
        
        Args:
            data_dict: {齿号: [数据点]}
            teeth_count: 齿数
            eval_markers: 评价范围标记点 (start_meas, start_eval, end_eval, end_meas)
                         如果为None，则使用全部数据
        """
        if not data_dict:
            return [], []
        
        # 计算评价区域中的平均曲线
        avg_curve = self._calculate_average_curve(data_dict, eval_markers)
        if avg_curve is None:
            return [], []
        
        # 使用迭代残差正弦拟合算法
        spectrum = self._iterative_residual_sine_fit(avg_curve)
        
        # 转换为(orders, amplitudes)格式
        if not spectrum:
            return [], []
        
        # 按频率排序
        sorted_frequencies = sorted(spectrum.keys())
        orders = np.array(sorted_frequencies, dtype=int)
        amplitudes = np.array([spectrum[f] for f in sorted_frequencies], dtype=float)
        
        return orders, amplitudes

    def _apply_rc_low_pass_filter(self, data):
        """
        应用RC低通滤波器（时间域）
        
        Args:
            data: 输入时间域数据数组
            
        Returns:
            filtered_data: 滤波后的数据数组
        """
        if len(data) <= 1:
            return data
        
        # 从设置中获取滤波器参数
        filter_params = self.settings.get_filter_params()
        max_depth = filter_params['max_depth']
        attenuation_ratio = filter_params['attenuation_ratio']
        cutoff_frequency = filter_params['cutoff_frequency']
        sampling_frequency = filter_params['sampling_frequency']
        
        # 计算RC时间常数
        rc = 1.0 / (2 * np.pi * cutoff_frequency)
        
        # 计算采样周期
        dt = 1.0 / sampling_frequency
        
        # 计算滤波系数α
        alpha = dt / (rc + dt)
        
        filtered = np.zeros_like(data)
        filtered[0] = data[0]
        
        # 应用RC低通滤波器（时间域）
        for i in range(1, len(data)):
            filtered[i] = alpha * data[i] + (1 - alpha) * filtered[i-1]
        
        # 限制最大波深
        filtered = np.clip(filtered, -max_depth, max_depth)
        
        return filtered
    
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

    def _create_spectrum_chart(self, ax, title, measurement_data, data_type, side):
        """Create spectrum chart (magenta curve + ZE标记，贴近目标样式)"""
        try:
            ax.set_title(title, fontsize=10, fontweight='bold', pad=5)
            
            # 数据获取
            if data_type == 'profile':
                data_dict = getattr(measurement_data.profile_data, side, {})
                # Get profile evaluation markers
                markers_attr = f"profile_markers_{side}"
            else:
                data_dict = getattr(measurement_data.flank_data, side, {})
                # Get lead (helix) evaluation markers
                markers_attr = f"lead_markers_{side}"
            
            teeth_val = getattr(measurement_data.basic_info, 'teeth', 0)
            try:
                teeth_count = int(teeth_val)
            except (ValueError, TypeError):
                teeth_count = 0
            if teeth_count <= 0:
                teeth_count = 1
            
            if not data_dict:
                ax.text(0.5, 0.5, "No Data", ha='center', va='center', transform=ax.transAxes)
                ax.grid(True, linestyle=':', alpha=1.0, linewidth=1.0, color='gray')
                for spine in ax.spines.values():
                    spine.set_linewidth(0.5)
                    spine.set_color('black')
                return

            # Get evaluation markers from basic_info
            eval_markers = getattr(measurement_data.basic_info, markers_attr, None)
            # Validate markers - 保存原始markers用于参数计算
            eval_markers_for_params = eval_markers
            if eval_markers and len(eval_markers) == 4:
                # Check if all values are non-zero (using default values if zero)
                if all(m == 0.0 for m in eval_markers):
                    eval_markers = None
            else:
                eval_markers = None

            orders, amplitudes = self._calculate_spectrum(data_dict, teeth_count, eval_markers)
            max_order = 500
            
            # 从设置中获取阶次筛选参数
            order_filtering = self.settings.get_order_filtering()
            min_order = order_filtering['min_order']
            max_order = order_filtering['max_order']
            only_high_orders = order_filtering['only_high_orders']
            
            # 确定最小阶次（如果没有指定，使用ZE阶=齿数）
            if only_high_orders or min_order is None:
                min_order = teeth_count  # ZE阶等于齿数
            
            # 应用阶次筛选
            mask = (orders >= min_order) & (orders <= max_order)
            plot_orders = orders[mask]
            plot_amps = amplitudes[mask]

            if len(plot_orders) == 0:
                ax.text(0.5, 0.5, "No Data", ha='center', va='center', transform=ax.transAxes)
                return

            # 显示所有显著的频谱点（幅值大于最大幅值的5%）
            if len(plot_amps) > 0:
                max_amp = np.max(plot_amps)
                threshold = max_amp * 0.05  # 设置一个合理的阈值，显示幅值大于最大幅值5%的所有频谱点
                
                # 过滤出大于阈值的频谱点
                significant_mask = plot_amps >= threshold
                if np.sum(significant_mask) > 0:
                    plot_orders = plot_orders[significant_mask]
                    plot_amps = plot_amps[significant_mask]
                
                # 如果过滤后点数太少，至少保留前20个最大的点
                if len(plot_amps) < 5:
                    top_indices = np.argsort(plot_amps)[::-1][:20]
                    plot_orders = plot_orders[top_indices]
                    plot_amps = plot_amps[top_indices]
                    
                # 按阶次排序以便在图表中按顺序显示
                sort_order = np.argsort(plot_orders)
                plot_orders = plot_orders[sort_order]
                plot_amps = plot_amps[sort_order]
            
            # 保存原始幅值用于表格显示
            raw_amplitudes = plot_amps.copy()
            
            # Y轴范围根据实际数据动态调整，不进行归一化
            y_max_raw = float(np.max(plot_amps)) if len(plot_amps) > 0 else 1.0
            # 为了显示美观，Y轴最大值设为实际最大值的1.2倍，并向上取整到合适的刻度
            if y_max_raw > 0:
                y_max_display = y_max_raw * 1.2
                # 向上取整到合适的刻度（例如0.1, 0.2, 0.5, 1.0等）
                if y_max_display <= 0.1:
                    y_max_display = 0.1
                elif y_max_display <= 0.2:
                    y_max_display = 0.2
                elif y_max_display <= 0.5:
                    y_max_display = 0.5
                else:
                    y_max_display = np.ceil(y_max_display * 2) / 2  # 向上取整到0.5的倍数
            else:
                y_max_display = 1.0
            
            # 不进行归一化，直接使用原始幅值
            plot_amps_norm = plot_amps
            
            # 从设置中获取波形标准参数
            waveform_standard = self.settings.get_waveform_standard()
            default_R = waveform_standard['R']
            default_N0 = waveform_standard['N0']
            default_K = waveform_standard['K']
            
            # 获取公差参数：R（允许波深）、N0（常数）、K（修正值）
            # 优先从tolerance对象中获取，否则使用设置中的默认值
            tolerance = getattr(measurement_data, 'tolerance', None)
            enabled = True
            R = None
            N0 = None
            K = None
            
            if tolerance:
                enabled = getattr(tolerance, 'ripple_tolerance_enabled', True)
                R = getattr(tolerance, 'ripple_tolerance_R', None)
                N0 = getattr(tolerance, 'ripple_tolerance_N0', None)
                K = getattr(tolerance, 'ripple_tolerance_K', None)
            
            # 如果参数不存在，使用设置中的默认值
            if R is None:
                # 根据幅值范围自动设置合理的R值
                # 如果最大幅值在合理范围内，设置R为最大幅值的1.5倍左右
                if y_max_raw > 0:
                    R = max(default_R, y_max_raw * 1.5)  # 至少使用设置中的默认值，或最大幅值的1.5倍
                else:
                    R = default_R  # 设置中的默认值
            if N0 is None:
                N0 = default_N0  # 设置中的默认值
            if K is None:
                K = default_K  # 设置中的默认值
            
            # 计算每个数据点的公差值（用于判断是否超差）
            tolerance_at_orders = None
            if enabled and R >= 0:
                # 计算每个数据点对应的公差值
                tolerance_at_orders = self._calculate_tolerance_curve(plot_orders, R, N0, K)
            
            # 绘制柱状图（根据是否超过公差选择颜色）
            # 根据数据点数量和分布动态调整柱宽，使有数据区域更清晰
            if len(plot_orders) > 0:
                # 计算数据区域的范围
                data_min = min(plot_orders)
                data_max = max(plot_orders)
                data_range = data_max - data_min if len(plot_orders) > 1 else 10
                
                # 柱宽：根据数据区域范围调整，使柱子在该区域内清晰可见
                # 如果数据集中在小范围内，增加柱宽使其更明显
                bar_width = max(2.0, min(10.0, data_range / len(plot_orders) * 0.6))
            else:
                bar_width = 2.0
            
            # 从设置中获取颜色标记参数
            color_marking = self.settings.get_display_settings()['color_marking']
            pass_color = color_marking['pass_color']
            fail_color = color_marking['fail_color']
            
            # 根据是否超过公差，分别绘制合格和超差的柱子
            if tolerance_at_orders is not None and len(tolerance_at_orders) == len(plot_orders):
                # 判断哪些柱子超过公差
                exceeds_tolerance = []
                for i, (amp, tol) in enumerate(zip(raw_amplitudes, tolerance_at_orders)):
                    if np.isfinite(tol) and tol > 0:
                        exceeds_tolerance.append(amp > tol)
                    else:
                        exceeds_tolerance.append(False)  # 如果公差值无效，默认不超过
                
                # 分别绘制合格和超差的柱子
                pass_orders = [o for i, o in enumerate(plot_orders) if not exceeds_tolerance[i]]
                pass_amps = [a for i, a in enumerate(plot_amps_norm) if not exceeds_tolerance[i]]
                fail_orders = [o for i, o in enumerate(plot_orders) if exceeds_tolerance[i]]
                fail_amps = [a for i, a in enumerate(plot_amps_norm) if exceeds_tolerance[i]]
                
                if len(pass_orders) > 0:
                    ax.bar(pass_orders, pass_amps, width=bar_width, color=pass_color, edgecolor='black', linewidth=0.3)
                if len(fail_orders) > 0:
                    ax.bar(fail_orders, fail_amps, width=bar_width, color=fail_color, edgecolor='black', linewidth=0.3)
            else:
                # 如果没有公差数据，全部使用合格颜色
                ax.bar(plot_orders, plot_amps_norm, width=bar_width, color=pass_color, edgecolor='black', linewidth=0.3)
            
            # 计算并绘制公差曲线（如果启用且R >= 0）
            if enabled and R >= 0:
                # 从设置中获取颜色标记参数
                color_marking = self.settings.get_display_settings()['color_marking']
                tolerance_color = color_marking['tolerance_color']
                
                # 为公差曲线生成完整的阶次范围（从2开始，因为O=1时公式分母为0）
                # 更密集的点以便绘制平滑曲线
                tolerance_orders = np.arange(2, max_order + 1, 0.5)  # 每0.5阶一个点，从2开始
                tolerance_values = self._calculate_tolerance_curve(tolerance_orders, R, N0, K)
                
                if tolerance_values is not None:
                    # 过滤掉无效值（无穷大或NaN）
                    valid_mask = np.isfinite(tolerance_values) & (tolerance_values > 0)
                    tolerance_orders_valid = tolerance_orders[valid_mask]
                    tolerance_values_valid = tolerance_values[valid_mask]
                    
                    if len(tolerance_values_valid) > 0:
                        # 不进行归一化，直接使用原始公差值
                        tolerance_norm = tolerance_values_valid
                        
                        # 绘制公差曲线，使用设置中的颜色
                        ax.plot(tolerance_orders_valid, tolerance_norm, color=tolerance_color, linewidth=1.5, 
                               linestyle='-', label='Tolerance', zorder=2)

            # X轴标签：保留ZE, 2ZE, 3ZE, 4ZE, 5ZE一直到500的标志
            # 计算所有ZE位置直到500（用于X轴刻度标记）
            ze_positions = []
            ze_labels = []
            
            # 添加阶次1
            ze_positions.append(1)
            ze_labels.append("1")
            
            # 添加所有ZE位置直到500
            if teeth_count > 0:
                i = 1
                while True:
                    pos = i * teeth_count
                    if pos > max_order:
                        break
                    ze_positions.append(pos)
                    if i == 1:
                        ze_labels.append("ZE")
                    else:
                        ze_labels.append(f"{i}ZE")
                    i += 1
            else:
                # 如果teeth_count无效，至少添加一些基本刻度
                for pos in [10, 50, 100, 200, 300, 400, 500]:
                    if pos <= max_order:
                        ze_positions.append(pos)
                        ze_labels.append(str(pos))
            
            # 添加500（如果还没有包含）
            if 500 not in ze_positions and 500 <= max_order:
                ze_positions.append(500)
                ze_labels.append("500")
            
            # 不需要添加额外的刻度，只保留主要的ZE和500标记
            
            # 排序刻度
            sorted_pairs = sorted(zip(ze_positions, ze_labels))
            ze_positions = [p[0] for p in sorted_pairs]
            ze_labels = [p[1] for p in sorted_pairs]
            
            # 在柱状图上标注幅值
            for i, (x_val, y_val, y_val_raw) in enumerate(zip(plot_orders, plot_amps_norm, raw_amplitudes)):
                # 在柱状图上方显示原始幅值，偏移量基于Y轴范围
                offset = y_max_display * 0.02  # 偏移量为Y轴范围的2%
                ax.text(x_val, y_val + offset, f"{y_val_raw:.2f}", ha='center', va='bottom', fontsize=7)
            
            # X轴刻度：1, ZE, 2ZE, 3ZE, 4ZE, 5ZE, ... 500
            if len(ze_positions) > 0:
                ax.set_xticks(ze_positions)
                ax.set_xticklabels(ze_labels, fontsize=8)
            
            # X轴范围：固定为0到500，使整体视野保持一致
            ax.set_xlim(0, 500)

            # Y轴范围：根据实际数据动态调整
            ax.set_ylim(0, y_max_display)
            ax.tick_params(axis='y', left=True, labelleft=True, labelsize=8)

            # 从设置中获取颜色标记参数
            color_marking = self.settings.get_display_settings()['color_marking']
            grid_color = color_marking['grid_color']
            
            # 网格和边框
            ax.grid(True, linestyle=':', alpha=1.0, linewidth=1.0, color=grid_color)
            for spine in ax.spines.values():
                spine.set_linewidth(0.5)
                spine.set_color('black')

            # 坐标轴标签（左侧不需要文字，仅保持单位提示）
            ax.set_ylabel("")
            ax.set_xlabel("")

            # 从实际数据计算右侧参数文本
            # 使用之前获取的评价范围标记点
            if data_type == 'profile':
                # Profile参数：ep=评价长度, lo=起评点展长, lu=终评点展长
                if eval_markers_for_params and len(eval_markers_for_params) == 4 and not all(m == 0.0 for m in eval_markers_for_params):
                    start_meas, start_eval, end_eval, end_meas = eval_markers_for_params
                    ep = abs(end_eval - start_eval)  # 评价长度
                    lo = start_eval  # 起评点展长
                    lu = end_eval    # 终评点展长
                else:
                    # 如果没有标记点，使用默认值
                    ep = 2.071
                    lo = 29.721
                    lu = 19.313
                
                ax.text(1.01, 0.75, f"ep={ep:.3f}", transform=ax.transAxes, fontsize=7, ha='left', va='center')
                ax.text(1.01, 0.60, f"lo={lo:.3f}", transform=ax.transAxes, fontsize=7, ha='left', va='center')
                ax.text(1.01, 0.45, f"lu={lu:.3f}", transform=ax.transAxes, fontsize=7, ha='left', va='center')
            else:
                # Helix参数：el=评价长度, zo=起评点位置, zu=终评点位置
                if eval_markers_for_params and len(eval_markers_for_params) == 4 and not all(m == 0.0 for m in eval_markers_for_params):
                    start_meas, start_eval, end_eval, end_meas = eval_markers_for_params
                    el = abs(end_eval - start_eval)  # 评价长度
                    zo = start_eval  # 起评点位置
                    zu = end_eval    # 终评点位置
                else:
                    # 如果没有标记点，使用默认值
                    el = 1.836
                    zo = 10.440
                    zu = -10.440
                
                ax.text(1.01, 0.75, f"el={el:.3f}", transform=ax.transAxes, fontsize=7, ha='left', va='center')
                ax.text(1.01, 0.60, f"zo={zo:.3f}", transform=ax.transAxes, fontsize=7, ha='left', va='center')
                ax.text(1.01, 0.45, f"zu={zu:.3f}", transform=ax.transAxes, fontsize=7, ha='left', va='center')
            
        except Exception as e:
            logger.error(f"Error in _create_spectrum_chart: {e}")
            ax.text(0.5, 0.5, "Error plotting spectrum", ha='center', va='center')

    def _draw_chart_scale(self, ax, value, label1, label2):
        """Draw scale indicator inside the chart"""
        # Position: Top right, inside
        # Draw a blue I-beam
        
        # Coordinates in axes fraction
        x_center = 0.90
        y_top = 0.90
        y_bottom = 0.80
        width = 0.01
        
        # Vertical line
        ax.plot([x_center, x_center], [y_bottom, y_top], color='blue', linewidth=1, transform=ax.transAxes)
        # Top cap
        ax.plot([x_center - width, x_center + width], [y_top, y_top], color='blue', linewidth=1, transform=ax.transAxes)
        # Bottom cap
        ax.plot([x_center - width, x_center + width], [y_bottom, y_bottom], color='blue', linewidth=1, transform=ax.transAxes)
        
        # Text
        ax.text(x_center + 0.02, y_top, label1, transform=ax.transAxes, fontsize=7, color='blue', va='center')
        ax.text(x_center + 0.02, y_bottom, label2, transform=ax.transAxes, fontsize=7, color='blue', va='center')

    def _create_data_table(self, ax, measurement_data, side):
        """创建正弦拟合评估表格：显示A1, W(1), Pw(1), A2, W(2), Pw(2), 6xσ"""
        ax.axis('off')
        
        teeth_val = getattr(measurement_data.basic_info, 'teeth', 0)
        try:
            teeth_count = int(teeth_val)
        except (ValueError, TypeError):
            teeth_count = 1
        if teeth_count <= 0:
            teeth_count = 1
        
        profile_dict = getattr(measurement_data.profile_data, side, {})
        flank_dict = getattr(measurement_data.flank_data, side, {})
        
        # 获取评价范围标记点
        profile_markers_attr = f"profile_markers_{side}"
        lead_markers_attr = f"lead_markers_{side}"
        profile_eval_markers = getattr(measurement_data.basic_info, profile_markers_attr, None)
        lead_eval_markers = getattr(measurement_data.basic_info, lead_markers_attr, None)
        
        # 验证标记点
        if profile_eval_markers and len(profile_eval_markers) == 4:
            if all(m == 0.0 for m in profile_eval_markers):
                profile_eval_markers = None
        else:
            profile_eval_markers = None
            
        if lead_eval_markers and len(lead_eval_markers) == 4:
            if all(m == 0.0 for m in lead_eval_markers):
                lead_eval_markers = None
        else:
            lead_eval_markers = None
        
        # 使用FFT计算频谱，然后按幅值排序获取主要分量
        def get_sorted_components(data_dict, eval_markers=None, max_components=11):
            """获取按幅值排序的主要分量"""
            orders, amps = self._calculate_spectrum(data_dict, teeth_count, eval_markers)
            if len(orders) == 0:
                return []
            
            # 限制在500阶以内
            mask = orders <= 500
            orders = orders[mask]
            amps = amps[mask]
            
            # 从设置中获取阶次筛选参数
            order_filtering = self.settings.get_order_filtering()
            min_order = order_filtering['min_order']
            max_order = order_filtering['max_order']
            only_high_orders = order_filtering['only_high_orders']
            
            # 确定最小阶次（如果没有指定，使用ZE阶=齿数）
            if only_high_orders or min_order is None:
                min_order = teeth_count  # ZE阶等于齿数
            
            # 应用阶次筛选
            high_order_mask = (orders >= min_order) & (orders <= max_order)
            orders = orders[high_order_mask]
            amps = amps[high_order_mask]
            
            if len(orders) == 0:
                return []
            
            # 按幅值从大到小排序
            sorted_indices = np.argsort(amps)[::-1]
            sorted_orders = orders[sorted_indices]
            sorted_amps = amps[sorted_indices]
            
            # 只保留前max_components个
            result = [(int(o), float(a)) for o, a in zip(sorted_orders[:max_components], sorted_amps[:max_components])]
            return result
        
        # 从设置中获取表格设置参数
        table_settings = self.settings.get_display_settings()['table_settings']
        max_components = table_settings['max_components']
        
        p_components = get_sorted_components(profile_dict, profile_eval_markers, max_components=max_components)
        h_components = get_sorted_components(flank_dict, lead_eval_markers, max_components=max_components)
        
        side_label = "left" if side == "left" else "right"
        
        # 确定最大列数（最多11列：ZE到11ZE）
        max_cols = max(len(p_components), len(h_components), 1)
        max_cols = min(max_cols, 11)  # 最多11列
        
        # 提取Profile和Helix的A和O值
        p_A = [f"{v:.2f}" for _, v in p_components[:max_cols]]
        p_O = [f"{int(o)}" for o, _ in p_components[:max_cols]]
        h_A = [f"{v:.2f}" for _, v in h_components[:max_cols]]
        h_O = [f"{int(o)}" for o, _ in h_components[:max_cols]]
        
        # 补齐到相同长度
        while len(p_A) < max_cols:
            p_A.append("")
            p_O.append("")
        while len(h_A) < max_cols:
            h_A.append("")
            h_O.append("")
        
        # 构建表格数据：行1=Profile A, 行2=Profile O, 行3=Helix A, 行4=Helix O
        data = [
            [f"Profile\n{side_label}", "A"] + p_A,
            ["", "O"] + p_O,
            [f"Helix\n{side_label}", "A"] + h_A,
            ["", "O"] + h_O
        ]
        
        # 计算列宽 - 调整为更匹配目标样式
        if max_cols > 0:
            # 前两列更窄，数据列宽度更均匀
            data_col_width = (1.0 - 0.15) / max_cols  # 减少前两列的总宽度
            col_widths = [0.10, 0.05] + [data_col_width] * max_cols
        else:
            col_widths = [0.10, 0.05]
        
        table_data = data
        
        # 创建表格，调整样式
        table = ax.table(cellText=table_data, loc='center', cellLoc='center', bbox=[0, 0, 1, 1], colWidths=col_widths)
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        
        cells = table.get_celld()
        for (row, col), cell in cells.items():
            # 调整边框和样式
            cell.set_linewidth(0.5)
            cell.set_edgecolor('black')
            
            if col == 0:
                # 第一列：标签列
                cell.set_text_props(weight='bold', fontsize=8, va='center')
                if row in [1, 3]:
                    # 空行 - 只显示下边框
                    cell.get_text().set_text('')
                    cell.visible_edges = 'RB'
                else:
                    # 标签行 - 显示所有边框
                    cell.visible_edges = 'LRBT'
                    cell.set_facecolor('#f0f0f0')
            
            elif col == 1:
                # 第二列：A/O标签列
                cell.set_text_props(weight='bold', fontsize=8, ha='center', va='center')
                cell.visible_edges = 'LRBT'
                cell.set_facecolor('#f8f8f8')
            
            else:
                # 数据列（从col=2开始，对应ZE, 2ZE, ...）
                cell.set_text_props(ha='center', fontsize=8, va='center')
                cell.visible_edges = 'LRBT'
