import asyncio
import os
import sys
from functools import partial

import markdown
from dotenv import load_dotenv
from PySide6.QtCore import QSize, Qt, QTimer, Slot
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QButtonGroup, QDialog, QFrame,
                               QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMainWindow,
                               QMessageBox, QPushButton, QRadioButton,
                               QScrollArea, QSizePolicy, QStackedLayout,
                               QTextBrowser, QVBoxLayout, QWidget)
from qasync import QEventLoop, asyncSlot
from src.qt.styles import STYLESHEET
from src.qt.widgets import (AdminPanelWidget, LoginPageWidget,
                            PersonalPageWidget, TestWidget, MainPageWidget)
from src.rest_client import AsyncApiClient

load_dotenv()

SERVER_PORT = os.getenv('SERVER_PORT')

API_BASE = f"http://127.0.0.1:{SERVER_PORT}/api"


class MainWindow(QMainWindow):
    def __init__(self, client: AsyncApiClient):
        super().__init__()
        self.client = client

        self.setWindowTitle("PDD Client")
        self.resize(1200, 800)

        # Центральный виджет с QStackedLayout
        central = QWidget()
        self.stacked = QStackedLayout()
        central.setLayout(self.stacked)
        self.setCentralWidget(central)

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

    # ===== МЕТОДЫ ОСНОВНОГО ОКНА =====
    @asyncSlot()
    async def on_personal(self):
        # Переключаемся на страницу PersonalPage
        self.parent.stacked.setCurrentWidget(self.parent.personal_page)

        # Запускаем асинхронную загрузку данных
        QTimer.singleShot(0, lambda: self.personal_page.load_data())

    @asyncSlot(object)
    def on_admin(self):
        """
        Вызывается при клике на кнопку "Admin Panel" в главном экране.
        Просто переключаемся на виджет AdminPanel и запускаем загрузку данных.
        """
        # Переключаемся на страницу с админ‐панелью
        self.stacked.setCurrentWidget(self.admin_panel)
        # Запускаем начальную загрузку данных (категории, пользователи, тесты и т.д.)
        QTimer.singleShot(0, self.admin_panel.load_all)

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
