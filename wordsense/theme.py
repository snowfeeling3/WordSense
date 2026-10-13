"""Everforest Dark Soft palette, based on the upstream sainnhe/everforest theme."""
GREEN = "#A7C080"
BLUE = "#7FBBB3"
RED = "#E67E80"
YELLOW = "#DBBC7F"
FOREGROUND = "#D3C6AA"
LEVEL_NAMES = {3: "完全理解", 2: "有点模糊", 0: "完全不懂"}


def configure_window(window):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPalette, QColor
    app = QApplication.instance()
    if app is not None and app.style().objectName().casefold() != "fusion":
        app.setStyle("Fusion")
    palette = QPalette()
    for role, color in ((QPalette.ColorRole.Window, "#293136"),
                        (QPalette.ColorRole.WindowText, FOREGROUND),
                        (QPalette.ColorRole.Base, "#333C43"),
                        (QPalette.ColorRole.AlternateBase, "#3A464C"),
                        (QPalette.ColorRole.Text, FOREGROUND),
                        (QPalette.ColorRole.Button, "#3A464C"),
                        (QPalette.ColorRole.ButtonText, GREEN),
                        (QPalette.ColorRole.ToolTipBase, "#434F55"),
                        (QPalette.ColorRole.ToolTipText, FOREGROUND),
                        (QPalette.ColorRole.Highlight, "#5C3F4F"),
                        (QPalette.ColorRole.HighlightedText, FOREGROUND),
                        (QPalette.ColorRole.PlaceholderText, "#9DA9A0")):
        palette.setColor(role, QColor(color))
    window.setPalette(palette)

STYLE = """
QWidget { background: #293136; color: #D3C6AA; font-family: 'Segoe UI'; font-size: 14px; }
QLabel#title { font-size: 24px; font-weight: 600; color: #A7C080; }
QLabel#hint { color: #9DA9A0; font-size: 12px; }
QLabel#sidebarTitle { color: #D3C6AA; font-size: 16px; font-weight: 600; }
QLabel#documentTab { color: #D3C6AA; background: #333C43; border-radius: 6px; padding: 8px 12px; }
QToolButton#documentMenuButton { background: #333C43; color: #D3C6AA;
    border: 1px solid #434F55; border-radius: 18px; padding: 0; font-size: 22px; }
QToolButton#documentMenuButton:hover { background: #3A464C; border-color: #859289; }
QToolButton#documentMenuButton::menu-indicator { image: none; width: 0; }
QMenu { background: #434F55; border: 1px solid #555F66; padding: 6px; }
QMenu QWidget { background: #434F55; }
QMenu::item { padding: 9px 16px; border-radius: 4px; }
QMenu::item:selected { background: #48584E; }
QMenu::separator { height: 1px; background: #555F66; margin: 5px 8px; }
QListWidget { background: #333C43; border: 1px solid #434F55; border-radius: 8px;
    padding: 4px; outline: none; }
QListWidget::item { padding: 10px 8px; border-radius: 4px; }
QListWidget::item:selected { background: #48584E; }
QListWidget::item:hover { background: #3A464C; }
QSplitter::handle { background: #293136; width: 12px; }
QLineEdit, QComboBox, QDateEdit { background: #3A464C; border: 1px solid #4D5960;
    border-radius: 6px; padding: 8px; selection-background-color: #5C3F4F;
    selection-color: #D3C6AA; }
QLineEdit:focus, QComboBox:focus, QDateEdit:focus { border-color: #859289; }
QComboBox QAbstractItemView { background: #434F55; color: #D3C6AA;
    selection-background-color: #48584E; selection-color: #D3C6AA; }
QPushButton { background: #3A464C; color: #A7C080; border: 1px solid #4D5960;
    border-radius: 6px; padding: 9px 15px; font-weight: 500; }
QPushButton:hover { background: #48584E; border-color: #859289; }
QPushButton:pressed { background: #434F55; }
QTextEdit { background: #333C43; color: #DBBC7F; border: 1px solid #434F55;
    border-radius: 8px; padding: 18px; font-family: Consolas; font-size: 18px;
    selection-background-color: #5C3F4F; selection-color: #D3C6AA; }
QScrollBar:vertical { background: #333C43; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #555F66; min-height: 24px; border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
"""
