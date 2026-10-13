from pathlib import Path
from PySide6.QtGui import QIcon

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def app_icon():
    return QIcon(str(ASSETS / "wordsense.ico"))
