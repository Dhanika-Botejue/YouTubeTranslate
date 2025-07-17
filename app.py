import os
import sys
import whisper
import yt_dlp

transcript_details = {}

video_id = input("Video ID: ")

# Download audio
ydl_opts = {
    'format': 'bestaudio[ext=m4a]',
    'outtmpl': 'temp_audio.m4a',
    'quiet': True
}

print("Downloading...")

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([f"https://youtu.be/{video_id}"])

audio_file = "temp_audio.m4a"

# Speech to text stuff
model = whisper.load_model("small").cuda()

print("Transcribing audio...")

result = model.transcribe(audio_file, word_timestamps=True, fp16=True)
for segment in result["segments"]:
    start = round(float(segment["start"]), 2)
    duration = round((float(segment["end"]) - start), 2)
    words = segment["text"].strip()

    info = [words, duration]
    transcript_details[start] = info
    #print(words, timing)
    #print(f"{round(segment['start'], 2)}s \n{segment['text']}")


print(transcript_details)

os.remove(audio_file)