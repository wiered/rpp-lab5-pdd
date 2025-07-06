import os

from dotenv import load_dotenv
from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow,
                               QPushButton, QStackedLayout, QVBoxLayout,
                               QWidget, QToolButton)
from qasync import asyncSlot
from src.qt.widgets import (AdminPanelWidget, LoginPageWidget, MainPageWidget,
                            PersonalPageWidget, TestWidget)
from src.rest_client import AsyncApiClient
from src.qt.styles import STYLESHEET
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize

load_dotenv()

SERVER_PORT = os.getenv('SERVER_PORT')

API_BASE = f"http://127.0.0.1:{SERVER_PORT}/api"

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
qt_dir = os.path.join(base_dir, "qt")
media_dir = os.path.join(qt_dir, "media")
svgs_dir = os.path.join(media_dir, "svgs")

maximize_svg_path = os.path.join(svgs_dir, "maximize.svg").replace("\\", "/")
minimize_svg_path = os.path.join(svgs_dir, "minimize.svg").replace("\\", "/")
collapse_svg_path = os.path.join(svgs_dir, "collapse.svg").replace("\\", "/")
close_svg_path = os.path.join(svgs_dir, "close.svg").replace("\\", "/")

for svg_path in (maximize_svg_path, minimize_svg_path, collapse_svg_path):
    if not os.path.exists(svg_path):
        print(f"SVG-файл не найден: {svg_path}")

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(35)
        self.setStyleSheet(STYLESHEET)

        self._resize_margin = 5
        self._resizing = False
        self._resize_edge = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)

        self.title_label = QLabel("ПДД Учебник")
        self.title_label.setStyleSheet("background-color: transparent; font-size: 16px; font-weight: bold; color: white;")
        layout.addWidget(self.title_label)

        layout.addStretch()

        self.min_btn = QToolButton()
        self.min_btn.setIcon(QIcon(collapse_svg_path))
        self.min_btn.setIconSize(QSize(16, 16))

        self.max_btn = QToolButton()
        self.max_btn.setIcon(QIcon(maximize_svg_path))
        self.max_btn.setIconSize(QSize(16, 16))

        self.close_btn = QToolButton()
        self.close_btn.setIcon(QIcon(close_svg_path))
        self.close_btn.setIconSize(QSize(16, 16))

        for btn in (self.min_btn, self.max_btn, self.close_btn):
            btn.setFixedSize(60, 35)
            btn.setStyleSheet("""
                QToolButton {
                    background-color: transparent;
                    color: white;
                    padding: 0px;
                }
                QToolButton:hover {
                    background-color: rgb(40,40,50);
                    border: 0px;
                }
            """)

        self.close_btn.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                color: white;
                border-radius: 3px;
            }
            QToolButton:hover {
                background-color: rgb(140,40,50);
                border: 0px;
                border-radius: 3px;
            }
        """)

        layout.addWidget(self.min_btn)
        layout.addWidget(self.max_btn)
        layout.addWidget(self.close_btn)

        self._mouse_pos = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.window().windowHandle().startSystemMove()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._resizing and event.buttons() & Qt.LeftButton:
            self._perform_resize(event.globalPos())
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._resizing = False
        event.accept()


class MainWindow(QMainWindow):
    def __init__(self, client: AsyncApiClient):
        super().__init__()
        self.client = client
        self.ROUNDED_STYLE = "QWidget#roundedContainer {border-radius: 3px;}"

        self._resizing = False
        self._resize_edge = None
        self._start_pos = None
        self._start_geom = None
        self._resize_margin = 15

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("PDD Client")
        self.setMinimumHeight(800)
        self.setMinimumWidth(1200)
        self.resize(1200, 800)

        # Кастомный заголовок
        self.title_bar = CustomTitleBar(self)

        # Навешиваем на кнопки тул-бара реальные слоты
        self.title_bar.min_btn.clicked.connect(self.showMinimized)
        self.title_bar.max_btn.clicked.connect(self.toggle_max_restore)
        self.title_bar.close_btn.clicked.connect(self.close)

        # ===== 0) Центральный виджет с QStackedLayout =====
        self.central = QWidget()
        self.central.setObjectName("roundedContainer")
        self.central.setStyleSheet(STYLESHEET + self.ROUNDED_STYLE)
        main_layout = QVBoxLayout(self.central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.central.setLayout(main_layout)
        self.setCentralWidget(self.central)

        main_layout.addWidget(self.title_bar)

        self.stacked = QStackedLayout()
        main_layout.addLayout(self.stacked)

        # ===== 1) СТРАНИЦА ЛОГИНА (index = 0) =====
        self.login_page = LoginPageWidget(self, client)

        # ===== 2) ОСНОВНАЯ СТРАНИЦА (index = 1) =====
        self.main_page_widget = MainPageWidget(self, client)
        self.main_page_widget.personal_btn.clicked.connect(self.on_personal)
        self.main_page_widget.admin_btn.clicked.connect(self.on_admin)

        # ===== 3) АДМИН-ПАНЕЛЬ (index = 2) =====
        self.admin_panel = AdminPanelWidget(self.client)

        # ===== 4) СТРАНИЦА ПЕРСОНАЛЬНЫХ ДАННЫХ (index = 3) =====
        self.personal_page = PersonalPageWidget(self.client)

        # список текущих TestWidget-ов (чтобы потом удалять)
        self.test_pages = []

        # Добавим все страницы в стек
        self.stacked.addWidget(self.login_page)
        self.stacked.addWidget(self.main_page_widget)
        self.stacked.addWidget(self.admin_panel)
        self.stacked.addWidget(self.personal_page)

        # Сразу переключаемся на страницу логина
        self.stacked.setCurrentIndex(0)

    def _detect_edge(self, pos):
        """Возвращает строку с гранью или углом, если курсор близко к краю."""
        x, y, w, h = pos.x(), pos.y(), self.width(), self.height()
        m = self._resize_margin

        left = x <= m
        right = x >= w - m
        top = y <= m
        bottom = y >= h - m

        if left and top:
            return 'top-left'
        if right and top:
            return 'top-right'
        if left and bottom:
            return 'bottom-left'
        if right and bottom:
            return 'bottom-right'
        if left:
            return 'left'
        if right:
            return 'right'
        if top:
            return 'top'
        if bottom:
            return 'bottom'
        return None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            edge = self._detect_edge(event.pos())
            if edge:
                self._resizing = True
                self._resize_edge = edge
                self._start_pos = event.globalPos()
                self._start_geom = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.pos()
        if not self._resizing:
            edge = self._detect_edge(pos)
            cursors = {
                'left': Qt.SizeHorCursor, 'right': Qt.SizeHorCursor,
                'top': Qt.SizeVerCursor, 'bottom': Qt.SizeVerCursor,
                'top-left': Qt.SizeFDiagCursor, 'bottom-right': Qt.SizeFDiagCursor,
                'top-right': Qt.SizeBDiagCursor, 'bottom-left': Qt.SizeBDiagCursor,
            }
            self.setCursor(cursors.get(edge, Qt.ArrowCursor))
        else:
            self._perform_resize(event.globalPos())
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self._resizing:
            self._resizing = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _perform_resize(self, global_pos):
        """Меняем геометрию окна в зависимости от стороны/угла."""
        delta = global_pos - self._start_pos
        geom = self._start_geom

        x, y, w, h = geom.x(), geom.y(), geom.width(), geom.height()
        min_w, min_h = self.minimumWidth(), self.minimumHeight()

        edge = self._resize_edge

        if 'left' in edge:
            new_x = x + delta.x()
            new_w = w - delta.x()
            if new_w >= min_w:
                x, w = new_x, new_w
        elif 'right' in edge:
            new_w = w + delta.x()
            if new_w >= min_w:
                w = new_w

        if 'top' in edge:
            new_y = y + delta.y()
            new_h = h - delta.y()
            if new_h >= min_h:
                y, h = new_y, new_h
        elif 'bottom' in edge:
            new_h = h + delta.y()
            if new_h >= min_h:
                h = new_h

        self.setGeometry(x, y, w, h)

    def toggle_max_restore(self):
        if self.isMaximized():
            self.showNormal()
            self.title_bar.max_btn.setIcon(QIcon(maximize_svg_path))
            self.central.setStyleSheet(STYLESHEET + self.ROUNDED_STYLE)
        else:
            self.showMaximized()
            self.title_bar.max_btn.setIcon(QIcon(minimize_svg_path))
            self.central.setStyleSheet(STYLESHEET)

    # ===== МЕТОДЫ ОСНОВНОГО ОКНА =====
    @asyncSlot()
    async def on_personal(self):
        # Переключаемся на страницу PersonalPage
        self.stacked.setCurrentWidget(self.personal_page)

        # Запускаем асинхронную загрузку данных
        QTimer.singleShot(0, lambda: self.personal_page.load_data())

    @asyncSlot(object)
    async def on_admin(self):
        """
        Вызывается при клике на кнопку "Admin Panel" в главном экране.
        Просто переключаемся на виджет AdminPanel и запускаем загрузку данных.
        """
        # Переключаемся на страницу с админ‐панелью
        self.stacked.setCurrentWidget(self.admin_panel)
        # Запускаем начальную загрузку данных (категории, пользователи, тесты и т.д.)
        await self.admin_panel.load_all()

    def on_test(self, test_id: int):
        test_window = TestWidget(self.client, test_id, self)
        # Добавляем в stacked как новую страницу
        self.stacked.addWidget(test_window)
        self.test_pages.append(test_window)
        # Инициируем асинхронную загрузку данных теста
        QTimer.singleShot(0, test_window.load_test)
        # Переключаемся на страницу с тестом (последний индекс в стеке)
        self.stacked.setCurrentWidget(test_window)

    def remove_test_page(self, test_window: TestWidget):
        """
        Удаляем данную страницу TestWidget из stacked и списка test_pages.
        Вызывается после того, как тест был отправлен.
        """
        if test_window in self.test_pages:
            idx = self.stacked.indexOf(test_window)
            if idx != -1:
                widget = self.stacked.widget(idx)
                # Прежде чем удалять виджет, делаем его невидимым
                self.stacked.removeWidget(widget)
                widget.deleteLater()
            self.test_pages.remove(test_window)
