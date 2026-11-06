"""Generate a faster, offline SVG London basemap from Geofabrik OSM shapefiles.

Keeps the same EPSG:27700 bounds and metadata contract as report_vector.py.
Run: python scripts/generate_london_map.py
"""
from pathlib import Path
import json
import gzip
import geopandas as gpd

BASE = Path(__file__).resolve().parents[1]
GEO = BASE / 'data' / 'geography'
OUT = BASE / 'reports'
CRS = 'EPSG:27700'
WIDTH = 1600
# Each SVG path may contain many disconnected subpaths. This cuts DOM node count.
MAX_COMMANDS_PER_PATH = 700
# Exclude fine-grained access routes from the regional overview.
# Keep residential and classified streets, so central London remains navigable.
MINOR_TYPES = {
    'tertiary', 'tertiary_link', 'residential', 'living_street',
    'unclassified', 'pedestrian',
}
MAJOR_TYPES = {
    'motorway', 'motorway_link', 'trunk', 'trunk_link',
    'primary', 'primary_link', 'secondary', 'secondary_link',
}


def load_layer(filename):
    path = GEO / filename
    if not path.exists():
        raise FileNotFoundError(f'Missing shapefile: {path}')
    print(f'Loading {filename}...', flush=True)
    return gpd.read_file(path).to_crs(CRS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    landuse = load_layer('gis_osm_landuse_a_free_1.shp')
    water = load_layer('gis_osm_water_a_free_1.shp')
    roads = load_layer('gis_osm_roads_free_1.shp')
    print(f'Road segments: {len(roads):,}; land use: {len(landuse):,}; water: {len(water):,}', flush=True)

    xmin, ymin, xmax, ymax = map(float, roads.total_bounds)
    margin = 3500.0
    xmin -= margin; ymin -= margin; xmax += margin; ymax += margin
    height = round(WIDTH * (ymax - ymin) / (xmax - xmin))
    sx = WIDTH / (xmax - xmin)
    sy = height / (ymax - ymin)

    def xy(x, y):
        # Two decimal places give ~metre-level display coordinates at this scale.
        return f'{(x-xmin)*sx:.2f},{(ymax-y)*sy:.2f}'

    def geometry_paths(geom):
        if geom is None or geom.is_empty:
            return
        kind = geom.geom_type
        if kind in ('MultiLineString', 'MultiPolygon', 'GeometryCollection'):
            for part in geom.geoms:
                yield from geometry_paths(part)
        elif kind == 'LineString':
            coords = geom.coords
            if len(coords) >= 2:
                yield 'M' + 'L'.join(xy(x, y) for x, y in coords)
        elif kind == 'Polygon':
            for ring in [geom.exterior, *geom.interiors]:
                if len(ring.coords) >= 4:
                    yield 'M' + 'L'.join(xy(x, y) for x, y in ring.coords) + 'Z'

    def write_group(f, geometries, style, tolerance, label):
        f.write(f'<g {style}>\n')
        count_features = 0
        count_elements = 0
        chunk = []
        for geom in geometries:
            if geom is None or geom.is_empty:
                continue
            simplified = geom.simplify(tolerance, preserve_topology=False)
            for d in geometry_paths(simplified):
                chunk.append(d)
                count_features += 1
                if len(chunk) >= MAX_COMMANDS_PER_PATH:
                    f.write('<path d="' + ''.join(chunk) + '"/>\n')
                    chunk.clear()
                    count_elements += 1
        if chunk:
            f.write('<path d="' + ''.join(chunk) + '"/>\n')
            count_elements += 1
        f.write('</g>\n')
        print(f'  {label}: {count_features:,} subpaths in {count_elements:,} SVG elements', flush=True)
        return count_features, count_elements

    svg_path = OUT / 'london_basemap_georeferenced.svg'
    with svg_path.open('w', encoding='utf-8') as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}">\n')
        f.write(f'<rect width="{WIDTH}" height="{height}" fill="#f8fafc"/>\n')
        green = landuse[landuse['fclass'].isin(['park', 'forest', 'grass', 'meadow', 'recreation_ground'])]
        write_group(f, green.geometry, 'fill="#d8ebd0" fill-rule="evenodd" stroke="none"', 22, 'green space')
        write_group(f, water.geometry, 'fill="#b9dff2" fill-rule="evenodd" stroke="none"', 12, 'water')
        minor = roads['fclass'].isin(MINOR_TYPES)
        major = roads['fclass'].isin(MAJOR_TYPES)
        print(f'  Retaining {int(minor.sum()):,} minor and {int(major.sum()):,} major road segments', flush=True)
        write_group(f, roads.loc[minor, 'geometry'], 'fill="none" stroke="#d1d5db" stroke-width="0.5" stroke-linecap="round" stroke-linejoin="round"', 18, 'minor roads')
        write_group(f, roads.loc[major, 'geometry'], 'fill="none" stroke="#e7a65b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"', 8, 'major roads')
        f.write('</svg>\n')

    metadata = {
        'image': svg_path.name,
        'crs': CRS,
        'bounds_projected_metres': {'left': xmin, 'bottom': ymin, 'right': xmax, 'top': ymax},
        'image_pixels': {'width': WIDTH, 'height': height},
        'pixel_mapping': 'x=(easting-left)/(right-left)*width; y=(top-northing)/(top-bottom)*height',
        'attribution': 'Map data © OpenStreetMap contributors, via Geofabrik; ODbL',
        'note': 'Police API crime locations are approximate, not exact incident addresses.'
    }
    bounds_path = OUT / 'london_theft_map_bounds.json'
    bounds_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(f'Optimised vector basemap: {svg_path} ({svg_path.stat().st_size / 1024 / 1024:.1f} MB)', flush=True)
    print(f'Projection metadata: {bounds_path}', flush=True)
    print('Next: run ./run.sh to embed the optimised SVG in the dashboard.', flush=True)


if __name__ == '__main__':
    main()
