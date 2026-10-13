"""Run from project root: python -m benchmarks.benchmark."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import json
import platform
import statistics
import time
from pathlib import Path
from PySide6 import __version__ as qt_binding_version
from PySide6.QtCore import QMimeData, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from wordsense.editor import WordEditor
from tools.qt_fonts import load_offscreen_fonts


def main():
    app = QApplication.instance() or QApplication([])
    load_offscreen_fonts(app)
    editor = WordEditor({"apple": ("苹果", 0), "pear": ("梨", 1)})
    editor.load_text("  ")
    text = "apple pear unknown.\n" * 6000
    mime = QMimeData()
    mime.setText(text)
    start = time.perf_counter_ns()
    editor.insertFromMimeData(mime)
    paste_ms = (time.perf_counter_ns() - start) / 1e6
    app.processEvents()
    samples = []
    counts = []
    cursor = editor.textCursor()
    cursor.setPosition(5)
    editor.setTextCursor(cursor)
    for _ in range(100):
        before = editor.highlighter.blocks_processed
        start = time.perf_counter_ns()
        QTest.keyClicks(editor, "x ")
        samples.append((time.perf_counter_ns() - start) / 1e6)
        counts.append(editor.highlighter.blocks_processed - before)
        QTest.keyClick(editor, Qt.Key.Key_Backspace)
        QTest.keyClick(editor, Qt.Key.Key_Backspace)
    # Also measure a single very long paragraph: QSyntaxHighlighter is block-granular.
    editor.load_text(text.replace("\n", " "))
    cursor = editor.textCursor()
    cursor.setPosition(5)
    editor.setTextCursor(cursor)
    start = time.perf_counter_ns()
    QTest.keyClicks(editor, "x ")
    single_block_ms = (time.perf_counter_ns() - start) / 1e6
    editor.load_text("apple pear unknown. " * 500)
    cursor = editor.textCursor()
    cursor.setPosition(5)
    editor.setTextCursor(cursor)
    start = time.perf_counter_ns()
    QTest.keyClicks(editor, "x ")
    ten_k_ms = (time.perf_counter_ns() - start) / 1e6
    result = {
        "python": platform.python_version(), "pyside6": qt_binding_version,
        "platform": platform.platform(), "characters": len(text), "paragraphs": 6000,
        "paste_ms": round(paste_ms, 3), "local_edit_samples": len(samples),
        "local_two_keys_median_ms": round(statistics.median(samples), 3),
        "local_two_keys_p95_ms": round(sorted(samples)[94], 3),
        "local_two_keys_max_ms": round(max(samples), 3),
        "max_blocks_per_two_keys": max(counts),
        "single_120k_character_paragraph_two_keys_ms": round(single_block_ms, 3),
        "single_10k_character_paragraph_two_keys_ms": round(ten_k_ms, 3),
        "fonts": "Windows Segoe UI, Consolas, Microsoft YaHei loaded for offscreen layout",
        "method": "offscreen QTest synchronous key event + highlighting; excludes disk and screen presentation"
    }
    Path("benchmarks/results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
