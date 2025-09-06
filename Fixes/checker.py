import json
import csv
import re
from shapely.geometry import Point, Polygon

def dms_to_decimal(dms):
    match = re.match(r'([NSEW])(\d{2,3})(\d{2})(\d{2})$', dms)
    if not match:
        raise ValueError(f"Ogiltigt koordinatformat: {dms}")
    direction, deg, minutes, seconds = match.groups()
    decimal = int(deg) + int(minutes) / 60 + int(seconds) / 3600
    if direction in ['S', 'W']:
        decimal = -decimal
    return decimal

def parse_position(pos_str):
    lat_str, lon_str = pos_str.strip().split()
    lat = dms_to_decimal(lat_str)
    lon = dms_to_decimal(lon_str)
    return lat, lon

def load_sectors(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    sectors = []
    for sector in data:
        name = sector["name"]
        polygon_coords = []
        for coord_str in sector["polygon"]:
            lat, lon = parse_position(coord_str)
            polygon_coords.append((lon, lat))
        polygon = Polygon(polygon_coords)
        saltitude = sector.get("saltitude", 0)
        ealtitude = sector.get("ealtitude", 999)
        sectors.append({
            "name": name,
            "polygon": polygon,
            "saltitude": saltitude,
            "ealtitude": ealtitude
        })
    return sectors

def load_fixes(filename):
    fixes = []
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row['name']
            lat, lon = parse_position(row['position'])
            fixes.append({
                "name": name,
                "point": Point(lon, lat)
            })
    return fixes

def assign_fixes_to_sectors(sectors, fixes):
    results = []
    for fix in fixes:
        fix_name = fix["name"]
        point = fix["point"]
        matched = []
        for sector in sectors:
            if sector["polygon"].covers(point):
                matched.append(sector["name"])
        if matched:
            for sector_name in matched:
                results.append((fix_name, sector_name))
        else:
            results.append((fix_name, "Outside"))
    return results

def assign_fixes_vertically(sectors, fixes):
    results = []
    for fix in fixes:
        fix_name = fix["name"]
        point = fix["point"]
        matching_sectors = []
        for sector in sectors:
            if sector["polygon"].covers(point):
                matching_sectors.append(sector)
        if matching_sectors:
            sorted_sectors = sorted(matching_sectors, key=lambda s: s["saltitude"])
            output_parts = [fix_name]
            for i, sector in enumerate(sorted_sectors):
                output_parts.append(sector["name"])
                if i < len(sorted_sectors) - 1:
                    boundary = sorted_sectors[i]["ealtitude"]
                    output_parts.append(str(boundary))
            results.append(":".join(output_parts))
        else:
            results.append(f"{fix_name} Outside")
    return results


def main():
    sectors = load_sectors("sektorer.json")
    fixes = load_fixes("fixes.csv")
    results = assign_fixes_vertically(sectors, fixes)

    with open("output.txt", "w") as f:
        for line in results:
            f.write(line + "\n")

if __name__ == "__main__":
    main()