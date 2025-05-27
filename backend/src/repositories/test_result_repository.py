from sqlmodel import Session

class TestResultRepository:
    def __init__(self, session: Session):
        self.session = session
