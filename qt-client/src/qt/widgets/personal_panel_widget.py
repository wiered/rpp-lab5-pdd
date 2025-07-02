import asyncio
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QPushButton
)
from PySide6.QtCore import Qt, Slot, QTimer
from qasync import asyncSlot

from src.rest_client import AsyncApiClient

STATUS_DICT = {
    "not_started": "Ожидается",
    "in_progress": "В процессе",
    "done": "Завершено"
}

class PersonalPageWidget(QWidget):
    def __init__(self, client: AsyncApiClient):
        super().__init__()
        self.client = client
        self.user_id = None  # будет заполнено при загрузке

        # Основной вертикальный layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # ===== Кнопка "Назад" =====
        self.back_btn = QPushButton("Back")
        self.back_btn.setFixedHeight(40)
        self.back_btn.clicked.connect(self.on_back)
        main_layout.addWidget(self.back_btn)

        # ===== Раздел 1: Прогресс (число решённых тестов из назначенных категорий) =====
        self.progress_group = QGroupBox("Прогресс пользователя")
        pg_layout = QVBoxLayout()
        self.progress_label = QLabel("Загрузка...")
        self.progress_label.setAlignment(Qt.AlignCenter)
        pg_layout.addWidget(self.progress_label)
        self.progress_group.setLayout(pg_layout)
        main_layout.addWidget(self.progress_group)

        # ===== Раздел 2: Прочтённые статьи (/progress) =====
        self.articles_group = QGroupBox("Прочтённые статьи")
        art_layout = QVBoxLayout()
        self.articles_list = QListWidget()
        art_layout.addWidget(self.articles_list)
        self.articles_group.setLayout(art_layout)
        main_layout.addWidget(self.articles_group)

        # ===== Раздел 3: Решённые тесты (/test-results) =====
        self.tests_group = QGroupBox("Решённые тесты")
        test_layout = QVBoxLayout()
        self.tests_list = QListWidget()
        test_layout.addWidget(self.tests_list)
        self.tests_group.setLayout(test_layout)
        main_layout.addWidget(self.tests_group)

         # ===== Кнопка "Назад" =====
        self.back_btn = QPushButton("Back")
        self.back_btn.setFixedHeight(40)
        self.back_btn.clicked.connect(self.on_back)
        main_layout.addWidget(self.back_btn)

    @Slot()
    def on_back(self):
        """
        При нажатии кнопки "Назад" возвращаемся к главной странице (index=1)
        """
        main_win = self.window()
        # Предполагается, что у MainWindow есть атрибут stacked
        main_win.stacked.setCurrentIndex(1)

    @asyncSlot()
    async def load_data(self):
        """
        Асинхронно загружает:
        1) текущего пользователя (GET /auth/me),
        2) его назначения (GET /assignments?user_id=...),
        3) списки тестов по каждому назначенному category_id (GET /tests/category/{category_id}),
        4) результаты тестов (GET /test-results?user_id=...),
        5) записи прогресса (GET /progress?user_id=...).

        По результатам формирует:
        - Для раздела «Прогресс» – строку вида «Решено тестов: X из Y».
        - Для раздела «Прочтённые статьи» – список записей progress (category_id и status).
        - Для раздела «Решённые тесты» – список с названием теста, баллами и статусом Passed/Failed.
        """
        # 1) Получаем текущего пользователя (нужен user_id)
        me = await self.client.me()
        self.user_id = me.get("id")

        # 2) Список назначений для этого пользователя
        assignments = await self.client.list_assignments(user_id=self.user_id)
        category_ids = [a["category_id"] for a in assignments]
        articles = []
        for assignment in assignments:
            articles_for_category = await self.client.list_articles_by_category(assignment["category_id"])
            articles.append(*articles_for_category)

        articles_ids = []
        for article in articles:
            articles_ids.append(article["id"])


        # 3) Собираем все тесты из назначенных категорий
        all_tests = []
        for cid in category_ids:
            try:
                tests_in_cat = await self.client.list_tests_by_category(cid)
            except Exception:
                tests_in_cat = []
            all_tests.extend(tests_in_cat)
        total_tests = len(all_tests)
        tests_ids_set = {t["id"] for t in all_tests}

        # 4) Получаем результаты тестов пользователя
        test_results = await self.client.list_test_results(user_id=self.user_id)
        solved_tests_count = sum(1 for tr in test_results if tr.get("test_id") in tests_ids_set)

        # Обновляем метку прогресса
        self.progress_label.setText(f"Решено тестов: {solved_tests_count} из {total_tests}")

        # ===== Заполняем «Прочтённые статьи» – просто список progress-элементов =====
        progresses = await self.client.list_progress(user_id=self.user_id)
        self.articles_list.clear()
        print(progresses)
        if progresses:
            for article in progresses:
                art_id = article.get("article_id")
                article_obj = await self.client.get_article(art_id)
                status = article.get("status")
                self.articles_list.addItem(f"Артикль {article_obj['title']}: {STATUS_DICT[status]}")
        else:
            self.articles_list.addItem("Нет прочтённых записей")

        # ===== Заполняем «Решённые тесты» – подробный список test results =====
        self.tests_list.clear()
        if test_results:
            for tr in test_results:
                test_id = tr.get("test_id")
                score = tr.get("score")
                max_score = tr.get("max_score")
                passed = tr.get("passed")
                try:
                    test_obj = await self.client.get_test(test_id)
                    test_title = test_obj.get("title", f"Тест #{test_id}")
                except Exception:
                    test_title = f"Тест #{test_id}"

                status_text = "Пройден" if passed else "Не пройден"
                self.tests_list.addItem(f"{test_title}: {score}/{max_score} ({status_text})")
        else:
            self.tests_list.addItem("Нет решённых тестов")
