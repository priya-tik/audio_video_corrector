import subprocess
import numpy as np
from scipy.signal import correlate
from scipy.io import wavfile
import os
from audio_offset_finder.audio_offset_finder import find_offset_between_files

def extract_audio(video_path, audio_path):
    subprocess.run([
        'ffmpeg', '-y', '-i', video_path,
        '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '1',
        audio_path
    ])

def get_offset(audio1_path, audio2_path, trim=None):
    if trim is not None:
        results = find_offset_between_files(audio1_path, audio2_path, trim=trim)
    else:
        results = find_offset_between_files(audio1_path, audio2_path)

    offset_sec = results["time_offset"]
    score = results["standard_score"]

    print(f"Offset: {offset_sec:.2f} seconds")
    print(f"Standard score (confidence): {score:.2f}")

    return offset_sec

def shift_video(input_video, output_video, offset_sec):
    if offset_sec >= 0:
        delay_ms = int(offset_sec * 1000)
        subprocess.run([
            'ffmpeg', '-y',
            '-i', input_video,
            '-filter_complex',
            f"[0:v]setpts=PTS+{offset_sec}/TB[v];"
            f"[0:a]adelay={delay_ms}|{delay_ms}[a]",
            '-map', '[v]', '-map', '[a]',
            '-c:v', 'libx264', '-c:a', 'aac',
            output_video
        ])
    else:
        subprocess.run([
            'ffmpeg', '-y',
            '-ss', str(abs(offset_sec)),
            '-i', input_video,
            '-c:v', 'libx264', '-c:a', 'aac',
            output_video
        ])

def sync_videos(video1, video2, synced1, synced2):
    extract_audio(video1, "audio1.wav")
    extract_audio(video2, "audio2.wav")

    offset = get_offset("audio1.wav", "audio2.wav")
    print(f"Offset (seconds): {offset}")

    shift_video(video2, synced2, offset)
    subprocess.run(['cp', video1, f'./{synced1}'])

    os.remove("audio1.wav")
    os.remove("audio2.wav")

# Call the sync function
sync_videos("desync-presentation.mp4", "desync-presenter.mp4",
            "presentation-sync.mp4", "presenter-sync_worked.mp4")
