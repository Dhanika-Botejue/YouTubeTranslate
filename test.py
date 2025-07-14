import youtube_transcript_api

ytt_api = youtube_transcript_api.YouTubeTranscriptApi()

try:
    fetched_transcript = ytt_api.fetch(input("Video ID: "))
    for snippet in fetched_transcript:
        print(snippet.text, snippet.start)
except youtube_transcript_api.TranscriptsDisabled:
    print("Error: Subtitles are disabled for this video.")
except Exception as e:
    print(f"Unexpected error: {e}")

