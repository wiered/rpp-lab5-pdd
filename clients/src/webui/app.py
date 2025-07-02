import json
import os
from pathlib import Path
from typing import Optional

import markdown
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from src.rest_client import AsyncApiClient
from src.tester import WebTester

load_dotenv()

SERVER_PORT = os.environ.get("SERVER_PORT")

API_BASE = f"http://127.0.0.1:{SERVER_PORT}/api"

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="CHANGE_THIS_TO_SECRET")

app.mount("/static", StaticFiles(directory="./src/webui/static"), name="static")

media_dir = Path(__file__).parent / "media"
print(media_dir)
app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")
templates = Jinja2Templates(directory="./src/webui/templates")

client = AsyncApiClient(API_BASE)
def get_client(request: Request) -> AsyncApiClient:
    token = request.session.get("token")
    if token:
        client.set_token(token)
    return client

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    if "token" not in request.session:
        return RedirectResponse("/login")
    return RedirectResponse("/categories")

# --- Login / Register ---
@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    cli: AsyncApiClient = Depends(get_client)
):
    try:
        await cli.login(username, password)
        request.session["token"] = cli.token
        return RedirectResponse("/categories", status_code=303)
    except Exception:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Login failed"})

@app.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    cli: AsyncApiClient = Depends(get_client)
):
    try:
        await cli.register(username, password)
        msg = "Registered successfully. Please login."
    except Exception:
        msg = "Registration failed."
    return templates.TemplateResponse("login.html", {"request": request, "error": msg})

# --- Categories / Articles listing ---
@app.get("/categories", response_class=HTMLResponse)
@app.get("/categories/{parent_id}", response_class=HTMLResponse)
async def view_categories(
    request: Request,
    parent_id: Optional[int] = None,
    cli: AsyncApiClient = Depends(get_client),
):
    tree = await cli.get_category_tree()

    # find node in tree
    def find_node(nodes: list[dict], target: int) -> dict|None:
        for n in nodes:
            if n["id"] == target:
                return n
            found = find_node(n.get("children", []), target)
            if found:
                return found
        return None

    if parent_id is None:
        # top-level categories
        sidebar_items = [
            {"id": c["id"], "title": c["title"], "type": "category"}
            for c in tree
        ]
        heading = "Выберите категорию"
    else:
        node = find_node(tree, parent_id)
        children = node.get("children", []) if node else []
        if children:
            # show subcategories
            sidebar_items = [
                {"id": c["id"], "title": c["title"], "type": "category"}
                for c in children
            ]
            heading = "Подкатегории"
        else:
            # no subcategories: list articles and tests
            articles = await cli.list_articles_by_category(parent_id)
            tests    = await cli.list_tests_by_category(parent_id)
            sidebar_items = (
                [{"id": a["id"], "title": a["title"], "type": "article"} for a in articles]
                + [{"id": t["id"], "title": t["title"], "type": "test"} for t in tests]
            )
            heading = "Материалы и тесты"

    return templates.TemplateResponse("categories.html", {
        "request": request,
        "sidebar_items": sidebar_items,
        "parent_id": parent_id,
        "active_type": "category",
        "active_id": parent_id,
        "heading": heading,
    })

# --- Просмотр статьи ---
@app.get("/article/{article_id}", response_class=HTMLResponse)
async def view_article(
    request: Request,
    article_id: int,
    cli: AsyncApiClient = Depends(get_client),
):
    art = await cli.get_article(article_id)
    if art["content_type"] == "markdown":
        content = markdown.markdown(art["content"])
    else:
        content = art["content"]
    media = await cli.list_media(article_id)
    for m in media:
        m["url"] = f"/media/{m['url']}"

    # в левой панели показываем статьи той же категории
    cat_id = art.get("category_id")
    articles = await cli.list_articles_by_category(cat_id)
    sidebar_items = [
        {"id": a["id"], "title": a["title"], "type": "article"}
        for a in articles
    ]

    return templates.TemplateResponse("article.html", {
        "request": request,
        "sidebar_items": sidebar_items,
        "active_type": "article",
        "active_id": article_id,
        "article": art,
        "content": content,
        "media": media,
    })

@app.get("/test/{test_id}", response_class=HTMLResponse)
async def view_test(
    request: Request,
    test_id: int,
    cli: AsyncApiClient = Depends(get_client),
):

    # fetch test info
    test = await cli.get_test(test_id)

    # fetch questions and options
    questions = await cli.list_questions_by_test(test_id)
    q_with_opts = []
    for q in questions:
        opts = await cli.list_options_by_question(q["id"])
        q_with_opts.append({"question": q, "options": opts})

    tester = WebTester(
        test_id=test["id"],
        category_id=test["category_id"],
        title=test["title"],
        max_attempts=test["max_attempts"],
        questions=q_with_opts
    )

    # sidebar: show same list as for article for that category
    cat_id = test.get("category_id")
    articles = await cli.list_articles_by_category(cat_id)
    tests    = await cli.list_tests_by_category(cat_id)
    sidebar_items = (
        [{"id": a["id"], "title": a["title"], "type": "article"} for a in articles]
        + [{"id": t["id"], "title": t["title"], "type": "test"} for t in tests]
    )

    state = {
        "test_id":      tester.test_id,
        "category_id":  tester.category_id,
        "title":        tester.title,
        "max_attempts": tester.max_attempts,
        "questions":    tester.questions,
        "current_index": 0,
        "score":         0,
    }
    first_q = tester.questions[0]

    return templates.TemplateResponse("test.html", {
        "request": request,
        "sidebar_items": sidebar_items,
        "active_type": "test",
        "active_id": test_id,
        "heading": "Материалы и тесты",
        "tester": tester,
        "tester_state": json.dumps(state),
        "questions": first_q,
    })

@app.post("/test/{test_id}", response_class=HTMLResponse)
async def submit_test(request: Request,
                      test_id: int,
                      tester_json: str = Form(...),
                      answer: int       = Form(...),
):
    # 1. reconstruct
    state = json.loads(tester_json)
    print(f"state: {state}")
    tester = WebTester(
        test_id=state["test_id"],
        category_id=state["category_id"],
        title=state["title"],
        max_attempts=state["max_attempts"],
        questions=state["questions"],
    )
    # restore pointer & score into the *private* attrs the class really uses
    idx = state.get("current_index", 0)
    tester._idx = idx
    tester.score = state.get("score", 0)

    # 2. record the answer
    current = tester.questions[idx]
    qid = str(current["id"])
    tester.answer(qid, answer)

    # 3. grade
    for opt in current["options"]:
        if opt["id"] == answer and opt.get("is_correct"):
            tester.score += current["weight"]
            break

    # 4. advance the iterator
    tester._idx += 1
    next_idx = tester._idx

    # 5. either show next…
    if next_idx < len(tester.questions):
        next_q = tester.questions[next_idx]
        new_state = {
            "test_id":       tester.test_id,
            "category_id":   tester.category_id,
            "title":         tester.title,
            "max_attempts":  tester.max_attempts,
            "questions":     tester.questions,
            "current_index": next_idx,
            "score":         tester.score,
        }
        return templates.TemplateResponse("test.html", {
            "request":      request,
            "tester": tester,
            "tester_state": json.dumps(new_state),
            "questions":    next_q,
        })

    # 6. …or render results
    else:
        max_score = sum(q["weight"] for q in tester.questions)
        return templates.TemplateResponse("test_result.html", {
            "request":   request,
            "score":     tester.score,
            "max_score": max_score,
            "tester": tester,
        })

# --- Stub pages ---
@app.get("/personal", response_class=HTMLResponse)
async def personal_page(request: Request):
    return templates.TemplateResponse("personal.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})
