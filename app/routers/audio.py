from fastapi import APIRouter, File, UploadFile, HTTPException, status, Depends, Form, Path
from fastapi.responses import FileResponse, JSONResponse
import os
import pathlib
import shutil
from mutagen.mp3 import MP3
import requests

from sqlalchemy.orm import Session
from models.audio import MusicSheet
from schemas.audio import MusicSheetRequest
from database import get_db
from dotenv import load_dotenv
load_dotenv()

from services.audio_service import calculate_segment_match, model_recognize_chord, midi_to_audio, base64_to_midi
from services.upload_file import upload_file
from services.audio import get_all_music, get_music_by_id
from services.user import get_user_by_id


router = APIRouter(prefix='/audio', tags=['Audio'])

temp_dir = pathlib.Path('Temp/temp_audio_files')
temp_dir.mkdir(exist_ok=True)


# 上传音频文件并计算与曲谱库中某个音频的匹配度
@router.post('/match', description="上传音频文件并计算与曲谱库中某个音频的匹配度")
async def compare_audio(
    audio_id: int = Form(..., description="曲谱库中的音频id"),
    file: UploadFile = File(..., description="上传的音频文件(支持wav/mp3)"),
    db: Session = Depends(get_db)
):
    print("start")
    # 查找曲谱库中的文件并临时保存
    music = get_music_by_id(db, audio_id)
    print("finish find music")
    if not music:
        raise HTTPException(status_code=404, detail="音频文件不存在")
    file1_path = os.path.join(temp_dir, f"{music.title}.mp3")
    print("finish save music")
    response = requests.get(music.audio_file_path)
    print("finish get music")
    with open(file1_path, 'wb') as f:
        f.write(response.content)
    print("finish save music")
    # 保存上传的文件
    file2_path = os.path.join(temp_dir, file.filename)
    with open(file2_path, 'wb') as f:
        f.write(await file.read())
    print("start match")
    try: 
        # 计算匹配度
        match_scores, mfcc_scores, pitch_scores, beats_scores = calculate_segment_match(file1_path, file2_path)

        return JSONResponse({
            "status": "success",
            "data": {
                "match_scores": match_scores,
                "mfcc_scores": mfcc_scores,
                "pitch_scores": pitch_scores,
                "beats_scores": beats_scores
            }
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(file1_path)
        os.remove(file2_path)

# 上传音频文件并识别和弦
@router.post("/recognize_chord", description="上传音频文件并识别和弦")
async def recognize_chord(file: UploadFile = File(..., description="上传的音频文件(支持wav/mp3)")):
    try:
        print("start")
        # 保存文件
        temp_path = temp_dir / file.filename
        print(temp_path)
        with open(temp_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)
        # 验证类型
        print("exmine type")
        if not file.filename.lower().endswith(('.wav', '.mp3')):
            raise HTTPException(status_code=400, detail="仅支持wav/mp3格式音频文件")
        print("recognize chord")
        # 识别和弦
        chord =model_recognize_chord(str(temp_path))
        print("extract pitch")
        temp_path.unlink()
        return JSONResponse({
            "status": "success",
            "chord": chord,
            "filename": file.filename
        })
    except Exception as e:
        if temp_path.exists():
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))


# 将上传至曲谱库
@router.post("/sheet/upload", description="上传音频文件并保存到曲谱库")
async def create_music(request: MusicSheetRequest, db: Session = Depends(get_db)):
    author_id = request.author_id
    title = request.title
    content = request.content
    base64_date = request.base64_data

    try:    
        # 检查用户是否存在
        user = get_user_by_id(db, author_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        print("start")
        midi_path = f"{temp_dir}/{title}.mid"
        base64_to_midi(base64_date, midi_path)
        print("to midi ok")
        audio_path = midi_to_audio(midi_path, temp_dir)
        print("to audio ok")
        duration = MP3(audio_path).info.length
        # audio_length = librosa.get_duration(path=audio_path)
        print("get duration ok")
        # 上传到服务器
        audio_db_path = upload_file(audio_path)
        print("upload ok")

        # 保存到数据库
        db_sheet = MusicSheet(
            title=title,
            content=content,
            duration=duration,  # 音乐时长
            audio_file_path=audio_db_path,
            author_id=author_id
        )
        try:
            db.add(db_sheet)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "message": "曲谱上传成功"
            }
        )
    
    except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的Base64数据: {str(e)}"
            )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"音频转换失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"未知错误: {str(e)}"
        )
    finally:
        if os.path.exists(midi_path):
            os.remove(midi_path)


# 获得曲谱库列表
@router.get("/sheet/list", description="获得曲谱库列表")
async def get_music_sheets(
    db: Session = Depends(get_db)
):
    try:
        sheets = db.query(MusicSheet).all()
        data = []
        for sheet in sheets:
            # 查询作者名字
            author = get_user_by_id(db, sheet.author_id)
            if not author:
                raise HTTPException(status_code=404, detail="作者不存在")
            data.append({
                "id": sheet.id,
                "title": sheet.title,
                "duration": sheet.duration,
                "author": author.username
            })
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "获得曲谱列表成功",
                "data": data
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# 根据id获得曲谱
@router.get("/sheet/{id}", description="根据id获得曲谱")
async def get_music_sheet(
    id: int = Path(..., description="曲谱id"),
    db: Session = Depends(get_db)
):
    try:
        sheet = get_music_by_id(db, id)
        if not sheet:
            raise HTTPException(status_code=404, detail="曲谱不存在")
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "获得曲谱成功",
                "data": sheet.to_dict()
            }    
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 根据id删除曲谱
@router.delete("/sheet/{id}", description="根据id删除曲谱")
async def delete_music_sheet(
    id: int = Path(..., description="曲谱id"),
    db: Session = Depends(get_db)
):
    try:
        music = get_music_by_id(db, id)
        if not music:
            raise HTTPException(status_code=404, detail="曲谱不存在")
        db.delete(music)
        db.commit()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "message": "曲谱删除成功"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))