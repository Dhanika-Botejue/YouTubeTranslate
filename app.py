import sys
import whisper
import youtube_transcript_api
import yt_dlp

ytt_api = youtube_transcript_api.YouTubeTranscriptApi()

try:
    # Use youtube subtitles
    video_id = input("Video ID: ")
    fetched_transcript = ytt_api.fetch(video_id)

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
        print(f"{round(segment['start'], 2)}s \n{segment['text']}")
    sys.exit()

except youtube_transcript_api.VideoUnavailable:
    sys.exit("Error: Invalid video.")

except Exception as e:
    sys.exit(f"Unexpected error: {e}")



for snippet in fetched_transcript:
        print(snippet.text, snippet.start)