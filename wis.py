import subprocess
import numpy as np
from scipy.signal import correlate
from scipy.io import wavfile
import os


def extract_audio(video_path, audio_path):
    # Extract audio using ffmpeg
    subprocess.run([
        'ffmpeg', '-y', '-i', video_path,
        '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '1',
        audio_path
    ])


def get_offset(audio1_path, audio2_path):
    # Load both audio files
    rate1, data1 = wavfile.read(audio1_path)
    rate2, data2 = wavfile.read(audio2_path)

    if rate1 != rate2:
        raise ValueError("Sample rates don't match")

    min_len = min(len(data1), len(data2))
    data1 = data1[:min_len]
    data2 = data2[:min_len]

    corr = correlate(data1, data2)
    lag = np.argmax(corr) - (len(data2) - 1)
    offset_sec = lag / rate1
    return offset_sec


def shift_video(input_video, output_video, offset_sec):
    # Use ffmpeg to shift the video
    if offset_sec > 0:
        # Delay the video
        subprocess.run([
            'ffmpeg', '-y', '-i', str(offset_sec), '-ss', input_video,
            '-c', 'copy', output_video
        ])
    else:
        # Delay the other video instead (you can modify based on use)
        subprocess.run([
            'ffmpeg', '-y', '-i', input_video,
            '-vf', f"setpts=PTS+{abs(offset_sec)}/TB",
            '-af', f"adelay={int(abs(offset_sec) * 1000)}|{int(abs(offset_sec) * 1000)}",
            output_video
        ])


def sync_videos(video1, video2, synced1, synced2):
    # Extract audios
    extract_audio(video1, "audio1.wav")
    extract_audio(video2, "audio2.wav")

    # Calculate offset
    offset = get_offset("audio1.wav", "audio2.wav")
    print(f"Offset (seconds): {offset}")

    # Shift video2 to align with video1
    shift_video(video2, synced2, offset)
    # Copy video1 without changes
    subprocess.run(['cp', video1, synced1])

    # Clean up
    os.remove("audio1.wav")
    os.remove("audio2.wav")


sync_videos("desync-presentation.mp4", "desync-presenter.mp4",
            "desync-presentation111.mp4", "desync-presenter1111.mp4")
