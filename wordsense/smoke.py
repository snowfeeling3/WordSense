"""Opt-in packaged-runtime verification; exclusively uses temporary user data."""
import json
import os
import sys
import tempfile
import traceback
from pathlib import Path
from PySide6.QtCore import QDate, QTimer, QEvent, Qt
from PySide6.QtGui import QKeyEvent
from .window import MainWindow
from . import __version__


def run_smoke(app, report_filename):
    report_path = Path(report_filename).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)

    def check():
        result = {"version": __version__, "frozen": bool(getattr(sys, "frozen", False)),
                  "qt_platform": app.platformName()}
        previous = os.environ.get("LOCALAPPDATA")
        window = None
        temporary_directory = tempfile.TemporaryDirectory()
        try:
            # Keep temporary files alive until the window/SQLite connection close,
            # even when an assertion fails during native-window verification.
            directory = temporary_directory.name
            if directory:
                os.environ["LOCALAPPDATA"] = directory
                window = MainWindow()
                assert not window.windowIcon().isNull()
                assert [window.level_input.itemText(i) for i in range(window.level_input.count())] == ["完全理解", "有点模糊", "完全不懂"]
                window.show()
                app.processEvents()
                today = window.document_date
                window.focus_word_input()
                window.word_input.setText("Apple")
                app.sendEvent(window.word_input, QKeyEvent(QEvent.Type.KeyPress,
                    Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier))
                assert window.focusWidget() is window.meaning_input
                assert "apple" not in window.words
                window.meaning_input.setText("苹果")
                window.level_input.setCurrentIndex(window.level_input.findData(0))
                app.sendEvent(window.meaning_input, QKeyEvent(QEvent.Type.KeyPress,
                    Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier))
                assert window.focusWidget() is window.editor
                assert window.words["apple"] == ("苹果", 0)
                assert window.sidebar.word_list.item(0).text() == "apple\n苹果"
                text = "  Apple, unknown words!\n  Markdown 文档 😀\n"
                window.editor.load_text(text)
                spans = window.editor.document().firstBlock().layout().formats()
                assert any(span.start == 9 and span.format.foreground().color().name().upper() == "#DBBC7F" for span in spans)
                assert window.save_markdown()
                today_path = window.storage.document_path(today)
                assert today_path.read_text(encoding="utf-8") == text
                window.date_input.setDate(QDate.currentDate().addDays(-1))
                assert window.editor.toPlainText() == "  "
                assert window.words == {"apple": ("苹果", 0)}
                window.editor.load_text("  Yesterday Apple.\n")
                assert window.save_markdown()
                assert len(list(window.storage.documents_directory.glob("*.md"))) == 2
                window.date_input.setDate(QDate.currentDate())
                assert window.editor.toPlainText() == text
                assert window.storage.path == Path(directory) / "WordSense" / "wordsense.sqlite3"
                old_documents = window.storage.documents_directory
                new_documents = Path(directory) / "English documents 文档"
                count, leftovers = window.storage.set_documents_directory(new_documents)
                assert count == 2 and leftovers == []
                assert not old_documents.exists()
                assert window.storage.load_text(today) == text
                old_database = window.storage.path
                new_database_directory = Path(directory) / "Vocabulary 统一词库"
                assert window.storage.set_database_directory(new_database_directory) == []
                assert not old_database.exists()
                assert window.storage.load_words()["apple"] == ("苹果", 0)
                window.close()
                window = MainWindow()
                window.show()
                app.processEvents()
                assert window.editor.toPlainText() == text
                assert window.words["apple"] == ("苹果", 0)
                assert window.storage.documents_directory == new_documents.resolve()
                assert window.storage.path == new_database_directory.resolve() / "wordsense.sqlite3"
                assert not old_documents.exists()
                assert window.grab().save(str(report_path.with_suffix(".png")))
                window.close()
                window = None
                result.update(status="passed", checks=["native window", "shared dictionary",
                    "UTF-8 Markdown save", "date switch", "two separate daily files",
                    "fixed user directory", "restart recovery", "Enter dictionary workflow",
                    "meaning without level suffix", "document directory migration and cleanup",
                    "document directory setting survives restart", "bundled application logo",
                    "shared database relocation and old-file cleanup", "database path survives restart",
                    "three understanding levels and yellow unrecorded words"])
        except Exception:
            result.update(status="failed", error=traceback.format_exc())
            if window is not None:
                window.close()
        finally:
            temporary_directory.cleanup()
            if previous is None:
                os.environ.pop("LOCALAPPDATA", None)
            else:
                os.environ["LOCALAPPDATA"] = previous
            report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            app.exit(0 if result.get("status") == "passed" else 1)

    QTimer.singleShot(0, check)
    return app.exec()
