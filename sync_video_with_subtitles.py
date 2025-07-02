import subprocess
import json
import os
import whisper

def get_audio_duration(filename):
    """
      Returns the duration (in seconds) of the first audio stream in a media file using ffprobe.

      Parameters:
          filename (str): Path to the media file.

      Returns:
          float: Duration of the audio stream in seconds.
      """
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
    """
    Returns the duration (in seconds) of a video file using ffprobe.

    Parameters:
        filename (str): Path to the video file.

    Returns:
        float: Duration of the video in seconds.
    """
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        filename
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    info = json.loads(result.stdout)
    return float(info['format']['duration'])

def extract_audio_for_whisper(video_path, output="audio.wav"):
    subprocess.run([
        'ffmpeg', '-y',
        '-i', video_path,
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        output
    ], check=True)

def transcribe_audio_to_srt(file_path, srt_output="subtitles.srt"):
    model = whisper.load_model("base")
    result = model.transcribe(file_path, verbose=False)

    def format_timestamp(seconds):
        hrs, rem = divmod(seconds, 3600)
        mins, secs = divmod(rem, 60)
        millis = int((secs - int(secs)) * 1000)
        return f"{int(hrs):02}:{int(mins):02}:{int(secs):02},{millis:03}"

    with open(srt_output, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"], start=1):
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"].strip()
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    return srt_output

def create_offset_video(ref_video, offset_duration, resolution="1280x720", output="blank_with_audio.mp4"):
    """
        Creates a blank black video with audio extracted from the start of the reference video.

        Parameters:
            ref_video (str): Path to the reference video to extract audio from.
            offset_duration (float): Duration of the blank segment to create.
            resolution (str): Resolution of the blank video (default "1280x720").
            output (str): Path to save the output blank video with audio.
        """
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
    """
       Re-encodes a video to standard resolution, frame rate, and audio settings.

       Parameters:
           video_path (str): Path to input video.
           output_path (str): Path to save the re-encoded output.
       """
    subprocess.run([
        'ffmpeg', '-y',
        '-i', video_path,
        '-vf', 'scale=1280:720,fps=25',
        '-ar', '44100', '-ac', '2',
        '-c:v', 'libx264', '-c:a', 'aac', '-b:a', '192k',
        output_path
    ], check=True)

def concat_videos(video1, video2, output):
    """
        Concatenates two video files into one output video.

        Parameters:
            video1 (str): Path to the first video.
            video2 (str): Path to the second video.
            output (str): Path to save the concatenated video.
        """
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

def auto_fix_offset(video_a, video_b, output="final.mp4"):
    """
        Automatically synchronizes two videos by adding blank padding to the shorter one.

        Parameters:
            video_a (str): Path to the first video.
            video_b (str): Path to the second video.
            output (str): Path to save the synchronized output video.
        """
    a1 = get_audio_duration(video_a)
    a2 = get_audio_duration(video_b)

    if abs(a1 - a2) < 0.1:
        print("[INFO] No sync adjustment needed.")
        subprocess.run(['cp', video_a, output])
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

def burn_subtitles_into_video(video_input, srt_file, video_output="video_with_subtitles.mp4"):
    subprocess.run([
        'ffmpeg', '-y',
        '-i', video_input,
        '-vf', f"subtitles={srt_file}",
        '-c:a', 'copy',
        video_output
    ], check=True)

auto_fix_offset("src1 (2).mp4", "src2 (1).mp4", output="final.mp4")

extract_audio_for_whisper("final.mp4", output="final_audio.wav")

srt_file = transcribe_audio_to_srt("final_audio.wav", srt_output="subtitles.srt")

burn_subtitles_into_video("final.mp4", srt_file, video_output="final_with_subtitles.mp4")
