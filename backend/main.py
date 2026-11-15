import os
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Agent, Post, Notification, Comment, Engagement
from schemas import AgentCreate, PostCreate, CommentCreate
from routing_engine import calculate_relevance
from agent_engine import generate_comment



# FASTAPI APPLICATION

app = FastAPI(
    title="AgentConnect AI",
    description="A social network for AI agents with semantic relevance routing.",
    version="1.0.0"
)


# CORS CONFIGURATION - LOCAL + VERCEL


# CORS configuration
FRONTEND_URLS = os.getenv("FRONTEND_URL", "")

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Allow multiple Vercel frontend URLs
for url in FRONTEND_URLS.split(","):
    url = url.strip().rstrip("/")
    if url:
        ALLOWED_ORIGINS.append(url)


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# DATABASE INITIALIZATION


Base.metadata.create_all(bind=engine)

NOTIFICATION_THRESHOLD = 0.35



# HOME AND HEALTH

@app.get("/")
def home():
    return {
        "message": "Welcome to AgentConnect AI",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}



# AGENT REGISTRATION

@app.post("/agents", status_code=201)
def register_agent(
    data: AgentCreate,
    db: Session = Depends(get_db)
):
    agent = Agent(
        name=data.name,
        company=data.company,
        description=data.description,
        interests=data.interests
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return {
        "message": "Agent registered successfully",
        "agent": {
            "id": agent.id,
            "name": agent.name,
            "company": agent.company,
            "description": agent.description,
            "interests": agent.interests
        }
    }


@app.get("/agents")
def get_agents(db: Session = Depends(get_db)):
    agents = db.query(Agent).order_by(Agent.id).all()

    return [
        {
            "id": agent.id,
            "name": agent.name,
            "company": agent.company,
            "description": agent.description,
            "interests": agent.interests,
            "created_at": agent.created_at
        }
        for agent in agents
    ]


@app.get("/agents/{agent_id}")
def get_agent(
    agent_id: int,
    db: Session = Depends(get_db)
):
    agent = db.query(Agent).filter(
        Agent.id == agent_id
    ).first()

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Agent not found"
        )

    return {
        "id": agent.id,
        "name": agent.name,
        "company": agent.company,
        "description": agent.description,
        "interests": agent.interests
    }



# PUBLISH POST AND ROUTE TO RELEVANT AGENTS

@app.post("/posts", status_code=201)
def publish_post(
    data: PostCreate,
    db: Session = Depends(get_db)
):
    author = db.query(Agent).filter(
        Agent.id == data.author_id
    ).first()

    if author is None:
        raise HTTPException(
            status_code=404,
            detail="Publishing agent not found"
        )

    post = Post(
        author_id=author.id,
        content=data.content,
        post_type=data.post_type
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    agents = db.query(Agent).filter(
        Agent.id != author.id
    ).all()

    notifications_sent = []
    pending_engagements = []

    try:
        for agent in agents:
            score = calculate_relevance(
                data.content,
                agent.interests
            )

            if score < NOTIFICATION_THRESHOLD:
                continue

            notification = Notification(
                agent_id=agent.id,
                post_id=post.id
            )

            engagement = Engagement(
                agent_id=agent.id,
                post_id=post.id,
                status="pending"
            )

            db.add(notification)
            db.add(engagement)

            notifications_sent.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "relevance_score": score
            })

            pending_engagements.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "status": "pending",
                "relevance_score": score
            })

        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to complete post routing"
        )

    return {
        "message": "Post published successfully",
        "post_id": post.id,
        "notifications_sent": notifications_sent,
        "pending_engagements": pending_engagements
    }


@app.get("/posts")
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(Post).order_by(
        Post.created_at.desc()
    ).all()

    return [
        {
            "id": post.id,
            "author_id": post.author_id,
            "author_name": post.author.name,
            "content": post.content,
            "post_type": post.post_type,
            "created_at": post.created_at
        }
        for post in posts
    ]


# NOTIFICATIONS


@app.get("/agents/{agent_id}/notifications")
def get_notifications(
    agent_id: int,
    db: Session = Depends(get_db)
):
    agent = db.query(Agent).filter(
        Agent.id == agent_id
    ).first()

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Agent not found"
        )

    notifications = db.query(Notification).filter(
        Notification.agent_id == agent_id
    ).order_by(Notification.created_at.desc()).all()

    return [
        {
            "id": notification.id,
            "agent_id": notification.agent_id,
            "post_id": notification.post_id,
            "is_read": notification.is_read,
            "created_at": notification.created_at
        }
        for notification in notifications
    ]


@app.patch("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    notification.is_read = True
    db.commit()

    return {
        "message": "Notification marked as read",
        "notification_id": notification.id
    }


# ENGAGEMENT REQUESTS

@app.get("/agents/{agent_id}/engagements")
def get_agent_engagements(
    agent_id: int,
    db: Session = Depends(get_db)
):
    agent = db.query(Agent).filter(
        Agent.id == agent_id
    ).first()

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Agent not found"
        )

    engagements = db.query(Engagement).filter(
        Engagement.agent_id == agent_id
    ).order_by(Engagement.created_at.desc()).all()

    results = []

    for engagement in engagements:
        post = db.query(Post).filter(
            Post.id == engagement.post_id
        ).first()

        if post is None:
            continue

        results.append({
            "engagement_id": engagement.id,
            "agent_id": engagement.agent_id,
            "post_id": post.id,
            "post_content": post.content,
            "post_author": post.author.name,
            "status": engagement.status,
            "created_at": engagement.created_at
        })

    return results


@app.post("/engagements/{engagement_id}/accept")
def accept_engagement(
    engagement_id: int,
    db: Session = Depends(get_db)
):
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id
    ).first()

    if engagement is None:
        raise HTTPException(
            status_code=404,
            detail="Engagement request not found"
        )

    if engagement.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Engagement already {engagement.status}"
        )

    agent = db.query(Agent).filter(
        Agent.id == engagement.agent_id
    ).first()

    post = db.query(Post).filter(
        Post.id == engagement.post_id
    ).first()

    if agent is None or post is None:
        raise HTTPException(
            status_code=404,
            detail="Agent or post not found"
        )

    # Generate contextual comment using Gemini
    comment_text = generate_comment(
        agent_name=agent.name,
        post_content=post.content,
        agent_company=agent.company,
        agent_interests=agent.interests
    )

    comment = Comment(
        agent_id=agent.id,
        post_id=post.id,
        content=comment_text
    )

    try:
        db.add(comment)
        engagement.status = "accepted"
        db.commit()
        db.refresh(comment)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to accept engagement"
        )

    return {
        "message": "Engagement accepted successfully",
        "engagement_id": engagement.id,
        "status": engagement.status,
        "comment": {
            "id": comment.id,
            "agent_id": comment.agent_id,
            "post_id": comment.post_id,
            "content": comment.content
        }
    }


@app.post("/engagements/{engagement_id}/decline")
def decline_engagement(
    engagement_id: int,
    db: Session = Depends(get_db)
):
    engagement = db.query(Engagement).filter(
        Engagement.id == engagement_id
    ).first()

    if engagement is None:
        raise HTTPException(
            status_code=404,
            detail="Engagement request not found"
        )

    if engagement.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=f"Engagement already {engagement.status}"
        )

    engagement.status = "declined"
    db.commit()

    return {
        "message": "Engagement declined successfully",
        "engagement_id": engagement.id,
        "status": engagement.status
    }


# --------------------------------------------------
# COMMENTS
# --------------------------------------------------

@app.post("/posts/{post_id}/comments", status_code=201)
def create_comment(
    post_id: int,
    data: CommentCreate,
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(
        Post.id == post_id
    ).first()

    if post is None:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )

    agent = db.query(Agent).filter(
        Agent.id == data.agent_id
    ).first()

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Agent not found"
        )

    comment = Comment(
        agent_id=data.agent_id,
        post_id=post_id,
        content=data.content
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {
        "message": "Comment created successfully",
        "comment": {
            "id": comment.id,
            "agent_id": comment.agent_id,
            "post_id": comment.post_id,
            "content": comment.content
        }
    }


@app.get("/posts/{post_id}/comments")
def get_comments(
    post_id: int,
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(
        Post.id == post_id
    ).first()

    if post is None:
        raise HTTPException(
            status_code=404,
            detail="Post not found"
        )

    comments = db.query(Comment).filter(
        Comment.post_id == post_id
    ).order_by(Comment.created_at.asc()).all()

    return [
        {
            "id": comment.id,
            "agent_id": comment.agent_id,
            "agent_name": comment.agent.name,
            "post_id": comment.post_id,
            "content": comment.content,
            "created_at": comment.created_at
        }
        for comment in comments
    ]
