#!/usr/bin/env python3
"""
Direct fix for the tolerance dialog quality level issue.
This script directly edits the file with a simpler approach.
"""

import os
import shutil

# Path to the original file
file_path = r"e:\python\gear measuring software - 20251217\gear_analysis_refactored\ui\tolerance_dialog.py"

# Create backup if not already exists
backup_path = file_path + '.bak_direct'
if not os.path.exists(backup_path):
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")

# Read the entire file
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Step 1: Find and fix the __init__ method to add current_page_id
init_start = -1
for i, line in enumerate(lines):
    if 'def __init__' in line and 'gear_data=None' in line:
        init_start = i
        break

if init_start != -1:
    # Find the end of __init__ method (next method definition)
    init_end = -1
    for i in range(init_start + 1, len(lines)):
        if lines[i].strip().startswith('def '):
            init_end = i
            break
    
    if init_end != -1:
        # Insert current_page_id and quality_spins after gear_data initialization
        for i in range(init_start, init_end):
            if 'self.gear_data' in lines[i]:
                # Insert after gear_data line
                insert_pos = i + 1
                lines.insert(insert_pos, '        self.current_page_id = None  # Track current page ID\n')
                lines.insert(insert_pos + 1, '        self.quality_spins = {}  # Dictionary to store quality spin boxes\n')
                break

# Step 2: Find and fix on_tree_item_clicked to track current page
on_tree_start = -1
for i, line in enumerate(lines):
    if 'def on_tree_item_clicked' in line:
        on_tree_start = i
        break

if on_tree_start != -1:
    # Find where page_id is set
    for i in range(on_tree_start, len(lines)):
        if 'page_id = item.data' in lines[i]:
            # Find the return line after page_id check
            for j in range(i, len(lines)):
                if 'return' in lines[j] and 'page_id is None' in lines[j-1]:
                    # Insert after return line
                    insert_pos = j + 1
                    lines.insert(insert_pos, '        self.current_page_id = page_id  # Track current page\n')
                    break
            break

# Step 3: Find and fix calculate_tolerances method
calc_start = -1
for i, line in enumerate(lines):
    if 'def calculate_tolerances' in line:
        calc_start = i
        break

if calc_start != -1:
    # Fix the method signature first
    lines[calc_start] = lines[calc_start].replace('\\(self, type_\\)', '(self, type_)')
    
    # Find the Q = self.profile_quality_spin.value() line
    for i in range(calc_start, len(lines)):
        if 'Q = self.profile_quality_spin.value()' in lines[i]:
            # Replace this line with the new logic
            lines[i] = '                # Get quality level from the current page\n'
            lines.insert(i+1, '                Q = 5  # Default value\n')
            lines.insert(i+2, '                current_widget = self.content_stack.currentWidget()\n')
            lines.insert(i+3, '                if current_widget:\n')
            lines.insert(i+4, '                    # Find the quality spin box in the current widget\n')
            lines.insert(i+5, '                    from PyQt5.QtWidgets import QSpinBox\n')
            lines.insert(i+6, '                    spin_boxes = current_widget.findChildren(QSpinBox)\n')
            lines.insert(i+7, '                    for spin_box in spin_boxes:\n')
            lines.insert(i+8, '                        if spin_box.minimum() == 1 and spin_box.maximum() == 12:\n')
            lines.insert(i+9, '                            Q = spin_box.value()\n')
            lines.insert(i+10, '                            break\n')
            break

# Step 4: Find all profile page creation methods and add to quality_spins
profile_pages = [
    'create_din3962_profile_page',
    'create_agma_profile_page',
    'create_iso1328_1997_profile_page',
    'create_iso1328_2013_profile_page',
    'create_ansi_b921_profile_page',
    'create_din5480_profile_page'
]

for page_method in profile_pages:
    page_start = -1
    for i, line in enumerate(lines):
        if f'def {page_method}' in line:
            page_start = i
            break
    
    if page_start != -1:
        # Find where self.profile_quality_spin is created
        for i in range(page_start, len(lines)):
            if 'self.profile_quality_spin = QSpinBox()' in lines[i]:
                # Insert after this line
                insert_pos = i + 1
                # Get the page ID from the method name
                page_id = page_method.replace('create_', '').replace('_page', '').replace('_profile', '_Profile')
                if page_id == 'din3962_Profile':
                    page_id = 'DIN 3962_Profile'
                elif page_id == 'agma_Profile':
                    page_id = 'AGMA_Profile'
                elif page_id == 'iso1328_1997_Profile':
                    page_id = 'ISO 1328 : 1997_Profile'
                elif page_id == 'iso1328_2013_Profile':
                    page_id = 'ISO 1328 : 2013_Profile'
                elif page_id == 'ansi_b921_Profile':
                    page_id = 'ANSI B92.1_Profile'
                elif page_id == 'din5480_Profile':
                    page_id = 'DIN 5480_Profile'
                
                lines.insert(insert_pos, f'        self.quality_spins["{page_id}"] = self.profile_quality_spin\n')
                break

# Write the fixed content back to the file
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\nDirect fix completed!")
print(f"Original file backed up to: {backup_path}")
print(f"Modified file saved to: {file_path}")