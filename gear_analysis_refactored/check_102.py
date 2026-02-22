
import re

file_path = r"e:\python\gear measuring software - 20251202\gear_analysis_refactored\testdata\202305021044.mka"

def check_102():
    try:
        with open(file_path, 'r', encoding='latin1') as f:
            for line in f:
                if "102" in line:
                    print(f"Line: {repr(line)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_102()
