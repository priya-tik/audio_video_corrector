import subprocess
import json
import os


def get_audio_duration(filename):
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-select_streams', 'a:0',
        '-show_entries', 'stream=duration',
        '-of', 'json',
        filename
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    info = json.loads(result.stdout)
    return float(info['streams'][0]['duration'])


def get_video_duration(filename):
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        filename
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    info = json.loads(result.stdout)
    return float(info['format']['duration'])


def create_offset_video(ref_video, offset_duration, resolution="1280x720", output="blank_with_audio.mp4"):
    print(f"[INFO] Creating blank video of {offset_duration:.2f}s using audio from: {ref_video}")

    subprocess.run([
        'ffmpeg', '-y',
        '-i', ref_video,
        '-t', str(offset_duration),
        '-vn',
        '-ar', '44100', '-ac', '2', '-b:a', '192k', '-acodec', 'aac',
        'temp_offset_audio.aac'
    ], check=True)

    subprocess.run([
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', f'color=black:s={resolution}:d={offset_duration}',
        '-i', 'temp_offset_audio.aac',
        '-vf', f'scale={resolution},fps=25',
        '-ar', '44100', '-ac', '2',
        '-c:v', 'libx264', '-c:a', 'aac', '-b:a', '192k',
        '-shortest', output
    ], check=True)

    os.remove("temp_offset_audio.aac")


def reencode_video(video_path, output_path):
    subprocess.run([
        'ffmpeg', '-y',
        '-i', video_path,
        '-vf', 'scale=1280:720,fps=25',
        '-ar', '44100', '-ac', '2',
        '-c:v', 'libx264', '-c:a', 'aac', '-b:a', '192k',
        output_path
    ], check=True)


def concat_videos(video1, video2, output):
    with open("concat_list.txt", "w") as f:
        f.write(f"file '{os.path.abspath(video1)}'\n")
        f.write(f"file '{os.path.abspath(video2)}'\n")

    subprocess.run([
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0',
        '-i', 'concat_list.txt',
        '-c', 'copy',
        output
    ], check=True)

    os.remove("concat_list.txt")


def auto_fix_offset(video_a, video_b, output="good_fixed.mp4"):
    a1 = get_audio_duration(video_a)
    a2 = get_audio_duration(video_b)

    if abs(a1 - a2) < 0.1:
        return

    if a1 > a2:
        ref = video_a
        desynced = video_b
        offset = a1 - a2
    else:
        ref = video_b
        desynced = video_a
        offset = a2 - a1

    create_offset_video(ref, offset_duration=offset, output="blank_with_audio.mp4")

    reencode_video(desynced, "desynced_fixed.mp4")

    concat_videos("blank_with_audio.mp4", "desynced_fixed.mp4", output)

    os.remove("blank_with_audio.mp4")
    os.remove("desynced_fixed.mp4")

    print(output)


auto_fix_offset("src1 (1).mp4", "src2.mp4", output="final_sync.mp4")
