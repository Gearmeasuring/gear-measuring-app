#!/usr/bin/env python3
# Script to add valueChanged connections to quality level spin boxes

import os

def add_valuechanged_connections():
    file_path = "tolerance_dialog.py"
    
    # Read the entire file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add valueChanged connection for profile quality spin box
    content = content.replace(
        "self.profile_quality_spin.setFixedWidth(50)\n        header_layout.addWidget(self.profile_quality_spin)",
        "self.profile_quality_spin.setFixedWidth(50)\n        self.profile_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances(\"profile\"))\n        header_layout.addWidget(self.profile_quality_spin)"
    )
    
    # Add valueChanged connection for lead quality spin box
    content = content.replace(
        "self.lead_quality_spin.setFixedWidth(50)\n        header_layout.addWidget(self.lead_quality_spin)",
        "self.lead_quality_spin.setFixedWidth(50)\n        self.lead_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances(\"lead\"))\n        header_layout.addWidget(self.lead_quality_spin)"
    )
    
    # Add valueChanged connection for spacing quality spin box
    content = content.replace(
        "self.spacing_quality_spin.setFixedWidth(50)\n        header_layout.addWidget(self.spacing_quality_spin)",
        "self.spacing_quality_spin.setFixedWidth(50)\n        self.spacing_quality_spin.valueChanged.connect(lambda: self.calculate_tolerances(\"spacing\"))\n        header_layout.addWidget(self.spacing_quality_spin)"
    )
    
    # Write the modified content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Successfully added valueChanged connections to all quality level spin boxes.")
    
    # Verify the changes
    with open(file_path, 'r', encoding='utf-8') as f:
        modified_content = f.read()
    
    # Check if connections were added
    profile_count = modified_content.count("self.profile_quality_spin.valueChanged.connect")
    lead_count = modified_content.count("self.lead_quality_spin.valueChanged.connect")
    spacing_count = modified_content.count("self.spacing_quality_spin.valueChanged.connect")
    
    print(f"Profile quality spin box connections: {profile_count}")
    print(f"Lead quality spin box connections: {lead_count}")
    print(f"Spacing quality spin box connections: {spacing_count}")

if __name__ == "__main__":
    # Change to the directory containing the script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    add_valuechanged_connections()