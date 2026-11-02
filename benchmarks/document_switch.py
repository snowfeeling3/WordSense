"""Synthetic document-switch timings; no personal documents or dictionary."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import json
import statistics
import tempfile
import time
from datetime import date, timedelta
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication
from wordsense.storage import Storage
from wordsense.window import MainWindow
from tools.qt_fonts import load_offscreen_fonts


def main():
    app = QApplication.instance() or QApplication([])
    load_offscreen_fonts(app)
    text = "apple pear unknown.\n" * 6000
    samples, passes = [], []
    with tempfile.TemporaryDirectory() as directory:
        storage = Storage(directory)
        window = MainWindow(storage)
        window.show()
        app.processEvents()
        for offset in range(1, 6):
            target = date.today() - timedelta(days=offset)
            storage.document_path(target).write_text(text, encoding="utf-8")
            before = window.editor.highlighter.blocks_processed
            start = time.perf_counter()
            window.date_input.setDate(QDate(target.year, target.month, target.day))
            app.processEvents()
            samples.append(round((time.perf_counter() - start) * 1000, 2))
            passes.append(window.editor.highlighter.blocks_processed - before)
            assert window.editor.toPlainText() == text
        window.close()
    print(json.dumps({"characters": len(text), "paragraphs": 6000,
                      "switch_ms": samples, "median_ms": statistics.median(samples),
                      "highlighted_blocks_per_switch": passes,
                      "method": "Qt offscreen; synchronous save, read, load and event processing; excludes physical screen presentation"}, indent=2))


if __name__ == "__main__":
    main()
