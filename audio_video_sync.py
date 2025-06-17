import subprocess
import os

def create_blank_video_with_slides_audio(slides_video, duration=9, resolution="1280x720", output="blank_fixed.mp4"):
    subprocess.run([
        'ffmpeg', '-y',
        '-i', slides_video,
        '-t', str(duration),
        '-vn', '-ar', '44100', '-ac', '2', '-b:a', '192k', '-acodec', 'aac',
        'slides_audio.aac'
    ], check=True)

    subprocess.run([
        'ffmpeg', '-y',
        '-f', 'lavfi', '-i', f'color=black:s={resolution}:d={duration}',
        '-i', 'slides_audio.aac',
        '-vf', f'scale={resolution},fps=25',
        '-ar', '44100', '-ac', '1',
        '-c:v', 'libx264', '-c:a', 'aac',
        '-shortest', output
    ], check=True)

    os.remove("slides_audio.aac")

def reencode_presenter(presenter_video, output="presenter_fixed.mp4"):
    subprocess.run([
        'ffmpeg', '-y',
        '-i', presenter_video,
        '-vf', 'scale=1280:720,fps=25',
        '-ar', '44100',
        '-ac', '1',
        '-c:v', 'libx264', '-c:a', 'aac',
        output
    ], check=True)

def concat_fixed_videos(blank, presenter, output):
    with open("concat_list.txt", "w") as f:
        f.write(f"file '{os.path.abspath(blank)}'\n")
        f.write(f"file '{os.path.abspath(presenter)}'\n")

    subprocess.run([
        'ffmpeg', '-y',
        '-f', 'concat', '-safe', '0',
        '-i', 'concat_list.txt',
        '-c', 'copy',
        output
    ], check=True)

    os.remove("concat_list.txt")

def pad_presenter_with_slides_audio(slides_video, presenter_video, output_presenter, duration=9):
    print("[INFO] Creating black video with slides audio...")
    create_blank_video_with_slides_audio(slides_video, duration, output="blank_fixed.mp4")

    print("[INFO] Re-encoding presenter video...")
    reencode_presenter(presenter_video, output="presenter_fixed.mp4")

    print("[INFO] Concatenating both parts...")
    concat_fixed_videos("blank_fixed.mp4", "presenter_fixed.mp4", output_presenter)

    os.remove("blank_fixed.mp4")
    os.remove("presenter_fixed.mp4")

    print(f"[✅ DONE] Output written to: {output_presenter}")

pad_presenter_with_slides_audio(
    slides_video="desync-presentation.mp4",
    presenter_video="desync-presenter.mp4",
    output_presenter="presenter-sync_worked.mp4",
    duration=9
)
