import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
import unittest
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch
from concurrent.futures import Future
from PySide6.QtCore import Qt, QMimeData, QDate
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from wordsense.editor import WordEditor, COLORS, NEUTRAL_COLOR
from wordsense.storage import Storage, normalize, write_markdown
from wordsense.window import MainWindow
from tools.qt_fonts import load_offscreen_fonts

APP = QApplication.instance() or QApplication([])
load_offscreen_fonts(APP)


def color_at(editor, position):
    block = editor.document().findBlock(position)
    for span in block.layout().formats():
        if span.start <= position - block.position() < span.start + span.length:
            return span.format.foreground().color().name().upper()
    return NEUTRAL_COLOR


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.words = {"apple": ("苹果", 0), "pear": ("梨", 2), "applepear": ("合并", 2)}
        self.editor = WordEditor(self.words)
        self.editor.load_text("  ")
        self.editor.show()
        APP.processEvents()

    def tearDown(self):
        self.editor.close()

    def type(self, text):
        QTest.keyClicks(self.editor, text)

    def move(self, position):
        cursor = self.editor.textCursor()
        cursor.setPosition(position)
        self.editor.setTextCursor(cursor)

    def test_casefold(self):
        self.type("Apple APPLE apple ")
        self.assertEqual(self.editor.toPlainText(), "  Apple APPLE apple ")
        for position in (2, 8, 14):
            self.assertEqual(color_at(self.editor, position), COLORS[0])

    def test_pending_then_separator_immediate(self):
        self.type("apple")
        self.assertEqual(color_at(self.editor, 2), NEUTRAL_COLOR)
        self.type(" ")
        self.assertEqual(color_at(self.editor, 2), COLORS[0])

    def test_delimiters(self):
        for separator in (",", ".", ";", "(", ")", "!", "1", "-"):
            self.editor.load_text("  ")
            self.type("apple" + separator)
            self.assertEqual(color_at(self.editor, 2), COLORS[0], separator)
        self.editor.load_text("  ")
        self.type("apple")
        QTest.keyClick(self.editor, Qt.Key.Key_Return)
        self.assertEqual(color_at(self.editor, 2), COLORS[0])
        self.assertEqual(self.editor.toPlainText(), "  apple\n  ")

    def test_unknown(self):
        self.type("banana ")
        self.assertEqual(color_at(self.editor, 2), NEUTRAL_COLOR)

    def test_recorded_words_colored_unknown_yellow_then_register(self):
        self.words["known"] = ("已理解", 3)
        self.editor.load_text("  known banana apple pear applepear ")
        for position, expected in ((2, COLORS[3]), (8, NEUTRAL_COLOR), (15, COLORS[0]),
                                   (21, COLORS[2]), (26, COLORS[2])):
            self.assertEqual(color_at(self.editor, position), expected)
        self.words["banana"] = ("香蕉", 0)
        self.editor.highlighter.rehighlight()
        self.assertEqual(color_at(self.editor, 8), COLORS[0])

    def test_dictionary_refresh_preserves_cursor_and_undo(self):
        self.type("apple ")
        position = self.editor.textCursor().position()
        self.words["apple"] = ("苹果", 2)
        self.editor.highlighter.rehighlight()
        self.assertEqual(color_at(self.editor, 2), COLORS[2])
        self.assertEqual(self.editor.textCursor().position(), position)
        self.editor.undo()
        self.editor.redo()
        self.assertEqual(self.editor.toPlainText(), "  apple ")

    def test_delete_separator_merge_and_complete(self):
        self.editor.load_text("  apple pear ")
        self.move(8)
        QTest.keyClick(self.editor, Qt.Key.Key_Backspace)
        self.assertEqual(self.editor.toPlainText(), "  applepear ")
        self.assertEqual(color_at(self.editor, 2), COLORS[2])
        self.move(11)
        self.type(",")
        self.assertEqual(color_at(self.editor, 2), COLORS[2])

    def test_delete_separator_with_delete_key(self):
        self.editor.load_text("  apple pear ")
        self.move(7)
        QTest.keyClick(self.editor, Qt.Key.Key_Delete)
        self.assertEqual(self.editor.toPlainText(), "  applepear ")
        self.assertEqual(color_at(self.editor, 2), COLORS[2])

    def test_middle_replacement(self):
        self.editor.load_text("  apple pear apple ")
        cursor = self.editor.textCursor()
        cursor.setPosition(8)
        cursor.setPosition(12, QTextCursor.MoveMode.KeepAnchor)
        self.editor.setTextCursor(cursor)
        self.type("apple")
        self.assertEqual(color_at(self.editor, 8), NEUTRAL_COLOR)
        self.type(" ")
        for position in (2, 8, 15):
            self.assertEqual(color_at(self.editor, position), COLORS[0])

    def test_paste_large_multiline_and_unicode(self):
        mime = QMimeData()
        text = "😀 apple pear.\n" * 3000
        mime.setText(text)
        self.editor.insertFromMimeData(mime)
        expected = "  " + text.replace("\n", "\n  ")
        self.assertEqual(self.editor.toPlainText(), expected)
        self.assertEqual(color_at(self.editor, 5), COLORS[0])
        self.assertEqual(color_at(self.editor, 11), COLORS[2])
        self.editor.undo()
        self.assertEqual(self.editor.toPlainText(), "  ")
        self.editor.redo()
        self.assertEqual(self.editor.toPlainText(), expected)

    def test_indentation_undo_redo_selection_and_backspace(self):
        self.type("apple")
        for _ in range(2):
            QTest.keyClick(self.editor, Qt.Key.Key_Return)
        self.assertEqual(self.editor.toPlainText(), "  apple\n  \n  ")
        expected_position = self.editor.textCursor().position()
        for _ in range(10):
            self.editor.undo()
            self.editor.redo()
            self.assertEqual(self.editor.textCursor().position(), expected_position)
        QTest.keyClick(self.editor, Qt.Key.Key_Backspace)
        self.assertEqual(self.editor.toPlainText(), "  apple\n  \n ")
        self.editor.selectAll()
        QTest.keyClick(self.editor, Qt.Key.Key_Return)
        self.assertEqual(self.editor.toPlainText(), "\n  ")
        self.editor.undo()
        self.assertEqual(self.editor.toPlainText(), "  apple\n  \n ")

    def test_soft_wrap_and_shift_enter(self):
        self.editor.resize(100, 200)
        self.type("apple " * 30)
        self.assertNotIn("\n", self.editor.toPlainText())
        QTest.keyClick(self.editor, Qt.Key.Key_Return, Qt.KeyboardModifier.ShiftModifier)
        self.assertTrue(self.editor.toPlainText().endswith("\n"))
        self.assertFalse(self.editor.toPlainText().endswith("\n  "))

    def test_local_block_work(self):
        self.editor.load_text("apple pear.\n" * 3000)
        count = self.editor.highlighter.blocks_processed
        self.move(6)
        self.type("x ")
        self.assertLess(self.editor.highlighter.blocks_processed - count, 12)

    def test_old_pending_block_refresh_on_edit_elsewhere(self):
        self.editor.load_text("  apple \n  ")
        self.type("pear")
        self.assertEqual(color_at(self.editor, 11), NEUTRAL_COLOR)
        self.move(7)
        self.type("!")
        self.assertEqual(color_at(self.editor, 12), COLORS[2])

    def test_paste_indentation_selection_one_undo(self):
        mime = QMimeData()
        mime.setText("Apple\r\n  pear\r\nbanana")
        self.editor.selectAll()
        self.editor.insertFromMimeData(mime)
        self.assertEqual(self.editor.toPlainText(), "  Apple\n  pear\n  banana")
        self.assertEqual(color_at(self.editor, 2), COLORS[0])
        self.editor.undo()
        self.assertEqual(self.editor.toPlainText(), "  ")


class PersistenceTests(unittest.TestCase):
    def test_restart_and_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(directory)
            storage.upsert_word("Apple", "苹果", 0)
            storage.upsert_word("APPLE", "苹果更新", 2)
            storage.save_text("  Apple\n  pear").result()
            storage.save_text("  最终 apple ").result()
            storage.close()
            storage = Storage(directory)
            self.assertEqual(storage.load_words(), {"apple": ("苹果更新", 2)})
            self.assertEqual(storage.load_text(), "  最终 apple ")
            row = storage.connection.execute("SELECT id,created_at,updated_at FROM words").fetchone()
            self.assertTrue(all(row))
            storage.close()

    def test_validation(self):
        for invalid in ("", "apple pear", "café", "apple1", "苹果"):
            with self.assertRaises(ValueError):
                normalize(invalid)

    def test_failed_background_save_can_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(directory)
            failed = Future()
            failed.set_exception(OSError("simulated disk failure"))
            storage.pending.append(failed)
            with self.assertRaises(OSError):
                storage.collect_finished()
            self.assertEqual(storage.pending, [])
            storage.save_text("  recovered ").result(timeout=5)
            storage.collect_finished()
            self.assertEqual(storage.load_text(), "  recovered ")
            storage.close()

    def test_window_lookup_save_close_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            window = MainWindow(Storage(directory))
            window.word_input.setText("Apple")
            window.meaning_input.setText("苹果")
            window.level_input.setCurrentIndex(window.level_input.findData(0))
            window.save_word()
            window.editor.load_text("  apple ")
            self.assertEqual(color_at(window.editor, 2), COLORS[0])
            window.word_input.setText("APPLE")
            self.assertEqual(window.meaning_input.text(), "苹果")
            window.level_input.setCurrentIndex(window.level_input.findData(2))
            window.save_word()
            self.assertEqual(color_at(window.editor, 2), COLORS[2])
            window.close()
            restored = MainWindow(Storage(directory))
            self.assertEqual(restored.editor.toPlainText(), "  apple ")
            self.assertEqual(restored.words["apple"], ("苹果", 2))
            restored.close()

    def test_event_triggered_background_autosave(self):
        with tempfile.TemporaryDirectory() as directory:
            window = MainWindow(Storage(directory))
            QTest.keyClicks(window.editor, "apple ")
            self.assertTrue(window.save_timer.isActive())
            QTest.qWait(850)
            self.assertFalse(window.save_timer.isActive())
            self.assertTrue(window.storage.pending)
            window.storage.pending[-1].result(timeout=5)
            self.assertEqual(window.storage.load_text(), "  apple ")
            window.close()


class SidebarTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        storage = Storage(self.directory.name)
        for word, meaning, level in (("pear", "梨", 2), ("apple", "苹果", 0),
                                     ("pineapple", "菠萝", 2)):
            storage.upsert_word(word, meaning, level)
        self.window = MainWindow(storage)
        self.window.show()
        APP.processEvents()

    def tearDown(self):
        self.window.close()
        self.directory.cleanup()

    def visible_words(self):
        widget = self.window.sidebar.word_list
        return [widget.item(index).data(Qt.ItemDataRole.UserRole)
                for index in range(widget.count()) if not widget.item(index).isHidden()]

    def test_search_english_chinese_no_match_and_clear(self):
        self.assertEqual(self.visible_words(), ["apple", "pear", "pineapple"])
        search = self.window.sidebar.search_input
        QTest.keyClicks(search, "APP")
        self.assertEqual(self.visible_words(), ["apple", "pineapple"])
        search.setText("苹果")
        self.assertEqual(self.visible_words(), ["apple"])
        search.setText("missing")
        self.assertEqual(self.visible_words(), [])
        self.assertIn("没有匹配结果", self.window.sidebar.result_label.text())
        search.clear()
        self.assertEqual(len(self.visible_words()), 3)

    def test_sidebar_has_meaning_without_level_suffix(self):
        widget = self.window.sidebar.word_list
        self.assertEqual(widget.item(0).text(), "apple\n苹果")
        self.assertEqual(widget.item(1).text(), "pear\n梨")
        self.assertEqual(widget.item(2).text(), "pineapple\n菠萝")
        self.assertEqual(widget.item(0).toolTip(), "apple\n苹果")
        self.assertEqual(widget.item(0).foreground().color().name().upper(), COLORS[0])

    def test_keyboard_add_word_flow_preserves_editor_cursor(self):
        self.window.editor.load_text("  apple pear ")
        cursor = self.window.editor.textCursor()
        cursor.setPosition(8)
        self.window.editor.setTextCursor(cursor)
        self.window.editor.setFocus()
        APP.processEvents()
        QTest.keyClick(self.window.editor, Qt.Key.Key_L, Qt.KeyboardModifier.ControlModifier)
        self.assertTrue(self.window.word_input.hasFocus())
        QTest.keyClicks(self.window.word_input, "banana")
        QTest.keyClick(self.window.word_input, Qt.Key.Key_Return)
        self.assertTrue(self.window.meaning_input.hasFocus())
        self.assertNotIn("banana", self.window.words)
        self.window.meaning_input.setText("香蕉")
        QTest.keyClick(self.window.meaning_input, Qt.Key.Key_Return)
        self.assertEqual(self.window.words["banana"], ("香蕉", 3))
        self.assertTrue(self.window.editor.hasFocus())
        self.assertEqual(self.window.editor.textCursor().position(), 8)
        self.assertEqual(self.window.editor.toPlainText(), "  apple pear ")
        QTest.keyClicks(self.window.editor, "banana ")
        self.assertEqual(self.window.editor.toPlainText(), "  apple banana pear ")
        QTest.keyClick(self.window.editor, Qt.Key.Key_L, Qt.KeyboardModifier.ControlModifier)
        self.assertEqual(self.window.word_input.selectedText(), "banana")

    def test_enter_updates_existing_word_and_returns_to_editor(self):
        self.window.word_input.setText("APPLE")
        self.window.word_input.setFocus()
        QTest.keyClick(self.window.word_input, Qt.Key.Key_Return)
        self.assertTrue(self.window.meaning_input.hasFocus())
        self.assertEqual(self.window.meaning_input.selectedText(), "苹果")
        self.window.meaning_input.setText("苹果；水果")
        self.window.level_input.setCurrentIndex(self.window.level_input.findData(2))
        QTest.keyClick(self.window.meaning_input, Qt.Key.Key_Return)
        self.assertEqual(self.window.storage.load_words()["apple"], ("苹果；水果", 2))
        self.assertTrue(self.window.editor.hasFocus())

    def test_invalid_word_enter_save_retains_input_for_correction(self):
        self.window.word_input.setText("bad1")
        self.window.meaning_input.setText("保留词义")
        self.window.meaning_input.setFocus()
        with patch("wordsense.window.QMessageBox.warning") as warning:
            QTest.keyClick(self.window.meaning_input, Qt.Key.Key_Return)
            warning.assert_called_once()
        self.assertTrue(self.window.word_input.hasFocus())
        self.assertEqual(self.window.word_input.selectedText(), "bad1")
        self.assertEqual(self.window.meaning_input.text(), "保留词义")
        self.assertNotIn("bad1", self.window.words)

    def test_select_update_filter_and_restart(self):
        self.window.editor.load_text("  apple ")
        cursor_position = self.window.editor.textCursor().position()
        sidebar = self.window.sidebar
        sidebar.search_input.setText("苹果")
        item = sidebar.word_list.item(0)
        QTest.mouseClick(sidebar.word_list.viewport(), Qt.MouseButton.LeftButton,
                         pos=sidebar.word_list.visualItemRect(item).center())
        self.assertEqual(self.window.word_input.text(), "apple")
        self.assertEqual(self.window.meaning_input.text(), "苹果")
        self.assertEqual(self.window.level_input.currentData(), 0)
        self.window.meaning_input.setText("苹果；水果")
        self.window.level_input.setCurrentIndex(self.window.level_input.findData(2))
        self.window.save_word()
        self.assertEqual(sidebar.search_input.text(), "苹果")
        self.assertEqual(self.visible_words(), ["apple"])
        self.assertIn("水果", sidebar.word_list.item(0).text())
        self.assertEqual(sidebar.word_list.item(0).foreground().color().name().upper(), COLORS[2])
        self.assertEqual(color_at(self.window.editor, 2), COLORS[2])
        self.assertEqual(self.window.editor.textCursor().position(), cursor_position)
        self.window.close()
        self.window = MainWindow(Storage(self.directory.name))
        self.assertEqual(len(self.visible_words()), 3)
        self.window.sidebar.word_list.setCurrentRow(0)
        self.assertEqual(self.window.meaning_input.text(), "苹果；水果")
        self.assertEqual(self.window.level_input.currentData(), 2)

    def test_empty_dictionary_add_under_active_search(self):
        self.window.close()
        # A separate database models a first launch with no recorded words.
        self.window = MainWindow(Storage(os.path.join(self.directory.name, "empty")))
        self.assertIn("词典为空", self.window.sidebar.result_label.text())
        self.window.sidebar.search_input.setText("APP")
        self.window.word_input.setText("Apple")
        self.window.meaning_input.setText("苹果")
        self.window.save_word()
        self.assertEqual(self.visible_words(), ["apple"])
        self.assertIn("1 / 1", self.window.sidebar.result_label.text())
        self.window.meaning_input.setText("水果")
        self.window.sidebar.search_input.setText("苹果")
        self.window.save_word()
        self.assertEqual(self.visible_words(), [])
        self.assertEqual(self.window.meaning_input.text(), "水果")


class MarkdownTests(unittest.TestCase):
    def test_document_menu_date_and_save_shortcut(self):
        with tempfile.TemporaryDirectory() as directory:
            window = MainWindow(Storage(directory))
            window.show()
            APP.processEvents()
            self.assertFalse(window.date_input.isVisible())
            window.editor.load_text("  Menu document ")
            window.editor.setFocus()
            QTest.keyClick(window.editor, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)
            self.assertEqual(window.storage.load_text(), "  Menu document ")
            window.document_menu.popup(window.document_menu_button.mapToGlobal(
                window.document_menu_button.rect().bottomLeft()))
            APP.processEvents()
            self.assertTrue(window.date_input.isVisible())
            selected = QDate.currentDate().addDays(-1)
            window.date_input.setDate(selected)
            self.assertEqual(window.document_label.text(), selected.toString("yyyy-MM-dd") + ".md")
            self.assertFalse(window.document_menu.isVisible())
            self.assertEqual(window.editor.toPlainText(), "  ")
            window.close()

    def test_daily_files_and_queued_saves_share_single_dictionary(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(directory)
            storage.upsert_word("Apple", "苹果", 0)
            first, second = "2026-10-11", "2026-10-12"
            a = storage.save_text("  # Day one\n  Apple 😀", first)
            b = storage.save_text("  # Day two\n  APPLE", second)
            a.result(timeout=5)
            b.result(timeout=5)
            self.assertEqual(storage.load_text(first), "  # Day one\n  Apple 😀")
            self.assertEqual(storage.load_text(second), "  # Day two\n  APPLE")
            self.assertEqual(storage.document_path(first).name, "2026-10-11.md")
            storage.close()
            storage = Storage(directory)
            self.assertEqual(storage.load_words(), {"apple": ("苹果", 0)})
            self.assertEqual(len(list(Path(directory).rglob("*.sqlite3"))), 1)
            self.assertEqual(len(list(storage.documents_directory.glob("*.md"))), 2)
            self.assertEqual(storage.load_text(first), "  # Day one\n  Apple 😀")
            storage.close()

    def create_legacy(self, directory):
        connection = sqlite3.connect(Path(directory) / "wordsense.sqlite3")
        with connection:
            connection.execute("CREATE TABLE editor_state(id INTEGER PRIMARY KEY, text TEXT NOT NULL)")
            connection.execute("INSERT INTO editor_state VALUES(1,?)", ("  Legacy Apple\n  旧文档",))
        connection.close()

    def test_legacy_text_migrates_once(self):
        with tempfile.TemporaryDirectory() as directory:
            self.create_legacy(directory)
            storage = Storage(directory)
            self.assertEqual(storage.load_text(), "  Legacy Apple\n  旧文档")
            storage.save_text("  New content").result()
            storage.close()
            storage = Storage(directory)
            self.assertEqual(storage.load_text(), "  New content")
            storage.close()

    def test_legacy_migration_never_overwrites_existing_daily_file(self):
        with tempfile.TemporaryDirectory() as directory:
            self.create_legacy(directory)
            documents = Path(directory) / "documents"
            documents.mkdir()
            path = documents / f"{date.today().isoformat()}.md"
            path.write_text("  Already saved", encoding="utf-8")
            storage = Storage(directory)
            self.assertEqual(storage.load_text(), "  Already saved")
            self.assertEqual(storage.connection.execute("SELECT text FROM editor_state").fetchone()[0],
                             "  Legacy Apple\n  旧文档")
            storage.close()

    def test_atomic_write_failure_keeps_previous_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "day.md"
            write_markdown(path, "previous")
            with patch("wordsense.storage.os.replace", side_effect=OSError("simulated replace failure")):
                with self.assertRaises(OSError):
                    write_markdown(path, "new text")
            self.assertEqual(path.read_text(encoding="utf-8"), "previous")
            self.assertEqual(list(Path(directory).glob("*.tmp")), [])

    def test_window_switch_autosaves_and_shares_word_updates(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(directory)
            storage.upsert_word("apple", "苹果", 0)
            window = MainWindow(storage)
            today = window.document_date
            previous = today - timedelta(days=1)
            window.editor.load_text("  Apple today ")
            window.date_input.setDate(QDate(previous.year, previous.month, previous.day))
            self.assertEqual(window.editor.toPlainText(), "  ")
            self.assertEqual(storage.load_text(today), "  Apple today ")
            window.editor.load_text("  apple yesterday ")
            window.word_input.setText("apple")
            window.level_input.setCurrentIndex(window.level_input.findData(2))
            window.save_word()
            window.date_input.setDate(QDate(today.year, today.month, today.day))
            self.assertEqual(window.editor.toPlainText(), "  Apple today ")
            self.assertEqual(color_at(window.editor, 2), COLORS[2])
            self.assertEqual(storage.load_text(previous), "  apple yesterday ")
            window.close()

    def test_export_markdown_preserves_text_and_does_not_create_dictionary(self):
        with tempfile.TemporaryDirectory() as directory:
            window = MainWindow(Storage(Path(directory) / "user"))
            text = "  # Heading\n  **Apple** 中文 😀\n"
            window.editor.load_text(text)
            output = Path(directory) / "exported"
            with patch("wordsense.window.QFileDialog.getSaveFileName", return_value=(str(output), "")):
                window.export_markdown()
            self.assertEqual(output.with_suffix(".md").read_text(encoding="utf-8"), text)
            self.assertEqual(window.storage.load_text(), text)
            self.assertEqual(len(list(Path(directory).rglob("*.sqlite3"))), 1)
            window.close()

    def test_failed_save_prevents_date_switch_and_keeps_editor(self):
        with tempfile.TemporaryDirectory() as directory:
            window = MainWindow(Storage(directory))
            window.editor.load_text("  Unsaved Apple ")
            today = window.document_date
            failed = Future()
            failed.set_exception(OSError("simulated disk failure"))
            with patch.object(window.storage, "save_text", return_value=failed), \
                    patch("wordsense.window.QMessageBox.warning") as warning:
                window.date_input.setDate(QDate.currentDate().addDays(-1))
                self.assertEqual(window.document_date, today)
                self.assertEqual(window.date_input.date(), QDate(today.year, today.month, today.day))
                self.assertEqual(window.editor.toPlainText(), "  Unsaved Apple ")
                warning.assert_called_once()
            window.close()


class DocumentLocationTests(unittest.TestCase):
    def test_migrate_verify_cleanup_and_restart_keep_single_dictionary(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(Path(directory) / "user")
            storage.upsert_word("apple", "苹果", 0)
            storage.save_text("  One 😀", "2026-10-11").result()
            storage.save_text("  Two 中文", "2026-10-12").result()
            old = storage.documents_directory
            (old / ".wordsense-crash.tmp").write_bytes(b"stale temporary")
            target = Path(directory) / "My English 文档"
            count, leftovers = storage.set_documents_directory(target)
            self.assertEqual((count, leftovers), (2, []))
            self.assertFalse(old.exists())
            self.assertEqual(storage.load_text("2026-10-11"), "  One 😀")
            self.assertEqual(storage.load_words(), {"apple": ("苹果", 0)})
            database = storage.path
            storage.close()
            storage = Storage(Path(directory) / "user")
            self.assertEqual(storage.documents_directory, target.resolve())
            self.assertEqual(storage.load_text("2026-10-12"), "  Two 中文")
            self.assertEqual(storage.path, database)
            self.assertFalse(old.exists())
            storage.close()

    def test_conflicting_destination_preserves_all_originals(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(Path(directory) / "user")
            storage.save_text("original", "2026-10-11").result()
            storage.save_text("second", "2026-10-12").result()
            old = storage.documents_directory
            target = Path(directory) / "other"
            target.mkdir()
            (target / "2026-10-12.md").write_text("different", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                storage.set_documents_directory(target)
            self.assertEqual(storage.documents_directory, old)
            self.assertEqual(storage.load_text("2026-10-11"), "original")
            self.assertEqual((target / "2026-10-12.md").read_text(encoding="utf-8"), "different")
            self.assertFalse((target / "2026-10-11.md").exists())
            storage.close()

    def test_copy_failure_keeps_old_setting_and_rolls_back_new_copies(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(Path(directory) / "user")
            storage.save_text("first", "2026-10-11").result()
            storage.save_text("second", "2026-10-12").result()
            old = storage.documents_directory
            target = Path(directory) / "other"
            from wordsense.storage import write_atomic
            def fail_second(path, data):
                if Path(path).name == "2026-10-12.md":
                    raise OSError("simulated copy failure")
                return write_atomic(path, data)
            with patch("wordsense.storage.write_atomic", side_effect=fail_second):
                with self.assertRaises(OSError):
                    storage.set_documents_directory(target)
            self.assertEqual(storage.documents_directory, old)
            self.assertEqual(len(list(old.glob("*.md"))), 2)
            self.assertEqual(list(target.glob("*.md")), [])
            storage.close()

    def test_locked_original_cleanup_can_retry_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(Path(directory) / "user")
            storage.save_text("original", "2026-10-11").result()
            old_file = storage.document_path("2026-10-11")
            old_directory = storage.documents_directory
            target = Path(directory) / "other"
            original_unlink = Path.unlink
            def busy(path, *args, **kwargs):
                if path == old_file:
                    raise PermissionError("simulated busy file")
                return original_unlink(path, *args, **kwargs)
            with patch.object(Path, "unlink", new=busy):
                count, leftovers = storage.set_documents_directory(target)
            self.assertEqual(count, 1)
            self.assertEqual(leftovers, [str(old_file)])
            self.assertTrue(old_file.exists())
            self.assertEqual(storage.load_text("2026-10-11"), "original")
            storage.close()
            storage = Storage(Path(directory) / "user")
            self.assertEqual(storage.cleanup_old_documents(), [])
            self.assertFalse(old_directory.exists())
            storage.close()

    def test_unrelated_files_and_nested_destination_are_protected(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(Path(directory) / "user")
            old = storage.documents_directory
            unrelated = old / "personal.txt"
            unrelated.write_text("keep", encoding="utf-8")
            unrelated_markdown = old / "project-notes.md"
            unrelated_markdown.write_text("keep notes", encoding="utf-8")
            with self.assertRaises(ValueError):
                storage.set_documents_directory(old / "nested")
            storage.save_text("document", "2026-10-11").result()
            storage.set_documents_directory(Path(directory) / "other")
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "keep")
            self.assertEqual(unrelated_markdown.read_text(encoding="utf-8"), "keep notes")
            self.assertFalse((old / "2026-10-11.md").exists())
            storage.close()

    def test_choose_location_flushes_current_document_and_preserves_cursor(self):
        with tempfile.TemporaryDirectory() as directory:
            window = MainWindow(Storage(Path(directory) / "user"))
            window.editor.load_text("  Current writing 😀 ")
            cursor_position = window.editor.textCursor().position()
            old = window.storage.documents_directory
            target = Path(directory) / "Chosen 文档"
            with patch("wordsense.window.QFileDialog.getExistingDirectory", return_value=str(target)):
                window.choose_documents_directory()
            self.assertEqual(window.storage.documents_directory, target.resolve())
            self.assertFalse(old.exists())
            self.assertEqual(window.storage.load_text(), "  Current writing 😀 ")
            self.assertEqual(window.editor.textCursor().position(), cursor_position)
            window.close()


class DatabaseLocationTests(unittest.TestCase):
    def test_migrate_database_preserves_words_documents_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            storage = Storage(home)
            storage.upsert_word("apple", "苹果", 0)
            storage.save_text("  Apple ").result()
            docs = Path(directory) / "Articles"
            storage.set_documents_directory(docs)
            old = storage.path
            target = Path(directory) / "统一词库 中文"
            self.assertEqual(storage.set_database_directory(target), [])
            self.assertFalse(old.exists())
            self.assertFalse(Path(str(old) + "-wal").exists())
            self.assertEqual(storage.load_words(), {"apple": ("苹果", 0)})
            self.assertEqual(storage.documents_directory, docs.resolve())
            storage.upsert_word("PEAR", "梨", 1)
            storage.close()
            storage = Storage(home)
            self.assertEqual(storage.path, target.resolve() / "wordsense.sqlite3")
            self.assertEqual(storage.load_words(), {"apple": ("苹果", 0), "pear": ("梨", 2)})
            self.assertEqual(storage.load_text(), "  Apple ")
            self.assertFalse(old.exists())
            self.assertEqual(len(list(Path(directory).rglob("*.sqlite3"))), 1)
            storage.close()

    def test_existing_target_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(Path(directory) / "home")
            storage.upsert_word("apple", "苹果", 0)
            target = Path(directory) / "occupied"
            target.mkdir()
            existing = target / "wordsense.sqlite3"
            existing.write_bytes(b"keep original target")
            old = storage.path
            with self.assertRaises(FileExistsError):
                storage.set_database_directory(target)
            self.assertEqual(existing.read_bytes(), b"keep original target")
            self.assertEqual(storage.path, old)
            self.assertEqual(storage.load_words()["apple"], ("苹果", 0))
            storage.close()

    def test_settings_failure_keeps_original_database_usable(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(Path(directory) / "home")
            storage.upsert_word("apple", "苹果", 0)
            old = storage.path
            target = Path(directory) / "other"
            with patch("wordsense.storage.write_atomic", side_effect=OSError("simulated configuration failure")):
                with self.assertRaises(OSError):
                    storage.set_database_directory(target)
            self.assertTrue(old.exists())
            self.assertFalse((target / "wordsense.sqlite3").exists())
            self.assertEqual(storage.path, old)
            self.assertEqual(storage.load_words()["apple"], ("苹果", 0))
            storage.upsert_word("pear", "梨", 1)
            storage.close()

    def test_missing_configured_database_does_not_create_empty_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            storage = Storage(home)
            target = Path(directory) / "other"
            storage.set_database_directory(target)
            storage.close()
            (target / "wordsense.sqlite3").unlink()
            with self.assertRaises(FileNotFoundError):
                Storage(home)
            self.assertFalse((home / "wordsense.sqlite3").exists())
            self.assertFalse((target / "wordsense.sqlite3").exists())

    def test_gui_chooses_database_directory_preserves_editor(self):
        with tempfile.TemporaryDirectory() as directory:
            window = MainWindow(Storage(Path(directory) / "home"))
            window.word_input.setText("apple")
            window.meaning_input.setText("苹果")
            window.save_word()
            window.editor.load_text("  apple ")
            position = window.editor.textCursor().position()
            target = Path(directory) / "Chosen database"
            with patch("wordsense.window.QFileDialog.getExistingDirectory", return_value=str(target)):
                window.choose_database_directory()
            self.assertEqual(window.storage.path, target.resolve() / "wordsense.sqlite3")
            self.assertEqual(window.editor.textCursor().position(), position)
            self.assertEqual(window.editor.toPlainText(), "  apple ")
            self.assertEqual(window.words["apple"], ("苹果", 3))
            window.close()


class UnderstandingLevelsTests(unittest.TestCase):
    def test_legacy_levels_migrate_without_losing_words_or_timestamps(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(directory)
            storage.close()
            connection = sqlite3.connect(Path(directory) / "wordsense.sqlite3")
            with connection:
                connection.execute("DELETE FROM app_meta WHERE key='understanding_levels'")
                for word, level in (("red", 0), ("oldyellow", 1), ("blue", 2), ("green", 3)):
                    connection.execute("INSERT INTO words(word,meaning,level) VALUES(?,?,?)", (word, "词义", level))
            before = connection.execute("SELECT id,word,meaning,created_at,updated_at FROM words ORDER BY id").fetchall()
            connection.close()
            storage = Storage(directory)
            after = storage.connection.execute("SELECT id,word,meaning,created_at,updated_at FROM words ORDER BY id").fetchall()
            self.assertEqual(before, after)
            self.assertEqual(storage.load_words(), {"red": ("词义", 0), "oldyellow": ("词义", 2),
                                                    "blue": ("词义", 2), "green": ("词义", 3)})
            self.assertEqual(storage.connection.execute("SELECT count(*) FROM words WHERE level=1").fetchone()[0], 0)
            storage.close()
            storage = Storage(directory)
            self.assertEqual(len(storage.load_words()), 4)
            storage.close()

    def test_three_choices_and_yellow_unknown_in_real_window(self):
        with tempfile.TemporaryDirectory() as directory:
            window = MainWindow(Storage(directory))
            self.assertEqual([window.level_input.itemText(i) for i in range(window.level_input.count())],
                             ["完全理解", "有点模糊", "完全不懂"])
            window.word_input.setText("fuzzy")
            window.meaning_input.setText("模糊")
            window.level_input.setCurrentIndex(window.level_input.findText("有点模糊"))
            window.save_word()
            window.editor.load_text("  fuzzy unknown ")
            self.assertEqual(color_at(window.editor, 2), "#7FBBB3")
            self.assertEqual(color_at(window.editor, 8), "#DBBC7F")
            self.assertEqual(window.storage.load_words()["fuzzy"], ("模糊", 2))
            window.close()


if __name__ == "__main__":
    unittest.main()
