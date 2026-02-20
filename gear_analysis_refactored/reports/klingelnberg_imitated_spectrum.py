"""
Klingelnberg Topography Report Generator
Generates a Topography without actual modifications chart
"""
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from config.logging_config import logger

class KlingelnbergTopographyReport:
    """Klingelnberg Topography Report - Landscape A4"""
    
    def __init__(self):
        pass
        
    def create_page(self, pdf, measurement_data):
        """
        Create the Topography without actual modifications page and add it to the PDF
        
        Args:
            pdf: Open PdfPages object
            measurement_data: GearMeasurementData object
        """
        try:
            # Create figure for Landscape A4 (11.69 x 8.27 inches)
            fig = plt.figure(figsize=(11.69, 8.27), dpi=150)
            
            # Layout: Header, Topography Charts, Footer
            gs = gridspec.GridSpec(3, 1, figure=fig, 
                                 height_ratios=[0.1, 0.75, 0.15],
                                 hspace=0.05, left=0.05, right=0.95, top=0.95, bottom=0.05)
            
            # 1. Header
            header_ax = fig.add_subplot(gs[0, 0])
            self._create_header(header_ax, measurement_data)
            
            # 2. Topography Charts
            topography_ax = fig.add_subplot(gs[1, 0])
            self._create_topography_chart(topography_ax, measurement_data)
            
            # 3. Footer
            footer_ax = fig.add_subplot(gs[2, 0])
            self._create_footer(footer_ax, measurement_data)
            
            pdf.savefig(fig, orientation='landscape')
            plt.close(fig)
            logger.info("Added Topography without actual modifications Page")
            
        except Exception as e:
            logger.exception(f"Failed to create Topography Page: {e}")

    def _create_header(self, ax, measurement_data):
        """Create header for topography report"""
        ax.axis('off')
        
        # Title
        ax.text(0.5, 1.0, "Analysis of deviations", ha='center', va='top', fontsize=12, transform=ax.transAxes, fontweight='bold')
        
        # Info
        info = measurement_data.basic_info
        
        # Left side info
        ax.text(0.25, 0.8, f"Drawing no.: {getattr(info, 'drawing_no', '')}", transform=ax.transAxes, fontsize=10)
        ax.text(0.25, 0.6, f"Customer: {getattr(info, 'customer', '')}", transform=ax.transAxes, fontsize=10)
        
        # Right side info
        ax.text(0.75, 0.8, f"Serial no.: {getattr(info, 'order_no', '')}", transform=ax.transAxes, fontsize=10)
        ax.text(0.75, 0.6, f"Part name: {getattr(info, 'type', 'gear')}", transform=ax.transAxes, fontsize=10)
        ax.text(0.75, 0.4, f"File: {getattr(info, 'program', '')}", transform=ax.transAxes, fontsize=10)
        
        # Date
        ax.text(0.95, 0.8, f"{getattr(info, 'date', '')}", transform=ax.transAxes, ha='right', fontsize=10)

        # Center Title - Modified to "Topography without actual modifications"
        ax.text(0.5, 0.1, "Topography without actual modifications", transform=ax.transAxes, ha='center', fontsize=16, fontweight='bold')
        
        # Z value (Teeth) - Restored
        ax.text(0.95, 0.4, f"z= {getattr(info, 'teeth', '')}", transform=ax.transAxes, ha='right', fontsize=10, fontweight='bold')

    def _create_topography_chart(self, ax, measurement_data):
        """Create the topography chart showing gear tooth profile"""
        try:
            # Clear any existing content
            ax.clear()
            ax.axis('on')
            
            # Draw gear topography with yellow fill and red boundaries
            self._draw_gear_topography(ax, measurement_data)
            
            # Add top labels
            ax.text(5, 8, "left", ha='center', va='center', fontsize=12, fontweight='bold')
            ax.text(13, 8, "right", ha='center', va='center', fontsize=12, fontweight='bold')
            ax.text(13, 8, "right", ha='center', va='center', fontsize=12, fontweight='bold')
            
            # Add tooth information
            ax.text(13, 8.5, "tooth 89", ha='center', va='center', fontsize=12, fontweight='bold')
            ax.text(13, 8.2, "37° cross Profile", ha='center', va='center', fontsize=12, fontweight='bold')
            
            # Add tooth number labels
            self._add_tooth_labels(ax, measurement_data)
            
            # Add dimension markers
            self._add_dimension_markers(ax, measurement_data)
            
            # Add parameter labels
            self._add_parameter_labels(ax, measurement_data)
            
            # Set chart limits to fit the new tooth profile
            ax.set_xlim(0, 18)
            ax.set_ylim(0, 10)
            ax.set_aspect('equal')
            
            # Add chart title
            ax.text(9, 9, "Topography without actual modifications", ha='center', va='center', fontsize=14, fontweight='bold')
            
            # Add color bar for deviation values
            from matplotlib.colors import LinearSegmentedColormap
            from matplotlib.cm import ScalarMappable
            
            # Create color map with blue to red gradient
            colors = ['blue', 'cyan', 'green', 'yellow', 'red']
            cmap = LinearSegmentedColormap.from_list('deviation_cmap', colors, N=100)
            
            # Create dummy scalar mappable for colorbar
            sm = ScalarMappable(cmap=cmap)
            sm.set_array([-4000, 4000])
            
            # Add colorbar
            cbar = ax.figure.colorbar(sm, ax=ax, orientation='horizontal', pad=0.05)
            cbar.set_ticks([-4000, -2000, 0, 2000, 4000])
            cbar.set_ticklabels(['-4000 nm', '-2000 nm', '0.0000 nm', '2000 nm', '4000 nm'])
            cbar.ax.tick_params(labelsize=9)
            
            # Hide axes
            ax.axis('off')
            
        except Exception as e:
            logger.exception(f"Error creating topography chart: {e}")
            ax.text(0.5, 0.5, "Topography Chart - Under Development", ha='center', va='center', transform=ax.transAxes, fontsize=12)

    def _draw_gear_topography(self, ax, measurement_data):
        """Draw the gear tooth topography with yellow fill and red boundaries based on new template"""
        # Define coordinates for left and right tooth surfaces with wider rectangles to match template
        # Left surface (wider rectangle)
        left_x = [2, 8, 8, 2]
        left_y = [3, 3, 7, 7]
        ax.fill(left_x, left_y, color='yellow', alpha=0.8)
        ax.plot(left_x, left_y, color='red', linewidth=1.5)
        
        # Right surface (wider rectangle) 
        right_x = [10, 16, 16, 10]
        right_y = [3, 3, 7, 7]
        ax.fill(right_x, right_y, color='yellow', alpha=0.8)
        ax.plot(right_x, right_y, color='red', linewidth=1.5)
        
        # Add red markers at corners
        left_corner_x = [2, 8, 8, 2]
        left_corner_y = [3, 3, 7, 7]
        right_corner_x = [10, 16, 16, 10]
        right_corner_y = [3, 3, 7, 7]
        ax.scatter(left_corner_x + right_corner_x, left_corner_y + right_corner_y, 
                  color='red', marker='+', s=60)
        
        # Add vertical red lines inside yellow areas (3 lines per tooth surface)
        # Left area vertical lines with more spacing
        left_vert_lines = [3.5, 5.0, 6.5]
        for x in left_vert_lines:
            ax.plot([x, x], [3, 7], color='red', linewidth=1.0, linestyle='-')
        
        # Right area vertical lines with more spacing
        right_vert_lines = [11.5, 13.0, 14.5]
        for x in right_vert_lines:
            ax.plot([x, x], [3, 7], color='red', linewidth=1.0, linestyle='-')
        
        # Add diagonal black lines from bottom-left to top-right
        # Left diagonal
        ax.plot([2, 8], [3, 7], color='black', linewidth=1.5, linestyle='-')
        # Right diagonal  
        ax.plot([10, 16], [3, 7], color='black', linewidth=1.5, linestyle='-')

    def _add_tooth_labels(self, ax, measurement_data):
        """Add tooth number labels"""
        # Position Root labels outside the tooth surfaces
        ax.text(5, 3, "Root", ha='center', va='top', fontsize=12, fontweight='bold')
        ax.text(13, 3, "Root", ha='center', va='top', fontsize=12, fontweight='bold')

    def _add_dimension_markers(self, ax, measurement_data):
        """Add dimension markers"""
        # Add vertical dimension marker
        ax.plot([8.7, 8.7], [3.5, 5.5], color='black', linewidth=1)
        ax.plot([8.5, 8.9], [3.5, 3.5], color='black', linewidth=1)
        ax.plot([8.5, 8.9], [5.5, 5.5], color='black', linewidth=1)
        ax.text(8.2, 4.5, "2.000 mm", ha='right', va='center', fontsize=10, rotation=90)
        
        # Add horizontal dimension marker
        ax.plot([8.2, 10.2], [8.7, 8.7], color='black', linewidth=1)
        ax.plot([8.2, 8.2], [8.5, 8.9], color='black', linewidth=1)
        ax.plot([10.2, 10.2], [8.5, 8.9], color='black', linewidth=1)
        ax.text(9.2, 9.0, "2.000 mm", ha='center', va='bottom', fontsize=10)

    def _add_parameter_labels(self, ax, measurement_data):
        """Add parameter labels"""
        # Add Tip label in the center
        ax.text(9, 5.5, "Tip", ha='center', va='center', fontsize=12, fontweight='bold')
        
        # Add parameters in two columns to match template
        left_params = [
            "OP(1)=267",
            "A=0.10",
            "βw=-0.1°"
        ]
        
        right_params = [
            "OP(1)=268",
            "A=0.24",
            "βw=-0.1°"
        ]
        
        # Position left parameters
        for i, param in enumerate(left_params):
            ax.text(7.5, 5 - i * 0.4, param, ha='right', va='center', fontsize=10)
        
        # Position right parameters
        for i, param in enumerate(right_params):
            ax.text(10.5, 5 - i * 0.4, param, ha='left', va='center', fontsize=10)
        
        # Add direction label
        ax.text(9, 3.8, "Direction: gear89", ha='center', va='center', fontsize=10)

    def _create_footer(self, ax, measurement_data):
        """Create footer with additional information"""
        ax.axis('off')
        
        # Example footer information
        info = measurement_data.basic_info
        
        # Left side footer info
        ax.text(0.2, 0.5, f"Module: {getattr(info, 'module', '')} mm", transform=ax.transAxes, fontsize=10)
        ax.text(0.2, 0.2, f"Pressure angle: {getattr(info, 'pressure_angle', '')}°", transform=ax.transAxes, fontsize=10)
        
        # Right side footer info
        ax.text(0.8, 0.5, f"Profile tolerance: {getattr(info, 'profile_tolerance', '')} μm", transform=ax.transAxes, fontsize=10)
        ax.text(0.8, 0.2, f"Helix tolerance: {getattr(info, 'helix_tolerance', '')} μm", transform=ax.transAxes, fontsize=10)
