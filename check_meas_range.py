"""
检查测量范围是否正确读取
"""

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ripple_waviness_analyzer import RippleWavinessAnalyzer

file_path = os.path.join(current_dir, "263751-018-WAV.mka")
analyzer = RippleWavinessAnalyzer(file_path)
analyzer.load_file()

print("齿形评价范围:")
print(f"  eval_start (d1): {analyzer.reader.profile_eval_range.eval_start}")
print(f"  eval_end (d2): {analyzer.reader.profile_eval_range.eval_end}")
print(f"  meas_start (da): {analyzer.reader.profile_eval_range.meas_start}")
print(f"  meas_end (de): {analyzer.reader.profile_eval_range.meas_end}")

print("\n齿向评价范围:")
print(f"  eval_start (b1): {analyzer.reader.helix_eval_range.eval_start}")
print(f"  eval_end (b2): {analyzer.reader.helix_eval_range.eval_end}")
print(f"  meas_start (ba): {analyzer.reader.helix_eval_range.meas_start}")
print(f"  meas_end (be): {analyzer.reader.helix_eval_range.meas_end}")
