from parse_mka_file import MKAParser

# Test script to verify pitch data matches actual teeth count
mka_file = '263751-018-WAV.mka'
parser = MKAParser(mka_file)

# Get teeth count from header
header_teeth_count = parser.get_teeth_count()
print(f"Teeth count from header: {header_teeth_count}")

# Get pitch data for both sides
left_pitch_teeth = len(parser.pitch_data.get('left', {}))
right_pitch_teeth = len(parser.pitch_data.get('right', {}))

print(f"Pitch data - Left side teeth: {left_pitch_teeth}")
print(f"Pitch data - Right side teeth: {right_pitch_teeth}")

# Check if pitch data teeth match header teeth count
if header_teeth_count > 0:
    left_match = left_pitch_teeth == header_teeth_count
    right_match = right_pitch_teeth == header_teeth_count
    
    print(f"\nMatch verification:")
    print(f"Left side pitch data matches header teeth count: {left_match}")
    print(f"Right side pitch data matches header teeth count: {right_match}")
    
    if left_match and right_match:
        print("✓ Pitch data matches actual teeth count!")
    else:
        print("✗ Pitch data does not match actual teeth count!")
else:
    print("\nCould not extract teeth count from header.")
    print(f"Using fallback teeth count: 87")

# Check specific tooth IDs in pitch data
print("\nSample pitch data tooth IDs:")
for side in ['left', 'right']:
    teeth = list(parser.pitch_data.get(side, {}).keys())[:10]
    print(f"{side} side: {teeth}")

# Check if all tooth IDs are valid numbers
print("\nTooth ID validation:")
invalid_tooth_ids = []
for side in ['left', 'right']:
    for tooth_id in parser.pitch_data.get(side, {}):
        if not tooth_id.isdigit():
            invalid_tooth_ids.append((side, tooth_id))

if invalid_tooth_ids:
    print(f"Found {len(invalid_tooth_ids)} invalid tooth IDs:")
    for side, tooth_id in invalid_tooth_ids:
        print(f"  {side}: {tooth_id}")
else:
    print("✓ All tooth IDs are valid numbers")

# Summary
print("\nSummary:")
print(f"Header teeth count: {header_teeth_count}")
print(f"Left pitch teeth: {left_pitch_teeth}")
print(f"Right pitch teeth: {right_pitch_teeth}")
print(f"Total pitch data points: {sum(len(data) for side_data in parser.pitch_data.values() for data in side_data.values())}")
