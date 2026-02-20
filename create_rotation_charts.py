import matplotlib.pyplot as plt
import numpy as np
from parse_mka_file import MKAParser

class RotationChartGenerator:
    def __init__(self, file_path):
        self.parser = MKAParser(file_path)
        self.combined_data = self.parser.get_combined_data(use_evaluation_range=True)
        self.evaluation_ranges = self.parser.get_evaluation_ranges()
        self.basic_info = {
            'teeth': self.parser.get_teeth_count() or 87,
            'module': self.parser.get_module(),
            'helix_angle': self.parser.get_helix_angle(),
            'pressure_angle': self.parser.get_pressure_angle(),
            'face_width': self.parser.get_face_width()
        }
        # Get pitch data
        self.pitch_data = self.parser.pitch_data
    
    def process_data(self, data, filter_points=True, max_points=1000):
        """
        Process data for plotting
        - Filter out extreme values
        - Resample if needed
        - Center data around zero
        """
        if not data:
            return np.array([]), np.array([])
        
        angles, values = zip(*data)
        angles = np.array(angles)
        values = np.array(values)
        
        # Filter out extreme values
        if filter_points:
            mean_val = np.mean(values)
            std_val = np.std(values)
            mask = np.abs(values - mean_val) < 3 * std_val
            angles = angles[mask]
            values = values[mask]
        
        # Resample if too many points
        if len(angles) > max_points:
            indices = np.linspace(0, len(angles) - 1, max_points, dtype=int)
            angles = angles[indices]
            values = values[indices]
        
        # Center data around zero
        values = values - np.mean(values)
        
        return angles, values
    
    def create_rotation_charts(self, output_file='rotation_charts.pdf'):
        """
        Create rotation charts for one complete revolution
        """
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Gear Rotation Analysis - One Complete Revolution', fontsize=16, fontweight='bold')
        
        # Plot profile left (tooth profile left)
        ax1 = axes[0, 0]
        data = self.combined_data.get('profile_left', [])
        if data:
            self._plot_separate_teeth(ax1, data, 'b', 'Tooth Profile - Left Side')
        else:
            ax1.set_title('Tooth Profile - Left Side')
            ax1.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax1.transAxes)
            ax1.set_xlabel('Rotation Angle (degrees)')
            ax1.set_ylabel('Deviation (μm)')
            ax1.set_xlim(0, 360)
            ax1.set_xticks(np.arange(0, 361, 60))
        
        # Plot profile right (tooth profile right)
        ax2 = axes[0, 1]
        data = self.combined_data.get('profile_right', [])
        if data:
            self._plot_separate_teeth(ax2, data, 'r', 'Tooth Profile - Right Side')
        else:
            ax2.set_title('Tooth Profile - Right Side')
            ax2.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_xlabel('Rotation Angle (degrees)')
            ax2.set_ylabel('Deviation (μm)')
            ax2.set_xlim(0, 360)
            ax2.set_xticks(np.arange(0, 361, 60))
        
        # Plot flank left (tooth flank left)
        ax3 = axes[1, 0]
        data = self.combined_data.get('flank_left', [])
        if data:
            self._plot_separate_teeth(ax3, data, 'g', 'Tooth Flank - Left Side')
            # Add center line at midpoint of face width
            face_width = self.basic_info['face_width']
            if face_width > 0:
                center_note = f'Face Width: {face_width} mm\nReference: Midpoint'
                ax3.text(0.05, 0.95, center_note, transform=ax3.transAxes, 
                        verticalalignment='top', bbox=dict(boxstyle='round', alpha=0.1))
        else:
            ax3.set_title('Tooth Flank - Left Side')
            ax3.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_xlabel('Rotation Angle (degrees)')
            ax3.set_ylabel('Deviation (μm)')
            ax3.set_xlim(0, 360)
            ax3.set_xticks(np.arange(0, 361, 60))
        
        # Plot flank right (tooth flank right)
        ax4 = axes[1, 1]
        data = self.combined_data.get('flank_right', [])
        if data:
            self._plot_separate_teeth(ax4, data, 'm', 'Tooth Flank - Right Side')
        else:
            ax4.set_title('Tooth Flank - Right Side')
            ax4.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax4.transAxes)
            ax4.set_xlabel('Rotation Angle (degrees)')
            ax4.set_ylabel('Deviation (μm)')
            ax4.set_xlim(0, 360)
            ax4.set_xticks(np.arange(0, 361, 60))
        
        # Add gear information
        info_text = f"Gear Parameters:\n"
        info_text += f"Teeth: {self.basic_info['teeth']}\n"
        info_text += f"Module: {self.basic_info['module']} mm\n"
        info_text += f"Helix Angle: {self.basic_info['helix_angle']}°\n"
        info_text += f"Pressure Angle: {self.basic_info['pressure_angle']}°\n"
        info_text += f"Face Width: {self.basic_info['face_width']} mm"
        
        # Add pitch data information
        pitch_info = "\nPitch Data:\n"
        for side in ['left', 'right']:
            pitch_values = []
            for tooth_id, data in self.pitch_data[side].items():
                pitch_values.extend(data)
            if pitch_values:
                avg_pitch = sum(pitch_values) / len(pitch_values)
                max_pitch = max(pitch_values)
                min_pitch = min(pitch_values)
                pitch_info += f"{side.capitalize()}: Avg={avg_pitch:.3f} μm, Max={max_pitch:.3f} μm, Min={min_pitch:.3f} μm\n"
        
        info_text += pitch_info
        info_text += "\nNote: Rotation angles adjusted for pitch deviations"
        
        # Add info box to the figure
        fig.text(0.02, 0.02, info_text, fontsize=10, 
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Adjust layout
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        
        # Save the figure
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Rotation charts saved to: {output_file}")
        return output_file
    
    def _plot_separate_teeth(self, ax, data, color, title):
        """
        Plot each tooth as a separate line segment
        """
        teeth = self.basic_info['teeth']
        angle_per_tooth = 360.0 / teeth
        
        # Process data
        angles, values = zip(*data)
        angles = np.array(angles)
        values = np.array(values)
        
        # Filter out extreme values
        mean_val = np.mean(values)
        std_val = np.std(values)
        mask = np.abs(values - mean_val) < 3 * std_val
        angles = angles[mask]
        values = values[mask]
        
        # Resample if too many points
        max_points = 2000
        if len(angles) > max_points:
            indices = np.linspace(0, len(angles) - 1, max_points, dtype=int)
            angles = angles[indices]
            values = values[indices]
        
        # Center data around zero
        values = values - np.mean(values)
        
        # Group data by tooth
        tooth_data = {}
        for angle, val in zip(angles, values):
            tooth_index = int(angle / angle_per_tooth)
            if tooth_index not in tooth_data:
                tooth_data[tooth_index] = []
            tooth_data[tooth_index].append((angle, val))
        
        # Plot each tooth separately
        for tooth_index, points in tooth_data.items():
            if len(points) < 2:
                continue
            # Sort points by angle
            points.sort(key=lambda x: x[0])
            tooth_angles, tooth_values = zip(*points)
            # Plot this tooth's data
            ax.plot(tooth_angles, tooth_values, '-', color=color, linewidth=0.5, alpha=0.7)
        
        # Set axis properties
        ax.set_title(title)
        ax.set_xlabel('Rotation Angle (degrees)')
        ax.set_ylabel('Deviation (μm)')
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.set_xlim(0, 360)
        ax.set_xticks(np.arange(0, 361, 60))
        
        # Add tooth separation lines
        for i in range(teeth + 1):
            angle = (i / teeth) * 360
            ax.axvline(x=angle, color='r', linestyle=':', alpha=0.3)
        
        # Add evaluation range information
        if 'Profile' in title:
            eval_range = self.evaluation_ranges.get('profile', {})
            if eval_range.get('start', 0) > 0 and eval_range.get('end', 0) > 0:
                range_text = f'Evaluation Range:\nStart: {eval_range["start"]} mm\nEnd: {eval_range["end"]} mm'
                ax.text(0.05, 0.05, range_text, transform=ax.transAxes, 
                        verticalalignment='bottom', bbox=dict(boxstyle='round', alpha=0.1))
        elif 'Flank' in title:
            eval_range = self.evaluation_ranges.get('flank', {})
            if eval_range.get('start', 0) > 0 and eval_range.get('end', 0) > 0:
                range_text = f'Evaluation Range:\nStart: {eval_range["start"]} mm\nEnd: {eval_range["end"]} mm'
                ax.text(0.05, 0.05, range_text, transform=ax.transAxes, 
                        verticalalignment='bottom', bbox=dict(boxstyle='round', alpha=0.1))
        # Add note that data is within evaluation range
        ax.text(0.95, 0.05, 'Data within evaluation range', transform=ax.transAxes, 
                verticalalignment='bottom', horizontalalignment='right', 
                bbox=dict(boxstyle='round', alpha=0.1, facecolor='lightgreen'))
    
    def create_detailed_rotation_chart(self, output_file='detailed_rotation_chart.pdf'):
        """
        Create a detailed rotation chart with all four datasets overlayed
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        fig.suptitle('Detailed Gear Rotation Analysis - One Complete Revolution', fontsize=16, fontweight='bold')
        
        # Plot all datasets
        datasets = [
            ('profile_left', 'Tooth Profile Left', 'blue', 0.7),
            ('profile_right', 'Tooth Profile Right', 'red', 0.7),
            ('flank_left', 'Tooth Flank Left', 'green', 0.7),
            ('flank_right', 'Tooth Flank Right', 'magenta', 0.7)
        ]
        
        for data_key, label, color, alpha in datasets:
            data = self.combined_data.get(data_key, [])
            if data:
                angles, values = zip(*data)
                angles = np.array(angles)
                values = np.array(values)
                
                # Filter out extreme values
                mean_val = np.mean(values)
                std_val = np.std(values)
                mask = np.abs(values - mean_val) < 3 * std_val
                angles = angles[mask]
                values = values[mask]
                
                # Resample if too many points
                max_points = 1000
                if len(angles) > max_points:
                    indices = np.linspace(0, len(angles) - 1, max_points, dtype=int)
                    angles = angles[indices]
                    values = values[indices]
                
                # Center data around zero
                values = values - np.mean(values)
                
                ax.plot(angles, values, '-', color=color, label=label, linewidth=0.8, alpha=alpha)
        
        # Add tooth markers
        teeth = self.basic_info['teeth']
        for i in range(teeth):
            angle = (i / teeth) * 360
            ax.axvline(x=angle, color='gray', linestyle=':', alpha=0.3)
        
        # Add reference line at zero
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # Add labels and legend
        ax.set_xlabel('Rotation Angle (degrees)', fontsize=12)
        ax.set_ylabel('Deviation (μm)', fontsize=12)
        ax.set_xlim(0, 360)
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.legend(loc='upper right', fontsize=10)
        
        # Add evaluation range information
        eval_text = "Evaluation Ranges:\n"
        if self.evaluation_ranges['profile']['start'] > 0:
            eval_text += f"Profile: {self.evaluation_ranges['profile']['start']} - {self.evaluation_ranges['profile']['end']} mm\n"
        if self.evaluation_ranges['flank']['start'] > 0:
            eval_text += f"Flank: {self.evaluation_ranges['flank']['start']} - {self.evaluation_ranges['flank']['end']} mm\n"
        eval_text += "\nData displayed within evaluation ranges only"
        
        fig.text(0.02, 0.02, eval_text, fontsize=10, 
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Add gear information
        info_text = f"Gear Parameters:\n"
        info_text += f"Teeth: {self.basic_info['teeth']}\n"
        info_text += f"Module: {self.basic_info['module']} mm\n"
        info_text += f"Pressure Angle: {self.basic_info['pressure_angle']}°\n"
        info_text += f"Face Width: {self.basic_info['face_width']} mm"
        
        # Add pitch data information
        pitch_info = "\nPitch Data:\n"
        for side in ['left', 'right']:
            pitch_values = []
            for tooth_id, data in self.pitch_data[side].items():
                pitch_values.extend(data)
            if pitch_values:
                avg_pitch = sum(pitch_values) / len(pitch_values)
                pitch_info += f"{side.capitalize()}: Avg={avg_pitch:.3f} μm\n"
        
        info_text += pitch_info
        info_text += "\nNote: Rotation angles adjusted for pitch deviations"
        
        fig.text(0.7, 0.02, info_text, fontsize=10, 
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Adjust layout
        plt.tight_layout(rect=[0, 0.1, 1, 0.95])
        
        # Save the figure
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Detailed rotation chart saved to: {output_file}")
        return output_file

if __name__ == '__main__':
    # Create rotation charts
    mka_file = '263751-018-WAV.mka'
    generator = RotationChartGenerator(mka_file)
    
    # Create individual charts
    generator.create_rotation_charts('rotation_charts_with_pitch.pdf')
    
    # Create detailed overlay chart
    generator.create_detailed_rotation_chart('detailed_rotation_chart_with_pitch.pdf')
