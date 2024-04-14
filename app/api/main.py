import json
import math

from fastapi import FastAPI, Depends, HTTPException, Response, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic_settings import BaseSettings
import secrets
from typing import Union, Annotated

from app.es import async_client
from app.services.decision import DecisionService


class Settings(BaseSettings):
    app_name: str = "CASS API"
    admin_password: str
    admin_user: str
    elastic_certs_path: str
    elastic_user: str
    elastic_password: str
    elastic_url: str
    elastic_index: str
    page_size: int = 100


class User:
    def __init__(self, **params):
        self.__dict__ = params


settings = Settings()
app = FastAPI()
security = HTTPBasic()
decision_service = DecisionService(settings.elastic_index)


def get_user(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    """Checks if a registered user."""
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = settings.admin_user.encode("utf8")
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = settings.admin_password.encode("utf8")
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return User(username=settings.admin_user, is_admin=True)


def get_admin(user: Annotated[User, Depends(get_user)]):
    """Checks if the use is admin."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user


@app.get("/info")
async def info(user: Annotated[User, Depends(get_admin)]):
    """Provides information about the backend."""
    return {
        "app_name": settings.app_name,
        "elastic_search_host": settings.elastic_url,
        "elastic_index": settings.elastic_index,
    }


@app.get("/summary")
async def get_decision_summary(
    user: Annotated[User, Depends(get_user)], page: int | None = None
):
    """List of rulling for all court."""
    cursor = (page - 1) * settings.page_size if page else 0
    decisions = []
    total = await decision_service.count
    count = 0
    total_page = math.ceil(total / settings.page_size)
    async for decision in decision_service.get_summary(cursor, settings.page_size):
        count += 1
        decisions.append(dict(decision))
    return {
        "stats": {
            "count": count,
            "total": total,
            "page": page or 1,
            "page_size": settings.page_size,
            "total_page": total_page,
        },
        "decisions": decisions,
    }


@app.get("/{code_chambre}/summary")
async def get_decision_summary_for_court(
    code_chambre: str, user: Annotated[User, Depends(get_user)], page: int | None = None
):
    """List of rulling for a specific court."""
    cursor = (page - 1) * settings.page_size if page else 0
    decisions = []
    total = await decision_service.count_court(code_chambre)
    count = 0
    total_page = math.ceil(total / settings.page_size)
    async for decision in decision_service.get_summary_for_court(
        code_chambre, cursor, settings.page_size
    ):
        count += 1
        decisions.append(dict(decision))
    return {
        "stats": {
            "count": count,
            "total": total,
            "page": page or 1,
            "page_size": settings.page_size,
            "total_page": total_page,
        },
        "decisions": decisions,
    }


@app.get("/decision/{decision_id}")
async def get_decision(
    decision_id, user: Annotated[User, Depends(get_user)], page: int | None = None
):
    """Get a specific decision by its identifier."""
    decision = await decision_service.get_decision(decision_id)
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doesn't exist",
        )
    return dict(decision)


@app.get("/search")
async def search_decision(
    query: str, user: Annotated[User, Depends(get_user)], page: int | None = None
):
    """Fulltext search on the content of court decision."""
    res = []
    async for score, dec in decision_service.fulltext_search(query):
        res.append({"score": score, "decision": dict(dec)})
    return {"result": res}
