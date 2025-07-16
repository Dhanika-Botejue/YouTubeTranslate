import sys
import whisper
import youtube_transcript_api
import yt_dlp

ytt_api = youtube_transcript_api.YouTubeTranscriptApi()
transcript_details = {}
try:
    # Use youtube subtitles
    video_id = input("Video ID: ")
    fetched_transcript = ytt_api.fetch(video_id)

    for snippet in fetched_transcript:
        transcript_details[round(snippet.start, 2)] = snippet.text.strip()
        #print(snippet.text, snippet.start)

except youtube_transcript_api.TranscriptsDisabled:
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
    model = whisper.load_model("small").to("cuda")
    
    print("Transcribing audio...")
    
    result = model.transcribe(audio_file, word_timestamps=True)
    for segment in result["segments"]:
        timing = round(segment["start"], 2)
        words = segment["text"]
        
        transcript_details[float(timing)] = words
        #print(words, timing)
        #print(f"{round(segment['start'], 2)}s \n{segment['text']}")

except youtube_transcript_api.VideoUnavailable:
    sys.exit("Error: Invalid video.")

except Exception as e:
    sys.exit(f"Unexpected error: {e}")


print(transcript_details)