from sqlmodel import Session

class ProgressRepository:
    def __init__(self, session: Session):
        self.session = session
