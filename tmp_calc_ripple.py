import os
import sys


def main() -> int:
    root = r"e:\python\gear measuring software - 20251217\gear measuring software - 20251217"
    sys.path.insert(0, root)
    sys.path.insert(0, os.path.join(root, "gear_analysis_refactored"))

    from gear_analysis_refactored.utils.file_parser import parse_mka_file
    from gear_analysis_refactored.models.gear_data import create_gear_data_from_dict
    from gear_analysis_refactored.reports.klingelnberg_ripple_spectrum import (
        KlingelnbergRippleSpectrumReport,
    )

    mka = os.environ.get(
        "MKA_PATH",
        r"e:\python\gear measuring software - 20251217\gear measuring software - 20251217\gear_analysis_refactored\testdata\新建文件夹\84-T3.2.47.02.76-G-WAV\263751-018-WAV.mka",
    )

    d = parse_mka_file(mka)
    md = create_gear_data_from_dict(d)
    rep = KlingelnbergRippleSpectrumReport()

    ze = int(md.basic_info.teeth or 0) or 1
    max_order = max(500, 7 * ze)

    cases = [
        ("Profile right", "profile", "right", md.profile_data.right, "profile_markers_right"),
        ("Profile left", "profile", "left", md.profile_data.left, "profile_markers_left"),
        ("Helix right", "flank", "right", md.flank_data.right, "lead_markers_right"),
        ("Helix left", "flank", "left", md.flank_data.left, "lead_markers_left"),
    ]

    print(f"MKA: {mka}")
    print(f"ZE (teeth): {ze}")
    print(f"max_order: {max_order}")
    for title, data_type, side, data_dict, markers_attr in cases:
        markers = getattr(md.basic_info, markers_attr, None)
        eval_length = rep._get_eval_length(md.basic_info, data_type, side, markers)
        base_diameter = rep._get_base_diameter(md.basic_info)
        orders, amps = rep._calculate_spectrum(
            data_dict,
            ze,
            markers,
            max_order=max_order,
            eval_length=eval_length,
            base_diameter=base_diameter,
            max_components=11,
            side=side,
            data_type=data_type,
            info=md.basic_info,
        )
        print("")
        print(title)
        if len(orders) == 0:
            print("  (no components)")
            continue
        for o, a in zip(orders.tolist(), amps.tolist()):
            print(f"  {int(o):4d}: {a:.4f} um")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

