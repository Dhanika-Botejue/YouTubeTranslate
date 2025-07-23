from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from functools import wraps
from gtts import gTTS
import os
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
import requests
import subprocess
import sqlite3
import sys
import whisper
import yt_dlp

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

transcript_details = {}

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function

def video_id_extractor(video_link):
    start = video_link.find("?") + 3
    end = video_link.find("&")
    video_id = video_link[start:end]
    if end == -1: # no '&' found
        video_id += video_link[-1]
    return video_id
    """
    Tested video links:
    https://www.youtube.com/watch?v=3xaVX0cluDo&ab_channel=Kombina
    https://www.youtube.com/watch?v=2Gvc-_TW5eY&ab_channel=DonsonXie
    https://www.youtube.com/watch?v=p_QT8C26W_w
    https://www.youtube.com/watch?v=EZcX0jkZ_JQ&list=RDcewNznnMpqU&index=5
    """
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

        # SQLite
        video_info = [session["user_id"], output_file]

        connection = sqlite3.connect("app.db")
        cursor = connection.cursor()
        rows = cursor.execute("""
            INSERT INTO video (user_id, video_dst)
            VALUES (?, ?)
        """, video_info)
        
        connection.commit()
        connection.close()

    except subprocess.CalledProcessError as e:
        sys.exit(f"Error: {e}")
    
    # Cleanup files
    if os.path.exists("temp_video.mp4"):
        os.remove("temp_video.mp4")
    os.remove(audio_file)


# ROUTES START FROM HERE
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        return render_template("index.html")
    else:
        # Get form submission elements
        video_link = request.form.get("yt_link")
        source = request.form.get("source")
        target = request.form.get("target")
        video_dst = request.form.get("dst")
        
        # Configure video path for download_and_replace audio function
        video_path = f"static/{video_dst}.mp4"
        # Configure video dst for render template
        video_dst = f"{video_dst}.mp4"


        video_id = video_id_extractor(video_link)
        get_video(video_id)

        auto_transcribe(source, target)

        create_audio(target, "combined.mp3")

        download_and_replace_audio(video_id, "combined.mp3", video_path)

        return render_template("video.html", video_dst=video_dst)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        user_info = [username, password]
        
        # SQLite
        
        connection = sqlite3.connect("app.db")
        cursor = connection.cursor()
        try:
            cursor.execute("""
                INSERT INTO user (username, password) VALUES(?, ?)""", user_info
            )
        except sqlite3.IntegrityError:
            connection.close()
            print("username already in use")
            msg = "username already in use"
            return render_template("register.html", msg=msg)

        connection.commit()
        connection.close()

        return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()     # forget user_id

    if request.method == "GET":
        return render_template("login.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")

        # SQLite
        connection = sqlite3.connect("app.db")
        cursor = connection.cursor()
        rows = cursor.execute("""
            SELECT id, password
            FROM user
            WHERE username = ?
        """, (username,))
        
        check_user_details = rows.fetchone()
        connection.close()
        if check_user_details[1] == password:
            session["user_id"] = check_user_details[0]
            return redirect("/")
        
        # Invalid User
        return redirect("/login")

@app.route("/logout")
def logout():
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/select_video")
def select_video():
    # Get all created videos installed on user's device
    connection = sqlite3.connect("app.db")
    cursor = connection.cursor()
    rows = cursor.execute("""
        SELECT video_dst
        FROM video
        WHERE user_id = ?
    """, (session["user_id"],))
    
    check_user_videos = rows.fetchall()
    connection.close()
    
    proper_video_format = []
    for i in range(len(check_user_videos)):
        # Remove static/ from each video_dst as not needed in html file
        proper_video_format.append(list(check_user_videos[i])[0][7:])
    print(proper_video_format)
    

    return render_template("select_video.html", video_dsts=proper_video_format)