from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QButtonGroup, QGroupBox, QHBoxLayout, QLabel,
                               QMainWindow, QMessageBox, QPushButton,
                               QRadioButton, QScrollArea, QVBoxLayout, QWidget)
from qasync import asyncSlot

from src.rest_client import AsyncApiClient


class TestWidget(QWidget):
    """
    Окно для прохождения одного теста. Будет добавляться в QStackedLayout в MainWindow
    как новая страница. Когда пользователь нажмёт «Отправить», расчитаем score,
    отправим POST /test-results/ и вернёмся обратно в MainWindow.
    """

    def __init__(self, client: AsyncApiClient, test_id: int, parent_window: QMainWindow):
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
