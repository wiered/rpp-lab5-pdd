from sqlmodel import Session

class QuestionRepository:
    def __init__(self, session: Session):
        self.session = session
