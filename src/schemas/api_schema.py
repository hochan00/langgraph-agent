from pydantic import BaseModel


class CommitDay(BaseModel):
    date: str
    count: int
