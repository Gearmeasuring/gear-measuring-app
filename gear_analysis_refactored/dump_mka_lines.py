
import sys

file_path = r"e:\python\gear measuring software - 20251202\gear_analysis_refactored\testdata\202305021044.mka"

try:
    with open(file_path, 'rb') as f:
        content = f.read(4000) # Read first 4000 bytes
        # Try to decode as latin1
        text = content.decode('latin1', errors='ignore')
        lines = text.split('\n')
        for i, line in enumerate(lines[:50]):
            print(f"{i}: {repr(line)}")
except Exception as e:
    print(f"Error: {e}")
