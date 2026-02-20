import textwrap
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

out_dir = Path('docs')
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / 'ripple_spectrum_help.pdf'

content = """
Klingelnberg Ripple Spectrum Report: Chart & Data Processing Notes

1. Layout
- File: gear_analysis_refactored/reports/klingelnberg_ripple_spectrum.py
- create_page() builds: header + 4 stacked spectrum charts (Profile/Helix left/right) + 2 tables at the bottom
- GridSpec rows: header (12%), 4 charts (18% each), tables (16%)

2. Spectrum Chart Pipeline (_create_spectrum_chart)
2.1 Data source
- Profile: measurement_data.profile_data.<left/right>
- Helix: measurement_data.flank_data.<left/right>
- Evaluation range: basic_info.profile_markers_<side> or lead_markers_<side>

2.2 Evaluation range slicing (if markers exist)
- markers = (start_meas, start_eval, end_eval, end_meas)
- Convert marker distances into index range idx_start/idx_end, then slice vals
- If remaining points are too few (<=5), that tooth is skipped

2.3 Detrend
- Fit a linear trend (1st order) and subtract it
- This removes slope in helix/lead before FFT

2.4 FFT spectrum (_calculate_spectrum)
- rFFT per tooth curve
- Magnitude normalization: mag = abs(fft) / n (n = original point count)
- Zero padding to min_fft_length (>=1000 or >=2*max_order+1) to reach higher orders
- Average across teeth
- Order mapping: FFT index 1 -> order 1; index 2 -> order 2 (DC index 0 is removed)

2.5 Filtering & display
- Keep orders in 1..max_order (default 500 or 2*ZE)
- Amplitude threshold = max_amp * 0.5%. If too few points, fall back to all points
- If too many points (>100), keep top 100 by amplitude and sort by order
- Y-axis range uses raw amplitudes (no normalization), with a 1.2x headroom

2.6 Tolerance curve (if enabled)
- Parameters R/N0/K from measurement_data.tolerance, fallback to defaults
- Tolerance curve: tolerance = R / (O-1)^N, N = N0 + K / O
- Used to color pass/fail points

3. Bottom tables (_create_data_table)
3.1 Data
- Profile and Helix each call _calculate_spectrum
- Restrict to <=500 orders, sort by amplitude, keep top 11 components

3.2 Table structure
- Rows: Profile A, Profile O, Helix A, Helix O
- Columns: main components (ZE, 2ZE, ...)
- A row shows amplitude; O row shows order
- Over-tolerance A values are bold

4. Key functions
- Layout: create_page(), _create_spectrum_chart()
- Spectrum: _calculate_spectrum()
- Tolerance: _calculate_tolerance_curve()
- Table: _create_data_table()

Note: To reduce visual density, raise the threshold or cap max points in _create_spectrum_chart.
""".strip()

wrapper = textwrap.TextWrapper(width=90)
lines = []
for paragraph in content.split('\n'):
    if not paragraph.strip():
        lines.append('')
        continue
    lines.extend(wrapper.wrap(paragraph))

pp = PdfPages(out_path)
page_lines = 48
for i in range(0, len(lines), page_lines):
    fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
    ax = fig.add_axes([0.06, 0.04, 0.88, 0.92])
    ax.axis('off')
    y = 0.98
    for line in lines[i:i+page_lines]:
        ax.text(0.0, y, line, fontsize=10, va='top')
        y -= 0.02
    pp.savefig(fig)
    plt.close(fig)
pp.close()

print('Font: DejaVu Sans')
print(f"Wrote {out_path}")
