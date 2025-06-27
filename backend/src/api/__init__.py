from fastapi import APIRouter
from .auth import router as auth_router

from .users import router as users_router
from .categories import router as categories_router
from .articles import router as articles_router
from .media import router as media_router
from .tests import router as tests_router
from .questions import router as questions_router
from .options import router as options_router
from .test_results import router as test_results_router
from .progress import router as progress_router
from .assigments import router as assignments_router
from .roles import router as roles_router

api_router = APIRouter()
api_router.include_router(auth_router, tags=["auth"])

api_router.include_router(users_router, tags=["users"])
api_router.include_router(categories_router, tags=["categories"])
api_router.include_router(articles_router, tags=["articles"])
api_router.include_router(media_router, tags=["media"])
api_router.include_router(tests_router, tags=["tests"])
api_router.include_router(questions_router, tags=["questions"])
api_router.include_router(options_router, tags=["options"])
api_router.include_router(test_results_router, tags=["test-results"])
api_router.include_router(progress_router, tags=["progress"])
api_router.include_router(assignments_router, tags=["assignments"])
api_router.include_router(roles_router, tags=["roles"])

