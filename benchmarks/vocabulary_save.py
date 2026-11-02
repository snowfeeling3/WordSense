"""Measure saving with synthetic vocabulary and documents, never user data."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import json
import tempfile
import time
from PySide6.QtWidgets import QApplication
from wordsense.storage import Storage
from wordsense.window import MainWindow
from tools.qt_fonts import load_offscreen_fonts


def main():
    app = QApplication.instance() or QApplication([])
    load_offscreen_fonts(app)
    with tempfile.TemporaryDirectory() as directory:
        storage = Storage(directory)
        def key(index):
            return "term" + "".join(chr(97 + (index // 26**j) % 26) for j in range(4))
        storage.connection.executemany(
            "INSERT INTO words(word,meaning,level) VALUES(?,?,0)",
            [(key(i), "demo definition") for i in range(6500)])
        storage.connection.commit()
        storage.upsert_word("apple", "apple definition", 0)
        window = MainWindow(storage)
        window.show()
        window.editor.load_text("apple pear unknown.\n" * 6000)
        app.processEvents()
        samples = {}
        for name, word, level in (("meaning_only", "apple", 0),
                                  ("level_all_paragraphs", "apple", 3),
                                  ("new_word_no_matches", "newword", 3)):
            window.word_input.setText(word)
            window.meaning_input.setText("updated definition")
            window.level_input.setCurrentIndex(window.level_input.findData(level))
            before = window.editor.highlighter.blocks_processed
            start = time.perf_counter()
            assert window.save_word()
            app.processEvents()
            samples[name] = {"ms": round((time.perf_counter() - start) * 1000, 2),
                             "highlighted_blocks": window.editor.highlighter.blocks_processed - before}
        window.close()
    print(json.dumps({"vocabulary": 6501, "characters": 120000, "results": samples,
                      "method": "Qt offscreen including event processing; excludes physical screen presentation"}, indent=2))


if __name__ == "__main__":
    main()
