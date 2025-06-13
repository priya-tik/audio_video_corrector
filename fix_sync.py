import subprocess
import os

def shift_audio(input_video, output_video, delay_seconds):

    # Temporary files
    audio_file = "recorded_videos/temp_extracted_audio.mp4"
    shifted_audio = "temp_shifted_audio.mp4"

    # Extract audio from input video
    print("Extracting audio...")
    subprocess.run([
        "ffmpeg", "-y", "-i", input_video,
        "-vn", "-acodec", "copy",
        audio_file
    ], check=True)

    if delay_seconds < 0:
        # Advance audio: trim from start
        start_trim = abs(delay_seconds)
        print(f"Advancing audio by {start_trim} seconds (trimming start)...")
        subprocess.run([
            "ffmpeg", "-y", "-i", audio_file,
            "-ss", str(start_trim),
            "-c", "copy",
            shifted_audio
        ], check=True)
    else:

        print(f"Delaying audio by {delay_seconds} seconds (adding silence)...")
        silence_file = "temp_silence.wav"

        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t", str(delay_seconds),
            silence_file
        ], check=True)

        concat_file = "concat_list.txt"
        with open(concat_file, "w") as f:
            f.write(f"file '{silence_file}'\n")
            f.write(f"file '{audio_file}'\n")

        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            shifted_audio
        ], check=True)


        os.remove(silence_file)
        os.remove(concat_file)


    print("Merging shifted audio with original video...")
    subprocess.run([
        "ffmpeg", "-y", "-i", input_video,
        "-i", shifted_audio,
        "-c:v", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_video
    ], check=True)


    os.remove(audio_file)
    os.remove(shifted_audio)

    print(f"Sync fixed video saved as {output_video}")


if __name__ == "__main__":
        input_file = "audio_folder/output_audio_delayed.mp4"
        output_temp = "output_audio_temp.mp4"
        audio_delay = -100

        shift_audio(input_file, output_temp, audio_delay)
