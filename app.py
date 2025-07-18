from gtts import gTTS
import os
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
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

def create_audio(target_lang):
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


    full_audio.export("combined.mp3", format="mp3")


transcript_details = {}
get_video()

# Must put correct 'language code' e.g. Spanish is es and English is en
source = input("Source (original) language: ")
target = input("Language to translate to: ")

print("Translating...")
auto_transcribe(source, target)

print("Creating audio file...")
create_audio(target)

print("Enjoy!")
#print(transcript_details)


