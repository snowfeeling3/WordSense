import sqlite3
from datetime import date
from pathlib import Path
from PySide6.QtCore import QTimer, Qt, QDate, QSignalBlocker, QUrl
from PySide6.QtGui import QColor, QAction, QKeySequence, QDesktopServices
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox, QSplitter,
                             QDateEdit, QFileDialog, QToolButton, QMenu, QWidgetAction)
from .editor import WordEditor, COLORS
from .storage import Storage, normalize, write_markdown
from .sidebar import VocabularySidebar
from . import __version__
from .branding import app_icon
from .theme import STYLE, LEVEL_NAMES, configure_window

class MainWindow(QMainWindow):
    def __init__(self, storage=None):
        super().__init__()
        configure_window(self)
        self.setWindowIcon(app_icon())
        self.storage = storage or Storage()
        self.words = self.storage.load_words()
        self.document_date = date.today()
        self.setWindowTitle(f"WordSense {__version__} · {self.document_date.isoformat()}.md")
        self.resize(1120, 760)
        self.setMinimumSize(720, 460)
        self.setStyleSheet(STYLE)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        title = QLabel("WordSense")
        title.setObjectName("title")
        header = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(app_icon().pixmap(38, 38))
        logo.setAccessibleName("WordSense 标志")
        header.addWidget(logo)
        header.addWidget(title)
        header.addStretch()
        self.document_label = QLabel(f"{self.document_date.isoformat()}.md")
        self.document_label.setObjectName("documentTab")
        header.addWidget(self.document_label)
        self.document_menu_button = QToolButton()
        self.document_menu_button.setObjectName("documentMenuButton")
        self.document_menu_button.setText("⋯")
        self.document_menu_button.setFixedSize(36, 36)
        self.document_menu_button.setToolTip("文章菜单：保存、另存为、切换日期")
        self.document_menu_button.setAccessibleName("文章菜单")
        self.document_menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.document_menu = QMenu(self.document_menu_button)
        self.document_menu_button.setMenu(self.document_menu)
        header.addWidget(self.document_menu_button)
        layout.addLayout(header)
        hint = QLabel("Ctrl+L 填写单词 · Enter 跳到词义 · 再按 Enter 保存并返回正文。")
        hint.setObjectName("hint")
        layout.addWidget(hint)
        row = QHBoxLayout()
        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("英文单词")
        self.word_input.setToolTip("Ctrl+L 跳到这里；填写单词后按 Enter 输入中文词义")
        self.word_input.setMaximumWidth(220)
        self.meaning_input = QLineEdit()
        self.meaning_input.setPlaceholderText("中文词义")
        self.level_input = QComboBox()
        for level, label in LEVEL_NAMES.items():
            self.level_input.addItem(label, level)
            self.level_input.setItemData(self.level_input.count() - 1, QColor(COLORS[level]), Qt.ItemDataRole.ForegroundRole)
        button = QPushButton("保存 / 更新")
        for widget in (self.word_input, self.meaning_input, self.level_input, button):
            row.addWidget(widget)
        layout.addLayout(row)
        legend = QLabel()
        legend.setText(' &nbsp; '.join(f'<span style="color:{COLORS[level]}">● {label}</span>'
            for level, label in LEVEL_NAMES.items()) +
            ' &nbsp; <span style="color:#DBBC7F">● 未记录 / 输入中</span>')
        layout.addWidget(legend)
        self.save_action = self.document_menu.addAction("保存 Markdown", self.save_markdown)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.addAction(self.save_action)
        self.export_action = self.document_menu.addAction("另存为…", self.export_markdown)
        self.export_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.addAction(self.export_action)
        self.document_menu.addSeparator()
        date_widget = QWidget()
        date_row = QHBoxLayout(date_widget)
        date_row.setContentsMargins(12, 8, 12, 8)
        date_row.addWidget(QLabel("日期"))
        self.date_input = QDateEdit(QDate(self.document_date.year, self.document_date.month, self.document_date.day))
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setMinimumWidth(156)
        date_row.addWidget(self.date_input)
        date_action = QWidgetAction(self.document_menu)
        date_action.setDefaultWidget(date_widget)
        self.document_menu.addAction(date_action)
        self.document_menu.addAction("返回今天", lambda: self.date_input.setDate(QDate.currentDate()))
        self.document_menu.addSeparator()
        self.document_menu.addAction("打开文档目录", lambda: QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(self.storage.documents_directory))))
        self.document_menu.addAction("设置文档位置…", self.choose_documents_directory)
        self.document_menu.addAction("清理旧文档残留", self.cleanup_old_documents)
        self.document_menu.addSeparator()
        self.document_menu.addAction("打开词库目录", lambda: QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(self.storage.path.parent))))
        self.document_menu.addAction("设置词库位置…", self.choose_database_directory)
        self.document_menu.addAction("清理旧词库残留", self.cleanup_old_database)
        self.editor = WordEditor(self.words)
        self.editor.load_text(self.storage.load_text(self.document_date))
        self.sidebar = VocabularySidebar(self.words)
        self.sidebar.word_selected.connect(self.select_dictionary_word)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.editor)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([260, 800])
        layout.addWidget(splitter, 1)
        self.statusBar().showMessage(f"已加载 {len(self.words)} 个单词 · 文本自动保存")
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(700)
        self.save_timer.timeout.connect(self.save_document)
        self.editor.textChanged.connect(self._schedule_save)
        self.word_input.textChanged.connect(self.lookup_word)
        self.word_input.returnPressed.connect(self.focus_meaning_input)
        self.meaning_input.returnPressed.connect(self.save_word)
        button.clicked.connect(self.save_word)
        self.date_input.dateChanged.connect(self.switch_document)
        for shortcut, callback in (("Ctrl+L", self.focus_word_input),):
            action = QAction(self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)
            self.addAction(action)
        self.editor.setFocus()

    def lookup_word(self, text):
        entry = self.words.get(text.strip().casefold())
        if entry:
            self.meaning_input.setText(entry[0])
            self.level_input.setCurrentIndex(self.level_input.findData(entry[1]))
        else:
            self.meaning_input.clear()
            self.level_input.setCurrentIndex(0)

    def select_dictionary_word(self, word):
        self.word_input.setText(word)
        self.lookup_word(word)

    def focus_word_input(self):
        self.word_input.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.word_input.selectAll()

    def focus_meaning_input(self):
        self.meaning_input.setFocus(Qt.FocusReason.OtherFocusReason)
        self.meaning_input.selectAll()

    def save_word(self):
        try:
            key = normalize(self.word_input.text())
            meaning = self.meaning_input.text().strip()
            level = self.level_input.currentData()
            self.storage.upsert_word(key, meaning, level)
        except (ValueError, OSError, sqlite3.Error) as error:
            QMessageBox.warning(self, "无法保存单词", str(error))
            if isinstance(error, ValueError):
                self.focus_word_input()
            return False
        self.words[key] = (meaning, level)
        self.sidebar.refresh()
        self.editor.highlighter.rehighlight()
        self.statusBar().showMessage(f"已保存 {key} · 词典共 {len(self.words)} 个单词")
        self.editor.setFocus(Qt.FocusReason.OtherFocusReason)
        return True

    def _schedule_save(self):
        self.save_timer.start()

    def save_document(self):
        try:
            self.storage.collect_finished()
            self.storage.save_text(self.editor.toPlainText(), self.document_date)
        except Exception as error:
            self.statusBar().showMessage(f"文本保存失败：{error}")

    def flush_document(self):
        self.save_timer.stop()
        self.storage.collect_finished()
        self.storage.save_text(self.editor.toPlainText(), self.document_date).result()
        self.storage.collect_finished()

    def save_markdown(self):
        try:
            self.flush_document()
        except Exception as error:
            QMessageBox.warning(self, "无法保存 Markdown", str(error))
            return False
        self.statusBar().showMessage(f"已保存：{self.storage.document_path(self.document_date)}")
        return True

    def switch_document(self, selected_date):
        new_date = date(selected_date.year(), selected_date.month(), selected_date.day())
        if new_date == self.document_date:
            return
        try:
            self.flush_document()
            text = self.storage.load_text(new_date)
        except Exception as error:
            with QSignalBlocker(self.date_input):
                old = self.document_date
                self.date_input.setDate(QDate(old.year, old.month, old.day))
            QMessageBox.warning(self, "无法切换文档", str(error))
            return
        self.document_date = new_date
        self.document_label.setText(f"{new_date.isoformat()}.md")
        self.editor.load_text(text)
        self.document_menu.close()
        self.editor.setFocus()
        self.setWindowTitle(f"WordSense {__version__} · {new_date.isoformat()}.md")
        self.statusBar().showMessage(f"已打开 {new_date.isoformat()}.md · 所有文档共用同一个词库")

    def export_markdown(self):
        filename, _ = QFileDialog.getSaveFileName(self, "另存为 Markdown",
            str(self.storage.document_path(self.document_date)), "Markdown 文档 (*.md)")
        if not filename:
            return
        path = Path(filename)
        if path.suffix.casefold() != ".md":
            path = path.with_name(path.name + ".md")
        try:
            self.flush_document()
            write_markdown(path, self.editor.toPlainText())
        except Exception as error:
            QMessageBox.warning(self, "无法导出 Markdown", str(error))
            return
        self.statusBar().showMessage(f"已导出：{path}")

    def choose_documents_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择文档目录（迁移现有 Markdown 并清理旧位置）",
                                                     str(self.storage.documents_directory))
        if not directory:
            return
        try:
            self.flush_document()
            count, leftovers = self.storage.set_documents_directory(directory)
        except Exception as error:
            QMessageBox.warning(self, "无法更换文档位置", str(error))
            return
        self.statusBar().showMessage(f"文档位置：{self.storage.documents_directory} · 已迁移 {count} 篇 · 词库保持统一")
        if leftovers:
            QMessageBox.warning(self, "文档已迁移，部分旧文件未能清理",
                "新位置已保存完整文档。请关闭占用旧文件的程序，再点击“清理旧文档残留”。\n" + '\n'.join(leftovers))

    def cleanup_old_documents(self):
        try:
            leftovers = self.storage.cleanup_old_documents()
        except Exception as error:
            QMessageBox.warning(self, "无法清理旧文档", str(error))
            return
        if leftovers:
            QMessageBox.warning(self, "仍有旧文件需要保留或正在被占用", '\n'.join(leftovers))
        else:
            self.statusBar().showMessage("旧文档残留已清理 · 当前文档和词库保留")

    def choose_database_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择统一词库位置（迁移现有词库）", str(self.storage.path.parent))
        if not directory:
            return
        try:
            self.flush_document()
            leftovers = self.storage.set_database_directory(directory)
        except Exception as error:
            QMessageBox.warning(self, "无法更换词库位置", str(error))
            return
        self.statusBar().showMessage(f"统一词库已迁移：{self.storage.path} · 所有文章继续共用")
        if leftovers:
            QMessageBox.warning(self, "词库已迁移，旧文件暂未清理",
                "请关闭占用旧词库的程序，再点击“清理旧词库残留”。\n" + '\n'.join(leftovers))

    def cleanup_old_database(self):
        try:
            leftovers = self.storage.cleanup_old_database()
        except Exception as error:
            QMessageBox.warning(self, "无法清理旧词库", str(error))
            return
        if leftovers:
            QMessageBox.warning(self, "旧词库仍被占用或已变化", '\n'.join(leftovers))
        else:
            self.statusBar().showMessage("旧词库残留已清理")

    def closeEvent(self, event):
        self.save_timer.stop()
        try:
            self.flush_document()
        except Exception as error:
            QMessageBox.warning(self, "无法保存文本", f"请复制文本备份后再关闭。\n{error}")
            event.ignore()
            return
        self.storage.close()
        event.accept()
