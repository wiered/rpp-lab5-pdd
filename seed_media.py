import asyncio
import aiohttp
import os
from urllib.parse import urljoin

API_URL = "http://127.0.0.1:8082/api"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzQ5MDgzMDE1fQ.67sAwucx2VIOgKFxLZkVBm5Ud7LMS3Ed0ICqrYMIlnI"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}

MAX_RETRIES = 5
RETRY_DELAY = 5  # секунды


async def _request_with_retries(session, method, url, **kwargs):
    """
    Вспомогательная функция: выполняет запрос session.{method}(url, **kwargs),
    при ошибке (например, 5xx или сетевой сбой) — ждёт RETRY_DELAY и пробует снова,
    до MAX_RETRIES раз.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with getattr(session, method)(url, **kwargs) as resp:
                if resp.status >= 500:
                    text = await resp.text()
                    raise aiohttp.ClientResponseError(
                        status=resp.status,
                        message=f"Server error: {text}"
                    )
                resp.raise_for_status()
                # Для GET возвращаем JSON. Для POST возвращаем JSON.
                return await resp.json()
        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"⚠ Ошибка ({method.upper()} {url}): {e!r}")
                print(f"  → повтор через {RETRY_DELAY} сек. (попытка {attempt}/{MAX_RETRIES})")
                await asyncio.sleep(RETRY_DELAY)
            else:
                print(f"❌ Запрос {method.upper()} {url} не удался после {MAX_RETRIES} попыток.")
                raise


async def fetch_all_articles(session):
    """
    Получает все статьи с сервера (GET /articles/).
    Возвращает список словарей вида ArticleRead: {id, category_id, title, content, ...}
    """
    url = f"{API_URL}/articles/"
    data = await _request_with_retries(session, "get", url)
    return data  # ожидается list[ArticleRead]


async def create_media(session, article_id, media_type, url_str, sort_order=0):
    """
    Создаёт запись Media для указанной статьи:
      POST /media/ { article_id, media_type, url, sort_order }
    media_type: 'svg', 'png' или 'webm'
    url_str: строка с путём или URL к файлу
    """
    payload = {
        "article_id": article_id,
        "media_type": media_type,
        "url": url_str,
        "sort_order": sort_order
    }
    endpoint = f"{API_URL}/media/"
    data = await _request_with_retries(session, "post", endpoint, json=payload)
    return data  # MediaRead


async def interactive_media_upload():
    """
    Основная логика:
    1) Получаем все статьи.
    2) Для каждой статьи выводим её id и название и ждём от пользователя ввода имени файла медиа.
    3) Если имя не пустое, определяем media_type по расширению и создаём запись медиа.
    4) Если пользователь ввёл пустую строку — пропускаем статью.
    """
    connector = aiohttp.TCPConnector(limit=1)  # ограничение 1 одновременного соединения
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        try:
            articles = await fetch_all_articles(session)
        except Exception as e:
            print(f"Не удалось получить список статей: {e!r}")
            return

        if not articles:
            print("На сервере нет ни одной статьи.")
            return

        total = len(articles)
        for idx, article in enumerate(articles, start=1):
            art_id = article["id"]
            title = article["title"]
            print(f"\n[{idx}/{total}] Статья ID={art_id}, Название: «{title}»")

            # Синхронный ввод через run_in_executor, чтобы не блокировать loop
            loop = asyncio.get_event_loop()
            prompt = (
                "Введите имя (или URL) файла медиа для этой статьи "
                "(расширение .png/.svg/.webm; ENTER — пропустить): "
            )
            filename = await loop.run_in_executor(None, lambda: input(prompt).strip())

            if not filename:
                print("→ Пропущено.")
                continue

            # Определяем media_type по расширению
            ext = os.path.splitext(filename)[1].lower()
            if ext == ".png":
                mtype = "png"
            elif ext == ".svg":
                mtype = "svg"
            elif ext == ".webm":
                mtype = "webm"
            else:
                print(f"❌ Неподдерживаемое расширение '{ext}'. "
                      "Ожидалось .png, .svg или .webm. Пропускаем статью.")
                continue

            # Создаём медиа-запись
            try:
                created = await create_media(session, art_id, mtype, filename, sort_order=0)
                media_id = created["id"]
                print(f"✓ Создано медиа (id={media_id}) для статьи ID={art_id}.")
            except Exception as e:
                print(f"❌ Не удалось создать медиа для статьи ID={art_id}: {e!r}")
                # Решаем: перейти к следующей статье или прервать?
                # Сейчас перейдём к следующей:
                continue

            # Чтобы не бить по серверу слишком быстро, немного ждём
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(interactive_media_upload())