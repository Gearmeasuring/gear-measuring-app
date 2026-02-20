#!/usr/bin/env python3
# Script to verify valueChanged connections are properly added to all quality level spin boxes

import os
import re

def verify_quality_connections():
    file_path = "tolerance_dialog.py"
    
    # Read the entire file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("=== Verifying Quality Level Spin Box Connections ===")
    
    # Search for all quality spin box definitions
    spin_box_patterns = [
        r'self\.profile_quality_spin\s*=\s*QSpinBox\(\)',
        r'self\.lead_quality_spin\s*=\s*QSpinBox\(\)',
        r'self\.spacing_quality_spin\s*=\s*QSpinBox\(\)'
    ]
    
    for pattern in spin_box_patterns:
        matches = re.finditer(pattern, content)
        count = 0
        for match in matches:
            count += 1
            spin_box_name = pattern.split()[0]
            
            # Check if this spin box has a valueChanged connection
            connection_pattern = f'{spin_box_name}\.valueChanged\.connect\(lambda: self\.calculate_tolerances\("[a-z]+"\)\)'
            connection_match = re.search(connection_pattern, content)
            
            if connection_match:
                status = "✓ Connected"
            else:
                status = "✗ Not connected"
                
        print(f"{spin_box_name}: {count} instances, {status}")
    
    print("\n=== Summary ===")
    profile_count = content.count("self.profile_quality_spin.valueChanged.connect")
    lead_count = content.count("self.lead_quality_spin.valueChanged.connect")
    spacing_count = content.count("self.spacing_quality_spin.valueChanged.connect")
    
    total_connections = profile_count + lead_count + spacing_count
    print(f"Total valueChanged connections added: {total_connections}")
    print(f"  - Profile: {profile_count}")
    print(f"  - Lead: {lead_count}")
    print(f"  - Spacing: {spacing_count}")
    
    # Check if all connections are present
    if profile_count > 0 and lead_count > 0 and spacing_count > 0:
        print("\n✓ All quality level spin boxes have valueChanged connections added!")
        return True
    else:
        print("\n✗ Some quality level spin boxes are missing valueChanged connections.")
        return False

if __name__ == "__main__":
    # Change to the directory containing the script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    verify_quality_connections()