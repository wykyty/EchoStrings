from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Depends
from fastapi.responses import JSONResponse

from pydantic import BaseModel
from http import HTTPStatus
from dashscope import Application
import re
import os
from dotenv import load_dotenv 

router = APIRouter(prefix='/ai', tags=['AI'])

load_dotenv()
my_api_key = os.getenv("DASHSCOPE_API_KEY")
my_app_id = "98fe03e7803a473cb63810c6284d85c0"

class ChatRequest(BaseModel):   
    user_id: str
    question: str

    @classmethod
    def as_form(
        cls,
        user_id: str = Form(..., description="用户ID"),
        question: str = Form(..., description="问题")
    ):
        return cls(user_id=user_id, question=question)

class ChatResponse(BaseModel):
    user_id: str
    answer: str

class MusicCreatRequest(BaseModel):
    user_id: str
    title: str
    instr_id: str
    tuning: str
    tempo: str
    artist: str
    time: str
    style_desc: str

    @classmethod
    def as_form(
        cls,
        user_id: str = Form(..., description="用户ID"),
        title: str = Form(..., description="乐曲标题"),
        instr_id: str = Form(..., description="乐器编号"),
        tuning: str = Form(..., description="吉他的调音"),
        tempo: str = Form(..., description="乐谱的tempo"),
        artist: str = Form(..., description="乐曲作者"),
        time: str = Form(..., description="乐谱的演奏时间"),
        style_desc: str = Form(..., description="乐曲风格描述")
    ):
        return cls(user_id=user_id, title=title, instr_id=instr_id, tuning=tuning, tempo=tempo, artist=artist, time=time, style_desc=style_desc)

# 普通对话
@router.post('/chat', description="普通对话")
async def chat(request: ChatRequest):
    user_id = request.user_id
    question = request.question
    upstream_response = Application.call(
        api_key=my_api_key,
        app_id=my_app_id,
        prompt=question
    )
    if (upstream_response.status_code == HTTPStatus.OK):
        response = ChatResponse(
            user_id=user_id,
            answer=upstream_response.output.text
        )
        return JSONResponse(response.dict(), status_code=HTTPStatus.OK)
    else:
        print(f'request_id={upstream_response.request_id}')
        print(f'code={upstream_response.status_code}')
        print(f'message={upstream_response.message}')
        print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')
        raise HTTPException(status_code=upstream_response.status_code, detail=upstream_response.text)


# 乐谱创作
@router.post('/music_creat', description="乐谱创作")
async def music_creat(request: MusicCreatRequest):
    user_id = request.user_id
    title = request.title
    instr_id = request.instr_id
    tuning = request.tuning
    tempo = request.tempo
    artist = request.artist
    time = request.time
    style_desc = request.style_desc

    upstream_response = Application.call(
        api_key=my_api_key,
        app_id=my_app_id,
        prompt=f"乐谱创作(独奏):创作一首名为{title}的乐谱，所使用的乐器编号为{instr_id}，吉他的调音为{tuning} ，乐谱的tempo为{tempo}，乐谱作者为{artist}，乐谱的演奏时间为{time}，乐谱的风格为{style_desc}"
    )

    def match_pattern(input_string):
        pattern = r'\(([^)]+)\)\.(\d+)(\s*\{([^}]*)\})?'
        matches = []
        for match in re.finditer(pattern, input_string):
            full_match = match.group(0)
            matches.append(full_match)
        return matches 
    # 对于乐谱创作的输出，进一步格式化
    def formatSingleScore(ori_content:str):
        content=ori_content.split("\n")[6]
        items=match_pattern(content)
        dealed_content=""
        for i in range(0,len(items),15):
            dealed_content+=" ".join(items[i:i+15])
            dealed_content+="|"
        dealed_content="\n".join(ori_content.split("\n")[:6])+"\n\staff {tabs}\n"+dealed_content
        print(dealed_content)
        return dealed_content
        

    if (upstream_response.status_code == HTTPStatus.OK):
        response = ChatResponse(
            user_id=user_id,
            answer=formatSingleScore(upstream_response.output.text)
        )
        return JSONResponse(response.dict(), status_code=HTTPStatus.OK)
    else:
        print(f'request_id={upstream_response.request_id}')
        print(f'code={upstream_response.status_code}')
        print(f'message={upstream_response.message}')
        print(f'请参考文档：https://help.aliyun.com/zh/model-studio/developer-reference/error-code')