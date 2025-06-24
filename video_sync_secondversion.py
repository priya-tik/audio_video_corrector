import subprocess
import os

def get_video_duration(video_path):
    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return float(result.stdout)

def extract_audio(slides_video, output_audio="presentation_audio.aac"):
    subprocess.run([
        'ffmpeg', '-y',
        '-i', slides_video,
        '-vn',
        '-acodec', 'aac',
        '-ar', '44100', '-ac', '2', '-b:a', '192k',
        output_audio
    ], check=True)

def create_black_video(duration, resolution="1280x720", output="black.mp4"):
    subprocess.run([
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', f"color=black:s={resolution}:d={duration}",
        '-r', '25',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        output
    ], check=True)

def make_silent_presenter(presenter_video, output="presenter_silent.mp4"):
    subprocess.run([
        'ffmpeg', '-y',
        '-fflags', '+genpts',
        '-i', presenter_video,
        '-an',
        '-vsync', 'cfr',
        '-r', '25',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        output
    ], check=True)

def pad_presenter_video(slides_video, presenter_video, output="presenter_padded.mp4"):

    extract_audio(slides_video, output_audio="presentation_audio.aac")

    slides_duration = get_video_duration(slides_video)
    presenter_duration = get_video_duration(presenter_video)

    offset = max(0, slides_duration - presenter_duration)

    create_black_video(duration=offset, output="black.mp4")

    make_silent_presenter(presenter_video, output="presenter_silent.mp4")

    with open("concat_list.txt", "w") as f:
        f.write(f"file '{os.path.abspath('black.mp4')}'\n")
        f.write(f"file '{os.path.abspath('presenter_silent.mp4')}'\n")

    subprocess.run([
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0',
        '-i', 'concat_list.txt',
        '-vsync', 'cfr',
        '-r', '25',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        'temp_no_audio.mp4'
    ], check=True)

    subprocess.run([
        'ffmpeg', '-y',
        '-fflags', '+genpts',
        '-i', 'temp_no_audio.mp4',
        '-i', 'presentation_audio.aac',
        '-c:v', 'copy',
        '-c:a', 'aac',
        output
    ], check=True)

    # Step 8: Cleanup
    for file in [
        "black.mp4", "presenter_silent.mp4",
        "concat_list.txt", "temp_no_audio.mp4",
        "presentation_audio.aac"
    ]:
        try:
            os.remove(file)
        except FileNotFoundError:
            pass

pad_presenter_video(
    slides_video="desync-presentation.mp4",
    presenter_video="desync-presenter.mp4",
    output="presenter_synced.mp4"
)