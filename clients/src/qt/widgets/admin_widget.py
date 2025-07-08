# adminpanel.py

import asyncio
import os

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFileDialog,
                               QFormLayout, QGroupBox, QHBoxLayout,
                               QInputDialog, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QMessageBox, QPushButton,
                               QScrollArea, QSpinBox, QTabWidget, QTextEdit,
                               QVBoxLayout, QWidget)
from qasync import asyncSlot
from src.rest_client import AsyncApiClient

BUTTONS_HEIGHT = 50


class AdminPanelWidget(QWidget):
    def __init__(self, client: AsyncApiClient):
        super().__init__()
        self.client = client

        # Main layout for AdminPanel is a QVBoxLayout containing a QTabWidget
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Title label
        title = QLabel("Админ Панель")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.main_layout.addWidget(title)

        # Tabs for different sections
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Initialize tabs
        self.categories_tab = CategoriesTab(self.client)
        self.articles_tab = ArticlesTab(self.client)
        self.tests_tab = TestsTab(self.client)
        self.users_tab = UsersTab(self.client)

        # Add tabs to QTabWidget
        self.tabs.addTab(self.categories_tab, "Категории")
        self.tabs.addTab(self.articles_tab, "Статьи")
        self.tabs.addTab(self.tests_tab, "Тесты")
        self.tabs.addTab(self.users_tab, "Пользователи")

        # --- Кнопка «Back» ---
        back_btn = QPushButton("Back")
        back_btn.setFixedHeight(BUTTONS_HEIGHT)
        back_btn.setFixedWidth(300)
        back_btn.clicked.connect(self.on_back_clicked)

        # Выравниваем по центру
        back_layout = QHBoxLayout()
        back_layout.addStretch(1)  # Растяжка слева
        back_layout.addWidget(back_btn)
        back_layout.addStretch(1)  # Растяжка справа

        self.main_layout.addLayout(back_layout)

    @Slot()
    def on_back_clicked(self):
        main_win = self.window()
        # Предполагается, что у MainWindow есть атрибут stacked
        main_win.stacked.setCurrentIndex(1)

    @Slot()
    def on_admin_back(self):
        # Переключаемся обратно на основную страницу (index = 1)
        self.stacked.setCurrentIndex(1)

    @asyncSlot()
    async def load_all(self):
        """
        Вызывается после перехода на AdminPanel (уже после логина).
        Загружаем категории, статьи, тесты, пользователей и роли.
        """
        # 1) Категории
        await self.categories_tab.load_categories()

        # 2) Статьи (комбобокс категорий внутри ArticlesTab)
        await self.articles_tab.load_categories()

        # 3) Тесты (комбобокс категорий внутри TestsTab)
        await self.tests_tab.load_categories()

        # 4) Пользователи: сначала роли, затем пользователи
        await self.users_tab.load_roles()
        await self.users_tab.load_users()


class CategoriesTab(QWidget):
    def __init__(self, client: AsyncApiClient):
        super().__init__()
        self.client = client

        layout = QVBoxLayout()
        self.setLayout(layout)

        # List widget to show all categories (flat list with parent info)
        self.cat_list = QListWidget()
        layout.addWidget(self.cat_list, stretch=3)

        # Buttons: Add, Edit, Delete
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить категорию")
        self.edit_btn = QPushButton("Редактировать")
        self.delete_btn = QPushButton("Удалить")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

        self.add_btn.setFixedHeight(BUTTONS_HEIGHT)
        self.edit_btn.setFixedHeight(BUTTONS_HEIGHT)
        self.delete_btn.setFixedHeight(BUTTONS_HEIGHT)

        # Connections
        self.add_btn.clicked.connect(self.on_add_category)
        self.edit_btn.clicked.connect(self.on_edit_category)
        self.delete_btn.clicked.connect(self.on_delete_category)

        # Internal: holds list of categories loaded from server
        self.categories = []

    @asyncSlot()
    async def load_categories(self):
        """
        Загружает все категории (плоский список) и отображает их в QListWidget.
        """
        self.cat_list.clear()
        try:
            cats = await self.client.list_categories()
            # Sort by id for consistency
            cats_sorted = sorted(cats, key=lambda c: c["id"])
            self.categories = cats_sorted
            for c in cats_sorted:
                parent_title = ""
                if c["parent_id"] is not None:
                    parent = next((pc for pc in cats_sorted if pc["id"] == c["parent_id"]), None)
                    if parent:
                        parent_title = f" (Родитель: {parent['title']})"
                item = QListWidgetItem(f"{c['id']}: {c['title']}{parent_title}")
                item.setData(Qt.UserRole, c)
                self.cat_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить категории:\n{e}")

    @Slot()
    def on_add_category(self):
        """
        Открывает диалог для добавления новой категории.
        """
        dlg = CategoryDialog(self.categories)
        if dlg.exec() == QDialog.Accepted:
            title, parent_id = dlg.get_data()
            QTimer.singleShot(0, lambda: self._create_category(title, parent_id))

    @asyncSlot(str, object)
    async def _create_category(self, title: str, parent_id):
        try:
            await self.client.create_category(**{"title": title, "parent_id": parent_id})
            await self.load_categories()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать категорию:\n{e}")

    @Slot()
    def on_edit_category(self):
        """
        Открывает диалог для редактирования выбранной категории.
        """
        sel_item = self.cat_list.currentItem()
        if not sel_item:
            QMessageBox.information(self, "Выбор", "Выберите категорию для редактирования")
            return
        c = sel_item.data(Qt.UserRole)
        dlg = CategoryDialog(self.categories, edit_data=c)
        if dlg.exec() == QDialog.Accepted:
            title, parent_id = dlg.get_data()
            QTimer.singleShot(0, lambda: self._update_category(c["id"], title, parent_id))

    @asyncSlot(int, str, object)
    async def _update_category(self, cat_id: int, title: str, parent_id):
        try:
            await self.client.update_category(cat_id, **{"title": title, "parent_id": parent_id})
            await self.load_categories()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить категорию:\n{e}")

    @Slot()
    def on_delete_category(self):
        """
        Подтверждение и удаление выбранной категории.
        """
        sel_item = self.cat_list.currentItem()
        if not sel_item:
            QMessageBox.information(self, "Выбор", "Выберите категорию для удаления")
            return
        c = sel_item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить категорию '{c['title']}'? Это действие нельзя отменить.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QTimer.singleShot(0, lambda: self._delete_category(c["id"]))

    @asyncSlot(int)
    async def _delete_category(self, cat_id: int):
        try:
            await self.client.delete_category(cat_id)
            await self.load_categories()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить категорию:\n{e}")


class CategoryDialog(QDialog):
    """
    Диалог для создания/редактирования категории.
    """
    def __init__(self, categories, edit_data=None):
        super().__init__()
        self.setWindowTitle("Категория")
        self.resize(300, 150)
        self.categories = categories
        self.edit_data = edit_data

        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()
        self.title_edit = QLineEdit()
        form.addRow("Название:", self.title_edit)

        self.parent_combo = QComboBox()
        self.parent_combo.addItem("Нет родителя", None)
        for c in categories:
            self.parent_combo.addItem(c["title"], c["id"])
        form.addRow("Родитель:", self.parent_combo)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Отмена")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.ok_btn.setFixedHeight(BUTTONS_HEIGHT)
        self.cancel_btn.setFixedHeight(BUTTONS_HEIGHT)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        if edit_data:
            # Pre-fill fields
            self.title_edit.setText(edit_data["title"])
            if edit_data["parent_id"] is None:
                self.parent_combo.setCurrentIndex(0)
            else:
                idx = self.parent_combo.findData(edit_data["parent_id"])
                if idx >= 0:
                    self.parent_combo.setCurrentIndex(idx)

    def get_data(self):
        title = self.title_edit.text().strip()
        parent_id = self.parent_combo.currentData()
        return title, parent_id


class ArticlesTab(QWidget):
    def __init__(self, client: AsyncApiClient):
        super().__init__()
        self.client = client

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Top: choose category to filter articles
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Категория:"))
        self.cat_combo = QComboBox()
        filter_layout.addWidget(self.cat_combo)
        self.refresh_cats_btn = QPushButton("Обновить категории")
        filter_layout.addWidget(self.refresh_cats_btn)
        layout.addLayout(filter_layout)

        # List of articles
        self.articles_list = QListWidget()
        layout.addWidget(self.articles_list, stretch=3)

        # Buttons: Add, Edit, Delete
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить статью")
        self.edit_btn = QPushButton("Редактировать")
        self.delete_btn = QPushButton("Удалить")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

        # Buttons for media management
        media_btn_layout = QHBoxLayout()
        self.media_btn = QPushButton("Управлять медиа")
        media_btn_layout.addWidget(self.media_btn)
        layout.addLayout(media_btn_layout)

        self.edit_btn.setFixedHeight(BUTTONS_HEIGHT)
        self.add_btn.setFixedHeight(BUTTONS_HEIGHT)
        self.delete_btn.setFixedHeight(BUTTONS_HEIGHT)
        self.media_btn.setFixedHeight(BUTTONS_HEIGHT)

        # Connections
        self.refresh_cats_btn.clicked.connect(self.on_refresh_categories)
        self.cat_combo.currentIndexChanged.connect(self.on_category_selected)
        self.add_btn.clicked.connect(self.on_add_article)
        self.edit_btn.clicked.connect(self.on_edit_article)
        self.delete_btn.clicked.connect(self.on_delete_article)
        self.media_btn.clicked.connect(self.on_manage_media)

        self.categories = []
        self.articles = []

    @asyncSlot()
    async def load_categories(self):
        """
        Загружает список категорий и заполняет comboBox.
        """
        self.cat_combo.clear()
        try:
            cats = await self.client.list_categories()
            self.categories = sorted(cats, key=lambda c: c["title"])
            self.cat_combo.addItem("Выберите категорию", None)
            for c in self.categories:
                self.cat_combo.addItem(c["title"], c["id"])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить категории:\n{e}")

    @Slot()
    def on_refresh_categories(self):
        QTimer.singleShot(0, lambda: self.load_categories())

    @Slot(int)
    def on_category_selected(self, index):
        cat_id = self.cat_combo.currentData()
        if cat_id is None:
            self.articles_list.clear()
            return
        QTimer.singleShot(0, lambda: self._load_articles(cat_id))

    @asyncSlot(int)
    async def _load_articles(self, cat_id: int):
        """
        Загружает статьи в выбранной категории.
        """
        self.articles_list.clear()
        try:
            arts = await self.client.list_articles_by_category(cat_id)
            self.articles = arts
            for art in arts:
                item = QListWidgetItem(f"{art['id']}: {art['title']}")
                item.setData(Qt.UserRole, art)
                self.articles_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить статьи:\n{e}")

    @Slot()
    def on_add_article(self):
        """
        Диалог для создания новой статьи.
        """
        current_cat_id = self.cat_combo.currentData()
        if current_cat_id is None:
            QMessageBox.information(self, "Категория", "Сначала выберите категорию")
            return
        dlg = ArticleDialog(self.categories, create=True, category_id=current_cat_id)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            QTimer.singleShot(0, lambda: self._create_article(data))

    @asyncSlot(dict)
    async def _create_article(self, data: dict):
        try:
            await self.client.create_article(**data)
            await self._load_articles(data["category_id"])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать статью:\n{e}")

    @Slot()
    def on_edit_article(self):
        sel_item = self.articles_list.currentItem()
        if not sel_item:
            QMessageBox.information(self, "Выбор", "Выберите статью для редактирования")
            return
        art = sel_item.data(Qt.UserRole)
        dlg = ArticleDialog(self.categories, edit_data=art)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            QTimer.singleShot(0, lambda: self._update_article(art["id"], data))

    @asyncSlot(int, dict)
    async def _update_article(self, article_id: int, data: dict):
        try:
            await self.client.update_article(article_id, title=data.get("title"), content=data.get("content"), content_type=data.get("content_type"))
            cat_id = data.get("category_id", self.cat_combo.currentData())
            await self._load_articles(cat_id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить статью:\n{e}")

    @Slot()
    def on_delete_article(self):
        sel_item = self.articles_list.currentItem()
        if not sel_item:
            QMessageBox.information(self, "Выбор", "Выберите статью для удаления")
            return
        art = sel_item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить статью '{art['title']}'? Это действие нельзя отменить.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QTimer.singleShot(0, lambda: self._delete_article(art["id"], art["category_id"]))

    @asyncSlot(int, int)
    async def _delete_article(self, article_id: int, category_id: int):
        try:
            await self.client.delete_article(article_id)
            await self._load_articles(category_id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить статью:\n{e}")

    @Slot()
    def on_manage_media(self):
        """
        Открывает диалог управления медиа для выбранной статьи.
        """
        sel_item = self.articles_list.currentItem()
        if not sel_item:
            QMessageBox.information(self, "Выбор", "Выберите статью для управления медиа")
            return
        art = sel_item.data(Qt.UserRole)
        dlg = MediaDialog(self.client, art["id"])
        dlg.exec()


class ArticleDialog(QDialog):
    """
    Диалог для создания/редактирования статьи.
    """
    def __init__(self, categories, create=False, category_id=None, edit_data=None):
        super().__init__()
        self.setWindowTitle("Статья")
        self.resize(500, 400)
        self.categories = categories
        self.edit_data = edit_data

        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()
        self.title_edit = QLineEdit()
        form.addRow("Заголовок:", self.title_edit)

        self.cat_combo = QComboBox()
        for c in categories:
            self.cat_combo.addItem(c["title"], c["id"])
        form.addRow("Категория:", self.cat_combo)

        self.content_edit = QTextEdit()
        self.content_edit.setStyleSheet("color: rgba(200, 200, 200, 1);")
        form.addRow("Содержание:", self.content_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItem("Markdown", "markdown")
        self.type_combo.addItem("HTML", "html")
        form.addRow("Тип контента:", self.type_combo)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Отмена")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.ok_btn.setFixedHeight(BUTTONS_HEIGHT)
        self.cancel_btn.setFixedHeight(BUTTONS_HEIGHT)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        if create and category_id is not None:
            idx = self.cat_combo.findData(category_id)
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)

        if edit_data:
            self.title_edit.setText(edit_data["title"])
            # Pre-select category
            idx = self.cat_combo.findData(edit_data["category_id"])
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)
            # Content
            self.content_edit.setPlainText(edit_data["content"])
            # Content type
            ctype = edit_data["content_type"]
            idx_type = 0 if ctype == "markdown" else 1
            self.type_combo.setCurrentIndex(idx_type)

    def get_data(self):
        return {
            "title": self.title_edit.text().strip(),
            "category_id": self.cat_combo.currentData(),
            "content": self.content_edit.toPlainText(),
            "content_type": self.type_combo.currentData()
        }


class MediaDialog(QDialog):
    """
    Диалог управления медиа для статьи: отображение списка медиа, добавление/удаление.
    """
    def __init__(self, client: AsyncApiClient, article_id: int):
        super().__init__()
        self.client = client
        self.article_id = article_id
        self.setWindowTitle(f"Медиа для статьи {article_id}")
        self.resize(600, 400)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # List of media
        self.media_list = QListWidget()
        layout.addWidget(self.media_list, stretch=3)

        # Buttons: Add, Delete
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить медиа")
        self.delete_btn = QPushButton("Удалить выбранное")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

        self.add_btn.setFixedHeight(BUTTONS_HEIGHT)
        self.delete_btn.setFixedHeight(BUTTONS_HEIGHT)

        self.add_btn.clicked.connect(self.on_add_media)
        self.delete_btn.clicked.connect(self.on_delete_media)

        QTimer.singleShot(0, lambda: self.load_media())

    @asyncSlot()
    async def load_media(self):
        """
        Загружает медиа для данной статьи.
        """
        self.media_list.clear()
        try:
            media_items = await self.client.list_media_by_article(self.article_id)
            for m in media_items:
                item = QListWidgetItem(f"{m['id']}: {m['url']} ({m['media_type']})")
                item.setData(Qt.UserRole, m)
                self.media_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить медиа:\n{e}")

    @Slot()
    def on_add_media(self):
        """
        Добавление нового медиа: открывает QFileDialog для выбора файла,
        определяет тип по расширению, загружает.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите медиа (SVG, PNG, WebM)", "", "Media files (*.svg *.png *.webm)"
        )
        if not file_path:
            return
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip(".")
        if ext not in ("svg", "png", "webm"):
            QMessageBox.warning(self, "Неподдерживаемый формат", "Выберите файл SVG, PNG или WebM")
            return
        # For simplicity, assume the server expects URL relative path.
        # In real app, file should be uploaded to server; here we store filename only.
        url = os.path.basename(file_path)
        # Prompt for sort order
        sort_order, ok = QInputDialog.getInt(self, "Порядок сортировки", "Введите порядок:", 0, 0)
        if not ok:
            sort_order = 0
        data = {
            "article_id": self.article_id,
            "media_type": ext,
            "url": url,
            "sort_order": sort_order
        }
        QTimer.singleShot(0, lambda: self._create_media(data))

    @asyncSlot(dict)
    async def _create_media(self, data: dict):
        try:
            await self.client.create_media(data)
            await self.load_media()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить медиа:\n{e}")

    @Slot()
    def on_delete_media(self):
        sel_item = self.media_list.currentItem()
        if not sel_item:
            QMessageBox.information(self, "Выбор", "Выберите медиа для удаления")
            return
        m = sel_item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить медиа '{m['url']}'? Это действие нельзя отменить.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QTimer.singleShot(0, lambda: self._delete_media(m["id"]))

    @asyncSlot(int)
    async def _delete_media(self, media_id: int):
        try:
            await self.client.delete_media(media_id)
            await self.load_media()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить медиа:\n{e}")


class TestsTab(QWidget):
    def __init__(self, client: AsyncApiClient):
        super().__init__()
        self.client = client

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Top: choose category to filter tests
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Категория:"))
        self.cat_combo = QComboBox()
        filter_layout.addWidget(self.cat_combo)
        self.refresh_cats_btn = QPushButton("Обновить категории")
        filter_layout.addWidget(self.refresh_cats_btn)
        layout.addLayout(filter_layout)

        # List of tests
        self.tests_list = QListWidget()
        layout.addWidget(self.tests_list, stretch=3)

        # Buttons: Add, Edit, Delete
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить тест")
        self.edit_btn = QPushButton("Редактировать тест")
        self.delete_btn = QPushButton("Удалить тест")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

        self.add_btn.setFixedHeight(BUTTONS_HEIGHT)
        self.edit_btn.setFixedHeight(BUTTONS_HEIGHT)
        self.delete_btn.setFixedHeight(BUTTONS_HEIGHT)

        # Connections
        self.refresh_cats_btn.clicked.connect(self.on_refresh_categories)
        self.cat_combo.currentIndexChanged.connect(self.on_category_selected)
        self.add_btn.clicked.connect(self.on_add_test)
        self.edit_btn.clicked.connect(self.on_edit_test)
        self.delete_btn.clicked.connect(self.on_delete_test)

        self.categories = []
        self.tests = []

    @asyncSlot()
    async def load_categories(self):
        """
        Загружает категории и заполняет comboBox.
        """
        self.cat_combo.clear()
        try:
            cats = await self.client.list_categories()
            self.categories = sorted(cats, key=lambda c: c["title"])
            self.cat_combo.addItem("Выберите категорию", None)
            for c in self.categories:
                self.cat_combo.addItem(c["title"], c["id"])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить категории:\n{e}")

    @Slot()
    def on_refresh_categories(self):
        QTimer.singleShot(0, lambda: self.load_categories())

    @Slot(int)
    def on_category_selected(self, index):
        cat_id = self.cat_combo.currentData()
        if cat_id is None:
            self.tests_list.clear()
            return
        QTimer.singleShot(0, lambda: self._load_tests(cat_id))

    @asyncSlot(int)
    async def _load_tests(self, cat_id: int):
        """
        Загружает тесты выбранной категории.
        """
        self.tests_list.clear()
        try:
            tests = await self.client.list_tests_by_category(cat_id)
            self.tests = tests
            for t in tests:
                item = QListWidgetItem(f"{t['id']}: {t['title']} (Попыток: {t['max_attempts']})")
                item.setData(Qt.UserRole, t)
                self.tests_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить тесты:\n{e}")

    @Slot()
    def on_add_test(self):
        """
        Открывает диалог для создания полного теста.
        """
        cat_id = self.cat_combo.currentData()
        if cat_id is None:
            QMessageBox.information(self, "Категория", "Сначала выберите категорию")
            return
        dlg = TestDialog(self.categories, create=True, category_id=cat_id)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            QTimer.singleShot(0, lambda: self._create_full_test(data))

    @asyncSlot(dict)
    async def _create_full_test(self, data: dict):
        try:
            await self.client.create_test_full(data)
            await self._load_tests(data["category_id"])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать тест:\n{e}")

    @asyncSlot()
    async def _load_test(self):
        sel_item = self.tests_list.currentItem()
        if not sel_item:
            QMessageBox.information(self, "Выбор", "Выберите тест для редактирования")
            return
        test_data = sel_item.data(Qt.UserRole)
        test_id = test_data["id"]
        test = await self.client.get_test_full(test_id)
        # Для редактирования теста и вопросов/вариантов лучше заново загрузить полный тест
        dlg = TestDialog(self.categories, edit_data=test)
        if dlg.exec() == QDialog.Accepted:
            data = dlg.get_data()
            QTimer.singleShot(0, lambda: self._update_full_test(test_id, data))

    @Slot()
    def on_edit_test(self):
        QTimer.singleShot(0, lambda: self._load_test())

    @asyncSlot(int, dict)
    async def _update_full_test(self, test_id: int, data: dict):
        try:
            # Обновляем сначала сам тест (title, max_attempts), потом вопросы/опции...
            # Здесь разбиваем на последовательные запросы: PUT /tests/{id}, затем перезаписываем вопросы/опции
            await self.client.update_test(test_id, {
                "title": data["title"],
                "max_attempts": data["max_attempts"]
            })
            # Для простоты удаляем старые вопросы/варианты и создаем новые
            old_full = await self.client.get_test_full(test_id)
            # Удаляем старые варианты и вопросы
            for q in old_full["questions"]:
                for opt in q["options"]:
                    await self.client.delete_option(opt["id"])
                await self.client.delete_question(q["id"])
            # Создаем новые вопросы и опции
            for q in data["questions"]:
                new_q = await self.client.create_question({
                    "test_id": test_id,
                    "text": q["text"],
                    "weight": q["weight"]
                })
                for opt in q["options"]:
                    await self.client.create_option({
                        "question_id": new_q["id"],
                        "text": opt["text"],
                        "is_correct": opt["is_correct"]
                    })
            # Обновляем список тестов в UI
            await self._load_tests(data["category_id"])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить тест:\n{e}")

    @Slot()
    def on_delete_test(self):
        sel_item = self.tests_list.currentItem()
        if not sel_item:
            QMessageBox.information(self, "Выбор", "Выберите тест для удаления")
            return
        t = sel_item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить тест '{t['title']}'? Это действие нельзя отменить.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QTimer.singleShot(0, lambda: self._delete_test(t["id"], t["category_id"]))

    @asyncSlot(int, int)
    async def _delete_test(self, test_id: int, category_id: int):
        try:
            await self.client.delete_test(test_id)
            await self._load_tests(category_id)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить тест:\n{e}")


class TestDialog(QDialog):
    """
    Диалог для создания/редактирования полного теста (TestFullCreate/TestReadWithQuestions).
    """
    def __init__(self, categories, create=False, category_id=None, edit_data=None):
        super().__init__()
        self.setWindowTitle("Тест")
        self.resize(700, 600)
        self.categories = categories
        self.edit_data = edit_data

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        form = QFormLayout()
        self.title_edit = QLineEdit()
        form.addRow("Название теста:", self.title_edit)

        self.cat_combo = QComboBox()
        for c in categories:
            self.cat_combo.addItem(c["title"], c["id"])
        form.addRow("Категория:", self.cat_combo)

        self.max_spin = QSpinBox()
        self.max_spin.setMinimum(1)
        self.max_spin.setMaximum(100)
        form.addRow("Макс. попыток:", self.max_spin)

        main_layout.addLayout(form)

        # Секцию вопросов делаем в ScrollArea
        self.questions_area = QScrollArea()
        self.questions_area.setWidgetResizable(True)
        self.questions_widget = QWidget()
        self.questions_layout = QVBoxLayout()
        self.questions_widget.setLayout(self.questions_layout)
        self.questions_area.setWidget(self.questions_widget)
        main_layout.addWidget(QLabel("Вопросы и варианты:"))
        main_layout.addWidget(self.questions_area, stretch=1)

        # Кнопка Добавить вопрос
        self.add_question_btn = QPushButton("Добавить вопрос")
        main_layout.addWidget(self.add_question_btn)
        self.add_question_btn.clicked.connect(self.on_add_question)

        # Buttons: OK/Cancel
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Отмена")
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)

        self.ok_btn.setFixedHeight(BUTTONS_HEIGHT)
        self.cancel_btn.setFixedHeight(BUTTONS_HEIGHT)

        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        # Храним виджеты вопросов: список QuestionWidget
        self.question_widgets = []

        if create and category_id is not None:
            idx = self.cat_combo.findData(category_id)
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)

        if edit_data:
            full = edit_data
            self.title_edit.setText(full["title"])
            idx = self.cat_combo.findData(full["category_id"])
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)
            self.max_spin.setValue(full["max_attempts"])
            # Добавляем существующие вопросы
            for q in full.get("questions", []):
                qw = QuestionWidget(edit=q)
                self.questions_layout.addWidget(qw)
                self.question_widgets.append(qw)

    @Slot()
    def on_add_question(self):
        qw = QuestionWidget()
        self.questions_layout.addWidget(qw)
        self.question_widgets.append(qw)

    def get_data(self):
        """
        Собирает данные для TestFullCreate:
        {
            "category_id": int,
            "title": str,
            "max_attempts": int,
            "questions": [
              {"text": str, "weight": int,
               "options": [ {"text": str, "is_correct": bool}, ... ]
              },
              ...
            ]
        }
        """
        data = {
            "category_id": self.cat_combo.currentData(),
            "title": self.title_edit.text().strip(),
            "max_attempts": self.max_spin.value(),
            "questions": []
        }
        for qw in self.question_widgets:
            qd = qw.get_data()
            if qd is None:
                continue
            data["questions"].append(qd)
        return data


class QuestionWidget(QGroupBox):
    """
    Виджет для одного вопроса с вариантами ответов.
    """
    def __init__(self, edit=None):
        super().__init__("Вопрос")
        layout = QVBoxLayout()
        self.setLayout(layout)

        form = QFormLayout()
        self.text_edit = QLineEdit()
        form.addRow("Текст вопроса:", self.text_edit)
        self.weight_spin = QSpinBox()
        self.weight_spin.setMinimum(1)
        self.weight_spin.setMaximum(10)
        form.addRow("Вес вопроса:", self.weight_spin)
        layout.addLayout(form)

        # Секция вариантов
        self.options_layout = QVBoxLayout()
        layout.addWidget(QLabel("Варианты ответов:"))
        layout.addLayout(self.options_layout)

        # Кнопка Добавить вариант
        self.add_option_btn = QPushButton("Добавить вариант")
        layout.addWidget(self.add_option_btn)
        self.add_option_btn.clicked.connect(self.on_add_option)

        self.add_option_btn.setFixedHeight(BUTTONS_HEIGHT)

        # Храним OptionWidget-ы
        self.option_widgets = []

        if edit:
            self.text_edit.setText(edit["text"])
            self.weight_spin.setValue(edit["weight"])
            for opt in edit.get("options", []):
                ow = OptionWidget(edit=opt)
                self.options_layout.addWidget(ow)
                self.option_widgets.append(ow)

    @Slot()
    def on_add_option(self):
        ow = OptionWidget()
        self.options_layout.addWidget(ow)
        self.option_widgets.append(ow)

    def get_data(self):
        """
        Возвращает dict с ключами text, weight, options: [ {text, is_correct}, ... ]
        """
        text = self.text_edit.text().strip()
        if not text:
            return None
        weight = self.weight_spin.value()
        opts = []
        for ow in self.option_widgets:
            od = ow.get_data()
            if od:
                opts.append(od)
        if not opts:
            return None
        return {"text": text, "weight": weight, "options": opts}


class OptionWidget(QWidget):
    """
    Виджет для одного варианта ответа: текст + флажок is_correct.
    """
    def __init__(self, edit=None):
        super().__init__()
        layout = QHBoxLayout(self)

        self.text_edit = QLineEdit()
        self.is_correct_chk = QCheckBox("Правильный")

        layout.addWidget(self.text_edit)
        layout.addWidget(self.is_correct_chk)

        if edit:
            self.text_edit.setText(edit["text"])
            self.is_correct_chk.setChecked(edit["is_correct"])

    def get_data(self):
        text = self.text_edit.text().strip()
        if not text:
            return None
        is_corr = self.is_correct_chk.isChecked()
        return {"text": text, "is_correct": is_corr}


class UsersTab(QWidget):
    def __init__(self, client: AsyncApiClient):
        super().__init__()
        self.client = client

        layout = QVBoxLayout()
        self.setLayout(layout)

        # List of users
        self.users_list = QListWidget()
        layout.addWidget(self.users_list, stretch=3)

        # Combobox for role selection
        role_layout = QHBoxLayout()
        role_layout.addWidget(QLabel("Новая роль:"))
        self.role_combo = QComboBox()


        # Пока не загружаем роли и пользователей – сделаем это из load_all() у AdminPanel
        role_layout.addWidget(self.role_combo)

        self.update_role_btn = QPushButton("Обновить роль")
        role_layout.addWidget(self.update_role_btn)
        layout.addLayout(role_layout)

        # Delete user button
        self.delete_btn = QPushButton("Удалить пользователя")
        layout.addWidget(self.delete_btn)

        self.update_role_btn.setFixedHeight(BUTTONS_HEIGHT)
        self.delete_btn.setFixedHeight(BUTTONS_HEIGHT)

        # Connections
        self.users_list.currentItemChanged.connect(self.on_user_selected)
        self.update_role_btn.clicked.connect(self.on_update_role)
        self.delete_btn.clicked.connect(self.on_delete_user)

        self.users = []
        self.selected_user = None

    @asyncSlot()
    async def load_roles(self):
        """
        Загружает список ролей (GET /roles/) и заполняет ComboBox.
        """
        self.role_combo.clear()
        try:
            roles = await self.client.list_roles()
            # Предполагаем, что roles = [{"id": 1, "name": "student"}, ...]
            for r in roles:
                display = f"{r['name'].capitalize()} (ID={r['id']})"
                self.role_combo.addItem(display, r["id"])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить роли:\n{e}")

    @asyncSlot()
    async def load_users(self):
        """
        Загружает список всех пользователей.
        """
        self.users_list.clear()
        try:
            users = await self.client.list_users(limit=1000)
            self.users = users
            for u in users:
                item = QListWidgetItem(f"{u['id']}: {u['username']} (Роль ID: {u['role_id']})")
                item.setData(Qt.UserRole, u)
                self.users_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить пользователей:\n{e}")

    @Slot(QListWidgetItem, QListWidgetItem)
    def on_user_selected(self, current, previous):
        if current:
            self.selected_user = current.data(Qt.UserRole)
            rid = self.selected_user.get("role_id", None)
            if rid is not None:
                idx = self.role_combo.findData(rid)
                if idx >= 0:
                    self.role_combo.setCurrentIndex(idx)

    @Slot()
    def on_update_role(self):
        if not self.selected_user:
            QMessageBox.information(self, "Выбор", "Выберите пользователя")
            return
        new_role = self.role_combo.currentData()
        payload = {"role_id": new_role}
        QTimer.singleShot(0, lambda: asyncio.create_task(self._update_user_role(self.selected_user["id"], payload)))

    @asyncSlot(int, dict)
    async def _update_user_role(self, user_id: int, payload: dict):
        try:
            await self.client.update_user(user_id, **payload)
            await self.load_users()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить роль:\n{e}")

    @Slot()
    def on_delete_user(self):
        if not self.selected_user:
            QMessageBox.information(self, "Выбор", "Выберите пользователя")
            return
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить пользователя '{self.selected_user['username']}'? Это действие нельзя отменить.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            QTimer.singleShot(0, lambda: asyncio.create_task(self._delete_user(self.selected_user["id"])))

    @asyncSlot(int)
    async def _delete_user(self, user_id: int):
        try:
            await self.client.delete_user(user_id)
            await self.load_users()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить пользователя:\n{e}")
