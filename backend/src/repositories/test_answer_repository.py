from sqlmodel import Session

class TestAnswerRepository:
    def __init__(self, session: Session):
        self.session = session
