import librosa
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import euclidean
from scipy.signal import savgol_filter
from dtaidistance import dtw
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from fastdtw import fastdtw
import subprocess
import base64
from midi2audio import FluidSynth
from pydub import AudioSegment
from utils.audio.CChordRec import CChordRec

SOUND_FONT = "utils/soundfonts/GeneralUser-GS.sf2"
model = CChordRec(path="utils/audio/model.pth")

# 提取音高
def extract_pitch(y, sr):
    pitches, magnitudes = librosa.core.piptrack(y=y, sr=sr)
    pitch = []
    for t in range(pitches.shape[1]):
        index = magnitudes[:, t].argmax() # 找到最大值的索引
        pitch.append(pitches[index, t]) # 最大值的音高
    return pitch

# 提取节拍
def extract_beats(y, sr):
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
    return beats

# 计算音频匹配度
def calculate_match(file_path1, file_path2):
    # 加载音频文件
    y1, sr1 = librosa.load(file_path1)
    y2, sr2 = librosa.load(file_path2)
    # y: 音频时间序列
    # sr: 音频的采样率

    # 提取音频特征
    mfcc1 = librosa.feature.mfcc(y=y1, sr=sr1)
    mfcc2 = librosa.feature.mfcc(y=y2, sr=sr2)

    # 使用DTW对齐MFCC特征
    distance, path = fastdtw(mfcc1.T, mfcc2.T, dist=euclidean)
    mfcc_match = 1 / (1 + distance)  # 将距离转换为相似度

    # 提取音高
    pitch1 = extract_pitch(y1, sr1)
    pitch2 = extract_pitch(y2, sr2)

    # 提取节拍
    beats1 = extract_beats(y1, sr1)
    beats2 = extract_beats(y2, sr2)

    # 计算音高的匹配度
    distance = dtw.distance(pitch1, pitch2)
    pitch_match = 1 / (1 + distance)
    # 计算节奏的匹配度
    distance = dtw.distance(beats1, beats2)
    beats_match = 1 / (1 + distance)

    # 加权计算音频匹配度
    match_score = 0.4 * mfcc_match + 0.3 * pitch_match + 0.3 * beats_match
    return match_score, mfcc_match, pitch_match, beats_match

# 计算音频匹配度（分段）
def calculate_segment_match(file_path1, file_path2, segment_length=1.0):
    # 加载音频文件
    y1, sr1 = librosa.load(file_path1)
    y2, sr2 = librosa.load(file_path2)

    # 检查音频长度
    audio_length1 = len(y1) / sr1
    audio_length2 = len(y2) / sr2
    print(f"Audio 1 length: {audio_length1:.2f} seconds")
    print(f"Audio 2 length: {audio_length2:.2f} seconds")

    if audio_length1 < segment_length or audio_length2 < segment_length:
        raise ValueError("Audio length is shorter than segment length. Please use shorter segment_length.")

    # 计算每段的帧数
    frame_length = int(segment_length * sr1)
    match_scores = []
    mfcc_scores = []
    pitch_scores = []
    beats_scores = []

    # 分段计算匹配度
    for i in range(0, min(len(y1), len(y2)) - frame_length, frame_length):
        segment1 = y1[i:i + frame_length]
        segment2 = y2[i:i + frame_length]

        # 提取特征
        mfcc1 = librosa.feature.mfcc(y=segment1, sr=sr1)
        mfcc2 = librosa.feature.mfcc(y=segment2, sr=sr2)
        pitch1 = extract_pitch(segment1, sr1)
        pitch2 = extract_pitch(segment2, sr2)
        beats1 = extract_beats(segment1, sr1)
        beats2 = extract_beats(segment2, sr2)

        # 计算匹配度
        distance, path = fastdtw(mfcc1.T, mfcc2.T, dist=euclidean)
        mfcc_match = 1 / (1 + distance)  # 将距离转换为相似度
        distance = dtw.distance(pitch1, pitch2)
        pitch_match = 1 / (1 + distance)
        distance = dtw.distance(beats1, beats2)
        beats_match = 1 / (1 + distance)

            # 检查匹配度是否为 NaN 或 Inf
        if np.isnan(mfcc_match) or np.isinf(mfcc_match):
            print(f"Warning: MFCC match is NaN or Inf at segment {i}")
        if np.isnan(pitch_match) or np.isinf(pitch_match):
            print(f"Warning: Pitch match is NaN or Inf at segment {i}")
        if np.isnan(beats_match) or np.isinf(beats_match):
            print(f"Warning: Beats match is NaN or Inf at segment {i}")

        # 加权计算整体匹配度
        match_score = 0.4 * mfcc_match + 0.3 * pitch_match + 0.3 * beats_match
        match_scores.append(match_score)  # 整体匹配度
        mfcc_scores.append(mfcc_match)  # MFCC匹配度
        pitch_scores.append(pitch_match) # 音高匹配度
        beats_scores.append(beats_match)  # 节拍匹配度

    return match_scores, mfcc_scores, pitch_scores, beats_scores

# 识别和弦
def model_recognize_chord(audio_path: str) -> str:
    try:
        result = model.predictChord(audio_path)
        return result
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to recognize chord: {e.stderr}")

# ----------------------------------------------
# 上传曲谱库


def base64_to_midi(base64_str: str, output_path: str) -> None:
    """将Base64字符串转换为MIDI文件"""
    try:
        data = base64_str
        midi_data = base64.b64decode(data)
        with open(output_path, "wb") as f:
            f.write(midi_data)
    except Exception as e:
        raise ValueError(f"Base64解码失败：{str(e)}")

def midi_to_audio(midi_path: str, output_dir: str) -> str:
    """将MIDI转换为WAV和MP3"""
    if not os.path.exists(midi_path):
        raise FileNotFoundError(f"MIDI文件不存在")

    # 初始化FluidSynth（需要安装fluidsynth和soundfont）
    fs = FluidSynth(sound_font=SOUND_FONT)
    
    # 输出路径
    filename = os.path.splitext(os.path.basename(midi_path))[0]
    wav_path = os.path.join(output_dir, filename + ".wav")
    mp3_path = os.path.join(output_dir, filename + ".mp3")
    
    try:
        # MIDI转WAV
        fs.midi_to_audio(str(midi_path), str(wav_path))
        
        # WAV转MP3
        audio = AudioSegment.from_wav(str(wav_path))
        audio.export(str(mp3_path), format="mp3")
        
        return mp3_path
    except Exception as e:
        # 清理可能生成的不完整文件
        if os.path.exists(wav_path):
            os.remove(wav_path)
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
        raise RuntimeError(f"音频转换失败: {str(e)}")
        


# -----------------------------------------------

if __name__ == "__main__":
    # audio_path = "app/data/audio1.wav"
    # print(recognize_chord(audio_path))
    midi_to_audio("data/我和我的祖国.mid", "data")
