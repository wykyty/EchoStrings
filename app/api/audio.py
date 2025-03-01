from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
from pathlib import Path
import shutil
import subprocess

from ..audio_process.audio_match import calculate_segment_match, generate_report
from ..audio_process.recognize_chord import recognize_chord

router = APIRouter()

temp_dir = Path('app/audio_process/temp_audio_files')
temp_dir.mkdir(exist_ok=True)

@router.get('/audio')
async def get_audio():
    return {'message': 'Audio API'}

# 上传两个音频文件并计算匹配度
@router.post('/audio/audio_match')
async def compare_audio(file1: UploadFile = File(...), file2: UploadFile = File(...)):
    file1_path = os.path.join(temp_dir, file1.filename)
    file2_path = os.path.join(temp_dir, file2.filename)
    try: 
        with open(file1_path, 'wb') as f1, open(file2_path, 'wb') as f2:
            f1.write(await file1.read())
            f2.write(await file2.read())
        print(f'Audio files saved to {temp_dir}')

        # 计算匹配度
        match_scores, mfcc_scores, pitch_scores, beats_scores = calculate_segment_match(file1_path, file2_path)

        return JSONResponse({
            "status": "success",
            "match_scores": match_scores,
            "mfcc_scores": mfcc_scores,
            "pitch_scores": pitch_scores,
            "beats_scores": beats_scores
        })
        # # 生成匹配度报告
        # report_path = generate_report(file1_path, file2_path, match_scores, mfcc_scores, pitch_scores, beats_scores)    

        # # 返回匹配度报告
        # return FileResponse(report_path, media_type='application/pdf', filename='audio_match_report.pdf')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(file1_path)
        os.remove(file2_path)

# # 下载和弦识别
# @router.on_event('startup')
# async def startup_event():
#     repo_path = Path("app/audio_process/Guitar-Chord-Auido-Recognition")
#     if not repo_path.exists():
#         subprocess.run([
#             "git", "clone",
#             "git@github.com:W1412X/Guitar-Chord-Audio-Recognition.git",
#         ], check=True, cwd="app/audio_process")

# 上传音频文件并识别和弦
@router.post("/audio/recognize_chord")
async def recognize_chord(file: UploadFile = File(..., description="上传的音频文件(支持wav/mp3)")):
    try:
        # 保存文件
        temp_path = temp_dir / file.filename
        with open(temp_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 验证类型
        if not file.filename.lower().endswith(('.wav', '.mp3')):
            raise HTTPException(status_code=400, detail="仅支持wav/mp3格式音频文件")

        # 识别和弦
        chord = recognize_chord(str(temp_path))

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


