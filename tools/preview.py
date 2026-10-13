"""Render the real Qt window using a temporary demo database."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
from pathlib import Path
from PySide6.QtWidgets import QApplication
from wordsense.storage import Storage
from wordsense.window import MainWindow
from tools.qt_fonts import load_offscreen_fonts


def main():
    app = QApplication([])
    load_offscreen_fonts(app)
    with tempfile.TemporaryDirectory() as directory:
        storage = Storage(directory)
        for word, meaning, level in (("beautiful", "美丽的", 2), ("curiosity", "好奇心", 2),
                                     ("resilience", "韧性；恢复能力", 0), ("understand", "理解", 3)):
            storage.upsert_word(word, meaning, level)
        window = MainWindow(storage)
        window.editor.load_text(
            "  Hello, beautiful world!\n  Every new word is a small discovery.\n\n"
            "  Curiosity brings us closer to the things we want to understand.\n"
            "  Learning takes patience, practice, and resilience.\n\n"
            "  Write freely. Let your vocabulary grow with you.")
        window.word_input.setText("resilience")
        window.show()
        app.processEvents()
        Path("docs").mkdir(exist_ok=True)
        if not window.grab().save("docs/preview.png"):
            raise RuntimeError("Unable to save preview")
        window.document_menu.popup(window.document_menu_button.mapToGlobal(
            window.document_menu_button.rect().bottomLeft()))
        app.processEvents()
        if not window.document_menu.grab().save("docs/document-menu.png"):
            raise RuntimeError("Unable to save menu preview")
        window.document_menu.close()
        window.close()
    print("docs/preview.png")


if __name__ == "__main__":
    main()
