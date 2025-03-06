from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
from pydantic import BaseModel
from http import HTTPStatus
from dashscope import Application

router = APIRouter()

my_api_key = os.getenv("DASHSCOPE_API_KEY")
my_app_id = "98fe03e7803a473cb63810c6284d85c0"

class ChatRequest(BaseModel):
    user_id: str
    question: str

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

# 普通对话
@router.post('/ai/chat')
async def chat(request: ChatRequest):
    user_id = request.user_id
    question = request.question
    upstream_response = Application.call(
        api_key = my_api_key,
        app_id = my_app_id,
        prompt = question
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
@router.post('/ai/music_creat')
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
        api_key = my_api_key,
        app_id = my_app_id,
        prompt = f"乐谱创作(独奏):创作一首名为{title}的乐谱，所使用的乐器编号为{instr_id}，吉他的调音为{tuning} ，乐谱的tempo为{tempo}，乐谱作者为{artist}，乐谱的演奏时间为{time}，乐谱的风格为{style_desc}"
    )

    # 对于乐谱创作的输出，进一步格式化
    def formatSingleScore(ori_content:str):
        content=ori_content.split("\n")[6]
        item_list=content.split("(")
        item_list=["("+i for i in item_list[1:]]
        time_list=[int(i.split(".")[-1].split(" ")[0]) for i in item_list]
        sum_time=0
        dealed_content=""
        for ind in range(len(time_list)):
            if(sum_time>=2):
                sum_time=0
                dealed_content+=" |\n"
                continue
            sum_time+=1.0/time_list[ind]
            dealed_content+=item_list[ind]
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