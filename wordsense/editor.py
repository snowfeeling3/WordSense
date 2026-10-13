"""Incremental ASCII highlighting, with Qt UTF-16 position handling."""
import re
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QTextEdit
from .theme import GREEN, BLUE, RED, YELLOW

COLORS = {0: RED, 2: BLUE, 3: GREEN}
NEUTRAL_COLOR = YELLOW
TOKEN = re.compile(r"[A-Za-z]+")


def ascii_letter(character):
    return "a" <= character <= "z" or "A" <= character <= "Z"


class WordHighlighter(QSyntaxHighlighter):
    def __init__(self, document, words, editor):
        super().__init__(document)
        self.words = words
        self.editor = editor
        self.formats = {}
        self.neutral_format = QTextCharFormat()
        self.neutral_format.setForeground(QColor(NEUTRAL_COLOR))
        self.blocks_processed = 0
        for level, color in COLORS.items():
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))
            self.formats[level] = fmt

    def highlightBlock(self, text):
        self.blocks_processed += 1
        # Python indexes code points; QTextDocument indexes UTF-16 code units.
        offsets = None
        if any(ord(char) > 0xFFFF for char in text):
            offsets = [0]
            for char in text:
                offsets.append(offsets[-1] + (2 if ord(char) > 0xFFFF else 1))
        pending = self.editor.pending_position
        base = self.currentBlock().position()
        for match in TOKEN.finditer(text):
            start, end = match.span()
            if offsets is not None:
                start, end = offsets[start], offsets[end]
            entry = self.words.get(match.group().casefold())
            level = (2 if entry[1] == 1 else entry[1]) if entry is not None else None
            fmt = self.formats[level] if level is not None else self.neutral_format
            if pending is not None and base + start < pending <= base + end:
                fmt = self.neutral_format
            self.setFormat(start, end - start, fmt)


class WordEditor(QTextEdit):
    def __init__(self, words, parent=None):
        super().__init__(parent)
        self.pending_position = None
        self._pending_block = None
        self._batch = False
        self.setAcceptRichText(False)
        self.setTextColor(QColor(NEUTRAL_COLOR))
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setTabChangesFocus(False)
        self.document().contentsChange.connect(self._contents_changed)
        self.highlighter = WordHighlighter(self.document(), words, self)

    def _contents_changed(self, position, removed, added):
        previous_block = self._pending_block
        end = position + added
        doc = self.document()
        self.pending_position = None
        self._pending_block = None
        if not self._batch and end > 0 and ascii_letter(doc.characterAt(end - 1)):
            incomplete = added > 0
            if added == 0:
                # A deletion can merge two already delimited words. Classify the
                # merged token immediately when its existing trailing delimiter remains.
                token_end = end
                while ascii_letter(doc.characterAt(token_end)):
                    token_end += 1
                incomplete = token_end == doc.characterCount() - 1
            if incomplete:
                self.pending_position = end
                self._pending_block = doc.findBlock(end - 1)
        # Qt handles edited blocks itself. An earlier pending block may need refresh.
        if previous_block is not None and previous_block.isValid():
            if previous_block != doc.findBlock(position):
                self.highlighter.rehighlightBlock(previous_block)

    def load_text(self, text):
        self._batch = True
        try:
            self.setPlainText(text)
            self.pending_position = None
            self._pending_block = None
            self.highlighter.rehighlight()
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.setTextCursor(cursor)
            self.document().clearUndoRedoStacks()
        finally:
            self._batch = False

    def insertFromMimeData(self, source):
        # One native edit operation, one incremental highlighting pass.
        if not source.hasText():
            return
        text = source.text().replace("\r\n", "\n").replace("\r", "\n")
        lines = text.split("\n")
        cursor = self.textCursor()
        start = cursor.selectionStart()
        at_paragraph_start = start == self.document().findBlock(start).position()
        for index, line in enumerate(lines):
            if (index > 0 or at_paragraph_start) and not line.startswith("  "):
                lines[index] = "  " + line
        self._batch = True
        try:
            self.insertPlainText("\n".join(lines))
        finally:
            self._batch = False

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (
                event.modifiers() & (Qt.KeyboardModifier.ShiftModifier |
                                     Qt.KeyboardModifier.ControlModifier |
                                     Qt.KeyboardModifier.AltModifier)):
            cursor = self.textCursor()
            cursor.beginEditBlock()
            cursor.insertText("\n  ")
            cursor.endEditBlock()
            self.setTextCursor(cursor)
        else:
            super().keyPressEvent(event)
