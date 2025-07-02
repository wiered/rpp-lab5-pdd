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
from src.qt.widgets import AdminPanelWidget, PersonalPageWidget, TestWidget
from src.rest_client import AsyncApiClient

class LoginPageWidget(QWidget):
    def __init__(self):
        super().__init__()
        outer_layout = QVBoxLayout()
        self.setLayout(outer_layout)

        # Верхний spacer
        outer_layout.addStretch(1)

        # Внутренний контейнер фиксированного размера
        login_container = QWidget()
        login_container.setFixedSize(320, 240)
        login_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # Собственно форма логина
        inner_layout = QVBoxLayout()
        login_container.setLayout(inner_layout)

        # ===== Большие поля и кнопки =====
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        self.user_input.setFixedHeight(30)

        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setFixedHeight(30)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedHeight(30)

        self.login_btn = QPushButton("Login")
        self.login_btn.setFixedHeight(30)

        self.reg_btn = QPushButton("Register")
        self.reg_btn.setFixedHeight(30)
        # =================================

        # Наполняем inner_layout
        inner_layout.addStretch(1)
        inner_layout.addWidget(self.user_input)
        inner_layout.addWidget(self.pass_input)

        # ===== Новый горизонтальный layout для двух кнопок =====
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.login_btn)
        btn_layout.addWidget(self.reg_btn)
        btn_layout.setSpacing(20)
        inner_layout.addLayout(btn_layout)
        # ===========================================================

        inner_layout.addWidget(self.status_label)
        inner_layout.addStretch(1)
        inner_layout.setSpacing(12)
        inner_layout.setContentsMargins(20, 10, 20, 10)

        # Центрирование login_container по горизонтали
        h_center_layout = QHBoxLayout()
        h_center_layout.addStretch(1)
        h_center_layout.addWidget(login_container)
        h_center_layout.addStretch(1)
        outer_layout.addLayout(h_center_layout)

        # Нижний spacer
        outer_layout.addStretch(1)