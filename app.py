import os
import requests
import sys
import whisper
import yt_dlp

def get_video():
    global transcript_details
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

        # Do not create empty caption when person not talking for long time
        if words == "" or duration == 0.0:
            continue

        info = [words, duration]
        transcript_details[start] = info
        #print(words, timing)
        #print(f"{round(segment['start'], 2)}s \n{segment['text']}")
    os.remove(audio_file)

def translate(text, target_lang='es', source_lang='en'):
    try:
        response = requests.get(
            "https://api.mymemory.translated.net/get",
            params={
                "q": text,
                "langpair": f"{source_lang}|{target_lang}",
                "de": "dhanikabotejue@gmail.com",
            }
        )
        return response.json()['responseData']['translatedText']
    except Exception as e:
        return f"Translation error: {str(e)}"


transcript_details = {}
get_video()
# Must put correct 'language code' e.g. Spanish is es and English is en
source = input("Language to translate from: ")
target = input("Language to translate to: ")

print("Translating...")

for key in transcript_details:
    transcript_details[key].append(translate(transcript_details[key][0], target, source))

print(transcript_details)

