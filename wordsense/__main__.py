import sys
import os
from PySide6.QtWidgets import QApplication
from .window import MainWindow
from . import __version__
from .branding import app_icon


def main():
    if os.name == "nt":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("WordSense.Desktop")
    app = QApplication(sys.argv)
    app.setApplicationName("WordSense")
    app.setOrganizationName("WordSense")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(app_icon())
    if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
        from .smoke import run_smoke
        return run_smoke(app, sys.argv[2])
    try:
        window = MainWindow()
    except Exception as error:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(None, "WordSense 无法启动", str(error))
        return 1
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
