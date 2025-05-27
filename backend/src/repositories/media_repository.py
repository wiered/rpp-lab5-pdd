from sqlmodel import Session

class MediaRepository:
    def __init__(self, session: Session):
        self.session = session
