import asyncio
import aiohttp
from typing import Any, Dict, List, Optional


class AsyncApiClient:
    """
    Async REST client for interfacing with the REST API using aiohttp.
    """

    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.headers = {'Content-Type': 'application/json'}
        self.token: Optional[str] = None
        if token:
            self.set_token(token)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self):
        """Close the underlying HTTP session."""
        await self.session.close()

    def set_token(self, token: str):
        """Set the Authorization header for subsequent requests."""
        self.token = token
        self.headers['Authorization'] = f'Bearer {token}'

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None
    ) -> Any:
        if self.session is None:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}{path}"

        async with self.session.request(
            method, url, headers=self.headers, params=params, json=json
        ) as resp:
            resp.raise_for_status()
            if resp.status == 204:
                return None
            return await resp.json()

    async def ensure_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    # Authentication
    async def register(self, username: str, password: str) -> Dict[str, Any]:
        """
        Register a new user and set the received JWT for future requests.
        """
        await self.ensure_session()
        payload = {'username': username, 'password': password}
        token_data = await self._request('POST', '/auth/register', json=payload)
        self.set_token(token_data['access_token'])
        return token_data

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Log in with username/password, receive and set JWT for future requests.
        """
        await self.ensure_session()
        url = f"{self.base_url}/auth/login"
        form = {'username': username, 'password': password}
        # OAuth2 form requires x-www-form-urlencoded
        headers = {k: v for k, v in self.headers.items() if k != 'Content-Type'}
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        async with self.session.post(url, headers=headers, data=form) as resp:
            print(resp.text)
            resp.raise_for_status()
            token_data = await resp.json()
        self.set_token(token_data['access_token'])
        return token_data

    async def me(self) -> Dict[str, Any]:
        """
        Get current user info. Requires a valid JWT set.
        """
        return await self._request('GET', '/auth/me')

    # Articles
    async def list_articles(self) -> List[Dict[str, Any]]:
        return await self._request('GET', '/articles')

    # Articles
    async def list_articles(self) -> List[Dict[str, Any]]:
        return await self._request('GET', '/articles')

    async def get_article(self, article_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/articles/{article_id}')

    async def list_articles_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        return await self._request('GET', f'/articles/category/{category_id}')

    async def create_article(
        self, category_id: int, title: str, content: str, content_type: str
    ) -> Dict[str, Any]:
        payload = {
            'category_id': category_id,
            'title': title,
            'content': content,
            'content_type': content_type
        }
        return await self._request('POST', '/articles', json=payload)

    async def update_article(
        self,
        article_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {}
        if title is not None:
            payload['title'] = title
        if content is not None:
            payload['content'] = content
        if content_type is not None:
            payload['content_type'] = content_type
        return await self._request('PUT', f'/articles/{article_id}', json=payload)

    async def delete_article(self, article_id: int) -> None:
        return await self._request('DELETE', f'/articles/{article_id}')

    # Assignments
    async def list_assignments(
        self,
        user_id: Optional[int] = None,
        group_id: Optional[int] = None,
        category_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if user_id is not None:
            params['user_id'] = user_id
        if group_id is not None:
            params['group_id'] = group_id
        if category_id is not None:
            params['category_id'] = category_id
        return await self._request('GET', '/assignments', params=params)

    async def get_assignment(self, assignment_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/assignments/{assignment_id}')

    async def create_assignment_for_user(
        self,
        assigned_by: int,
        category_id: int,
        user_id: int,
        assigned_at: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {
            'assigned_by': assigned_by,
            'category_id': category_id,
            'user_id': user_id
        }
        if assigned_at:
            payload['assigned_at'] = assigned_at
        return await self._request('POST', '/assignments/user', json=payload)

    async def create_assignment_for_group(
        self,
        assigned_by: int,
        category_id: int,
        group_id: int,
        assigned_at: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {
            'assigned_by': assigned_by,
            'category_id': category_id,
            'group_id': group_id
        }
        if assigned_at:
            payload['assigned_at'] = assigned_at
        return await self._request('POST', '/assignments/group', json=payload)

    async def update_assignment(
        self,
        assignment_id: int,
        user_id: Optional[int] = None,
        group_id: Optional[int] = None
    ) -> Dict[str, Any]:
        payload = {}
        if user_id is not None:
            payload['user_id'] = user_id
        if group_id is not None:
            payload['group_id'] = group_id
        return await self._request('PUT', f'/assignments/{assignment_id}', json=payload)

    async def delete_assignment(self, assignment_id: int) -> None:
        return await self._request('DELETE', f'/assignments/{assignment_id}')

    # Categories
    async def list_categories(self) -> List[Dict[str, Any]]:
        return await self._request('GET', '/categories')

    async def get_category_tree(self) -> List[Dict[str, Any]]:
        return await self._request('GET', '/categories/tree')

    async def get_category(self, category_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/categories/{category_id}')

    async def create_category(
        self,
        title: str,
        parent_id: Optional[int] = None
    ) -> Dict[str, Any]:
        payload = {'title': title}
        if parent_id is not None:
            payload['parent_id'] = parent_id
        return await self._request('POST', '/categories', json=payload)

    async def update_category(
        self,
        category_id: int,
        title: Optional[str] = None,
        parent_id: Optional[int] = None
    ) -> Dict[str, Any]:
        payload = {}
        if title is not None:
            payload['title'] = title
        if parent_id is not None:
            payload['parent_id'] = parent_id
        return await self._request('PUT', f'/categories/{category_id}', json=payload)

    async def delete_category(self, category_id: int) -> None:
        return await self._request('DELETE', f'/categories/{category_id}')

    # Media
    async def list_media(self, article_id: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {}
        if article_id is not None:
            params['article_id'] = article_id
        return await self._request('GET', '/media', params=params)

    async def get_media(self, media_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/media/{media_id}')

    async def list_media_by_article(self, article_id: int) -> List[Dict[str, Any]]:
        return await self._request('GET', f'/media/article/{article_id}')

    async def create_media(
        self,
        article_id: int,
        media_type: str,
        url: str,
        sort_order: int = 0
    ) -> Dict[str, Any]:
        payload = {
            'article_id': article_id,
            'media_type': media_type,
            'url': url,
            'sort_order': sort_order
        }
        return await self._request('POST', '/media', json=payload)

    async def update_media(
        self,
        media_id: int,
        media_type: Optional[str] = None,
        url: Optional[str] = None,
        sort_order: Optional[int] = None
    ) -> Dict[str, Any]:
        payload = {}
        if media_type is not None:
            payload['media_type'] = media_type
        if url is not None:
            payload['url'] = url
        if sort_order is not None:
            payload['sort_order'] = sort_order
        return await self._request('PUT', f'/media/{media_id}', json=payload)

    async def delete_media(self, media_id: int) -> None:
        return await self._request('DELETE', f'/media/{media_id}')

    # Answer Options
    async def list_options(self, question_id: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {}
        if question_id is not None:
            params['question_id'] = question_id
        return await self._request('GET', '/options', params=params)

    async def get_option(self, option_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/options/{option_id}')

    async def list_options_by_question(self, question_id: int) -> List[Dict[str, Any]]:
        return await self._request('GET', f'/options/question/{question_id}')

    async def create_option(
        self,
        question_id: int,
        text: str,
        is_correct: bool = False
    ) -> Dict[str, Any]:
        payload = {'question_id': question_id, 'text': text, 'is_correct': is_correct}
        return await self._request('POST', '/options', json=payload)

    async def update_option(
        self,
        option_id: int,
        text: Optional[str] = None,
        is_correct: Optional[bool] = None
    ) -> Dict[str, Any]:
        payload = {}
        if text is not None:
            payload['text'] = text
        if is_correct is not None:
            payload['is_correct'] = is_correct
        return await self._request('PUT', f'/options/{option_id}', json=payload)

    async def delete_option(self, option_id: int) -> None:
        return await self._request('DELETE', f'/options/{option_id}')

    # Progress
    async def list_progress(
        self,
        user_id: Optional[int] = None,
        article_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if user_id is not None:
            params['user_id'] = user_id
        if article_id is not None:
            params['article_id'] = article_id
        return await self._request('GET', '/progress', params=params)

    async def get_progress(self, progress_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/progress/{progress_id}')

    async def create_progress(
        self,
        user_id: int,
        article_id: int,
        status: str = "not_started"
    ) -> Dict[str, Any]:

        payload = {'user_id': user_id, 'article_id': article_id, 'status': status}
        return await self._request('POST', '/progress', json=payload)

    async def update_progress(
        self,
        user_id: int,
        article_id: int,
        status: str
    ) -> Dict[str, Any]:
        payload = {'user_id': user_id, 'article_id': article_id, 'status': status}
        return await self._request('PUT', '/progress', json=payload)

    async def delete_progress(self, progress_id: int) -> None:
        return await self._request('DELETE', f'/progress/{progress_id}')

    # Questions
    async def list_questions(self) -> List[Dict[str, Any]]:
        return await self._request('GET', '/questions')

    async def get_question(self, question_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/questions/{question_id}')

    async def list_questions_by_test(self, test_id: int) -> List[Dict[str, Any]]:
        return await self._request('GET', f'/questions/test/{test_id}')

    async def get_test_full(self, test_id: int) -> Dict[str, Any]:
        """
        Получить полный тест вместе с вопросами и вариантами по его идентификатору.
        Делает GET /tests/full/{test_id}.
        """
        return await self._request('GET', f'/tests/full/{test_id}')

    async def create_question(
        self,
        test_id: int,
        text: str,
        weight: int = 1
    ) -> Dict[str, Any]:
        payload = {'test_id': test_id, 'text': text, 'weight': weight}
        return await self._request('POST', '/questions', json=payload)

    async def update_question(
        self,
        question_id: int,
        text: Optional[str] = None,
        weight: Optional[int] = None
    ) -> Dict[str, Any]:
        payload = {}
        if text is not None:
            payload['text'] = text
        if weight is not None:
            payload['weight'] = weight
        return await self._request('PUT', f'/questions/{question_id}', json=payload)

    async def delete_question(self, question_id: int) -> None:
        return await self._request('DELETE', f'/questions/{question_id}')

    # Test Results
    async def list_test_results(
        self,
        user_id: Optional[int] = None,
        test_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if user_id is not None:
            params['user_id'] = user_id
        if test_id is not None:
            params['test_id'] = test_id
        return await self._request('GET', '/test-results', params=params)

    async def get_test_result(self, result_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/test-results/{result_id}')

    async def list_test_result_answers(self, result_id: int) -> List[Dict[str, Any]]:
        return await self._request('GET', f'/test-results/{result_id}/answers')

    async def create_test_result(
        self,
        user_id: int,
        test_id: int,
        score: float,
        max_score: float,
        passed: bool,
        answers: List[Dict[str, int]]
    ) -> Dict[str, Any]:
        payload = {
            'user_id': user_id,
            'test_id': test_id,
            'score': score,
            'max_score': max_score,
            'passed': passed,
            'answers': answers
        }
        return await self._request('POST', '/test-results', json=payload)

    async def delete_test_result(self, result_id: int) -> None:
        return await self._request('DELETE', f='/test-results/{result_id}')

    # Tests
    async def list_tests(self) -> List[Dict[str, Any]]:
        return await self._request('GET', '/tests')

    async def get_test(self, test_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/tests/{test_id}')

    async def list_tests_by_category(self, category_id: int) -> List[Dict[str, Any]]:
        return await self._request('GET', f'/tests/category/{category_id}')

    async def create_test(
        self,
        category_id: int,
        title: str,
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        payload = {'category_id': category_id, 'title': title, 'max_attempts': max_attempts}
        return await self._request('POST', '/tests', json=payload)

    async def update_test(
        self,
        test_id: int,
        title: Optional[str] = None,
        max_attempts: Optional[int] = None
    ) -> Dict[str, Any]:
        payload = {}
        if title is not None:
            payload['title'] = title
        if max_attempts is not None:
            payload['max_attempts'] = max_attempts
        return await self._request('PUT', f'/tests/{test_id}', json=payload)

    async def delete_test(self, test_id: int) -> None:
        return await self._request('DELETE', f'/tests/{test_id}')

    async def import_tests(self, tests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return await self._request('POST', '/tests/import', json=tests)

    async def export_tests(self) -> List[Dict[str, Any]]:
        return await self._request('GET', '/tests/export')

    # Users
    async def list_users(self, role: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if role:
            params['role'] = role
        return await self._request('GET', '/users', params=params)

    async def get_user(self, user_id: int) -> Dict[str, Any]:
        return await self._request('GET', f'/users/{user_id}')

    async def update_user(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        role_id: Optional[int] = None
    ) -> Dict[str, Any]:
        payload = {}

        if full_name is not None:
            payload['full_name'] = full_name
        if role_id is not None:
            payload['role_id'] = role_id
        print(payload)
        return await self._request('PUT', f'/users/{user_id}', json=payload)

    async def delete_user(self, user_id: int) -> None:
        return await self._request('DELETE', f'/users/{user_id}')

    async def export_users(self) -> List[Dict[str, Any]]:
        return await self._request('POST', '/users/export')

    async def import_users(self, users: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return await self._request('POST', '/users/import', json=users)

    async def list_roles(self) -> List[Dict[str, Any]]:
        """
        Получить список всех ролей.
        Делает GET /roles и возвращает список словарей с данными ролей.
        """
        return await self._request('GET', '/roles')

    async def close(self):
        try:
            await self.session.close()
        except:
            pass