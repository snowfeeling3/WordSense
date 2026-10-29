"""Ink Slate interface with Everforest-inspired vocabulary colors."""
GREEN = "#A7C080"
BLUE = "#7FBBB3"
RED = "#E67E80"
YELLOW = "#DBBC7F"
FOREGROUND = "#E0E7EF"
LEVEL_NAMES = {3: "完全理解", 2: "有点模糊", 0: "完全不懂"}


def configure_window(window):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QPalette, QColor
    app = QApplication.instance()
    if app is not None and app.style().objectName().casefold() != "fusion":
        app.setStyle("Fusion")
    palette = QPalette()
    for role, color in ((QPalette.ColorRole.Window, "#202936"),
                        (QPalette.ColorRole.WindowText, FOREGROUND),
                        (QPalette.ColorRole.Base, "#263241"),
                        (QPalette.ColorRole.AlternateBase, "#303F50"),
                        (QPalette.ColorRole.Text, FOREGROUND),
                        (QPalette.ColorRole.Button, "#303F50"),
                        (QPalette.ColorRole.ButtonText, GREEN),
                        (QPalette.ColorRole.ToolTipBase, "#41546A"),
                        (QPalette.ColorRole.ToolTipText, FOREGROUND),
                        (QPalette.ColorRole.Highlight, "#405676"),
                        (QPalette.ColorRole.HighlightedText, FOREGROUND),
                        (QPalette.ColorRole.PlaceholderText, "#B2BFCE")):
        palette.setColor(role, QColor(color))
    window.setPalette(palette)

STYLE = """
QWidget { background: #202936; color: #E0E7EF; font-family: 'Segoe UI', 'Microsoft YaHei UI'; font-size: 14px; }
QLabel#title { font-size: 26px; font-weight: 600; color: #A7C080; }
QLabel#hint { color: #B2BFCE; font-size: 13px; }
QLabel#sidebarTitle { color: #E0E7EF; font-size: 16px; font-weight: 600; }
QLabel#documentTab { color: #E0E7EF; background: #263241; border-radius: 6px; padding: 8px 12px; }
QToolButton#documentMenuButton { background: #263241; color: #E0E7EF;
    border: 1px solid #41546A; border-radius: 10px; padding: 0; font-size: 14px; }
QToolButton#documentMenuButton:hover { background: #303F50; border-color: #A7C080; }
QToolButton#documentMenuButton::menu-indicator { image: none; width: 0; }
QMenu { background: #41546A; border: 1px solid #60758B; padding: 6px; }
QMenu QWidget { background: #41546A; }
QMenu::item { padding: 9px 16px; border-radius: 4px; }
QMenu::item:selected { background: #354F52; }
QMenu::separator { height: 1px; background: #60758B; margin: 5px 8px; }
QListWidget { background: #263241; border: 1px solid #41546A; border-radius: 8px;
    padding: 4px; outline: none; }
QListWidget::item { padding: 10px 8px; border-radius: 4px; }
QListWidget::item:selected { background: #354F52; }
QListWidget::item:hover { background: #303F50; }
QSplitter::handle { background: #202936; width: 12px; }
QLineEdit, QComboBox, QDateEdit { background: #303F50; border: 1px solid #52677F;
    border-radius: 6px; padding: 8px; selection-background-color: #405676;
    selection-color: #E0E7EF; }
QLineEdit:focus, QComboBox:focus, QDateEdit:focus { border-color: #A7C080; }
QComboBox QAbstractItemView { background: #41546A; color: #E0E7EF;
    selection-background-color: #354F52; selection-color: #E0E7EF; }
QPushButton { background: #303F50; color: #A7C080; border: 1px solid #52677F;
    border-radius: 6px; padding: 9px 15px; font-weight: 500; }
QPushButton:hover { background: #354F52; border-color: #A7C080; }
QPushButton:pressed { background: #41546A; }
QTextEdit { background: #263241; color: #DBBC7F; border: 1px solid #41546A;
    border-radius: 8px; padding: 18px; font-family: 'Cascadia Code', Consolas; font-size: 19px;
    selection-background-color: #405676; selection-color: #E0E7EF; }
QScrollBar:vertical { background: #263241; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #60758B; min-height: 24px; border-radius: 5px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
"""

STYLE += """
QLabel#fieldLabel { color: #B2BFCE; font-size: 13px; }
QPushButton#saveWordButton { background: #A7C080; color: #202936; border-color: #A7C080; font-weight: 600; }
QPushButton#saveWordButton:hover { background: #BCD29A; }
QPushButton#saveWordButton:pressed { background: #90AC69; }
QPushButton:focus, QToolButton:focus, QListWidget:focus, QTextEdit:focus { border: 2px solid #A7C080; }
QStatusBar { color: #B2BFCE; border-top: 1px solid #41546A; padding: 5px 12px; }
QToolTip { background: #303F50; color: #E0E7EF; border: 1px solid #60758B; padding: 6px; }
QWidget:disabled { color: #8E9CAD; }
"""
