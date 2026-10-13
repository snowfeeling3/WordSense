"""Fetch pinned upstream license texts once; store them with the release materials."""
from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
import shutil
import importlib.metadata

SOURCES = {
    "Python-3.13.5-LICENSE.txt": "https://raw.githubusercontent.com/python/cpython/v3.13.5/LICENSE",
    "LGPL-3.0-only.txt": "https://raw.githubusercontent.com/qt/qtbase/v6.8.3/LICENSES/LGPL-3.0-only.txt",
    "GPL-3.0-only.txt": "https://raw.githubusercontent.com/qt/qtbase/v6.8.3/LICENSES/GPL-3.0-only.txt",
    "Qt-GPL-exception-1.0.txt": "https://raw.githubusercontent.com/qt/qtbase/v6.8.3/LICENSES/Qt-GPL-exception-1.0.txt",
}


def main():
    directory = Path(__file__).resolve().parents[1] / "packaging" / "licenses"
    directory.mkdir(exist_ok=True)
    def fetch(entry):
        name, url = entry
        destination = directory / name
        if not destination.exists():
            with urlopen(url, timeout=30) as response:
                payload = response.read()
            if len(payload) < 500:
                raise RuntimeError(f"Invalid license download: {name}")
            destination.write_bytes(payload)
        return name
    with ThreadPoolExecutor(max_workers=4) as pool:
        for name in pool.map(fetch, SOURCES.items()):
            print(name)
    distribution = importlib.metadata.distribution("PyInstaller")
    license_file = next(p for p in distribution.files if str(p).endswith("licenses/COPYING.txt"))
    shutil.copyfile(distribution.locate_file(license_file), directory / "PyInstaller-COPYING.txt")
    (directory / "SOURCES.txt").write_text("\n".join(f"{name}: {url}" for name, url in SOURCES.items()) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
