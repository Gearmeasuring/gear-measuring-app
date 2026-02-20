
import sys

file_path = r"e:\python\gear measuring software - 20251202\gear_analysis_refactored\testdata\202305021044.mka"
keywords = ["Zahn", "Teeth", "Order", "Serial", "Location", "Condition", "Profilverschiebungsfaktor", "Kugel", "Stylus", "Modul", "Eingriffswinkel", "Schrägungswinkel"]

try:
    with open(file_path, 'r', encoding='latin1') as f:
        for i, line in enumerate(f):
            if i > 500: break # Only check first 500 lines
            for kw in keywords:
                if kw.lower() in line.lower():
                    print(f"{i}: {line.strip()}")
except Exception as e:
    print(f"Error: {e}")
