from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import shutil
import os
import pathlib
from typing import Optional

from database import get_db
from models.user import User
from schemas.user import UserCreate

from services.upload_file import upload_file
from services.user import get_user_by_id, get_user_by_username, create_user, update_user, delete_user

router = APIRouter(prefix="/user", tags=["User"])

temp_dir = pathlib.Path("Temp/temp_audio_files")
temp_dir.mkdir(parents=True, exist_ok=True)


# 注册
@router.post("/register", description="注册")
def register(
    user: UserCreate = Depends(UserCreate.as_form),  
    avatar: Optional[UploadFile] = File(None, description="用户头像"),
    db: Session = Depends(get_db)
):
    try:
        if get_user_by_username(db, user.username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")
        # print(user.username)
        # 保存文件到临时目录
        avatar_path = None
        if avatar:
            save_path = temp_dir / avatar.filename
            with open(save_path, 'wb') as buffer:
                shutil.copyfileobj(avatar.file, buffer)
            avatar_path = upload_file(str(save_path))
            os.remove(save_path)

        # 保存用户到数据库
        db_user = User(
            username=user.username, 
            password=user.password,
            level=user.level,
            avatar=avatar_path
        )
        create_user(db, db_user)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "message": "Register success",
                "data": {
                    "id": db_user.id,
                    "username": db_user.username,
                    "level": db_user.level,
                    "avatar": db_user.avatar
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# 登录
@router.post("/login", description="登录")
def login(
    username: str = Form(..., min_length=1, max_length=50, description="Username, 1-50位"),
    password: str = Form(..., min_length=6, max_length=50, description="Password, 最短6位"),
    db: Session = Depends(get_db)
):
    try:
        db_user = get_user_by_username(db, username)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        if db_user.password != password:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Login success",
                "data": {
                    "id": db_user.id,
                    "username": db_user.username,
                    "level": db_user.level,
                    "avatar": db_user.avatar
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# 获取用户信息
@router.get("/{username}", description="根据用户名获取用户信息")
def get_user_info_by_username(
    username: str = Path(..., min_length=1, max_length=50, description="Username, 1-50位"),
    db: Session = Depends(get_db)
):
    try:
        db_user = get_user_by_username(db, username)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Get user info success",
                "data": {    
                    "id": db_user.id,
                    "username": db_user.username,
                    "level": db_user.level,
                    "avatar": db_user.avatar
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
# 获取用户信息
@router.get("/{user_id}", description="根据用户ID获取用户信息")
def get_user_info_by_id(
    user_id: int = Path(..., ge=1, description="User ID, 1以上"),
    db: Session = Depends(get_db)
):
    try:
        db_user = get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Get user info success",
                "data": {    
                    "id": db_user.id,
                    "username": db_user.username,
                    "level": db_user.level,
                    "avatar": db_user.avatar
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# 更新用户信息
@router.put("/{user_id}", description="根据用户ID更新用户信息")
def update_user_info(
    user_id: int = Path(..., ge=1, description="User ID, 1以上"),
    user: UserCreate = Depends(UserCreate.as_form),
    avatar: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    try:
        db_user = get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        # 保存文件到临时目录
        avatar_path = None
        if avatar:
            save_path = temp_dir / avatar.filename
            with open(save_path, 'wb') as buffer:
                shutil.copyfileobj(avatar.file, buffer)
            avatar_path = upload_file(str(save_path))
            os.remove(save_path)

        # 更新用户信息
        db_user.username = user.username
        db_user.password = user.password
        db_user.level = user.level
        db_user.avatar = avatar_path
        update_user(db, db_user)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Update user info success",
                "data": {    
                    "id": db_user.id,
                    "username": db_user.username,
                    "level": db_user.level,
                    "avatar": db_user.avatar
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# 删除用户
@router.delete("/{user_id}", description="根据用户ID删除用户信息")
def delete_user_info(
    user_id: int = Path(..., ge=1, description="User ID, 1以上"),
    db: Session = Depends(get_db)
):
    try:
        db_user = get_user_by_id(db, user_id)
        if not db_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        delete_user(db, user_id)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "Delete user success",
                "data": {    
                    "id": db_user.id,
                    "username": db_user.username,
                    "level": db_user.level,
                    "avatar": db_user.avatar
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))