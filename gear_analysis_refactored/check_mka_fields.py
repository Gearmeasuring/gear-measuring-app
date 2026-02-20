
import re

file_path = r"e:\python\gear measuring software - 20251202\gear_analysis_refactored\testdata\202305021044.mka"

def check_lines():
    try:
        with open(file_path, 'r', encoding='latin1') as f:
            lines = f.readlines()
            
        for line in lines:
            # Check for specific parameter numbers
            if re.search(r'^\s*7\s*:', line):
                print(f"Line 7 (Order): {repr(line)}")
            elif re.search(r'^\s*22\s*:', line):
                print(f"Line 22 (Teeth): {repr(line)}")
            elif re.search(r'^\s*25\s*:', line):
                print(f"Line 25 (Mod Coeff): {repr(line)}")
            elif re.search(r'^\s*5\s*:', line):
                print(f"Line 5 (Location): {repr(line)}")
            elif re.search(r'^\s*10\s*:', line):
                print(f"Line 10 (Condition): {repr(line)}")
            elif re.search(r'^\s*30\s*:', line): # Stylus might be around here
                print(f"Line 30: {repr(line)}")
            elif "Kugel" in line or "Stylus" in line:
                print(f"Stylus line: {repr(line)}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_lines()
