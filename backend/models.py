
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    company = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    interests = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="agent")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    content = Column(Text, nullable=False)
    post_type = Column(String(50), default="announcement")
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("Agent", back_populates="posts")
    comments = relationship("Comment", back_populates="post")


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("agent_id", "post_id", name="unique_agent_post_notification"),
    )

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", back_populates="comments")
    post = relationship("Post", back_populates="comments")


class Engagement(Base):
    __tablename__ = "engagements"

    __table_args__ = (
        UniqueConstraint(
            "agent_id",
            "post_id",
            name="unique_agent_post_engagement"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    agent_id = Column(
        Integer,
        ForeignKey("agents.id"),
        nullable=False
    )

    post_id = Column(
        Integer,
        ForeignKey("posts.id"),
        nullable=False
    )

    status = Column(
        String(20),
        default="pending",
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
