import tempfile
import unittest
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QTextCursor
from PySide6.QtTest import QTest
from wordsense.inflections import build_aliases, forms
from wordsense.storage import Storage
from wordsense.window import MainWindow
from test_wordsense import APP, color_at, COLORS


class InflectionTests(unittest.TestCase):
    def test_save_updates_only_affected_paragraphs_and_keeps_sidebar_items(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(directory)
            storage.upsert_word("write", "写", 3)
            storage.upsert_word("walk", "行走", 3)
            window = MainWindow(storage)
            window.editor.load_text("writing wrote\nwalking\nunknown")
            APP.processEvents()
            item = window.sidebar._items["write"]
            window.sidebar.search_input.setText("写")
            window.select_dictionary_word("write")
            window.meaning_input.setText("书写")
            before = window.editor.highlighter.blocks_processed
            window.save_word()
            self.assertEqual(window.editor.highlighter.blocks_processed, before)
            self.assertIs(window.sidebar._items["write"], item)
            self.assertFalse(item.isHidden())
            window.level_input.setCurrentIndex(window.level_input.findData(0))
            before = window.editor.highlighter.blocks_processed
            window.save_word()
            self.assertEqual(window.editor.highlighter.blocks_processed - before, 1)
            self.assertEqual(color_at(window.editor, 1), COLORS[0])
            window.meaning_input.setText("compose")
            window.save_word()
            self.assertTrue(item.isHidden())
            self.assertEqual(window.sidebar._visible_count, 0)
            window.word_input.setText("writing")
            window.meaning_input.setText("写作")
            window.level_input.setCurrentIndex(window.level_input.findData(2))
            window.save_word()
            self.assertEqual(color_at(window.editor, 1), COLORS[2])
            self.assertEqual(color_at(window.editor, 9), COLORS[0])
            self.assertEqual(window.sidebar._visible_count, 1)
            window.close()

    def test_document_replacement_highlights_once_and_restores_editing(self):
        from wordsense.editor import WordEditor
        editor = WordEditor({"write": ("写", 3)})
        text = "Writing wrote written.\n" * 1500
        before = editor.highlighter.blocks_processed
        editor.load_text(text)
        APP.processEvents()
        self.assertEqual(editor.highlighter.blocks_processed - before,
                         editor.document().blockCount())
        self.assertEqual(editor.toPlainText(), text)
        self.assertEqual(color_at(editor, 1), COLORS[3])
        self.assertTrue(editor.document().isLayoutEnabled())
        self.assertTrue(editor.updatesEnabled())
        self.assertTrue(editor.isUndoRedoEnabled())
        self.assertFalse(editor.document().isUndoAvailable())
        editor.insertPlainText("test")
        editor.undo()
        self.assertEqual(editor.toPlainText(), text)
        editor.close()

    def test_spelling_rules(self):
        for base, expected in {
            "walk": {"walked", "walking"}, "study": {"studied", "studying"},
            "make": {"made", "making"}, "stop": {"stopped", "stopping"},
            "open": {"opened", "opening"}, "tie": {"tied", "tying"},
            "write": {"wrote", "written", "writing"},
            "see": {"saw", "seen", "seeing"},
        }.items():
            self.assertEqual(forms(base), expected)
        self.assertNotIn("stoped", forms("stop"))

    def test_explicit_entries_and_ambiguity(self):
        self.assertNotIn("writing", build_aliases({"write": ("写", 3), "writing": ("写作", 2)}))
        self.assertNotIn("lying", build_aliases({"lie": ("躺", 3), "ly": ("例外", 2)}))

    def test_click_edit_highlight_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = Storage(directory)
            storage.upsert_word("write", "写", 3)
            window = MainWindow(storage)
            window.editor.load_text("😀 Writing, wrote written! unknown ")
            window.show()
            APP.processEvents()
            self.assertEqual(color_at(window.editor, 4), COLORS[3])
            cursor = window.editor.textCursor()
            cursor.setPosition(5)
            point = window.editor.cursorRect(cursor).center() + QPoint(2, 0)
            QTest.mouseClick(window.editor.viewport(), Qt.MouseButton.LeftButton, pos=point)
            self.assertEqual(window.word_input.text(), "write")
            self.assertEqual(window.meaning_input.text(), "写")
            self.assertFalse(window.editor.textCursor().hasSelection())
            window.meaning_input.setText("书写")
            window.level_input.setCurrentIndex(window.level_input.findData(2))
            self.assertTrue(window.save_word())
            APP.processEvents()
            self.assertEqual(color_at(window.editor, 4), COLORS[2])
            window.word_input.setText("writing")
            window.meaning_input.setText("写作")
            window.level_input.setCurrentIndex(window.level_input.findData(0))
            window.save_word()
            APP.processEvents()
            self.assertEqual(color_at(window.editor, 4), COLORS[0])
            self.assertEqual(color_at(window.editor, 14), COLORS[2])
            window.inspect_document_word("unknown")
            self.assertEqual(window.word_input.text(), "unknown")
            self.assertEqual(window.meaning_input.text(), "")
            window.close()
            storage = Storage(directory)
            window = MainWindow(storage)
            self.assertNotIn("writing", window.editor.highlighter.aliases)
            self.assertEqual(window.words["write"], ("书写", 2))
            window.close()
