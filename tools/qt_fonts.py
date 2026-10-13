"""Supply real Windows fonts when Qt's offscreen plugin has no system fonts."""
import os
from pathlib import Path
from PySide6.QtGui import QFontDatabase


def load_offscreen_fonts(app):
    if app.platformName() != "offscreen" or os.name != "nt":
        return
    directory = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for name in ("segoeui.ttf", "consola.ttf", "msyh.ttc"):
        path = directory / name
        if path.exists():
            QFontDatabase.addApplicationFont(str(path))
