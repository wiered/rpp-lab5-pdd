from sqlmodel import Session

class AnswerOptionRepository:
    def __init__(self, session: Session):
        self.session = session
