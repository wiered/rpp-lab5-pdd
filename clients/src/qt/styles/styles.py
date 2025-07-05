# проверим, что файл done.svg там есть
import os

from PySide6.QtCore import QUrl

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
media_dir = os.path.join(base_dir, "media")

done_svg_path = os.path.join(media_dir, "done.svg").replace("\\", "/")
if not os.path.exists(done_svg_path):
    # Если SVG-файла нет, можно сразу предупредить:
    print(f"Warning: не найден файл галочки: {done_svg_path}")

STYLESHEET = '''
* {
    background-color: rgba(30, 30, 40, 1);
    font-size: 16px;
}

QLineEdit {
    color: rgba(200, 200, 200, 1);
}

QPlainTextEdit, QListView, QListWidget, QLineEdit, QTextBrowser {
    background-color: rgba(50, 50, 70, 1);
    color: rgba(200, 200, 200, 1);
    border: 0px solid rgba(255, 255, 255, 0.3);
    border-radius: 3px;
}

QPlainTextEdit, QTextBrowser {
    padding: 10px;
}

QPushButton {
    background-color: #6464A0;
    border: 0px solid rgba(255, 255, 255, 0.3);
    border-radius: 3px;
    color: white;
}
QPushButton:pressed  {
    background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                      stop: 0 #dadbde, stop: 1 #f6f7fa);
}

QFrame {
    border: 1px;
    border-radius: 3px;
    background-color: rgba(50, 50, 70, 1);
}

QLabel {
    background-color: rgba(50, 50, 70, 1);
    border-radius: 3px;
    color: rgba(200, 200, 200, 1);
}

QCheckBox {
    border: 0px solid;
    background-color: rgba(50, 50, 70, 0);
    border-radius: 3px;
    color: rgba(200, 200, 200, 1);
}
QCheckBox::indicator {
    width: 13px;
    height: 13px;
}
QCheckBox::indicator:unchecked {
    background-color: rgba(50, 50, 70, 0);
    border-radius: 3px;
    border: 1px solid rgba(30, 30, 40, 1);
}
QCheckBox::indicator:checked {
    background-color: #6464A0;
    border-radius: 3px;
    border: 1px solid rgba(30, 30, 40, 1);
    image: url("'''+ done_svg_path +'''");
}

/* Scroll Bars */

QAbstractScrollArea {
        padding: 5px 6px 5px 5px;
        border-radius: 5px;
}

/* Vertical */

QScrollBar::vertical {
    border: 0px solid rgba(50, 50, 70, 1);
    background: rgba(30, 30, 40, 1);
    width: 10px;
        border-radius: 3px;
}

QScrollBar::handle:vertical {
    background: #6464A0;
    border-radius: 2px;
    min-height: 0px;
}

QScrollBar::add-line:vertical {
    border: 0px solid grey;
    background: rgba(50, 50, 70, 1);
    height: 0px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
}

QScrollBar::sub-line:vertical {
    border: 0px solid grey;
    background: rgba(50, 50, 70, 1);
    height: 0px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}
QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
    border: 0px solid grey;
    width: 0px;
    height: 0px;
    background: rgba(50, 50, 70, 1);
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* Horizontal */

QScrollBar::horizontal {
    border: 0px solid rgba(50, 50, 70, 1);
    background: rgba(30, 30, 40, 1);
    height: 10px;
    border-radius: 3px;
}

QScrollBar::handle:horizontal {
    background: #6464A0;
    border-radius: 2px;
    min-width: 0px;
}

QScrollBar::add-line:horizontal {
    border: 0px solid grey;
    background: rgba(50, 50, 70, 1);
    width: 0px;
    subcontrol-position: right;
    subcontrol-origin: margin;
}

QScrollBar::sub-line:horizontal {
    border: 0px solid grey;
    background: rgba(50, 50, 70, 1);
    width: 0px;
    subcontrol-position: left;
    subcontrol-origin: margin;
}

QScrollBar::left-arrow:horizontal,
QScrollBar::right-arrow:horizontal {
    border: 0px solid grey;
    width: 0px;
    height: 0px;
    background: rgba(50, 50, 70, 1);
}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {
    background: none;
}

/* QTabWidget и QTabBar */
QTabWidget::pane {
    border: 0px;
    background: rgba(50, 50, 70, 1);
}

QTabBar::tab {
    background: rgba(50, 50, 70, 1);
    color: rgba(200, 200, 200, 1);
    padding: 8px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-bottom: none;
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background: rgba(30, 30, 40, 1);
}

QTabBar::tab:hover {
    background: rgba(80, 80, 100, 1);
}

QTabBar::tab:!selected {
    margin-top: 2px;
}

/* QComboBox */
QComboBox {
    background-color: rgba(50, 50, 70, 1);
    color: rgba(200, 200, 200, 1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 3px;
    padding: 3px 5px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
    border-left: 0px;
}

QComboBox::down-arrow {
    image: none;
    width: 7px;
    height: 7px;
}

QComboBox QAbstractItemView {
    background-color: rgba(50, 50, 70, 1);
    selection-background-color: #6464A0;
    color: rgba(200, 200, 200, 1);
    border: none;
}

/* QSpinBox */
QSpinBox {
    background-color: rgba(50, 50, 70, 1);
    color: rgba(200, 200, 200, 1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 3px;
    padding: 3px;
}

QSpinBox::up-button, QSpinBox::down-button {
    width: 16px;
    background: rgba(50, 50, 70, 1);
}

QSpinBox::up-arrow, QSpinBox::down-arrow {
    width: 7px;
    height: 7px;
    image: none;
}

/* QGroupBox */
QGroupBox {
    background-color: rgba(50, 50, 70, 1);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 3px;
    margin-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px;
    color: rgba(200, 200, 200, 1);
}

/* QRadioButton */
QRadioButton {
    color: rgba(200, 200, 200, 1);
    spacing: 5px;
    background-color: rgba(50, 50, 70, 0);
}

QRadioButton::indicator {
    width: 13px;
    height: 13px;
    border-radius: 6px;
    border: 1px solid rgba(200, 200, 200, 0.8);
    background-color: rgba(50, 50, 70, 0);
}

QRadioButton::indicator:checked {
    background-color: #6464A0;
    border: 1px solid rgba(200, 200, 200, 0.8);
}

'''