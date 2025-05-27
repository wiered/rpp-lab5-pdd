from sqlmodel import Session

class CategoryRepository:
    def __init__(self, session: Session):
        self.session = session
