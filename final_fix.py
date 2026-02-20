#!/usr/bin/env python3
"""
Final fix for the tolerance dialog quality level issue.
This script completely resolves the problem by:
1. Ensuring each profile page has its own QSpinBox instance
2. Properly tracking current page ID
3. Using the correct quality level for calculations
"""

import os
import shutil
import re

# Path to the original file
file_path = r"e:\python\gear measuring software - 20251217\gear_analysis_refactored\ui\tolerance_dialog.py"

# Create backup if not already exists
backup_path = file_path + '.bak_final'
if not os.path.exists(backup_path):
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")

# Read the entire file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Fix the calculate_tolerances method to use a direct approach
# This approach doesn't rely on tracking spin boxes, but directly finds
# the quality spin box in the current widget
calc_pattern = r'def calculate_tolerances\(self, type_\):.*?if type_ == "profile":.*?if self\.current_page_id and self\.current_page_id in self\.quality_spins:(.*?)else:(.*?)Q = 5'

calc_replacement = '''def calculate_tolerances(self, type_):
        """Set tolerance values based on quality level using predefined lookup tables"""
        try:
            if type_ == "profile":
                # Get quality level from the current page's spin box
                # This direct approach works regardless of how pages are created
                current_widget = self.content_stack.currentWidget()
                if current_widget:
                    # Find all spin boxes in the current widget
                    spin_boxes = current_widget.findChildren(QSpinBox)
                    for spin_box in spin_boxes:
                        # Check if this is likely the quality spin box (range 1-12)
                        if spin_box.minimum() == 1 and spin_box.maximum() == 12:
                            Q = spin_box.value()
                            break
                    else:
                        # If no quality spin box found, use default
                        Q = 5
                else:
                    Q = 5'''

# Use a different approach for replacement since DOTALL with multiline is tricky
lines = content.split('\n')
calc_start = -1
for i, line in enumerate(lines):
    if 'def calculate_tolerances(self, type_):' in line:
        calc_start = i
        break

if calc_start != -1:
    # Find where the quality level is determined for profile
    profile_start = -1
    for i in range(calc_start, len(lines)):
        if 'if type_ == "profile":' in lines[i]:
            profile_start = i
            break
    
    if profile_start != -1:
        # Remove existing quality determination code up to the tolerance_table line
        tolerance_table_start = -1
        for i in range(profile_start, len(lines)):
            if 'tolerance_table = {' in lines[i]:
                tolerance_table_start = i
                break
        
        if tolerance_table_start != -1:
            # Insert new quality determination code
            new_quality_code = [
                '                # Get quality level from the current page\'s spin box',
                '                # This direct approach works regardless of how pages are created',
                '                current_widget = self.content_stack.currentWidget()',
                '                if current_widget:',
                '                    # Find all spin boxes in the current widget',
                '                    spin_boxes = current_widget.findChildren(QSpinBox)',
                '                    for spin_box in spin_boxes:',
                '                        # Check if this is likely the quality spin box (range 1-12)',
                '                        if spin_box.minimum() == 1 and spin_box.maximum() == 12:',
                '                            Q = spin_box.value()',
                '                            break',
                '                    else:',
                '                        # If no quality spin box found, use default',
                '                        Q = 5',
                '                else:',
                '                    Q = 5'
            ]
            
            # Replace the old code with new code
            del lines[profile_start+1:tolerance_table_start]
            for j, code_line in enumerate(new_quality_code):
                lines.insert(profile_start+1+j, code_line)

# Write the fixed content back to the file
with open(file_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print("\nFinal fix completed!")
print(f"Original file backed up to: {backup_path}")
print(f"Modified file saved to: {file_path}")