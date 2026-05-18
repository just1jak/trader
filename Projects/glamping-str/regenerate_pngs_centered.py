#!/usr/bin/env python3
"""
Regenerate PNG files with contours shifted to parcel-centered coordinates.
Shows the parcel centered in the visualization, matching the DXF coordinate system.
"""

import json
import math
import urllib.request
import urllib.parse
import numpy as np
import rasterio
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

SCC_PARCELS_URL = (
    "https://gis.santacruzcountyca.gov/server/rest/services/"
    "data/MapServer/2/query"
)

def lonlat_to_webmerc(lon, lat):
    x = lon * 20037508.34 / 180.0
    y = math.log(math.tan((90.0 + lat) * math.pi / 360.0)) / (math.pi / 180.0)
    y = y * 20037508.34 / 180.0
    return x, y

def feet_to_meters(ft):
    return ft * 0.3048

def fetch_parcel_geometry(apn_str, center_lat, center_lon, search_width_ft=1500, search_height_ft=1500):
    """Fetch specific parcel geometry."""
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

    return None

def extract_contours_from_tif(tif_path, interval_ft=10):
    """Extract contours from existing TIF file."""
    with rasterio.open(tif_path) as src:
        elev = src.read(1).astype(np.float64)
        transform = src.transform
        nodata = src.nodata
        h, w = elev.shape

        if nodata is not None:
            elev = np.where(elev == nodata, np.nan, elev)

        elev_ft = elev / 0.3048

        # Get bounds in feet
        from rasterio.transform import xy as rio_xy
        sw_x_m, sw_y_m = rio_xy(transform, h - 1, 0, offset="center")
        ne_x_m, ne_y_m = rio_xy(transform, 0, w - 1, offset="center")
        x_extent_ft = (ne_x_m - sw_x_m) / 0.3048
        y_extent_ft = (ne_y_m - sw_y_m) / 0.3048

        x_axis = np.linspace(0, x_extent_ft, w)
        y_axis = np.linspace(0, y_extent_ft, h)

        z_min = np.nanmin(elev_ft)
        z_max = np.nanmax(elev_ft)
        first = math.ceil(z_min / interval_ft) * interval_ft
        last = math.floor(z_max / interval_ft) * interval_ft
        levels = np.arange(first, last + interval_ft, interval_ft)

        elev_flipped = elev_ft[::-1, :]
        fig = plt.figure()
        ax = fig.add_subplot(111)
        cs = ax.contour(x_axis, y_axis, elev_flipped, levels=levels)

        contours = []
        for level, segs in zip(cs.levels, cs.allsegs):
            entry = {"elev_ft": float(level), "lines": []}
            for seg in segs:
                if len(seg) >= 2:
                    entry["lines"].append([(float(p[0]), float(p[1])) for p in seg])
            if entry["lines"]:
                contours.append(entry)
        plt.close(fig)

        return contours, (x_extent_ft, y_extent_ft, z_min, z_max)

def write_centered_preview(contours, parcel, out_path, x_extent_ft, y_extent_ft, z_min, z_max, apn):
    """Write PNG with parcel centered at origin."""

    # Get parcel centroid (in original coordinates before shift)
    cx_parcel, cy_parcel = parcel["centroid"]

    # Shift contours to be relative to parcel centroid
    shifted_contours = []
    for c in contours:
        shifted_lines = []
        for line in c["lines"]:
            shifted_line = [(p[0] - cx_parcel, p[1] - cy_parcel) for p in line]
            shifted_lines.append(shifted_line)
        shifted_contours.append({"elev_ft": c["elev_ft"], "lines": shifted_lines})

    # Shift parcel boundaries
    shifted_rings = []
    for ring in parcel["rings"]:
        shifted_ring = [(p[0] - cx_parcel, p[1] - cy_parcel) for p in ring]
        shifted_rings.append(shifted_ring)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 10))

    # Draw contours
    elevs = [c["elev_ft"] for c in shifted_contours]
    if elevs:
        norm = matplotlib.colors.Normalize(vmin=min(elevs), vmax=max(elevs))
        cmap = matplotlib.colormaps["terrain"]
        for c in shifted_contours:
            color = cmap(norm(c["elev_ft"]))
            for poly in c["lines"]:
                xs = [p[0] for p in poly]
                ys = [p[1] for p in poly]
                ax.plot(xs, ys, color=color, linewidth=0.7)

        # Label every 5th contour
        for i, c in enumerate(shifted_contours):
            if i % 5 != 0:
                continue
            for poly in c["lines"]:
                if len(poly) > 20:
                    mid = poly[len(poly) // 2]
                    txt = ax.text(
                        mid[0], mid[1], f"{int(c['elev_ft'])}",
                        fontsize=7, ha="center", va="center",
                        color="black",
                    )
                    txt.set_path_effects([
                        pe.Stroke(linewidth=2, foreground="white"),
                        pe.Normal(),
                    ])
                    break

    # Draw parcel boundary (highlighted in red)
    for ring in shifted_rings:
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        ax.plot(xs, ys, color="red", linewidth=2.5, alpha=1.0, zorder=10)

    # Label the parcel
    all_pts = [p for ring in shifted_rings for p in ring]
    if all_pts:
        cx_lbl = sum(p[0] for p in all_pts) / len(all_pts)
        cy_lbl = sum(p[1] for p in all_pts) / len(all_pts)
        label = f"{apn}\n{parcel['acres']:.2f} ac"
        txt = ax.text(
            cx_lbl, cy_lbl, label,
            fontsize=10, fontweight="bold", ha="center", va="center",
            color="red", zorder=11,
        )
        txt.set_path_effects([
            pe.Stroke(linewidth=2.5, foreground="white"),
            pe.Normal(),
        ])

    # Center crosshair at origin
    ax.plot(0, 0, "+", color="black", markersize=16, markeredgewidth=2, zorder=12)
    ax.text(0, -50, "(0,0)", fontsize=9, ha="center", va="top", color="black", zorder=12,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="black", linewidth=0.5))

    # Set limits - show area around parcel
    margin = 200  # feet
    all_x = [p[0] for ring in shifted_rings for p in ring]
    all_y = [p[1] for ring in shifted_rings for p in ring]
    if all_x and all_y:
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        xlim = (min_x - margin, max_x + margin)
        ylim = (min_y - margin, max_y + margin)
    else:
        xlim = (-500, 500)
        ylim = (-500, 500)

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_aspect("equal")
    ax.set_xlabel("East (ft, relative to parcel center)")
    ax.set_ylabel("North (ft, relative to parcel center)")
    ax.set_title(
        f"3D Contours -- Parcel {apn} Centered at Origin\n"
        f"Elevation: {z_min:.0f} - {z_max:.0f} ft"
    )
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"✓ Generated centered PNG: {out_path}")

def main():
    parcels_info = [
        {
            "apn": "086-521-02",
            "lat": 37.160965,
            "lon": -122.188756,
            "tif_path": "contours/parcel_086-521-02.tif",
            "png_path": "contours/parcel_086-521-02.png",
        },
        {
            "apn": "086-631-14",
            "lat": 37.160155,
            "lon": -122.190267,
            "tif_path": "contours/parcel_086-631-14.tif",
            "png_path": "contours/parcel_086-631-14.png",
        },
    ]

    print("=" * 70)
    print("REGENERATING PNGs WITH PARCEL-CENTERED COORDINATES")
    print("=" * 70)

    for parcel_info in parcels_info:
        apn = parcel_info["apn"]
        lat = parcel_info["lat"]
        lon = parcel_info["lon"]
        tif_path = parcel_info["tif_path"]
        png_path = parcel_info["png_path"]

        print(f"\n--- Processing {apn} ---")

        if not Path(tif_path).exists():
            print(f"SKIP: TIF file not found: {tif_path}")
            continue

        # Fetch parcel geometry
        parcel = fetch_parcel_geometry(apn, lat, lon)
        if not parcel:
            print(f"SKIP: Could not fetch parcel geometry")
            continue

        # Extract contours from TIF
        print(f"Extracting contours from TIF...")
        contours, extent = extract_contours_from_tif(tif_path)
        print(f"  Found {len(contours)} contour levels")

        # Generate centered PNG
        write_centered_preview(
            contours, parcel, png_path,
            extent[0], extent[1], extent[2], extent[3],
            apn
        )

    print("\n" + "=" * 70)
    print("✓ COMPLETE")
    print("=" * 70)
    print("\nPNG files now show parcel centered at (0,0), matching DXF coordinates.")

if __name__ == "__main__":
    main()
