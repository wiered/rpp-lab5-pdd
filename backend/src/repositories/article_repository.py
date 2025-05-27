from sqlmodel import Session

class ArticleRepository:
    def __init__(self, session: Session):
        self.session = session
