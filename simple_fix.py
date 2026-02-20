#!/usr/bin/env python3
"""
Simple script to fix the tolerance dialog quality level issue.
"""

import re
import os
import shutil

# Path to the original file
file_path = r"e:\python\gear measuring software - 20251217\gear_analysis_refactored\ui\tolerance_dialog.py"

# Create backup
backup_path = file_path + '.bak_simple'
if not os.path.exists(backup_path):
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")

# Read the original file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Add current_page_id tracking to on_tree_item_clicked
# This is a simpler approach that just adds the current_page_id tracking
on_tree_pattern = r'def on_tree_item_clicked\(self, item, column\):\s*page_id = item.data\(0, Qt\.UserRole\)\s*if page_id is None:\s*return'
on_tree_replacement = r'def on_tree_item_clicked\(self, item, column\):\n        page_id = item.data(0, Qt.UserRole)\n        if page_id is None:\n            return\n        self.current_page_id = page_id'

content = re.sub(on_tree_pattern, on_tree_replacement, content, flags=re.DOTALL)

# Step 2: Modify calculate_tolerances to use a direct approach for profile pages
calc_pattern = r'def calculate_tolerances\(self, type_\):\s*"""Set tolerance values based on quality level using predefined lookup tables"""\s*try:\s*if type_ == "profile":\s*Q = self\.profile_quality_spin\.value\(\)'

# This approach directly uses the current page ID to determine the quality level
# without needing to track all spin boxes
calc_replacement = '''def calculate_tolerances(self, type_):
        """Set tolerance values based on quality level using predefined lookup tables"""
        try:
            if type_ == "profile":
                # Get quality level from the current page's spin box
                # This direct approach works because the current page is what the user sees
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

content = re.sub(calc_pattern, calc_replacement, content, flags=re.DOTALL)

# Save the modified file
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\nSimple fix completed!")
print(f"Original file backed up to: {backup_path}")
print(f"Modified file saved to: {file_path}")