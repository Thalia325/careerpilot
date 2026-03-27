from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.bootstrap import ServiceContainer


def get_container(request: Request) -> ServiceContainer:
    return request.app.state.container


def get_db_session(db: Session = Depends(get_db)) -> Session:
    return db

