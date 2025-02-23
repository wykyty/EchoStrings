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
        match_scores.append(match_score)
        mfcc_scores.append(mfcc_match)
        pitch_scores.append(pitch_match)
        beats_scores.append(beats_match)

    return match_scores, mfcc_scores, pitch_scores, beats_scores

# def generate_report(file_path1, file_path2, match_score, mfcc_match, pitch_match, beats_match):
#     temp_dir = "temp_audio_match_report"
#     os.makedirs(temp_dir, exist_ok=True)

#     # 生成可视化图表
#     plt.figure(figsize=(10, 5))
#     labels = ['Overall Match', 'MFCC Match', 'Pitch Match', 'Beats Match']
#     values = [match_score, mfcc_match, pitch_match, beats_match]
#     plt.bar(labels, values, color=['blue', 'green', 'orange', 'red'])
#     plt.title('Audio Match Score')
#     plt.ylabel('Score')
#     plt.ylim(0, 1)
#     chart_path = os.path.join(temp_dir, 'match_chart.png')
#     plt.savefig(chart_path)
#     plt.close()

#     # 生成PDF报告
#     pdf_path = os.path.join(temp_dir, 'audio_match_report.pdf')
#     c = canvas.Canvas(pdf_path, pagesize=letter)
#     c.drawString(100, 750, "Audio Match Report")
#     c.drawString(100, 730, f"File 1: {os.path.basename(file_path1)}")
#     c.drawString(100, 710, f"File 2: {os.path.basename(file_path2)}")
#     c.drawString(100, 690, f"Overall Match Score: {match_score:.2f}")
#     c.drawString(100, 670, f"MFCC Match Score: {mfcc_match:.2f}")
#     c.drawString(100, 650, f"Pitch Match Score: {pitch_match:.2f}")
#     c.drawString(100, 630, f"Beats Match Score: {beats_match:.2f}")
#     c.drawImage(chart_path, 100, 400, width=400, height=300)
#     c.save()

#     return pdf_path

def generate_report(file_path1, file_path2, match_scores, mfcc_scores, pitch_scores, beats_scores, segment_length=1.0):
    temp_dir = f"app/audio_process/temp_audio_files"
    os.makedirs(temp_dir, exist_ok=True)

    # 打印数据以检查是否为空
    print(f"Match Scores: {match_scores}")
    print(f"MFCC Scores: {mfcc_scores}")
    print(f"Pitch Scores: {pitch_scores}")
    print(f"Beats Scores: {beats_scores}")

    # 生成匹配度变化图
    time_axis = np.arange(len(match_scores)) * segment_length
    # 对match_scores进行平滑处理
    smooth_match_scores = savgol_filter(match_scores, window_length=5, polyorder=3)

    plt.figure(figsize=(10, 5))
    plt.plot(time_axis, smooth_match_scores, label='Overall Match Score', color='blue')

    plt.xlabel('Time (seconds)')
    plt.ylabel('Match Score')
    plt.title('Audio Match Scores Over Time')

    plt.legend()  # 显示图例
    plt.ylim(0, 1.05)  # 设置纵轴范围为0到1
    chart1_path = os.path.join(f"{temp_dir}", 'match_chart1.png')
    plt.savefig(chart1_path)
    plt.close()

    # MFCC Match Score
    plt.figure(figsize=(10, 5))
    plt.plot(time_axis, mfcc_scores, label='MFCC Match Score', color='green')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Match Score')
    plt.title('MFCC Match Scores Over Time')
    plt.legend()
    plt.ylim(0, 1.05)  # 设置纵轴范围为0到1
    chart2_path = os.path.join(f"{temp_dir}", 'match_chart2.png')
    plt.savefig(chart2_path)
    plt.close()

    # Pitch Match Socre
    plt.figure(figsize=(10, 5))
    plt.plot(time_axis, pitch_scores, label='Pitch Match Score', color='orange')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Match Score')
    plt.title('Pitch Match Scores Over Time')
    plt.legend()
    plt.ylim(0, 1.05)  # 设置纵轴范围为0到1
    chart3_path = os.path.join(f"{temp_dir}", 'match_chart3.png')   
    plt.savefig(chart3_path)
    plt.close()

    # Beats Match Score
    plt.figure(figsize=(10, 5))
    plt.plot(time_axis, beats_scores, label='Beats Match Score', color='red')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Match Score')
    plt.title('Beats Match Scores Over Time')
    plt.legend()
    plt.ylim(0, 1.05)  # 设置纵轴范围为0到1
    chart4_path = os.path.join(f"{temp_dir}", 'match_chart4.png')
    plt.savefig(chart4_path)
    plt.close()


    # 生成PDF报告
    pdf_path = os.path.join(f"{temp_dir}", 'audio_match_report.pdf')
    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "Audio Match Report")
    c.drawString(100, 730, f"File 1: {os.path.basename(file_path1)}")
    c.drawString(100, 710, f"File 2: {os.path.basename(file_path2)}")

    # 图表插入，调整位置和大小
    chart_width = 250  # 图表宽度
    chart_height = 200  # 图表高度
    margin = 50  # 边距

    c.drawImage(chart1_path, margin, 400, width=chart_width, height=chart_height)
    c.drawImage(chart2_path, margin + chart_width + margin, 400, width=chart_width, height=chart_height)
    c.drawImage(chart3_path, margin, 100, width=chart_width, height=chart_height)
    c.drawImage(chart4_path, margin + chart_width + margin, 100, width=chart_width, height=chart_height)

    c.save()

    return pdf_path

if __name__ == '__main__':
    file_path1 = 'app/data/audio1.wav'
    file_path2 = 'app/data/audio2.wav'
    match_scores, mfcc_scores, pitch_scores, beats_scores = calculate_segment_match(file_path1, file_path2, segment_length=1.0)
    pdf_path = generate_report(file_path1, file_path2, match_scores, mfcc_scores, pitch_scores, beats_scores, segment_length=1.0)
    print(f"Report saved to {pdf_path}")


