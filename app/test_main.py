from main import app
from fastapi.testclient import TestClient
from http import HTTPStatus
from dashscope import Application
import base64

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_auidio_upload():
    file1 = open("app/data/audio1.wav", "rb")
    file2 = open("app/data/audio2.wav", "rb")

    response = client.post("/audio/audio_match", files=[
        ("file1", file1), ("file2", file2)
    ])

    file1.close()
    file2.close()

    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    assert isinstance(response.json['match_scores'], list)
    assert isinstance(response.json['mfcc_scores'], list)
    assert isinstance(response.json['pitch_scores'], list)
    assert isinstance(response.json['beats_scores'], list)

def test_ai_chat():
    request = {
        "user_id": "1001",
        "question": "你都会做些什么？"
    }

    response = client.post("/ai/chat", json=request)

    assert response.status_code == 200
    assert "user_id" in response.json()
    assert "answer" in response.json()

    response_data = response.json()
    print(response_data)

# def test_chat_failure(client, monkeypatch):
#     request_data = {
#         "user_id": "test_user",
#         "question": "这是一个测试问题。"
#     }
    
#     def mock_application_call(*args, **kwargs):
#         class MockResponse:
#             status_code = 400
#             request_id = "mock_request_id"
#             message = "模拟错误"
#             def json(self):
#                 return {"message": self.message}
#             def text(self):
#                 return self.message
#         return MockResponse()
    
#     monkeypatch.setattr(Application, "call", mock_application_call)
    
#     response = client.post("/ai/chat", json=request_data)
#     assert response.status_code == 400
#     assert response.text == "模拟错误"

def test_ai_music_creat():
    request = {
        "user_id": "1001",
        "title": "我的家乡",
        "instr_id": "26",
        "tuning": "E3 B3 G3 D3 A3 E3",
        "tempo": "65",
        "artist": "sir",
        "time": "5min",
        "style_desc": "民谣"
    }
    response = client.post("/ai/music_creat", json=request)
    assert response.status_code == 200
    assert response.status_code == HTTPStatus.OK, f"Expected status code {HTTPStatus.OK}, but got {response.status_code}"
    
    response_data = response.json()
    print(response_data)

def test_audio_sheet_upload():
    midi_file = "data/我和我的祖国.mid"
    # 将midi文件编码为base64格式
    base64_data = base64.b64encode(open(midi_file, "rb").read())
    base64_data = base64_data.decode("utf-8")
    request = {
        "title": "我和我的祖国",
        "content": "我和我的祖国",
        "base64_data": base64_data
    }
    
    response = client.post("/audio/sheet/upload", json=request)
    # assert response.status_code == 200
    # assert response.status_code == HTTPStatus.OK, f"Expected status code {HTTPStatus.OK}, but got {response.status_code}"
    
    response_data = response.json()
    print(response_data)

if __name__ == "__main__":

    # test_ai_chat()
    # test_chat_failure()
    # test_ai_music_creat()
    test_audio_sheet_upload()