import os
import requests
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DB_HOST")
url = f"http://{host}:1412/upload"

def upload_file(file_path: str) -> str:
    """
    上传文件到数据库, 返回网址
    """
    files = {"file": open(file_path, "rb")}
    response = requests.post(url, files=files)
    
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"上传文件失败: {response.text}")
    
    # 网址
    path = response.json()[0]["path"].split("/")[-1]
    db_path = f"http://{host}/{path}"
    return db_path

if __name__ == "__main__":
    file_path = "test.md"
    db_path = upload_file(file_path)
    print(db_path)
