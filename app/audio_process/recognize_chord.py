import subprocess

def recognize_chord(audio_path: str) -> str:
    try:
        result = subprocess.run(
            ["python", "app/audio_process/Guitar-Chord-Audio-Recognition/example/CChordRec.py"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to recognize chord: {e.stderr}")

if __name__ == "__main__":
    audio_path = "app/data/audio1.wav"
    print(recognize_chord(audio_path))