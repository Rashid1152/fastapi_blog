from typing import List
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import redis
from app.core.config import settings
from app.db.init_db import get_db
from app.models.models import Post, User
from app.schemas.post import PostCreate, PostUpdate, Post as PostSchema
from app.api.auth import oauth2_scheme

router = APIRouter()
redis_client = redis.from_url(settings.REDIS_URL)

async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    from jose import jwt, JWTError
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/posts", response_model=PostSchema)
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_post = Post(**post.model_dump(), author_id=current_user.id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    # Invalidate cache
    redis_client.delete("all_posts")
    return db_post

@router.get("/posts", response_model=List[PostSchema])
def read_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Try to get from cache
    cached_posts = redis_client.get("all_posts")
    if cached_posts:
        return json.loads(cached_posts)
    
    # If not in cache, get from database
    posts = db.query(Post).all()
    # Cache the results
    redis_client.setex("all_posts", 300, json.dumps([{
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "created_at": post.created_at.isoformat(),
        "author_id": post.author_id
    } for post in posts]))
    return posts

@router.get("/posts/{post_id}", response_model=PostSchema)
def read_post(
    post_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.put("/posts/{post_id}", response_model=PostSchema)
def update_post(
    post_id: int,
    post_update: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if db_post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this post")
    
    for key, value in post_update.model_dump().items():
        setattr(db_post, key, value)
    
    db.commit()
    db.refresh(db_post)
    # Invalidate cache
    redis_client.delete("all_posts")
    return db_post

@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if db_post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    
    db.delete(db_post)
    db.commit()
    # Invalidate cache
    redis_client.delete("all_posts")
    return {"message": "Post deleted successfully"} 