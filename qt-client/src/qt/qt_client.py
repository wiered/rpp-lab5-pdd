import asyncio
import os
import sys
from functools import partial

import markdown
from PySide6.QtCore import QSize, Qt, QTimer, Slot
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QButtonGroup, QDialog, QFrame,
                               QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QListWidget, QListWidgetItem, QMainWindow,
                               QMessageBox, QPushButton, QRadioButton,
                               QScrollArea, QSizePolicy, QStackedLayout,
                               QTextBrowser, QVBoxLayout, QWidget)
from qasync import QEventLoop, asyncSlot
from src.rest_client import AsyncApiClient
from src.qt.adminpanel import AdminPanel
from src.qt.personalpage import PersonalPage

base_dir = os.path.abspath(os.path.dirname(__file__))
media_dir = os.path.join(base_dir, "media")

# проверим, что файл done.svg там есть
done_svg_path = os.path.join(media_dir, "done.svg")
if not os.path.exists(done_svg_path):
    # Если SVG-файла нет, можно сразу предупредить:
    print(f"Warning: не найден файл галочки: {done_svg_path}")
# Приведём путь к Unix-формату, чтобы Qt корректно его понял:
done_svg_url = done_svg_path.replace("\\", "/")  # на Windows заменим слэши

# Global styling
STYLESHEET = '''
* {
    background-color: rgba(30, 30, 40, 1);
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
    image: url("file:///''' + done_svg_url + '''");
}


QAbstractScrollArea {
        padding: 5px 6px 5px 0;
        border-radius: 5px;
}

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

API_BASE = "http://127.0.0.1:8082/api"

class TestWindow(QWidget):
    """
    Окно для прохождения одного теста. Будет добавляться в QStackedLayout в MainWindow
    как новая страница. Когда пользователь нажмёт «Отправить», расчитаем score,
    отправим POST /test-results/ и вернёмся обратно в MainWindow.
    """

    def __init__(self, client: AsyncApiClient, test_id: int, parent_window: 'MainWindow'):
        super().__init__()
        self.client = client
        self.test_id = test_id
        self.parent_window = parent_window  # чтобы после завершения перейти обратно
        self.questions = []       # список вопросов с вложенными опциями
        self.option_buttons = {}  # словарь question_id -> QButtonGroup
        self.max_score = 0

        # === Основной вертикальный layout: ===
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)  # убираем дополнительные промежутки, чтобы прокрутка и кнопка смыкались

        # 1) Область прокрутки для вопросов:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll, 1)  # растягиваем на всё доступное пространство

        # Внутри scroll – контейнер с вертикальным layout'ом
        container = QWidget()
        self.vbox = QVBoxLayout(container)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.vbox.setSpacing(10)
        scroll.setWidget(container)

        # 2) Ниже – отдельный контейнер для кнопки «Отправить»:
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 10, 0, 0)  # небольшой отступ сверху
        btn_layout.addStretch(1)

        # Кнопка «Отправить»:
        self.submit_btn = QPushButton("Отправить результаты теста")
        self.submit_btn.setEnabled(False)  # станет активной после загрузки вопросов

        # Устанавливаем фиксированную высоту, чтобы кнопка была «выше»
        self.submit_btn.setMinimumHeight(40)
        self.submit_btn.setMaximumHeight(40)
        # Ограничиваем максимальную ширину (по желанию); убрать или скорректировать под дизайн:
        self.submit_btn.setMaximumWidth(300)

        # Присоединяем слот (asyncSlot из qasync)
        self.submit_btn.clicked.connect(self.on_submit)

        # Центрируем кнопку в горизонтальном layout
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addStretch(1)

        # Добавляем контейнер с кнопкой в основной layout:
        main_layout.addWidget(btn_container, 0)

    @asyncSlot()
    async def load_test(self):
        """
        Асинхронно вызывается сразу после создания TestWindow.
        Запрашивает GET /tests/full/{test_id}, парсит вопросы и варианты,
        динамически создаёт виджеты внутри self.vbox.
        """
        try:
            test_data = await self.client.get_test_full(self.test_id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить тест: {e}")
            self.parent_window.stacked.setCurrentIndex(1)
            return

        # Сохраняем вопросы и вычисляем max_score
        self.questions = test_data.get("questions", [])
        self.max_score = sum(q["weight"] for q in self.questions)

        # 1) Заголовок теста
        title_lbl = QLabel(f"Тест: {test_data['title']}")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: rgba(200, 200, 200, 1);
            background-color: rgba(50, 50, 70, 1);
            border-radius: 3px;
            padding: 6px;
            margin-bottom: 15px;
        """)
        self.vbox.addWidget(title_lbl)

        # 2) Вопросы и варианты
        for idx, q in enumerate(self.questions, start=1):
            # Создаём QGroupBox для каждого вопроса
            qbox = QGroupBox(f"{idx}. {q['text']} (вес: {q['weight']})")
            # Здесь задаём фон и скругление, чтобы совпадало с полями категорий/медиа (#323246)
            qbox.setStyleSheet("""
                QGroupBox {
                    background-color: #323246;
                    border-radius: 3px;
                    color: rgba(200, 200, 200, 1);
                    margin: 5px 0px;
                    padding: 8px;
                }
            """)
            q_layout = QVBoxLayout(qbox)
            q_layout.setContentsMargins(8, 8, 8, 8)
            q_layout.setSpacing(6)

            # Группа радиокнопок для вариантов
            button_group = QButtonGroup(qbox)
            self.option_buttons[q["id"]] = button_group

            for opt in q["options"]:
                rb = QRadioButton(opt["text"])
                # Прозрачный фон у радиокнопки, чтобы через неё был виден фон QGroupBox
                rb.setStyleSheet("""
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
                """)
                rb.setProperty("option_id", opt["id"])
                button_group.addButton(rb, opt["id"])
                q_layout.addWidget(rb)

            self.vbox.addWidget(qbox)

        # Вставляем «гибкий» отступ, чтобы вопросник занял всё место,
        # а кнопка осталась прижатой к низу
        self.vbox.addStretch(1)

        # Активируем кнопку «Отправить»
        self.submit_btn.setEnabled(True)

    @asyncSlot()
    async def on_submit(self):
        """
        Собираем ответы пользователя, вычисляем score, формируем тело для POST /test-results/,
        отправляем на сервер и возвращаемся к главной странице.
        """
        # Проверяем, что на каждый вопрос выбран хотя бы один вариант
        answers = []
        for q in self.questions:
            qid = q["id"]
            group: QButtonGroup = self.option_buttons.get(qid)
            checked_id = group.checkedId()  # id выбранной опции или -1, если не выбрано
            if checked_id == -1:
                QMessageBox.warning(
                    self,
                    "Не все вопросы отвечены",
                    "Пожалуйста, выберите вариант ответа для каждого вопроса."
                )
                return
            answers.append({
                "question_id": qid,
                "selected_option_id": checked_id
            })

        # Вычисляем score: суммируем вес тех вопросов, где выбранная опция была правильной
        score = 0.0
        for q in self.questions:
            qid = q["id"]
            weight = q["weight"]
            selected_option_id = next(
                ans["selected_option_id"]
                for ans in answers
                if ans["question_id"] == qid
            )
            # Ищем полный объект выбранной опции внутри q["options"]
            for opt in q["options"]:
                if opt["id"] == selected_option_id and opt["is_correct"]:
                    score += weight
                    break

        # Определяем, прошёл ли пользователь тест:
        passed = (score >= self.max_score)

        # Асинхронно получаем текущего пользователя, чтобы взять user_id
        try:
            current = await self.parent_window.client.me()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить данные пользователя: {e}")
            return

        user_id = current.get("id")
        if user_id is None:
            QMessageBox.critical(self, "Ошибка", "Не удалось определить user_id.")
            return

        body = {
            "user_id": user_id,
            "test_id": self.test_id,
            "score": score,
            "max_score": self.max_score,
            "passed": passed,
            "answers": answers
        }

        # Отправляем результаты теста
        await self.send_result(body)

    async def send_result(self, body: dict):
        try:
            await self.client.create_test_result(**body)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось отправить результаты теста: {e}")
            return



        # Успешно отправили – показываем сообщение и возвращаемся к списку категорий/статей
        QMessageBox.information(self, "Готово", "Результаты теста успешно отправлены.")
        # Возвращаемся к главной странице (index = 1 у QStackedLayout)
        self.parent_window.stacked.setCurrentIndex(1)
        # И удаляем это окно из стека, чтобы при повторном прохождении теста не дублировалось
        self.parent_window.remove_test_page(self)

        if body["passed"]:
            try:
                test_id = body["test_id"]
                test = await self.client.get_test(test_id)
                category_id = test["category_id"]
                category = await self.client.get_category(category_id)
                articles = await self.client.list_articles_by_category(category_id)
                user_id = body["user_id"]
                for article in articles:
                    await self.client.update_progress(
                        user_id=user_id,
                        article_id=article["id"],
                        status="done"
                    )
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось отправить результаты теста: {e}")
                return


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
        login_page = QWidget()
        outer_layout = QVBoxLayout()
        login_page.setLayout(outer_layout)

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
        # Опционально: можно добавить отступы между кнопками
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

        # Подключаем асинхронные слоты для логина/регистрации
        self.login_btn.clicked.connect(self.on_login_clicked)
        self.reg_btn.clicked.connect(self.on_register_clicked)

        self.stacked.addWidget(login_page)  # это будет index=0

        # ===== 2) ОСНОВНАЯ СТРАНИЦА (index = 1) =====
        main_page = QWidget()
        main_layout = QHBoxLayout()
        main_page.setLayout(main_layout)

        # Левая панель — увеличиваем минимальную ширину списка
        left = QVBoxLayout()
        self.category_label = QLabel("Корневые категории")
        self.category_label.setAlignment(Qt.AlignCenter)
        self.category_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        left.addWidget(self.category_label)

        self.back_btn = QPushButton("Back")
        self.back_btn.setEnabled(False)
        self.back_btn.setFixedHeight(40)
        left.addWidget(self.back_btn)

        self.list_widget = QListWidget()
        self.list_widget.setMinimumWidth(300)
        self.list_widget.setStyleSheet("font-size: 14px;")
        left.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.personal_btn = QPushButton("Personal Page")
        self.personal_btn.setFixedHeight(40)
        self.admin_btn = QPushButton("Admin Panel")
        self.admin_btn.setFixedHeight(40)
        btn_layout.addWidget(self.personal_btn)
        btn_layout.addWidget(self.admin_btn)
        left.addLayout(btn_layout)

        # Правая панель — добавляем заголовок статьи и убираем метку "Media:"
        right = QVBoxLayout()

        # Название статьи (или заглушка, если не выбрана)
        self.title_label = QLabel("Программа ПДД учебник")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        right.addWidget(self.title_label)

        # Сам контент статьи (или описание программы, пока не выбран артикль)
        self.article_view = QTextBrowser()
        self.article_view.setStyleSheet("background-color: #1e1e28; font-size: 14px;")
        self.article_view.setMinimumHeight(400)
        # Устанавливаем начальное описание программы вместо статьи
        self.article_view.setHtml(
            "<p style='color: white; font-size:14px;'>"
            "Добро пожаловать в приложение «ПДД учебник». "
            "Здесь вы можете просматривать категории, выбирать статьи по правилам дорожного движения "
            "и смотреть связанные материалы. Выберите категорию слева, чтобы начать."
            "</p>"
        )
        right.addWidget(self.article_view, 3)

        # Поле с картинками (медиа)
        self.media_area = QListWidget()
        self.media_area.setViewMode(QListWidget.IconMode)
        self.media_area.setIconSize(QSize(700, 700))
        self.media_area.setMinimumHeight(200)
        right.addWidget(self.media_area, 2)

        main_layout.addLayout(left, 2)
        main_layout.addLayout(right, 5)

        # Переменные для работы с историей
        self.history = []
        self.current_id = None

        # Сигналы основной страницы
        self.back_btn.clicked.connect(self.on_back)
        self.list_widget.itemClicked.connect(self.on_item)
        self.personal_btn.clicked.connect(self.on_personal)
        self.admin_btn.clicked.connect(self.on_admin)

        # Применяем стили
        self.list_widget.setStyleSheet(STYLESHEET)
        self.media_area.setStyleSheet(STYLESHEET)

        self.stacked.addWidget(main_page)  # это будет index=1
        self.test_pages = []  # список текущих TestWindow-ов (чтобы потом удалять)

         # === Админ-панель (index = 2) ===
        self.admin_panel = AdminPanel(self.client)
        self.stacked.addWidget(self.admin_panel)

        # Указываем, что personal_page будет создаваться при первом же нажатии
        self.personal_page = None

        # Сразу переключаемся на страницу логина
        self.stacked.setCurrentIndex(0)

    # ===== АСИНХРОННЫЕ СЛОТЫ ДЛЯ ЛОГИНА/РЕГИСТРАЦИИ =====
    @asyncSlot()
    async def on_login_clicked(self):
        """
        Этот слот вызывается, когда пользователь нажал кнопку «Login» на login-странице.
        Если успешный login, переключаемся на основную страницу и запускаем load_categories.
        """
        user = self.user_input.text().strip()
        pwd = self.pass_input.text().strip()

        if not user or not pwd:
            self.status_label.setText("Username and password are required")
            return

        try:
            await self.client.login(user, pwd)
        except Exception as e:
            self.status_label.setText("Login failed")
            print(f"Login error: {e}")
            return

         # --- Сразу после успешного login делаем GET /auth/me, чтобы узнать роль ---
        try:
            me = await self.client.me()  # или get_auth_me()
            role = me.get("role") or me.get("role_id")
            # Если поле role — строковое (например, "admin"), проверяем на "admin"
            # Если role_id — числовое, нужно свериться, какой ID админа в базе
            if role != "admin" and role != 3:
                self.admin_btn.hide()
        except Exception as e:
            # Если даже GET /auth/me не сработал, скрываем Admin без лишнего шума
            print(f"Не удалось получить current_user: {e}")
            self.admin_btn.hide()
        # ------------------------------------------------------------------------

        # Если залогинились успешно — переключаемся на основную страницу
        self.stacked.setCurrentIndex(1)

        # После показа основной страницы запускаем загрузку категорий
        QTimer.singleShot(0, lambda: self.load_categories(None))

    @asyncSlot()
    async def on_register_clicked(self):
        """
        Этот слот вызывается, когда пользователь нажал кнопку «Register» на login-странице.
        Пытаемся зарегистрировать, и при успехе показываем сообщение, что можно войти.
        """
        user = self.user_input.text().strip()
        pwd = self.pass_input.text().strip()

        if not user or not pwd:
            self.status_label.setText("Username and password are required")
            return

        try:
            await self.client.register(user, pwd)
        except Exception as e:
            self.status_label.setText("Registration failed")
            print(f"Register error: {e}")
            return

        self.status_label.setText("Registered. You can login.")

    # ===== МЕТОДЫ ОСНОВНОГО ОКНА (КАТЕГОРИИ / СТАТЬИ) =====
    @asyncSlot(object)
    async def on_item(self, item: QListWidgetItem):
        data = item.data(Qt.UserRole)
        kind = data.get("type")
        if kind == "category":
            self.history.append(self.current_id)
            await self.load_categories(data["id"])
        elif kind == "article":
            await self.load_article(data["id"])
        elif kind == "test":
            # Новый блок: обработка клика по тесту
            test_id = data["id"]
            # Создаём окно теста (TestWindow) и добавляем в стек
            test_window = TestWindow(self.client, test_id, self)
            # Добавляем в stacked как новую страницу
            self.stacked.addWidget(test_window)
            self.test_pages.append(test_window)
            # Инициируем асинхронную загрузку данных теста
            QTimer.singleShot(0, test_window.load_test)
            # Переключаемся на страницу с тестом (последний индекс в стеке)
            self.stacked.setCurrentWidget(test_window)

        elif kind == "test_ui":  # зарезервировано, если понадобится
            pass
        elif kind == "test_results":
            pass
        else:
            QMessageBox.information(self, "Test", "Неизвестный элемент списка")

    @asyncSlot(object)
    async def load_categories(self, parent_id):
        self.list_widget.clear()
        self.current_id = parent_id

        # 1) Подкатегории (как было)
        cats = await self.client.list_categories()
        subs = [c for c in cats if c["parent_id"] == parent_id]
        for c in subs:
            item = QListWidgetItem(c["title"])
            item.setData(Qt.UserRole, {"type": "category", "id": c["id"]})
            self.list_widget.addItem(item)

        # 2) Статьи (как было)
        if parent_id is not None:
            arts = await self.client.list_articles_by_category(parent_id)
            for art in arts:
                item = QListWidgetItem(art["title"])
                item.setData(Qt.UserRole, {"type": "article", "id": art["id"]})
                self.list_widget.addItem(item)

        # 3) ** Добавляем проверку: есть ли у этой категории тесты? **
        if parent_id is not None:
            try:
                tests = await self.client.list_tests_by_category(parent_id)
                # tests — список объектов { "id": int, "category_id": int, "title": str, "max_attempts": int }
                for t in tests:
                    item = QListWidgetItem(f"Тест: {t['title']}")
                    item.setData(Qt.UserRole, {"type": "test", "id": t["id"]})
                    # (по желанию можно установить другой фон/иконку)
                    self.list_widget.addItem(item)
            except Exception as e:
                # Если API отвалился — не фатально, просто не рисуем тесты
                print(f"Ошибка при загрузке тестов: {e}")

        self.back_btn.setEnabled(bool(self.history))


    @asyncSlot(int)
    async def load_article(self, article_id):
        # Запрашиваем саму статью по ID
        art = await self.client.get_article(article_id)

        # Устанавливаем название статьи сверху
        self.title_label.setText(art.get("title", ""))

        # Отображаем контент статьи
        if art["content_type"] == "markdown":
            html = markdown.markdown(art["content"])
        else:
            html = art["content"]
        self.article_view.setHtml(html)

        # Загружаем медиа этого article_id
        media = await self.client.list_media_by_article(article_id)
        self.media_area.clear()

        base_dir = os.path.abspath(os.path.dirname(__file__))
        media_dir = os.path.join(base_dir, "media")

        for m in media:
            image_path = os.path.join(media_dir, m["url"])
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                icon = QIcon(pixmap)
                item = QListWidgetItem(icon, "")
            else:
                item = QListWidgetItem(m["url"])
            self.media_area.addItem(item)

        me = await self.client.me()
        await self.client.create_progress(
            user_id=me["id"],
            article_id=article_id,
            status="in_progress"
        )

    @asyncSlot()
    async def on_back(self):
        """
        Теперь on_back тоже асинхронный слот.
        При клике достаём последний ID из history и ждём load_categories.
        """
        if self.history:
            prev = self.history.pop()
            await self.load_categories(prev)

    @asyncSlot()
    async def on_personal(self):
        # Если ещё не создали PersonalPage, создаём и добавляем в стек
        if self.personal_page is None:
            self.personal_page = PersonalPage(self.client)
            self.stacked.addWidget(self.personal_page)

        # Переключаемся на страницу PersonalPage
        self.stacked.setCurrentWidget(self.personal_page)

        # Запускаем асинхронную загрузку данных
        QTimer.singleShot(0, lambda: self.personal_page.load_data())

    def on_admin(self):
        """
        Вызывается при клике на кнопку "Admin Panel" в главном экране.
        Просто переключаемся на виджет AdminPanel и запускаем загрузку данных.
        """
        # Переключаемся на страницу с админ‐панелью
        self.stacked.setCurrentWidget(self.admin_panel)
        # Запускаем начальную загрузку данных (категории, пользователи, тесты и т.д.)
        QTimer.singleShot(0, self.admin_panel.load_all)


    def remove_test_page(self, test_window: TestWindow):
        """
        Удаляем данную страницу TestWindow из stacked и списка test_pages.
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

def main():
    """
    Точка входа. Создаем QApplication + qasync‐цикл, передаем client в MainWindow
    и сразу же показываем главное окно (в котором по‐умолчанию будет отображаться форма логина).
    """
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    client = AsyncApiClient(base_url=API_BASE)
    window = MainWindow(client)
    window.show()

    with loop:
        loop.run_forever()


if __name__ == '__main__':
    main()
