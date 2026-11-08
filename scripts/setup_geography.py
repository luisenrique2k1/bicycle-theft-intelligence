
"""Download and prepare Greater London OpenStreetMap shapefiles."""

from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlparse
from zipfile import ZipFile
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "data" / "geography"

URL = (
    "https://download.geofabrik.de/europe/united-kingdom/"
    "england/greater-london-latest-free.shp.zip"
)

LAYERS = (
    "gis_osm_landuse_a_free_1",
    "gis_osm_water_a_free_1",
    "gis_osm_roads_free_1",
)

EXTENSIONS = (".shp", ".shx", ".dbf", ".prj")


def files_present():
    return all(
        (DESTINATION / f"{layer}{extension}").is_file()
        for layer in LAYERS
        for extension in EXTENSIONS
    )


def main():
    DESTINATION.mkdir(parents=True, exist_ok=True)

    if files_present():
        print("Geographical shapefiles already exist. Skipping download.")
        return

    print("Downloading Greater London OpenStreetMap shapefiles...")

    with tempfile.TemporaryDirectory() as temporary:
        archive_path = Path(temporary) / "greater-london.zip"

        with urlopen(URL, timeout=120) as response, archive_path.open("wb") as output:
            shutil.copyfileobj(response, output)

        print("Extracting required geographical layers...")

        with ZipFile(archive_path) as archive:
            for member in archive.infolist():
                if member.is_dir():
                    continue

                name = Path(member.filename).name
                if not name.startswith(LAYERS):
                    continue

                if Path(name).suffix.lower() not in (*EXTENSIONS, ".cpg"):
                    continue

                with archive.open(member) as source:
                    with (DESTINATION / name).open("wb") as target:
                        shutil.copyfileobj(source, target)

    if not files_present():
        raise RuntimeError("Required geographical shapefiles are missing.")

    print("Geographical data preparation completed successfully.")


if __name__ == "__main__":
    main()
