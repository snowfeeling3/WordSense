import unittest
from PySide6.QtGui import QInputMethodEvent
from wordsense.editor import WordEditor
from test_wordsense import APP
class InputMethodTests(unittest.TestCase):
 def test_preedit_commit_unicode_and_undo(self):
  editor=WordEditor({});editor.show();editor.setFocus()
  APP.sendEvent(editor,QInputMethodEvent("zhong",[]))
  self.assertEqual(editor.toPlainText(),"")
  commit=QInputMethodEvent();commit.setCommitString("中文😀 hello ");APP.sendEvent(editor,commit);APP.processEvents()
  self.assertEqual(editor.toPlainText(),"中文😀 hello ");self.assertEqual(editor.word_count,1)
  editor.undo();self.assertEqual(editor.toPlainText(),"")
  editor.redo();self.assertEqual(editor.toPlainText(),"中文😀 hello ");editor.close()
