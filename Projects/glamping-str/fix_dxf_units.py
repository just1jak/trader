#!/usr/bin/env python3
"""
Fix DXF files by adding proper unit headers (feet) and regenerate PNGs with better labeling.
"""

import re
from pathlib import Path
import subprocess

def fix_dxf_units(dxf_path, output_path=None):
    """Read DXF file and add proper unit headers specifying feet.
    INSUNITS code 33 = feet"""
    if output_path is None:
        output_path = dxf_path

    with open(dxf_path, 'r') as f:
        content = f.read()

    # Replace the minimal HEADER section with a proper one
    header_section = """0
SECTION
2
HEADER
9
$INSUNITS
70
33
9
$UNITS
70
4
0
ENDSEC"""

    # Find and replace the HEADER section
    # Look for "0\nSECTION\n2\nHEADER\n0\nENDSEC"
    pattern = r'0\nSECTION\n2\nHEADER\n0\nENDSEC'
    content = re.sub(pattern, header_section, content, count=1)

    with open(output_path, 'w') as f:
        f.write(content)

    print(f"✓ Fixed DXF headers: {output_path}")
    return output_path

def regenerate_pngs():
    """Regenerate PNGs from the existing TIF files with better label placement."""
    # Run contour_grabber with both parcels and output to a temp location
    # to verify the PNG generation works correctly
    parcel_info = [
        ("086-521-02", 37.160965, -122.188756),
        ("086-631-14", 37.160155, -122.190267),
    ]

    for apn, lat, lon in parcel_info:
        cmd = [
            "python3", "contour_grabber.py",
            "--lat", str(lat),
            "--lon", str(lon),
            "--width", "1500",
            "--height", "1500",
            "--interval", "10",
            "--out", f"contours/parcel_{apn}",
            "--apn", apn,
            "--no-roads"
        ]
        print(f"\nRegenerating PNG for {apn}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Regenerated files for parcel {apn}")
        else:
            print(f"✗ Failed to regenerate {apn}:")
            print(result.stderr)

if __name__ == "__main__":
    # Fix DXF files
    dxf_files = [
        "contours/parcel_086-521-02.dxf",
        "contours/parcel_086-631-14.dxf",
    ]

    print("=" * 60)
    print("FIXING DXF UNIT HEADERS")
    print("=" * 60)

    for dxf_file in dxf_files:
        if Path(dxf_file).exists():
            fix_dxf_units(dxf_file)
        else:
            print(f"⚠ Not found: {dxf_file}")

    print("\n" + "=" * 60)
    print("REGENERATING PNGS WITH PROPER LABELING")
    print("=" * 60)
    regenerate_pngs()

    print("\n" + "=" * 60)
    print("✓ COMPLETE")
    print("=" * 60)
    print("\nDXF files now specify feet as the unit.")
    print("When opened in CAD software (AutoCAD, FreeCAD, etc.):")
    print("  - 1500 units = 1500 feet (not 1500 inches)")
    print("  - Parcel coordinates are preserved")
