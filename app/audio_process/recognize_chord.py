import subprocess

def recognize_chord(audio_path: str) -> str:
    try:
        result = subprocess.run(
            ["python", "app/audio_process/Guita-Chord-Audio-Recognition/example/recognize_chord.py", audio_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to recognize chord: {e.stderr}")

        