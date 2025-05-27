from sqlmodel import Session

class TestRepository:
    def __init__(self, session: Session):
        self.session = session
