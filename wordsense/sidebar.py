"""Search the in-memory vocabulary and select entries for editing."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem
from .editor import COLORS

class VocabularySidebar(QWidget):
    word_selected = Signal(str)

    def __init__(self, words, parent=None):
        super().__init__(parent)
        self.words = words
        self.setMinimumWidth(190)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        title = QLabel("我的词典")
        title.setObjectName("sidebarTitle")
        layout.addWidget(title)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索单词 / 中文词义")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setAccessibleName("检索已记录单词")
        layout.addWidget(self.search_input)
        self.result_label = QLabel()
        self.result_label.setObjectName("hint")
        layout.addWidget(self.result_label)
        self.word_list = QListWidget()
        self.word_list.setAccessibleName("已记录单词列表")
        self.word_list.setWordWrap(True)
        layout.addWidget(self.word_list, 1)
        hint = QLabel("选择单词，在上方编辑并保存")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.word_list.currentItemChanged.connect(self._select_word)
        self.search_input.textChanged.connect(self.filter_words)
        self.refresh()

    def _select_word(self, current, previous):
        if current is not None:
            self.word_selected.emit(current.data(Qt.ItemDataRole.UserRole))

    def refresh(self):
        current = self.word_list.currentItem()
        selected = current.data(Qt.ItemDataRole.UserRole) if current else None
        self.word_list.blockSignals(True)
        try:
            self.word_list.clear()
            for word, (meaning, level) in sorted(self.words.items()):
                detail = meaning or "未填写词义"
                item = QListWidgetItem(f"{word}\n{detail}")
                item.setData(Qt.ItemDataRole.UserRole, word)
                item.setForeground(QColor(COLORS[level]))
                item.setToolTip(f"{word}\n{detail}")
                self.word_list.addItem(item)
                if word == selected:
                    self.word_list.setCurrentItem(item)
            self.filter_words()
        finally:
            self.word_list.blockSignals(False)

    def filter_words(self, text=None):
        query = self.search_input.text().strip().casefold()
        visible = 0
        for index in range(self.word_list.count()):
            item = self.word_list.item(index)
            word = item.data(Qt.ItemDataRole.UserRole)
            meaning = self.words[word][0]
            matched = query in word or query in meaning.casefold()
            item.setHidden(not matched)
            visible += matched
        if not self.words:
            self.result_label.setText("词典为空，请在上方添加单词")
        elif not visible:
            self.result_label.setText(f"没有匹配结果 · 共 {len(self.words)} 个单词")
        else:
            self.result_label.setText(f"显示 {visible} / {len(self.words)} 个单词")
