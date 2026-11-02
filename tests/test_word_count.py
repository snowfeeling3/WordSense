import random
import tempfile
import unittest
from PySide6.QtCore import QDate, QMimeData
from PySide6.QtGui import QTextCursor
from wordsense.editor import WordEditor, TOKEN
from wordsense.storage import Storage
from wordsense.window import MainWindow
from test_wordsense import APP


class WordCountTests(unittest.TestCase):
    def test_edits_splits_joins_undo_and_bulk_paste(self):
        editor = WordEditor({})
        editor.load_text("😀 Hello, 中文 world! 123\nHello")
        self.assertEqual(editor.word_count, 3)
        mime = QMimeData()
        mime.setText("\nnew words\nanother line")
        editor.insertFromMimeData(mime)
        self.assertEqual(editor.word_count, 7)
        editor.undo()
        self.assertEqual(editor.word_count, 3)
        editor.redo()
        self.assertEqual(editor.word_count, 7)
        editor.load_text("alpha beta\ngamma\ndelta")
        rng = random.Random(8)
        for _ in range(150):
            cursor = editor.textCursor()
            start = rng.randrange(editor.document().characterCount())
            end = rng.randrange(start, editor.document().characterCount())
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            cursor.insertText(rng.choice(["", "\n", "one two", "x\ny\nz", "123!"]))
            APP.processEvents()
            self.assertEqual(editor.word_count, len(TOKEN.findall(editor.toPlainText())))
            self.assertEqual(len(editor._block_word_counts), editor.document().blockCount())
        editor.close()

    def test_counter_persists_through_status_messages_and_date_switch(self):
        with tempfile.TemporaryDirectory() as directory:
            window = MainWindow(Storage(directory))
            window.editor.load_text("one two three")
            self.assertEqual(window.word_count_label.text(), "词数：3")
            window.statusBar().showMessage("保存成功")
            self.assertEqual(window.word_count_label.text(), "词数：3")
            window.date_input.setDate(QDate.currentDate().addDays(-1))
            self.assertEqual(window.word_count_label.text(), "词数：0")
            window.date_input.setDate(QDate.currentDate())
            self.assertEqual(window.word_count_label.text(), "词数：3")
            window.close()
