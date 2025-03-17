from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import shutil
import os
import pathlib
from typing import Optional

from database import get_db
from models.activity import Activity, Work
from schemas.activity import ActivityCreate, WorkCreate

from services.upload_file import upload_file
from services.user import get_user_by_id, get_user_by_username, create_user, update_user, delete_user

router = APIRouter(prefix="/activity", tags=["Activity and Work"])

temp_dir = pathlib.Path('Temp/temp_files')
temp_dir.mkdir(parents=True, exist_ok=True)

# 获取活动列表
@router.get("/list", description="获取活动列表")
def get_activity_list(
    db: Session = Depends(get_db)
):
    # 返回活动id及活动标题
    try:
        activities = db.query(Activity.id, Activity.title).all()
        data = [{"id": activity.id, "title": activity.title} for activity in activities]
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "获取活动列表成功",
                "data": data
            }
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# 获取活动详情
@router.get("/{activity_id}", description="获取活动详情")
def get_activity_detail(
    activity_id: int = Path(..., description="活动ID"),
    db: Session = Depends(get_db)
):
    try:
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "获取活动详情成功",
                "data": {
                    "id": activity.id,
                    "title": activity.title,
                    "start_time": activity.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": activity.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": activity.status,
                    "participants": activity.participants,
                    "cover_url": activity.cover_url,
                    "intro_url": activity.intro_url,
                    "creator_id": activity.creator_id
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# 获得活动的热门作品列表
@router.get("/{activity_id}/hotworks", description="获得活动的热门作品列表")
def get_activity_hotworks(
    activity_id: int = Path(..., description="活动ID"),
    db: Session = Depends(get_db)
):
    try:
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
        hotworks = activity.hotworks
        data = [{"id": hotwork.id, "title": hotwork.title} for hotwork in hotworks]
        # TODO: 按作品的热度排序 
        data.sort(key=lambda x: x['id'], reverse=True)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "获得活动的热门作品列表成功",
                "data": data
            }
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# 获得作品详情
@router.get("/{activity_id}/works/{work_id}", description="获得作品详情")
def get_work(
    activity_id: int = Path(..., description="活动ID"),
    work_id: int = Path(..., description="作品ID"),
    db: Session = Depends(get_db)
):
    # 检查活动是否存在
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
    try:
        work = db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="作品不存在")
        data = {
            "id": work.id,
            "title": work.title,
            "author": work.author,
            "content_url": work.content_url,
            "author_id": work.author_id,
            "activity_id": work.activity_id

        }
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "获得作品详情成功",
                "data": data
            }
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# 上传作品到某个活动
@router.post("/{activity_id}/uploadwork", description="上传作品到某个活动")
def upload_work_to_activity(
    activity_id: int = Path(..., description="活动ID"),
    work: WorkCreate = Depends(WorkCreate.as_form),
    content: UploadFile = File(..., description="作品文件"),
    db: Session = Depends(get_db)
):
    # 检验活动是否存在
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
    # 检验作者是否存在
    author = get_user_by_id(db, work.author_id)
    if not author:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="作者不存在")
    
    # 上传作品文件
    save_path = os.path.join(temp_dir, content.filename)
    with open(save_path, 'wb') as f:
        shutil.copyfileobj(content.file, f)
    file_path = upload_file(save_path)
    os.remove(save_path)

    # 保存作品信息到数据库
    work_db = Work(
        title=work.title,
        author=author.username,
        content_url=file_path,
        author_id=work.author_id,
        activity_id=activity_id
    )
    try:
        db.add(work_db)
        db.commit()
        db.refresh(work_db)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "id": work_db.id,
            "message": "上传作品成功"
        }
    )



# 发布活动
@router.put("/publish", description="发布活动")
def publish_activity(
    activity: ActivityCreate = Depends(ActivityCreate.as_form),
    cover: UploadFile = File(..., description="活动封面"),
    intro: UploadFile = File(None, description="活动介绍"),
    db: Session = Depends(get_db)
):
    try:
        # 临时保存并上传封面
        save_path = os.path.join(temp_dir, cover.filename)
        with open(save_path, 'wb') as f:
            shutil.copyfileobj(cover.file, f)
        cover_path = upload_file(save_path)
        os.remove(save_path)
        
        # 上传介绍（md文件）
        intro_path = None
        if intro:
            save_path = os.path.join(temp_dir, intro.filename)
            with open(save_path, 'wb') as f:
                shutil.copyfileobj(intro.file, f)
            intro_path = upload_file(save_path)
            os.remove(save_path)

        # 创建活动
        activity_db = Activity(
            title=activity.title,
            start_time=activity.start_time,
            end_time=activity.end_time,
            status=activity.status,
            participants=activity.participants,
            cover_url=cover_path,
            intro_url=intro_path,
            creator_id=activity.creator_id
        )
        db.add(activity_db)
        db.commit()
        db.refresh(activity_db)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED, 
            content={"id": activity_db.id, "message": "发布活动成功"}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
# 编辑活动
@router.put("/{activity_id}", description="编辑活动")
def edit_activity(
    activity_id: int = Path(..., description="活动ID"),
    activity: ActivityCreate = Depends(ActivityCreate.as_form),
    cover: UploadFile = File(None, description="活动封面"),
    intro: UploadFile = File(None, description="活动介绍"),
    db: Session = Depends(get_db)
):
    try:
        # 检查活动是否存在
        activity_db = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity_db:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")

        # 临时保存并上传封面
        save_path = os.path.join(temp_dir, cover.filename)
        with open(save_path, 'wb') as f:
            shutil.copyfileobj(cover.file, f)
        cover_path = upload_file(save_path)
        os.remove(save_path)
        
        # 上传介绍（md文件）
        intro_path = None
        if intro:
            save_path = os.path.join(temp_dir, intro.filename)
            with open(save_path, 'wb') as f:
                shutil.copyfileobj(intro.file, f)
            intro_path = upload_file(save_path)
            os.remove(save_path)

        activity_db.title = activity.title
        activity_db.start_time = activity.start_time
        activity_db.end_time = activity.end_time
        activity_db.status = activity.status
        activity_db.participants = activity.participants
        activity_db.cover_url = cover_path
        activity_db.intro_url = intro_path
        db.commit()
        db.refresh(activity_db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"id": activity_db.id, "message": "编辑活动成功"}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# 删除活动
@router.delete("/{activity_id}", description="删除活动")
def delete_activity(
    activity_id: int = Path(..., description="活动ID"),
    db: Session = Depends(get_db)
):
    try:
        activity = db.query(Activity).filter(Activity.id == activity_id).first()
        if not activity:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="活动不存在")
        db.delete(activity)
        db.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "删除活动成功"}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
