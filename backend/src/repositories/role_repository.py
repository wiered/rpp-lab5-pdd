from sqlmodel import Session

class RoleRepository:
    def __init__(self, session: Session):
        self.session = session
