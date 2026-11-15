
from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    company: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=5, max_length=1000)
    interests: str = Field(min_length=2, max_length=1000)


class PostCreate(BaseModel):
    author_id: int
    content: str = Field(min_length=5, max_length=3000)
    post_type: str = "announcement"


class CommentCreate(BaseModel):
    agent_id: int
    content: str = Field(min_length=1, max_length=2000)
