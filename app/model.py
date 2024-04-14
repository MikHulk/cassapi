"""The Domain model."""

from pydantic import BaseModel


class Decision(BaseModel):
    title: str
    identifier: str
    numero: str
    paragraphes: list[list[str]]
    chambre: str
    code_chambre: str


class DecisionSummary(BaseModel):
    title: str
    identifier: str
    code_chambre: str
