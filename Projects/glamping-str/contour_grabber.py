#!/usr/bin/env python3
"""
contour_grabber.py

Pulls a DEM (Digital Elevation Model) tile from the USGS 3DEP service
for a user-specified lat/lon bounding box, generates 3D contour lines
at a chosen interval, and writes them as a DAE (Collada) file for
SketchUp / FreeCAD import. Also writes a DXF as a backup format.

No authentication required. Works with any USGS 3DEP coverage area.

Usage example (Bloom Grade, Boulder Creek CA):
python contour_grabber.py \
--lat 37.160497 --lon -122.189089 \
--width 1500 --height 1500 \
--interval 10 \
--out parcel_contours

Outputs:
<out>.tif  – the raw clipped DEM (for QGIS / FreeCAD Geodata)
<out>.dae  – 3D contours for SketchUp (drag-and-drop import)
<out>.dxf  – 3D contours for AutoCAD / FreeCAD / QCAD
<out>.png  – preview image showing the contours
"""

import argparse
import json
import math
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import xy as rio_xy
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

SCC_PARCELS_URL = (
    "https://gis.santacruzcountyca.gov/server/rest/services/"
    "data/MapServer/2/query"
)

SCC_ROADS_URL = (
    "https://gis.santacruzcountyca.gov/server/rest/services/"
    "data/MapServer/7/query"
)

USGS_3DEP_EXPORT = (
    "https://elevation.nationalmap.gov/arcgis/rest/services/"
    "3DEPElevation/ImageServer/exportImage"
)

def lonlat_to_webmerc(lon, lat):
    """Convert lon/lat (EPSG:4326) to Web Mercator meters (EPSG:3857)."""
    x = lon * 20037508.34 / 180.0
    y = math.log(math.tan((90.0 + lat) * math.pi / 360.0)) / (math.pi / 180.0)
    y = y * 20037508.34 / 180.0
    return x, y

def feet_to_meters(ft):
    return ft * 0.3048

def fetch_dem(center_lat, center_lon, width_ft, height_ft, out_tif):
    """Fetch a DEM clipped to a bounding box centered on (lat, lon).
    Width and height are in feet. Output is a GeoTIFF in Web Mercator,
    elevation values in meters (3DEP native)."""
    cx, cy = lonlat_to_webmerc(center_lon, center_lat)
    half_w = feet_to_meters(width_ft) / 2.0
    half_h = feet_to_meters(height_ft) / 2.0
    xmin, ymin = cx - half_w, cy - half_h
    xmax, ymax = cx + half_w, cy + half_h

    # Pixel size: target ~1 meter per pixel; cap at 2000x2000
    px_w = min(2000, int(round(feet_to_meters(width_ft))))
    px_h = min(2000, int(round(feet_to_meters(height_ft))))

    params = {
        "bbox": f"{xmin},{ymin},{xmax},{ymax}",
        "bboxSR": "3857",
        "imageSR": "3857",
        "size": f"{px_w},{px_h}",
        "format": "tiff",
        "pixelType": "F32",
        "interpolation": "RSP_BilinearInterpolation",
        "f": "image",
    }
    url = USGS_3DEP_EXPORT + "?" + urllib.parse.urlencode(params)
    print(f"[fetch] requesting {px_w}x{px_h} px DEM tile...")
    print(f"        URL: {url[:120]}...")

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36", "Referer": "https://elevation.nationalmap.gov/", "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()

    if len(data) < 1000:
        raise RuntimeError(
            f"DEM response too small ({len(data)} bytes); likely an error. "
            f"First bytes: {data[:200]!r}"
        )

    Path(out_tif).write_bytes(data)
    print(f"[fetch] saved {out_tif} ({len(data)/1024:.1f} KB)")
    return out_tif

def extract_contours(tif_path, interval_ft, units_in="m", requested_width_ft=None, requested_height_ft=None):
    """Read DEM and extract contour line segments at the given interval (ft).
    Returns list of contours; each contour is a dict:
    {"elev_ft": float, "lines": [ [(x_ft, y_ft), …], … ]}
    Coordinates are in feet, with the SW corner of the DEM at (0, 0).
    Also returns the actual Web Mercator bbox of the DEM for coordinate alignment.
    If requested_width/height are provided, scales to those dimensions."""
    with rasterio.open(tif_path) as src:
        elev = src.read(1).astype(np.float64)
        transform = src.transform
        nodata = src.nodata
        h, w = elev.shape

        if nodata is not None:
            elev = np.where(elev == nodata, np.nan, elev)

        if units_in == "m":
            elev_ft = elev / 0.3048
        else:
            elev_ft = elev

        sw_x_m, sw_y_m = rio_xy(transform, h - 1, 0, offset="center")
        ne_x_m, ne_y_m = rio_xy(transform, 0, w - 1, offset="center")
        # Use requested dimensions if provided, otherwise calculate from rasterio
        if requested_width_ft is not None:
            x_extent_ft = requested_width_ft
        else:
            x_extent_ft = (ne_x_m - sw_x_m) / 0.3048
        if requested_height_ft is not None:
            y_extent_ft = requested_height_ft
        else:
            y_extent_ft = (ne_y_m - sw_y_m) / 0.3048
        x_axis = np.linspace(0, x_extent_ft, w)
        y_axis = np.linspace(0, y_extent_ft, h)

        z_min = np.nanmin(elev_ft)
        z_max = np.nanmax(elev_ft)
        first = math.ceil(z_min / interval_ft) * interval_ft
        last = math.floor(z_max / interval_ft) * interval_ft
        levels = np.arange(first, last + interval_ft, interval_ft)
        print(f"[contour] elevation range: {z_min:.1f} - {z_max:.1f} ft")
        print(f"[contour] generating {len(levels)} contour levels "
              f"({first:.0f} - {last:.0f} ft, {interval_ft} ft interval)")

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

        return contours, (x_extent_ft, y_extent_ft, z_min, z_max, sw_x_m, sw_y_m)

def write_dxf(contours, out_path, parcels=None, roads=None):
    """Write 3D contour polylines, parcel boundaries, and roads as a minimal DXF.
    Uses POLYLINE entities (simplest format that all tools accept).
    Parcels are drawn at z=0 (ground level, projected onto the terrain base)."""
    lines = []
    lines.append("0\nSECTION\n2\nHEADER\n0\nENDSEC")
    lines.append("0\nSECTION\n2\nENTITIES")

    for c in contours:
        z = c["elev_ft"]
        for poly in c["lines"]:
            lines.append("0\nPOLYLINE\n8\nCONTOURS")
            lines.append("66\n1")
            lines.append("70\n8")
            for (x, y) in poly:
                lines.append("0\nVERTEX\n8\nCONTOURS")
                lines.append("70\n32")
                lines.append(f"10\n{x:.4f}")
                lines.append(f"20\n{y:.4f}")
                lines.append(f"30\n{z:.4f}")
            lines.append("0\nSEQEND\n8\nCONTOURS")

    for parcel in (parcels or []):
        for ring in parcel["rings"]:
            lines.append("0\nPOLYLINE\n8\nPARCELS")
            lines.append("66\n1")
            lines.append("70\n8")
            for p in ring:
                x, y = p[0], p[1]
                z = p[2] if len(p) > 2 else 0.0
                lines.append("0\nVERTEX\n8\nPARCELS")
                lines.append("70\n32")
                lines.append(f"10\n{x:.4f}")
                lines.append(f"20\n{y:.4f}")
                lines.append(f"30\n{z:.4f}")
            lines.append("0\nSEQEND\n8\nPARCELS")

    for road in (roads or []):
        for line in road["lines"]:
            lines.append("0\nPOLYLINE\n8\nROADS")
            lines.append("66\n1")
            lines.append("70\n0")
            for p in line:
                x, y = p[0], p[1]
                z = p[2] if len(p) > 2 else 0.0
                lines.append("0\nVERTEX\n8\nROADS")
                lines.append("70\n0")
                lines.append(f"10\n{x:.4f}")
                lines.append(f"20\n{y:.4f}")
                lines.append(f"30\n{z:.4f}")
            lines.append("0\nSEQEND\n8\nROADS")

    lines.append("0\nENDSEC\n0\nEOF")
    Path(out_path).write_text("\n".join(lines))
    print(f"[write] {out_path}")

def write_dae(contours, out_path, bbox_extent, parcels=None, roads=None):
    """Write 3D contour polylines, parcel boundaries, and roads as a Collada (.dae) file.
    Each contour level is a separate <geometry> with line primitives.
    Parcels are drawn at z=0 (ground level, projected onto the terrain base).
    SketchUp imports this natively via File -> Import."""
    x_extent, y_extent = bbox_extent[0], bbox_extent[1]

    geometries = []
    for idx, c in enumerate(contours):
        z = c["elev_ft"]
        verts = []
        line_indices = []
        vcount = 0
        for poly in c["lines"]:
            start = vcount
            for (x, y) in poly:
                verts.extend([x, y, z])
                vcount += 1
            for i in range(start, vcount - 1):
                line_indices.append(i)
                line_indices.append(i + 1)
        if not line_indices:
            continue
        verts_str = " ".join(f"{v:.4f}" for v in verts)
        idx_str = " ".join(str(i) for i in line_indices)
        geom = f'''  <geometry id="contour_{idx}" name="contour_{int(z)}ft">
<mesh>
  <source id="contour_{idx}_pos">
    <float_array id="contour_{idx}_pos_arr" count="{len(verts)}">{verts_str}</float_array>
    <technique_common>
      <accessor source="#contour_{idx}_pos_arr" count="{vcount}" stride="3">
        <param name="X" type="float"/>
        <param name="Y" type="float"/>
        <param name="Z" type="float"/>
      </accessor>
    </technique_common>
  </source>
  <vertices id="contour_{idx}_vtx">
    <input semantic="POSITION" source="#contour_{idx}_pos"/>
  </vertices>
  <lines count="{len(line_indices) // 2}">
    <input semantic="VERTEX" source="#contour_{idx}_vtx" offset="0"/>
    <p>{idx_str}</p>
  </lines>
</mesh>
</geometry>'''
        geometries.append((idx, int(z), geom))

    pidx = len(contours)
    for p_id, parcel in enumerate(parcels or []):
        apn = parcel.get("apn", f"parcel_{p_id}")
        for ring_id, ring in enumerate(parcel["rings"]):
            verts = []
            line_indices = []
            vcount = 0
            for p in ring:
                x, y = p[0], p[1]
                z = p[2] if len(p) > 2 else 0.0
                verts.extend([x, y, z])
                vcount += 1
            for i in range(vcount - 1):
                line_indices.append(i)
                line_indices.append(i + 1)
            if line_indices:
                verts_str = " ".join(f"{v:.4f}" for v in verts)
                idx_str = " ".join(str(i) for i in line_indices)
                geom = f'''  <geometry id="parcel_{pidx}" name="parcel_{apn}">
<mesh>
  <source id="parcel_{pidx}_pos">
    <float_array id="parcel_{pidx}_pos_arr" count="{len(verts)}">{verts_str}</float_array>
    <technique_common>
      <accessor source="#parcel_{pidx}_pos_arr" count="{vcount}" stride="3">
        <param name="X" type="float"/>
        <param name="Y" type="float"/>
        <param name="Z" type="float"/>
      </accessor>
    </technique_common>
  </source>
  <vertices id="parcel_{pidx}_vtx">
    <input semantic="POSITION" source="#parcel_{pidx}_pos"/>
  </vertices>
  <lines count="{len(line_indices) // 2}">
    <input semantic="VERTEX" source="#parcel_{pidx}_vtx" offset="0"/>
    <p>{idx_str}</p>
  </lines>
</mesh>
</geometry>'''
                geometries.append((pidx, 0, geom))
                pidx += 1

    for r_id, road in enumerate(roads or []):
        for path_id, path in enumerate(road["lines"]):
            verts = []
            line_indices = []
            vcount = 0
            for p in path:
                x, y = p[0], p[1]
                z = p[2] if len(p) > 2 else 0.0
                verts.extend([x, y, z])
                vcount += 1
            for i in range(vcount - 1):
                line_indices.append(i)
                line_indices.append(i + 1)
            if line_indices:
                verts_str = " ".join(f"{v:.4f}" for v in verts)
                idx_str = " ".join(str(i) for i in line_indices)
                road_name = road.get("name", "road")
                geom = f'''  <geometry id="road_{pidx}" name="{road_name}">
<mesh>
  <source id="road_{pidx}_pos">
    <float_array id="road_{pidx}_pos_arr" count="{len(verts)}">{verts_str}</float_array>
    <technique_common>
      <accessor source="#road_{pidx}_pos_arr" count="{vcount}" stride="3">
        <param name="X" type="float"/>
        <param name="Y" type="float"/>
        <param name="Z" type="float"/>
      </accessor>
    </technique_common>
  </source>
  <vertices id="road_{pidx}_vtx">
    <input semantic="POSITION" source="#road_{pidx}_pos"/>
  </vertices>
  <lines count="{len(line_indices) // 2}">
    <input semantic="VERTEX" source="#road_{pidx}_vtx" offset="0"/>
    <p>{idx_str}</p>
  </lines>
</mesh>
</geometry>'''
                geometries.append((pidx, 0, geom))
                pidx += 1

    geom_xml = "\n".join(g[2] for g in geometries)
    nodes_xml = "\n".join(
        f'      <node id="n_{idx}" name="contour_{z}ft">\n'
        f'        <instance_geometry url="#contour_{idx}"/>\n'
        f'      </node>'
        for (idx, z, _) in geometries
    )

    dae = f'''<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
<asset>
  <unit name="foot" meter="0.3048"/>
  <up_axis>Z_UP</up_axis>
</asset>
<library_geometries>
{geom_xml}
</library_geometries>
<library_visual_scenes>
  <visual_scene id="scene" name="scene">
    <node id="contours" name="contours">
{nodes_xml}
    </node>
  </visual_scene>
</library_visual_scenes>
<scene>
  <instance_visual_scene url="#scene"/>
</scene>
</COLLADA>
'''
    Path(out_path).write_text(dae)
    print(f"[write] {out_path}")

def webmerc_to_lonlat(x, y):
    """Inverse of lonlat_to_webmerc: EPSG:3857 meters -> EPSG:4326 degrees."""
    lon = x / 20037508.34 * 180.0
    lat = y / 20037508.34 * 180.0
    lat = 180.0 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
    return lon, lat


def recenter_to_parcel_centroid(contours, parcels, roads=None):
    """Shift all geometry so that the centroid of all parcels is at (0, 0).
    Returns shifted contours, parcels, roads, and the offset applied."""
    if not parcels:
        return contours, parcels, roads or [], (0, 0)

    # Calculate centroid of all parcel vertices
    all_verts = []
    for parcel in parcels:
        for ring in parcel["rings"]:
            for vert in ring:
                all_verts.append((vert[0], vert[1]))  # Extract x,y only

    if not all_verts:
        return contours, parcels, roads or [], (0, 0)

    cx = sum(v[0] for v in all_verts) / len(all_verts)
    cy = sum(v[1] for v in all_verts) / len(all_verts)
    offset = (cx, cy)

    # Shift contours
    shifted_contours = []
    for c in contours:
        shifted_lines = []
        for line in c["lines"]:
            shifted_line = [(p[0] - cx, p[1] - cy) for p in line]
            shifted_lines.append(shifted_line)
        shifted_contours.append({"elev_ft": c["elev_ft"], "lines": shifted_lines})

    # Shift parcels (preserve per-vertex z if present)
    shifted_parcels = []
    for parcel in parcels:
        shifted_rings = []
        for ring in parcel["rings"]:
            shifted_ring = [(p[0] - cx, p[1] - cy) + tuple(p[2:]) for p in ring]
            shifted_rings.append(shifted_ring)
        shifted_parcels.append({**parcel, "rings": shifted_rings})

    # Shift roads (preserve per-vertex z if present)
    shifted_roads = []
    if roads:
        for road in roads:
            shifted_lines = []
            for line in road["lines"]:
                shifted_line = [(p[0] - cx, p[1] - cy) + tuple(p[2:]) for p in line]
                shifted_lines.append(shifted_line)
            shifted_roads.append({**road, "lines": shifted_lines})

    return shifted_contours, shifted_parcels, shifted_roads, offset


def fetch_road_lines(center_lat, center_lon, width_ft, height_ft):
    """Fetch roads from OpenStreetMap (disabled due to API issues).
    To manually add roads, import the preview PNG as a CAD reference."""
    print(f"[roads] road fetching temporarily disabled (OSM API unavailable)")
    return []


def sample_dem_ft(dem_array, x_ft, y_ft, x_extent_ft, y_extent_ft):
    """Sample DEM elevation (ft) at (x_ft, y_ft) where (0,0) is the SW corner
    of the bbox. The raw rasterio array has row 0 at the NORTH edge, so we
    flip the y axis when converting to a pixel index."""
    if dem_array is None or x_extent_ft <= 0 or y_extent_ft <= 0:
        return float("nan")
    h, w = dem_array.shape
    fx = max(0.0, min(1.0, x_ft / x_extent_ft))
    fy = max(0.0, min(1.0, y_ft / y_extent_ft))
    px = int(round(fx * (w - 1)))
    py = int(round((1.0 - fy) * (h - 1)))
    elev_m = dem_array[py, px]
    if np.isnan(elev_m):
        return float("nan")
    return float(elev_m) / 0.3048


def lift_polylines(polylines, dem_array, x_extent_ft, y_extent_ft, z_base_ft):
    """Convert a list of 2D polylines into 3D polylines by sampling the DEM
    at every vertex and subtracting z_base_ft. NaN samples fall back to 0
    (the zero-based ground plane)."""
    lifted = []
    for poly in polylines:
        new_poly = []
        for p in poly:
            x_ft, y_ft = p[0], p[1]
            z = sample_dem_ft(dem_array, x_ft, y_ft, x_extent_ft, y_extent_ft)
            z_out = 0.0 if math.isnan(z) else z - z_base_ft
            new_poly.append((x_ft, y_ft, z_out))
        lifted.append(new_poly)
    return lifted


def fetch_parcel_polygons(center_lat, center_lon, width_ft, height_ft, dem_bbox=None, dem_array=None):
    """Query the Santa Cruz County parcel layer for any parcel polygons that
    intersect the contour bbox. Returns list of dicts:
    {"apn": "086-631-14", "acres": 9.95, "rings": [[(x_ft, y_ft), ...], ...]}
    where coordinates are in feet relative to the SW corner of the actual DEM bbox.
    If dem_bbox is provided, uses that for coordinate alignment; otherwise calculates it.
    """
    if dem_bbox:
        x_extent_ft, y_extent_ft, z_min, z_max, xmin, ymin = dem_bbox
        xmax = xmin + x_extent_ft * 0.3048
        ymax = ymin + y_extent_ft * 0.3048
    else:
        cx, cy = lonlat_to_webmerc(center_lon, center_lat)
        half_w = feet_to_meters(width_ft) / 2.0
        half_h = feet_to_meters(height_ft) / 2.0
        xmin, ymin = cx - half_w, cy - half_h
        xmax, ymax = cx + half_w, cy + half_h
        x_extent_ft = width_ft
        y_extent_ft = height_ft

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
    print(f"[parcel] querying SCC GIS for parcels in bbox...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"[parcel] WARN: query failed ({type(e).__name__}: {e}); skipping overlay")
        return []

    parcels = []
    for feat in data.get("features", []):
        attrs = feat.get("attributes", {})
        apn = attrs.get("APN", "")
        try:
            acres = float(attrs.get("ACRES") or 0)
        except (TypeError, ValueError):
            acres = 0.0
        rings = []
        for ring in feat.get("geometry", {}).get("rings", []):
            ring_ft = []
            for x_m, y_m in ring:
                x_ft = (x_m - xmin) / 0.3048
                y_ft = (y_m - ymin) / 0.3048
                # Clip to contour bbox
                if 0 <= x_ft <= x_extent_ft and 0 <= y_ft <= y_extent_ft:
                    ring_ft.append((x_ft, y_ft))
            if ring_ft:
                rings.append(ring_ft)
        if rings:
            parcels.append({"apn": apn, "acres": acres, "rings": rings})
    print(f"[parcel] found {len(parcels)} parcel(s) in bbox (clipped to contour area)")
    return parcels


def write_preview(contours, out_path, bbox_extent, center_lat, center_lon,
                  parcels=None, highlight_apns=None):
    """Write a PNG preview showing the contour map (top-down)."""
    x_extent, y_extent, z_min, z_max = bbox_extent[0], bbox_extent[1], bbox_extent[2], bbox_extent[3]
    fig, ax = plt.subplots(figsize=(10, 10 * y_extent / x_extent))

    elevs = [c["elev_ft"] for c in contours]
    if elevs:
        norm = matplotlib.colors.Normalize(vmin=min(elevs), vmax=max(elevs))
        cmap = matplotlib.colormaps["terrain"]
        for c in contours:
            color = cmap(norm(c["elev_ft"]))
            for poly in c["lines"]:
                xs = [p[0] for p in poly]
                ys = [p[1] for p in poly]
                ax.plot(xs, ys, color=color, linewidth=0.7)
        for i, c in enumerate(contours):
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

    # Draw parcel boundaries (clipped to axes; labels only if centroid is in view)
    highlight_set = set(a.strip() for a in (highlight_apns or []))
    for parcel in (parcels or []):
        is_hi = parcel["apn"].strip() in highlight_set
        color = "red" if is_hi else "#444444"
        lw    = 2.2  if is_hi else 1.0
        alpha = 1.0  if is_hi else 0.55
        for ring in parcel["rings"]:
            xs = [p[0] for p in ring]
            ys = [p[1] for p in ring]
            ax.plot(xs, ys, color=color, linewidth=lw, alpha=alpha,
                    zorder=10 if is_hi else 5, clip_on=True)
        all_pts = [(p[0], p[1]) for ring in parcel["rings"] for p in ring]
        if not all_pts:
            continue
        cx_lbl = sum(p[0] for p in all_pts) / len(all_pts)
        cy_lbl = sum(p[1] for p in all_pts) / len(all_pts)
        # Skip label if centroid falls outside the contour bbox; matplotlib
        # would otherwise let the off-screen text expand tight_layout.
        if not (0 <= cx_lbl <= x_extent and 0 <= cy_lbl <= y_extent) and not is_hi:
            continue
        label = f"{parcel['apn']}\n{parcel['acres']:.2f} ac"
        txt = ax.text(
            cx_lbl, cy_lbl, label,
            fontsize=9 if is_hi else 7,
            fontweight="bold" if is_hi else "normal",
            ha="center", va="center",
            color=color, zorder=11 if is_hi else 6,
            clip_on=True,
        )
        txt.set_path_effects([
            pe.Stroke(linewidth=2.5, foreground="white"),
            pe.Normal(),
        ])

    # Lat/lon labels at each VERTEX of the highlighted parcel polygon.
    # Coordinates in `parcel["rings"]` are in feet relative to the SW corner
    # of the DEM bbox; convert each vertex back to EPSG:3857 -> EPSG:4326
    # to label it with its true lat/lon.
    cx_m, cy_m = lonlat_to_webmerc(center_lon, center_lat)
    sw_x_m = cx_m - feet_to_meters(x_extent) / 2.0
    sw_y_m = cy_m - feet_to_meters(y_extent) / 2.0

    for parcel in (parcels or []):
        if parcel["apn"].strip() not in highlight_set:
            continue
        # Polygon centroid (for placing labels OUTWARD from parcel interior)
        all_pts = [p for ring in parcel["rings"] for p in ring]
        if not all_pts:
            continue
        cx_p = sum(p[0] for p in all_pts) / len(all_pts)
        cy_p = sum(p[1] for p in all_pts) / len(all_pts)
        for ring in parcel["rings"]:
            # Drop the closing duplicate vertex if present
            verts = ring[:-1] if len(ring) > 1 and ring[0] == ring[-1] else ring
            # Filter to "real" corners: skip vertices where the turn angle is
            # small (boundary essentially straight) -- avoids labeling the
            # dozens of surveyor vertices that some county polygons carry.
            corner_verts = []
            n = len(verts)
            for i in range(n):
                p_prev = verts[(i - 1) % n]
                p_curr = verts[i]
                p_next = verts[(i + 1) % n]
                ax_in, ay_in   = p_curr[0] - p_prev[0], p_curr[1] - p_prev[1]
                ax_out, ay_out = p_next[0] - p_curr[0], p_next[1] - p_curr[1]
                len_in  = math.hypot(ax_in, ay_in)
                len_out = math.hypot(ax_out, ay_out)
                if len_in == 0 or len_out == 0:
                    continue
                cos_a = (ax_in*ax_out + ay_in*ay_out) / (len_in * len_out)
                cos_a = max(-1.0, min(1.0, cos_a))
                turn_deg = math.degrees(math.acos(cos_a))
                if turn_deg >= 15.0:
                    corner_verts.append(p_curr)
            if not corner_verts:
                corner_verts = verts
            for cv in corner_verts:
                vx_ft, vy_ft = cv[0], cv[1]
                # Convert vertex feet -> mercator -> lon/lat
                vx_m = sw_x_m + vx_ft * 0.3048
                vy_m = sw_y_m + vy_ft * 0.3048
                v_lon, v_lat = webmerc_to_lonlat(vx_m, vy_m)
                ns = "N" if v_lat >= 0 else "S"
                ew = "E" if v_lon >= 0 else "W"
                label = f"{abs(v_lat):.6f}°{ns}\n{abs(v_lon):.6f}°{ew}"
                # Push label point slightly outward from polygon centroid,
                # but anchor the text so it extends BACK INTO the plot --
                # keeps labels readable when the parcel hugs the DEM edge.
                dx = vx_ft - cx_p
                dy = vy_ft - cy_p
                d  = math.hypot(dx, dy) or 1.0
                offset = max(x_extent, y_extent) * 0.012
                lx = vx_ft + dx / d * offset
                ly = vy_ft + dy / d * offset
                # Anchor alignment so text extends INWARD from anchor
                ha = "right"  if dx >= 0 else "left"
                va = "top"    if dy >= 0 else "bottom"
                # Marker dot at the vertex itself
                ax.plot(vx_ft, vy_ft, "o", color="red", markersize=4,
                        markeredgecolor="white", markeredgewidth=0.8, zorder=15)
                ax.text(
                    lx, ly, label,
                    fontsize=7, fontweight="bold",
                    ha=ha, va=va, color="darkred",
                    zorder=16, clip_on=True,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                              edgecolor="darkred", linewidth=0.5, alpha=0.9),
                )

    # Center crosshair + label
    cx_ft, cy_ft = x_extent / 2.0, y_extent / 2.0
    ax.plot(cx_ft, cy_ft, "+", color="black", markersize=14, markeredgewidth=1.5,
            zorder=12)
    ctr = ax.text(
        cx_ft, cy_ft - max(x_extent, y_extent) * 0.025,
        f"{center_lat:.6f}, {center_lon:.6f}",
        fontsize=7, ha="center", va="top", color="black", zorder=12,
    )
    ctr.set_path_effects([
        pe.Stroke(linewidth=2, foreground="white"),
        pe.Normal(),
    ])

    ax.set_aspect("equal")
    ax.set_xlim(0, x_extent)
    ax.set_ylim(0, y_extent)
    ax.set_xlabel("East (ft)")
    ax.set_ylabel("North (ft)")
    title_extra = ""
    if highlight_set:
        title_extra = f"  |  parcel(s): {', '.join(sorted(highlight_set))}"
    ax.set_title(
        f"3D Contours -- center: {center_lat:.6f}, {center_lon:.6f}{title_extra}\n"
        f"Elevation: {z_min:.0f} - {z_max:.0f} ft  |  "
        f"Extent: {x_extent:.0f} x {y_extent:.0f} ft"
    )
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"[write] {out_path}")

def main():
    p = argparse.ArgumentParser(
        description="Fetch a DEM and generate 3D contours for SketchUp/FreeCAD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--lat", type=float, required=True,
                   help="Center latitude in decimal degrees")
    p.add_argument("--lon", type=float, required=True,
                   help="Center longitude in decimal degrees (negative for W)")
    p.add_argument("--width", type=float, default=1500,
                   help="Bounding box width in feet (default 1500)")
    p.add_argument("--height", type=float, default=1500,
                   help="Bounding box height in feet (default 1500)")
    p.add_argument("--interval", type=float, default=10.0,
                   help="Contour interval in feet (default 10)")
    p.add_argument("--out", type=str, default="contours",
                   help="Output filename prefix (default 'contours')")
    p.add_argument("--apn", type=str, action="append", default=[],
                   help="Parcel APN(s) to highlight on the preview "
                        "(can be repeated). All parcels intersecting the bbox "
                        "are drawn; highlighted ones are drawn red and labeled "
                        "in bold. Example: --apn 086-631-14")
    p.add_argument("--no-parcels", action="store_true",
                   help="Skip Santa Cruz County parcel boundary fetch")
    p.add_argument("--no-roads", action="store_true",
                   help="Skip Santa Cruz County road fetch")
    args = p.parse_args()

    out_tif = f"{args.out}.tif"
    out_dxf = f"{args.out}.dxf"
    out_dae = f"{args.out}.dae"
    out_png = f"{args.out}.png"

    fetch_dem(args.lat, args.lon, args.width, args.height, out_tif)
    contours, bbox_extent = extract_contours(out_tif, args.interval,
                                             requested_width_ft=args.width,
                                             requested_height_ft=args.height)

    # Load DEM for elevation lookup on parcel boundaries
    dem_array = None
    try:
        with rasterio.open(out_tif) as src:
            dem_array = src.read(1).astype(np.float64)
    except Exception as e:
        print(f"[parcel] WARN: could not load DEM for elevation projection ({e})")

    parcels = []
    if not args.no_parcels:
        parcels = fetch_parcel_polygons(args.lat, args.lon, args.width, args.height,
                                        dem_bbox=bbox_extent, dem_array=dem_array)
    roads = []
    if not args.no_roads:
        roads = fetch_road_lines(args.lat, args.lon, args.width, args.height)

    # Zero-base the terrain so the lowest contour sits at z=0 (so the FreeCAD
    # origin lines up with the bottom of the terrain). Drape parcels and roads
    # onto the DEM at each vertex so they trace the ground surface.
    x_extent_ft, y_extent_ft, z_min, z_max = bbox_extent[0], bbox_extent[1], bbox_extent[2], bbox_extent[3]
    z_base = z_min
    print(f"[zero-base] shifting contours down by {z_base:.1f} ft "
          f"(terrain z now spans 0 - {z_max - z_base:.1f} ft)")
    for c in contours:
        c["elev_ft"] = c["elev_ft"] - z_base
    bbox_extent = (x_extent_ft, y_extent_ft, 0.0, z_max - z_base) + bbox_extent[4:]

    for parcel in parcels:
        parcel["rings"] = lift_polylines(parcel["rings"], dem_array,
                                         x_extent_ft, y_extent_ft, z_base)
    for road in roads:
        road["lines"] = lift_polylines(road["lines"], dem_array,
                                       x_extent_ft, y_extent_ft, z_base)

    # Recenter so parcel centroid is at (0, 0)
    contours, parcels, roads, offset = recenter_to_parcel_centroid(contours, parcels, roads)
    if offset != (0, 0):
        print(f"[center] recentered to parcel centroid: offset ({offset[0]:.1f}, {offset[1]:.1f}) ft")

    write_dxf(contours, out_dxf, parcels=parcels, roads=roads)
    write_dae(contours, out_dae, bbox_extent, parcels=parcels, roads=roads)
    write_preview(contours, out_png, bbox_extent, args.lat, args.lon,
                  parcels=parcels, highlight_apns=args.apn)

    print()
    print("Done. Files written:")
    print(f"  {out_tif}  -- raw DEM (open in QGIS / FreeCAD Geodata)")
    print(f"  {out_dxf}  -- 3D contours for AutoCAD / FreeCAD / QCAD")
    print(f"  {out_dae}  -- 3D contours for SketchUp")
    print(f"  {out_png}  -- preview image")

if __name__ == "__main__":
    main()
