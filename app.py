from gtts import gTTS
import os
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
import requests
import subprocess
import sys
import whisper
import yt_dlp

def get_video(video_id):
    global transcript_details

    # Download audio
    ydl_opts = {
    'format': 'bestaudio[ext=m4a]',
    'outtmpl': 'temp_audio.mp3',
    'quiet': True
    }

    print("Downloading...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://youtu.be/{video_id}"])
    except yt_dlp.utils.DownloadError:
        sys.exit("Invalid Youtube video id")

    audio_file = "temp_audio.mp3"

    # Speech to text stuff
    model = whisper.load_model("small").cuda()

    print("Transcribing audio...")

    result = model.transcribe(audio_file, word_timestamps=True, fp16=True)
    for segment in result["segments"]:
        start = round(float(segment["start"]), 2)
        duration = round((float(segment["end"]) - start), 2)
        words = segment["text"].strip()

        # Do not create empty caption when person not talking for long time
        if words == "" or duration == 0.0:
            continue

        info = [words, duration]
        transcript_details[start] = info
        #print(words, timing)
        #print(f"{round(segment['start'], 2)}s \n{segment['text']}")
    
    os.remove("temp_audio.mp3")
    

def translate(text, target_lang='es', source_lang='en'):
    try:
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={
                "q": text,
                "langpair": f"{source_lang}|{target_lang}",
                "de": "akinahd1@gmail.com",
            }
        )
        return response.json()['responseData']['translatedText']
    except Exception as e:
        return f"Translation error: {str(e)}"

def auto_transcribe(source, target):
    global transcript_details

    for key in transcript_details:
        transcript_details[key].append(translate(transcript_details[key][0], target, source))

def trim_silence(audio):
    """Remove leading/trailing silence below threshold (in dBFS)"""
    start_trim = detect_leading_silence(audio, silence_threshold=-40)
    end_trim = detect_leading_silence(audio.reverse(), silence_threshold=-40)
    return audio[start_trim:len(audio)-end_trim]

def create_audio(target_lang, export_location):
    global transcript_details

    full_audio = AudioSegment.empty()

    previous_end = 0

    temp_file = "output.mp3"

    for key in transcript_details:
        # Add silence between clips for speaker's pauses (in milliseconds)
        full_audio += AudioSegment.silent(duration=((key - previous_end) * 1000))

        tts = gTTS(text=transcript_details[key][2], lang=target_lang)
        tts.save(temp_file)

        # Match translation clip timing with original timing (adjust speed)
        clip = trim_silence(AudioSegment.from_mp3(temp_file))
        original_duration = transcript_details[key][1]
        new_duration = clip.duration_seconds

        boost_factor = new_duration / original_duration
        
        clip = clip._spawn(
            clip.raw_data,
            overrides={"frame_rate" : int(clip.frame_rate * boost_factor)}
        )

        full_audio += clip

        # Save end of clip time
        previous_end = (transcript_details[key][1] + key)

        os.remove(temp_file)


    full_audio.export(export_location, format="mp3")

def download_and_replace_audio(video_id, audio_file, output_file):
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    
    try:
        # Step 1: Download video-only using yt-dlp
        print("Downloading video (no audio)...")
        subprocess.run([
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]",
            "--merge-output-format", "mp4",
            "-o", "temp_video.mp4",
            youtube_url
        ], check=True)

        # Step 2: Merge with local audio using FFmpeg
        print("Merging your audio...")
        subprocess.run([
            "ffmpeg",
            "-i", "temp_video.mp4",  # Downloaded video
            "-i", audio_file,        # Your audio file
            "-c:v", "copy",          # Preserve video quality
            "-c:a", "aac",           # Encode audio to AAC (or "libmp3lame" for MP3)
            "-map", "0:v:0",         # Use video stream
            "-map", "1:a:0",         # Use audio stream
            "-shortest",             # Match shortest duration
            output_file
        ], check=True)

        print(f"Success! Output saved to: {output_file}")

    except subprocess.CalledProcessError as e:
        sys.exit(f"Error: {e}")
    
    # Cleanup files
    if os.path.exists("temp_video.mp4"):
        os.remove("temp_video.mp4")
    os.remove(audio_file)


transcript_details = {}
video_id = input("Video ID: ")
get_video(video_id)

# Must put correct 'language code' e.g. Spanish is es and English is en
source = input("Source (original) language: ")
target = input("Language to translate to: ")

print("Translating...")
auto_transcribe(source, target)

print("Creating audio file...")

create_audio(target, "combined.mp3")

download_and_replace_audio(video_id, "combined.mp3", "final.mp4")
print("Enjoy!")
#print(transcript_details)


