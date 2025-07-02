import os

import markdown
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QMessageBox, QPushButton,
                               QTextBrowser, QVBoxLayout, QWidget)
from qasync import asyncSlot

from src.qt.styles import STYLESHEET

class MainPageWidget(QWidget):
    def __init__(self, parent = None, client = None):
        super().__init__()
        self.parent = parent
        self.client = client

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

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

         # Применяем стили
        self.list_widget.setStyleSheet(STYLESHEET)
        self.media_area.setStyleSheet(STYLESHEET)

        self.back_btn.clicked.connect(self.on_back)
        self.list_widget.itemClicked.connect(self.on_item)

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
            self.parent.on_test(test_id)

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
        print(f"Загружаю статью {article_id}")
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

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
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
