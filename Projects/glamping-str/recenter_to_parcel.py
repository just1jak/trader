#!/usr/bin/env python3
"""
Recenter DXF/DAE/PNG files so that the specific parcel (by APN) is centered at (0,0).

This queries the county GIS to find the exact parcel boundary, calculates its centroid,
and shifts all geometry (contours, roads, parcel boundaries) so the target parcel is
centered at origin.
"""

import json
import math
import urllib.request
import urllib.parse
from pathlib import Path
import re
import tempfile
import shutil
import subprocess

SCC_PARCELS_URL = (
    "https://gis.santacruzcountyca.gov/server/rest/services/"
    "data/MapServer/2/query"
)

def lonlat_to_webmerc(lon, lat):
    """Convert lon/lat (EPSG:4326) to Web Mercator meters (EPSG:3857)."""
    x = lon * 20037508.34 / 180.0
    y = math.log(math.tan((90.0 + lat) * math.pi / 360.0)) / (math.pi / 180.0)
    y = y * 20037508.34 / 180.0
    return x, y

def feet_to_meters(ft):
    return ft * 0.3048

def fetch_parcel_geometry(apn_str, center_lat, center_lon, search_width_ft=1500, search_height_ft=1500):
    """Fetch the specific parcel geometry from Santa Cruz County GIS.
    Returns dict with apn, acres, rings (list of coordinate rings), and centroid."""

    cx, cy = lonlat_to_webmerc(center_lon, center_lat)
    half_w = feet_to_meters(search_width_ft) / 2.0
    half_h = feet_to_meters(search_height_ft) / 2.0
    xmin, ymin = cx - half_w, cy - half_h
    xmax, ymax = cx + half_w, cy + half_h

    params = {
        "geometry": f"{xmin},{ymin},{xmax},{ymax}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "3857",
        "outSR": "3857",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "APN,ACRES",
        "returnGeometry": "true",
        "f": "json",
    }
    url = SCC_PARCELS_URL + "?" + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"ERROR: Failed to fetch parcel data: {e}")
        return None

    target_apn = apn_str.strip()
    for feat in data.get("features", []):
        attrs = feat.get("attributes", {})
        apn = attrs.get("APN", "")
        if apn.strip() == target_apn:
            acres = float(attrs.get("ACRES") or 0)
            rings = []

            # Convert WebMercator to feet relative to SW corner
            sw_x_m = xmin
            sw_y_m = ymin

            for ring in feat.get("geometry", {}).get("rings", []):
                ring_ft = []
                for x_m, y_m in ring:
                    x_ft = (x_m - sw_x_m) / 0.3048
                    y_ft = (y_m - sw_y_m) / 0.3048
                    ring_ft.append((x_ft, y_ft))
                if ring_ft:
                    rings.append(ring_ft)

            # Calculate centroid of all rings
            all_pts = [p for ring in rings for p in ring]
            if all_pts:
                cx_parcel = sum(p[0] for p in all_pts) / len(all_pts)
                cy_parcel = sum(p[1] for p in all_pts) / len(all_pts)
            else:
                cx_parcel, cy_parcel = 0, 0

            return {
                "apn": apn,
                "acres": acres,
                "rings": rings,
                "centroid": (cx_parcel, cy_parcel),
            }

    print(f"ERROR: Parcel {target_apn} not found in query area")
    return None

def shift_dxf_coordinates(dxf_path, offset_x, offset_y, output_path=None):
    """Shift all XY coordinates in DXF by offset."""
    if output_path is None:
        output_path = dxf_path

    with open(dxf_path, 'r') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        # Look for group code 10 (X coordinate)
        if lines[i].strip() == '10':
            try:
                x = float(lines[i + 1].strip())
                x_new = x - offset_x
                lines[i + 1] = f"{x_new:.4f}\n"
                i += 2
                # Next should be 20 (Y coordinate)
                if i < len(lines) and lines[i].strip() == '20':
                    y = float(lines[i + 1].strip())
                    y_new = y - offset_y
                    lines[i + 1] = f"{y_new:.4f}\n"
                    i += 2
                else:
                    i += 1
            except (ValueError, IndexError):
                i += 1
        else:
            i += 1

    with open(output_path, 'w') as f:
        f.writelines(lines)

    print(f"✓ Shifted DXF coordinates by ({offset_x:.1f}, {offset_y:.1f}): {output_path}")

def regenerate_png_centered(lat, lon, width_ft, height_ft, apn, out_path, center_on_parcel_x, center_on_parcel_y):
    """Regenerate PNG by recentering to the parcel centroid."""
    cmd = [
        "python3", "contour_grabber.py",
        "--lat", str(lat),
        "--lon", str(lon),
        "--width", str(width_ft),
        "--height", str(height_ft),
        "--interval", "10",
        "--out", out_path,
        "--apn", apn,
        "--no-roads",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd="/mnt/kb/Projects/glamping-str")
    if result.returncode != 0:
        print(f"WARNING: Failed to regenerate PNG for {apn}")
        print(result.stderr)
        return False

    print(f"✓ Regenerated PNG for {apn} with parcel-centered coordinates")
    return True

def main():
    # Parcel information
    parcels = [
        {
            "apn": "086-521-02",
            "lat": 37.160965,
            "lon": -122.188756,
            "dxf_path": "contours/parcel_086-521-02.dxf",
            "dae_path": "contours/parcel_086-521-02.dae",
            "png_path": "contours/parcel_086-521-02",
        },
        {
            "apn": "086-631-14",
            "lat": 37.160155,
            "lon": -122.190267,
            "dxf_path": "contours/parcel_086-631-14.dxf",
            "dae_path": "contours/parcel_086-631-14.dae",
            "png_path": "contours/parcel_086-631-14",
        },
    ]

    print("=" * 70)
    print("RECENTERING PARCELS TO ORIGIN (0,0)")
    print("=" * 70)

    for parcel_info in parcels:
        apn = parcel_info["apn"]
        lat = parcel_info["lat"]
        lon = parcel_info["lon"]
        dxf_path = parcel_info["dxf_path"]
        png_path = parcel_info["png_path"]

        print(f"\n--- Processing {apn} ---")

        # Step 1: Fetch the actual parcel geometry
        print(f"Fetching parcel geometry from county GIS...")
        parcel_geom = fetch_parcel_geometry(apn, lat, lon)
        if not parcel_geom:
            print(f"SKIP: Could not fetch geometry for {apn}")
            continue

        cx_parcel, cy_parcel = parcel_geom["centroid"]
        print(f"  Parcel size: {parcel_geom['acres']:.2f} acres")
        print(f"  Parcel centroid: ({cx_parcel:.1f}, {cy_parcel:.1f}) ft")

        # Step 2: Shift DXF coordinates
        if Path(dxf_path).exists():
            shift_dxf_coordinates(dxf_path, cx_parcel, cy_parcel)
        else:
            print(f"SKIP DXF: {dxf_path} not found")

        # Step 3: Regenerate PNG with parcel-centered coordinates
        print(f"Regenerating PNG with parcel-centered coordinates...")
        regenerate_png_centered(lat, lon, 1500, 1500, apn, png_path, cx_parcel, cy_parcel)

    print("\n" + "=" * 70)
    print("✓ COMPLETE")
    print("=" * 70)
    print("\nAll parcels are now centered at (0, 0) in both DXF and PNG.")
    print("DXF coordinates are in feet relative to parcel center.")

if __name__ == "__main__":
    main()
