from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import shutil
import os
import pathlib
from typing import Optional
from datetime import datetime

from database import get_db
from models.post import Post, Comment
from schemas.post import PostCreate

from services.upload_file import upload_file
from services.user import get_user_by_username
from services.post import get_post_by_id

router = APIRouter(prefix="/post", tags=["Post"])

temp_dir = pathlib.Path("Temp/temp_files")
temp_dir.mkdir(parents=True, exist_ok=True)

    
# 获取帖子列表
@router.get("/list", description="获取帖子列表")
def get_post_list(
    db: Session = Depends(get_db)
):
    try:
        total = db.query(Post).count()
        posts = db.query(Post).all()
        data = []
        for post in posts:
            data.append({
                "id": post.id,
                "title": post.title,
                "author_id": post.author_id,
                "time": post.time.isoformat(),
                "file_list": post.file_list
            })
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "获取成功",
                "data": {
                    "total": total,
                    "posts": data
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# 获取帖子详情
@router.get("/{post_id}", description="根据帖子ID获取帖子详情")
def get_post_detail(
    post_id: int = Path(..., description="帖子ID"),
    db: Session = Depends(get_db)
):
    try:
        post = get_post_by_id(db, post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在")
        
        data = {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "author_id": post.author_id,
            "time": post.time.isoformat(),
            "like_count": post.like_count,  
            "comment_count": post.comment_count,
            "file_list": post.file_list
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "获取成功",
                "data": data
            }
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# 点赞帖子
@router.post("/{post_id}/like", description="点赞帖子")
def like_post(
    post_id: int = Path(..., description="帖子ID"),
    db: Session = Depends(get_db)
):
    try:
        post = get_post_by_id(db, post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在")
        
        post.like_count += 1
        db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "点赞成功",
                "data": {
                    "like_count": post.like_count
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# 发布帖子
@router.post("/create", description="发布帖子")
def create_post(
    post: PostCreate = Depends(PostCreate.as_form),
    files: Optional[list[UploadFile]] = File(None, description="支持图片/视频文件"),
    db: Session = Depends(get_db)
):
    try: 
        user = get_user_by_username(db, post.author_name)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
        
        file_urls = []
        if files:
            for file in files:
                file_path = os.path.join(temp_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                file_url = upload_file(file_path)
                file_urls.append(file_url)
                os.remove(file_path)

        post_db = Post(
            title=post.title,
            content=post.content,
            author_id=user.id,
            time=post.time,
            like_count=post.like_count,
            comment_count=post.comment_count,
            file_list=file_urls
        )
        # 保存到数据库
        try:
            db.add(post_db)
            db.commit()
            db.refresh(post_db)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="发布失败:" + str(e))

        return JSONResponse(
            status_code=status.HTTP_201_CREATED, 
            content={
                "message": "发布成功",
                "data": {
                    "id": post_db.id,
                    "title": post_db.title,
                    "author_id": post_db.author_id,
                    "time": post_db.time.isoformat(),
                    "file_list": post_db.file_list
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# 删除帖子
@router.delete("/{post_id}", description="删除帖子")
def delete_post(
    post_id: int = Path(..., description="帖子ID"),
    db: Session = Depends(get_db)
):
    try:
        post = get_post_by_id(db, post_id)
        if not post:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="帖子不存在")
        
        db.delete(post)
        db.commit()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "删除成功"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))