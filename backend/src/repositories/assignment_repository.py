from sqlmodel import Session

class AssignmentRepository:
    def __init__(self, session: Session):
        self.session = session
