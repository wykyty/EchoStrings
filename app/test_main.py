from .main import app
from fastapi.testclient import TestClient

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
